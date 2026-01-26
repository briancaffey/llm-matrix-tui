"""Main entry point for Matrix Rain TUI."""

import asyncio
import argparse
import sys
from .llm import LLMClient
from .config import load_config
from .renderer import Renderer
from .supervisor import StreamSupervisor


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
    return parser.parse_args()


async def main():
    """Main entry point for the Matrix Rain TUI application."""
    args = parse_args()

    # Validate columns argument
    if args.columns < 1:
        print("Error: --columns must be >= 1", file=sys.stderr)
        return 1

    renderer = Renderer()
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

        # Initialize stream supervisor
        supervisor = StreamSupervisor(
            client, renderer, args.prompts, include_langs, exclude_langs, args.line
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
