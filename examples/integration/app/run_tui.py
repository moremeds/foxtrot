#!/usr/bin/env python3
"""
Foxtrot TUI Application Runner

This script runs the Text User Interface version of Foxtrot,
which is better suited for headless servers and terminal environments.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from foxtrot.app.tui.main_app import main

if __name__ == "__main__":
    main()
