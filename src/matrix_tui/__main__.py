"""Main entry point for Matrix Rain TUI."""

import argparse
import asyncio
import sys

from .animation import AnimationConfig, get_animation_preset
from .config import load_config
from .image_mode import ImageModeController, is_pillow_available
from .llm import LLMClient
from .renderer import Renderer
from .supervisor import StreamSupervisor
from .themes import get_theme, list_themes, load_custom_theme


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Matrix Rain TUI - AI streaming terminal interface"
    )
    parser.add_argument(
        "--columns",
        "-c",
        type=int,
        default=1,
        help="Number of parallel columns to run (default: 1)",
    )
    parser.add_argument(
        "--prompts",
        "-p",
        type=str,
        default="prompts.yml",
        help="Path to prompts YAML file (default: prompts.yml)",
    )
    parser.add_argument(
        "--include-langs",
        "-i",
        type=str,
        default=None,
        help="Comma-separated list of language codes to include (e.g., 'en,zh,ja'). If not provided, all languages are included.",
    )
    parser.add_argument(
        "--exclude-langs",
        "-e",
        type=str,
        default=None,
        help="Comma-separated list of language codes to exclude (e.g., 'en,zh'). If not provided, no languages are excluded.",
    )
    parser.add_argument(
        "--line",
        "-l",
        type=str,
        choices=["linear", "quadratic", "exponential"],
        default="linear",
        help="Fade curve type for character trailing effect (default: linear)",
    )
    parser.add_argument(
        "--test-connection",
        "-T",
        action="store_true",
        help="Test connection to LLM server and exit",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=180,
        help="Timeout in seconds after which the program will exit (default: 180)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output for debugging",
    )

    # Theme arguments
    parser.add_argument(
        "--theme",
        type=str,
        default="nvidia",
        help="Color theme name (classic, nvidia, amber, cyan, hacker, purple, fire, ice, blood, gold)",
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List available themes and exit",
    )
    parser.add_argument(
        "--custom-theme",
        type=str,
        default=None,
        help="Path to custom theme JSON file",
    )

    # Animation arguments
    parser.add_argument(
        "--animation-preset",
        type=str,
        choices=["calm", "default", "intense", "chaos"],
        default=None,
        help="Animation preset (calm, default, intense, chaos)",
    )
    parser.add_argument(
        "--fall-speed",
        type=str,
        default=None,
        help="Speed range 'min,max' (e.g., '0.5,2.0')",
    )
    parser.add_argument(
        "--trail-length",
        type=str,
        default=None,
        help="Trail length range 'min,max' (e.g., '10,30')",
    )
    parser.add_argument(
        "--density",
        type=float,
        default=None,
        help="Column density 0.0-1.0 (fraction of columns that are active)",
    )
    parser.add_argument(
        "--flash-prob",
        type=float,
        default=None,
        help="Flash probability 0.0-1.0 (chance of flash effect per frame)",
    )
    parser.add_argument(
        "--mutation-prob",
        type=float,
        default=None,
        help="Character mutation probability 0.0-1.0",
    )

    # Benchmark arguments
    parser.add_argument(
        "--bench",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Run benchmark for N seconds with FakeLLMClient and HeadlessRenderer, then exit",
    )
    parser.add_argument(
        "--bench-output",
        type=str,
        default=None,
        metavar="PATH",
        help="Write benchmark results JSON to this path",
    )
    parser.add_argument(
        "--bench-label",
        type=str,
        default=None,
        help="Free-form label embedded in bench results (e.g., 'before-buffering')",
    )
    parser.add_argument(
        "--bench-tps",
        type=float,
        default=50.0,
        help="Tokens per second per fake stream (default: 50)",
    )
    parser.add_argument(
        "--bench-tokens",
        type=int,
        default=200,
        help="Tokens per fake response (default: 200)",
    )
    parser.add_argument(
        "--bench-width",
        type=int,
        default=120,
        help="Simulated terminal width for bench (default: 120)",
    )
    parser.add_argument(
        "--bench-height",
        type=int,
        default=40,
        help="Simulated terminal height for bench (default: 40)",
    )

    # Image mode arguments
    parser.add_argument(
        "--image",
        "-I",
        type=str,
        default=None,
        help="Path to image file for visualization mode",
    )
    parser.add_argument(
        "--image-threshold",
        type=float,
        default=0.2,
        help="Minimum brightness for column activity (default: 0.2)",
    )
    parser.add_argument(
        "--image-invert",
        action="store_true",
        help="Invert image (dark areas become bright)",
    )
    return parser.parse_args()


async def main():
    """Main entry point for the Matrix Rain TUI application."""
    args = parse_args()

    # Handle --list-themes
    if args.list_themes:
        themes = list_themes()
        print("Available themes:")
        for name, theme in sorted(themes.items()):
            print(f"  {name:12} - {theme.description}")
        return 0

    # Validate columns argument
    if args.columns < 1:
        print("Error: --columns must be >= 1", file=sys.stderr)
        return 1

    # Load theme
    theme = None
    if args.custom_theme:
        try:
            theme = load_custom_theme(args.custom_theme)
        except Exception as e:
            print(f"Error loading custom theme: {e}", file=sys.stderr)
            return 1
    else:
        theme = get_theme(args.theme)
        if theme is None:
            print(f"Error: Unknown theme '{args.theme}'", file=sys.stderr)
            print("Use --list-themes to see available themes", file=sys.stderr)
            return 1

    # Build animation config
    animation_config = None
    if args.animation_preset or any(
        [
            args.fall_speed,
            args.trail_length,
            args.density,
            args.flash_prob,
            args.mutation_prob,
        ]
    ):
        # Start with preset or default
        if args.animation_preset:
            animation_config = get_animation_preset(args.animation_preset)
            if animation_config is None:
                print(
                    f"Error: Unknown animation preset '{args.animation_preset}'",
                    file=sys.stderr,
                )
                return 1
            # Create a copy so we can modify it
            animation_config = AnimationConfig(
                min_fall_speed=animation_config.min_fall_speed,
                max_fall_speed=animation_config.max_fall_speed,
                min_trail_length=animation_config.min_trail_length,
                max_trail_length=animation_config.max_trail_length,
                min_start_delay=animation_config.min_start_delay,
                max_start_delay=animation_config.max_start_delay,
                flash_probability=animation_config.flash_probability,
                mutation_probability=animation_config.mutation_probability,
                column_density=animation_config.column_density,
            )
        else:
            animation_config = AnimationConfig()

        # Apply individual overrides
        if args.fall_speed:
            try:
                parts = args.fall_speed.split(",")
                animation_config.min_fall_speed = float(parts[0])
                animation_config.max_fall_speed = float(parts[1])
            except (ValueError, IndexError):
                print(
                    "Error: --fall-speed must be 'min,max' (e.g., '0.5,2.0')",
                    file=sys.stderr,
                )
                return 1

        if args.trail_length:
            try:
                parts = args.trail_length.split(",")
                animation_config.min_trail_length = int(parts[0])
                animation_config.max_trail_length = int(parts[1])
            except (ValueError, IndexError):
                print(
                    "Error: --trail-length must be 'min,max' (e.g., '10,30')",
                    file=sys.stderr,
                )
                return 1

        if args.density is not None:
            if not 0.0 <= args.density <= 1.0:
                print("Error: --density must be between 0.0 and 1.0", file=sys.stderr)
                return 1
            animation_config.column_density = args.density

        if args.flash_prob is not None:
            if not 0.0 <= args.flash_prob <= 1.0:
                print(
                    "Error: --flash-prob must be between 0.0 and 1.0", file=sys.stderr
                )
                return 1
            animation_config.flash_probability = args.flash_prob

        if args.mutation_prob is not None:
            if not 0.0 <= args.mutation_prob <= 1.0:
                print(
                    "Error: --mutation-prob must be between 0.0 and 1.0",
                    file=sys.stderr,
                )
                return 1
            animation_config.mutation_probability = args.mutation_prob

    # Bench mode: skip real terminal/LLM and run the harness instead.
    if args.bench is not None:
        from .bench import run_bench

        # Parse language filtering for bench too
        bench_include = (
            [lang.strip() for lang in args.include_langs.split(",")]
            if args.include_langs
            else None
        )
        bench_exclude = (
            [lang.strip() for lang in args.exclude_langs.split(",")]
            if args.exclude_langs
            else None
        )
        await run_bench(
            duration_s=args.bench,
            columns=args.columns,
            width=args.bench_width,
            height=args.bench_height,
            tokens_per_second=args.bench_tps,
            tokens_per_response=args.bench_tokens,
            theme=theme,
            animation_config=animation_config,
            fade_curve=args.line,
            prompts_file=args.prompts,
            include_langs=bench_include,
            exclude_langs=bench_exclude,
            output_path=args.bench_output,
            label=args.bench_label,
        )
        return 0

    renderer = Renderer(theme=theme)
    supervisor = None

    try:
        # Initialize renderer
        renderer.init()

        # Validate that requested columns don't exceed terminal width
        if args.columns > renderer.width:
            print(
                f"Error: Requested {args.columns} columns exceeds terminal width of {renderer.width}",
                file=sys.stderr,
            )
            return 1

        # Load configuration
        cfg = load_config(verbose=args.verbose)

        # Initialize LLM client
        client = LLMClient(cfg)

        # Test connection before starting
        connection_ok = await client.test_connection()
        if not connection_ok:
            print("Failed to connect to LLM server. Please check your configuration.")
            return 1

        # If test-connection flag is set, exit after testing
        if args.test_connection:
            return 0

        # Parse language filtering parameters
        include_langs = None
        exclude_langs = None

        if args.include_langs:
            include_langs = [lang.strip() for lang in args.include_langs.split(",")]

        if args.exclude_langs:
            exclude_langs = [lang.strip() for lang in args.exclude_langs.split(",")]

        # Initialize image mode controller if image path is provided
        image_controller = None
        if args.image:
            if not is_pillow_available():
                print(
                    "Error: Pillow is required for image mode. "
                    "Install with: pip install Pillow>=10.0.0",
                    file=sys.stderr,
                )
                return 1
            try:
                image_controller = ImageModeController(
                    args.image,
                    renderer.width,
                    renderer.height,
                    activity_threshold=args.image_threshold,
                    invert=args.image_invert,
                )
            except FileNotFoundError:
                print(f"Error: Image file not found: {args.image}", file=sys.stderr)
                return 1
            except Exception as e:
                print(f"Error loading image: {e}", file=sys.stderr)
                return 1

        # Initialize stream supervisor
        supervisor = StreamSupervisor(
            client,
            renderer,
            args.prompts,
            include_langs,
            exclude_langs,
            args.line,
            theme=theme,
            animation_config=animation_config,
            image_controller=image_controller,
        )

        # Start streaming with the specified number of columns
        try:
            await asyncio.wait_for(supervisor.start(args.columns), timeout=args.timeout)
        except asyncio.TimeoutError:
            print(f"\nTimeout reached ({args.timeout} seconds). Exiting...")
            return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up
        if supervisor:
            await supervisor.stop()
        # Always restore terminal state
        renderer.finalize()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
