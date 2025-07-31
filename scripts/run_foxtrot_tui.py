#!/usr/bin/env python3
"""
Convenience script to run Foxtrot TUI

This is a simple wrapper around the main run_tui.py script for easy execution.
"""

from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import and run the main script
if __name__ == "__main__":
    # Import the main function from run_tui.py
    from run_tui import main

    # Run the TUI application
    main()
