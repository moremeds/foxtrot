#!/usr/bin/env python3
"""
Foxtrot TUI Entry Point

Standalone script to run the Foxtrot Text User Interface.
This script provides command-line options and handles initialization.
"""

import argparse
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Foxtrot TUI - Text User Interface for Event-Driven Trading Platform"
    )

    parser.add_argument("--config", type=str, help="Path to configuration file")

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose logging"
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    parser.add_argument(
        "--theme",
        choices=["dark", "light", "high_contrast", "trading_green"],
        default="dark",
        help="TUI color theme (default: dark)",
    )

    parser.add_argument(
        "--adapter",
        type=str,
        help="Trading adapter to use (e.g., binance, ibrokers, crypto)"
    )

    parser.add_argument(
        "--paper-trading",
        action="store_true",
        help="Enable paper trading mode (no real money)"
    )

    parser.add_argument(
        "--fallback-gui", action="store_true", help="Fall back to GUI if TUI fails to start"
    )

    parser.add_argument("--version", action="version", version="Foxtrot TUI v0.1.0")

    return parser.parse_args()


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    import logging

    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("foxtrot_tui.log"), logging.StreamHandler()],
    )


def check_dependencies():
    """Check if all required dependencies are available."""
    missing_deps = []

    try:
        import textual
    except ImportError:
        missing_deps.append("textual")

    try:
        import foxtrot
    except ImportError:
        missing_deps.append("foxtrot")

    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nInstall dependencies with: uv sync")
        return False

    return True


def main():
    """Main entry point for the TUI application."""
    args = parse_arguments()

    # Setup logging
    setup_logging(args.debug)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Display startup banner
    print("╔" + "═" * 48 + "╗")
    print("║          Foxtrot TUI - Trading Platform       ║")
    print("║         Event-Driven Architecture             ║")
    print("╚" + "═" * 48 + "╝")
    print()

    if args.debug:
        print("Debug mode enabled")

    if args.config:
        print(f"Using config file: {args.config}")

    print(f"Theme: {args.theme}")

    if args.adapter:
        print(f"Trading Adapter: {args.adapter}")

    if args.paper_trading:
        print("Paper Trading Mode: ENABLED (no real money)")

    print()

    try:
        # Import and run the TUI application
        # Set up environment variables based on arguments
        import os

        from foxtrot.app.tui.main_app import main as run_tui

        if args.debug:
            os.environ["TEXTUAL_DEBUG"] = "1"

        if args.no_color:
            os.environ["NO_COLOR"] = "1"

        # Set theme environment variable
        os.environ["FOXTROT_TUI_THEME"] = args.theme

        # Set adapter preference if specified
        if args.adapter:
            os.environ["FOXTROT_PREFERRED_ADAPTER"] = args.adapter

        # Set paper trading mode
        if args.paper_trading:
            os.environ["FOXTROT_PAPER_TRADING"] = "1"

        # Run the TUI
        run_tui()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}")

        if args.debug:
            import traceback

            traceback.print_exc()

        if args.fallback_gui:
            print("Attempting to start GUI fallback...")
            try:
                # TODO: Implement GUI fallback
                print("GUI fallback not yet implemented")
            except Exception as gui_error:
                print(f"GUI fallback also failed: {gui_error}")

        sys.exit(1)


if __name__ == "__main__":
    main()
