# CLAUDE.md

Matrix-style TUI that visualizes high-throughput LLM token streams as falling
characters. Multiple concurrent OpenAI-compatible streams (default: a local
endpoint), one terminal column per stream, rendered with `blessed`.

## Run / dev

- `uv run python -m matrix_tui [-c N] [--theme X] [--animation-preset Y]`
- `uv run pytest` · `make black` · `make run`
- `.env` keys: `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`. Designed for
  local OpenAI-compatible servers (vLLM, llama.cpp, LM Studio, etc.).
- Currently developed against vLLM serving `nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4`
  (served as `nemotron-3-nano-omni`, `--max-num-seqs 16`). Reasoning model — both
  `delta.reasoning` and `delta.content` are forwarded to the rain. Full docker
  command in README "Example LLM endpoint" section.

## Module map (src/matrix_tui/)

- `__main__.py` — argparse CLI; constructs theme/animation/image controllers,
  initializes Renderer, runs StreamSupervisor with asyncio timeout.
- `supervisor.py` — `StreamSupervisor` orchestrates: spawns one
  `ColumnWriter` per active column, runs a continuous request generator that
  reuses columns as streams complete, plus a 60fps `_fade_renderer` task that
  re-paints every column every frame.
- `vertical_column.py` — `ColumnWriter` owns per-column character history,
  fade math, mutation, flash, brightness modulation. Also a legacy
  `SingleColumnWriter` (early phase, mostly redundant with ColumnWriter).
- `renderer.py` — `blessed.Terminal` wrapper. Per-cell `print(..., flush=True)`
  for every draw_cell. `fill_background` writes every cell individually.
- `themes.py` — 10 builtin themes + JSON loader. Just RGB triples for
  head/trail/background.
- `animation.py` — `AnimationConfig` (presets: calm/default/intense/chaos)
  and per-column `ColumnAnimationState` (fall_speed, trail_length,
  start_delay, flash_active). Mutation char set is half-width katakana + ASCII.
- `image_mode.py` — Pillow-based brightness map sized to terminal. Drives the
  "image emerges from rain" effect via per-cell brightness multipliers.
- `llm.py` — `AsyncOpenAI` client. Forwards `delta.reasoning` AND
  `delta.content` so reasoning models show their thinking tokens too.
  Hardcoded `max_tokens=200`, `verify=False`.
- `prompt_loader.py` — loads `prompts.yml`, supports include/exclude language
  filtering, has English fallback.
- `fade_math.py` — linear / quadratic / exponential fade curves.
- `config.py` — `.env` loader with multi-path search.

## Important gotchas / pitfalls

- **Test-mode branches in production code.** `ColumnWriter` and the renderer
  branch on `hasattr(renderer.draw_cell, "call_args_list")` to detect mocks.
  This is leaking test concerns into production. Prefer a proper `FakeRenderer`
  over Mock and delete the branches.
- **Rendering is per-character `print(flush=True)`.** Every cell draw is one
  flushed write; `fill_background` does this for every cell. The 60fps fade
  task redraws every char in every column. This is the dominant perf hit —
  switch to a single buffered write per frame.
- **Backward-compat aliases.** `ColumnWriter` exposes `row`, `last_pos`,
  `last_char` only for tests. Real state is `current_row` / `character_history`.
- **Resize handling exists but isn't wired.** `supervisor.on_resize()` and
  `ColumnWriter.on_resize()` are defined but no SIGWINCH handler installs them.
- **`SingleColumnWriter`** is legacy from early phases — `ColumnWriter` covers
  its behavior. Safe to delete once tests are updated.
- **`prompts.yml` is large** (~27KB, 9 languages × 20 prompts). Don't read it
  in full unless needed.
- **Image mode persists characters.** `_cleanup_old_characters` is a no-op in
  image mode (capped at 2× height) so the image stays visible.

## Benchmarking

See `BENCHMARKING.md` for the full workflow. Quick version:

- `make bench LABEL=foo` — runs `--bench 10` with FakeLLMClient +
  HeadlessRenderer, writes `bench-results/foo.json`.
- `make compare BEFORE=… AFTER=…` — diffs two result files.
- `bench.py` defines `FakeLLMClient`, `HeadlessRenderer`, `CountingStdout`,
  `BenchResults`. The JSON schema is the cross-language contract for any
  Rust/Go rewrite.
- Supervisor exposes `_frame_count` for fps measurement; if you refactor
  the fade loop, keep that increment.

## Testing notes

- `tests/test_basic.py`, `test_renderer*.py` use real `Terminal` — be aware
  some tests may be flaky in non-tty environments.
- Tests use `Mock` renderers heavily — see test-mode-branch gotcha above.
- `pytest-asyncio` is in `[dependency-groups]` but not in `[project.optional-dependencies]`.

## Conventions

- `black`, line length 88, target py3.11.
- No type checker configured; type hints are partial.
- All user-facing text is print-to-stdout (no logger).
