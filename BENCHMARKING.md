# Benchmarking & Profiling

How to measure perf in this project, before/after a change, and across
language rewrites.

## TL;DR — workflow for a buffering change

```bash
# 1. Baseline before any changes
mkdir -p bench-results
make bench LABEL=before-buffering
git add -A && git commit -m "wip: bench baseline"

# 2. Make your change (e.g., buffer per-frame writes)
# ... edit code ...

# 3. Re-bench
make bench LABEL=after-buffering

# 4. Compare
make compare BEFORE=bench-results/before-buffering.json \
             AFTER=bench-results/after-buffering.json
```

You should see **`writes/frame`** drop dramatically (thousands → ~1) and
**`fps`** go up. `cells/s` should also rise because the renderer is no longer
syscall-bound.

## What gets measured

The bench harness swaps in two stand-ins:

- `FakeLLMClient` — yields a fixed number of characters per request at a
  fixed rate, so results don't depend on network or LLM speed.
- `HeadlessRenderer` — subclass of the real `Renderer` with fixed
  dimensions; uses real ANSI escape composition so the byte count is real,
  but skips clear/cursor calls. Paired with a `CountingStdout` redirect
  that counts `write()` calls and bytes instead of emitting to a terminal.

Everything else — supervisor, column writers, fade math, animation,
themes — runs unchanged. So perf changes you make to those modules show up
honestly in the metrics.

## Metrics emitted (see `BenchResults` in `bench.py`)

| Metric                  | Meaning                                         | Buffering should… |
|-------------------------|-------------------------------------------------|-------------------|
| `fps`                   | Full frame redraws/sec from the fade loop       | ↑ go up           |
| `cells_per_second`      | `draw_cell` calls/sec                           | ↑ go up           |
| `bytes_per_second`      | UTF-8 bytes/sec going to stdout                 | ≈ stay same       |
| `write_calls_per_frame` | `print(...)` (or equiv) calls per rendered frame| ↓ drop hard       |
| `write_calls_per_second`| Same, per second                                | ↓ drop hard       |
| `avg_bytes_per_write`   | Bytes per write call                            | ↑ go way up       |
| `cpu_time_s`            | User+sys CPU time                               | ↓ go down         |
| `rss_max_mb`            | Peak RSS                                        | ≈ stay same       |

These are intentionally language-neutral. A Rust/Go rewrite emits the same
JSON schema → `bench_compare.py` works across implementations.

## Profiling tools

The bench gives you aggregate metrics. To see *where* time is spent, use
one of these — none requires modifying the app.

### py-spy (recommended for sampling profiling)

It's a Rust binary, not a Python dep:

```bash
brew install py-spy

# Record a 20-second flamegraph while a bench runs
py-spy record -o flame.svg -d 20 -- \
  uv run python -m matrix_tui --bench 20 -c 80 --animation-preset intense

# Or attach to a running PID (live)
py-spy top --pid <pid>
```

### pyinstrument (call-tree, Python dev dep)

```bash
make profile           # writes pyinstrument.html
# or directly:
uv run pyinstrument -o report.html -r html \
    -m matrix_tui --bench 10 -c 80 --animation-preset intense
```

Open `pyinstrument.html` in a browser — the call tree shows where wall
time is going, function-by-function.

### cProfile (built-in, raw stats)

```bash
uv run python -m cProfile -o profile.out -m matrix_tui --bench 10 -c 80
uv run python -c "import pstats; p=pstats.Stats('profile.out'); p.sort_stats('cumulative').print_stats(30)"
```

## CLI flags reference

```
--bench SECONDS          Run bench for N seconds, then exit
--bench-output PATH      Write JSON results
--bench-label STRING     Embedded in JSON for later identification
--bench-tps FLOAT        Tokens/sec per fake stream (default: 50)
--bench-tokens INT       Tokens per fake response (default: 200)
--bench-width INT        Simulated terminal width (default: 120)
--bench-height INT       Simulated terminal height (default: 40)
```

Bench mode also respects existing flags: `--theme`, `--animation-preset`,
`--density`, `--flash-prob`, `--mutation-prob`, `--line`, `--columns`, etc.
This means you can compare the same code under different configs (e.g.,
"how does flash-prob affect cells/sec?").

## Designing changes for cross-language portability

The current module split is the contract a Rust/Go rewrite would honor:

| Module             | Responsibility                       | Cross-lang notes |
|--------------------|--------------------------------------|------------------|
| `llm.py`           | Async token producer                 | Trait/interface  |
| `renderer.py`      | Cell-level terminal output           | Trait/interface  |
| `vertical_column.py` | Per-column state + fade math       | Pure compute     |
| `supervisor.py`    | Concurrency, frame loop              | Goroutines/async |
| `fade_math.py`     | Color interpolation                  | Pure compute     |
| `themes.py`, `image_mode.py`, `animation.py` | Configuration | Plain data |

When rewriting:
1. Keep the bench JSON schema identical.
2. Keep `prompts.yml` and theme JSON formats identical.
3. The supervisor's "60Hz frame loop redraws every column" loop is the
   thing being measured — make sure your rewrite has the equivalent.

## Caveats

- **Init cost is included in metrics.** `fill_background` writes
  `width × height` cells once at start. For a 10s bench this dilutes
  steady-state by ~1–5%, depending on terminal size. Run longer benches
  (30s+) for sensitive comparisons.
- **CountingStdout counts UTF-8 bytes, not characters.** Wide CJK chars
  count as 3 bytes each, ASCII as 1. This matches what the kernel sees.
- **Headless mode skips the real terminal,** so you don't measure the
  user's terminal-emulator latency. That's a feature: it isolates *your*
  code from the user's setup.
- **Frame counter requires `_frame_count` on the supervisor.** If you
  refactor the fade loop, keep that increment.
