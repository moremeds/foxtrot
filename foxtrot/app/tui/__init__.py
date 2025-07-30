"""
Foxtrot TUI (Text User Interface) Package

A modern terminal-based interface for the Foxtrot trading platform,
built with Textual framework to provide the same functionality as the Qt GUI.
"""

from .main_app import FoxtrotTUIApp, main

__all__ = ["FoxtrotTUIApp", "main"]