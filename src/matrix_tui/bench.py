"""Benchmarking infrastructure for matrix_tui.

Provides:
- FakeLLMClient: deterministic, network-free token producer for repeatable runs.
- HeadlessRenderer: subclass of Renderer that uses fixed dimensions and skips
  cursor/clear-screen calls. Paired with CountingStdout it composes the exact
  same ANSI bytes as production but writes nowhere — letting us measure
  rendering output cost without real terminal I/O.
- CountingStdout: stdout replacement that counts bytes and write() calls.
- BenchResults / run_bench: the harness itself.

Metrics reported are intentionally language-neutral so a future Rust/Go
rewrite can emit the same JSON schema and use the same comparison tooling.
"""

import asyncio
import json
import platform
import resource
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

from blessed import Terminal

from .renderer import Renderer
from .themes import ColorTheme


class CountingStdout:
    """sys.stdout replacement that counts bytes/calls instead of writing.

    Use as: ``sys.stdout = CountingStdout()`` during a bench, then restore.
    """

    def __init__(self) -> None:
        self.bytes_written: int = 0
        self.write_calls: int = 0

    def write(self, s: str) -> int:
        # Count UTF-8 bytes — what would actually go to the kernel.
        self.bytes_written += len(s.encode("utf-8", errors="replace"))
        self.write_calls += 1
        return len(s)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        # Some libraries probe this; return the real stdout fd as a courtesy.
        return sys.__stdout__.fileno()


class HeadlessRenderer(Renderer):
    """Renderer with fixed dimensions and no real terminal control.

    Composes identical ANSI escape sequences to the production Renderer so
    byte counts in CountingStdout reflect real-world output volume.
    """

    def __init__(
        self, theme: Optional[ColorTheme], width: int, height: int
    ) -> None:
        super().__init__(theme=theme)
        # Force ANSI generation regardless of whether stdout is a tty.
        self.term = Terminal(force_styling=True)
        self._fixed_width = width
        self._fixed_height = height
        self._cells_drawn: int = 0

    def init(self) -> None:
        # Skip clear/hide_cursor — those would touch the real terminal.
        self.current_x = 0
        self.current_y = 0
        self.height = self._fixed_height
        self.width = self._fixed_width
        # Still call fill_background so its (large) cost shows up in metrics.
        self.fill_background(self.background_color)

    def refresh_dims(self) -> None:
        self.height = self._fixed_height
        self.width = self._fixed_width

    def draw_cell(self, row, col, ch, fg_rgb, bg_rgb):
        self._cells_drawn += 1
        super().draw_cell(row, col, ch, fg_rgb, bg_rgb)

    def finalize(self) -> None:
        # No cursor to restore.
        pass


class FakeLLMClient:
    """Deterministic, network-free stand-in for LLMClient.

    Yields a fixed number of characters per response at a fixed rate, so
    benchmark runs don't depend on network or LLM throughput.
    """

    def __init__(
        self,
        tokens_per_second: float = 50.0,
        tokens_per_response: int = 200,
        char_set: str = (
            "ｦｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎ"
            "0123456789"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "@#$%^&*()_+-=[]{}|;:,.<>?"
        ),
    ) -> None:
        self.tokens_per_second = tokens_per_second
        self.tokens_per_response = tokens_per_response
        self.char_set = char_set
        self._req_id = 0

    async def test_connection(self) -> bool:
        return True

    async def stream_response(
        self,
        system: str,
        user: str,
        on_fragment: Callable[[str], Awaitable[None]],
        max_tokens: int = 200,
    ) -> None:
        delay = 1.0 / self.tokens_per_second if self.tokens_per_second > 0 else 0.0
        n = min(self.tokens_per_response, max_tokens)
        base = self._req_id
        self._req_id += 1
        for i in range(n):
            ch = self.char_set[(base + i) % len(self.char_set)]
            await on_fragment(ch)
            if delay > 0:
                await asyncio.sleep(delay)


@dataclass
class BenchResults:
    # Schema is the cross-language contract: any rewrite should emit this shape.
    duration_s: float
    columns_requested: int
    width: int
    height: int
    cells_drawn: int
    bytes_written: int
    write_calls: int
    frames: int
    fps: float
    cells_per_second: float
    bytes_per_second: float
    write_calls_per_second: float
    write_calls_per_frame: float
    avg_bytes_per_write: float
    cpu_time_s: float
    rss_max_mb: float
    config: Dict[str, Any]
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _max_rss_mb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS, kilobytes on Linux/BSD.
    if sys.platform == "darwin":
        return rss / 1024 / 1024
    return rss / 1024


def _cpu_time_s() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return ru.ru_utime + ru.ru_stime


async def run_bench(
    *,
    duration_s: float,
    columns: int,
    width: int,
    height: int,
    tokens_per_second: float,
    tokens_per_response: int,
    theme: ColorTheme,
    animation_config,
    fade_curve: str,
    prompts_file: str,
    include_langs,
    exclude_langs,
    output_path: Optional[str],
    label: Optional[str] = None,
) -> BenchResults:
    """Run a single bench and return structured results.

    Late-imports StreamSupervisor to avoid a circular import.
    """
    from .supervisor import StreamSupervisor  # local to avoid cycle

    renderer = HeadlessRenderer(theme=theme, width=width, height=height)
    client = FakeLLMClient(
        tokens_per_second=tokens_per_second,
        tokens_per_response=tokens_per_response,
    )

    real_stdout = sys.stdout
    counter = CountingStdout()

    cpu_start = _cpu_time_s()
    wall_start = time.monotonic()

    # Redirect AFTER any setup that might want real stdout. Renderer.init()
    # itself prints heavily, which is what we want to count.
    sys.stdout = counter
    supervisor: Optional[StreamSupervisor] = None
    try:
        renderer.init()
        supervisor = StreamSupervisor(
            client,
            renderer,
            prompts_file,
            include_langs,
            exclude_langs,
            fade_curve,
            theme=theme,
            animation_config=animation_config,
        )
        try:
            await asyncio.wait_for(
                supervisor.start(columns), timeout=duration_s
            )
        except asyncio.TimeoutError:
            pass  # expected — bench is bounded by duration
    finally:
        if supervisor is not None:
            await supervisor.stop()
        renderer.finalize()
        sys.stdout = real_stdout

    wall_elapsed = time.monotonic() - wall_start
    cpu_elapsed = _cpu_time_s() - cpu_start

    frames = getattr(supervisor, "_frame_count", 0) if supervisor else 0
    cells = getattr(renderer, "_cells_drawn", None)
    if cells is None:
        cells = 0  # not yet instrumented; stays 0 until renderer counter added

    results = BenchResults(
        duration_s=wall_elapsed,
        columns_requested=columns,
        width=width,
        height=height,
        cells_drawn=cells,
        bytes_written=counter.bytes_written,
        write_calls=counter.write_calls,
        frames=frames,
        fps=frames / wall_elapsed if wall_elapsed > 0 else 0.0,
        cells_per_second=cells / wall_elapsed if wall_elapsed > 0 else 0.0,
        bytes_per_second=counter.bytes_written / wall_elapsed
        if wall_elapsed > 0
        else 0.0,
        write_calls_per_second=counter.write_calls / wall_elapsed
        if wall_elapsed > 0
        else 0.0,
        write_calls_per_frame=counter.write_calls / frames if frames > 0 else 0.0,
        avg_bytes_per_write=counter.bytes_written / counter.write_calls
        if counter.write_calls > 0
        else 0.0,
        cpu_time_s=cpu_elapsed,
        rss_max_mb=_max_rss_mb(),
        config={
            "label": label,
            "tokens_per_second": tokens_per_second,
            "tokens_per_response": tokens_per_response,
            "fade_curve": fade_curve,
            "theme": theme.name,
            "animation_preset": getattr(animation_config, "_preset_name", None)
            if animation_config
            else None,
        },
        meta={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "timestamp": time.time(),
        },
    )

    if output_path:
        Path(output_path).write_text(json.dumps(results.to_dict(), indent=2))

    print_summary(results, output_path)
    return results


def print_summary(r: BenchResults, output_path: Optional[str]) -> None:
    print()
    print("=== Matrix TUI Benchmark ===")
    if r.config.get("label"):
        print(f"Label:              {r.config['label']}")
    print(f"Duration:           {r.duration_s:.2f} s")
    print(
        f"Terminal:           {r.width}x{r.height}, "
        f"{r.columns_requested} columns requested"
    )
    print(f"Frames rendered:    {r.frames}  ({r.fps:.1f} fps)")
    print(
        f"Cells drawn:        {r.cells_drawn:,}  "
        f"({r.cells_per_second:,.0f} /s)"
    )
    mb_per_s = r.bytes_per_second / 1024 / 1024
    print(
        f"stdout-equiv bytes: {r.bytes_written:,}  ({mb_per_s:.2f} MB/s)"
    )
    print(
        f"Write calls:        {r.write_calls:,}  "
        f"({r.write_calls_per_frame:,.1f} /frame, "
        f"{r.write_calls_per_second:,.0f} /s)"
    )
    print(f"Avg write size:     {r.avg_bytes_per_write:,.1f} bytes")
    print(f"CPU time:           {r.cpu_time_s:.2f} s")
    print(f"Max RSS:            {r.rss_max_mb:.1f} MB")
    if output_path:
        print(f"Wrote:              {output_path}")
    print()
