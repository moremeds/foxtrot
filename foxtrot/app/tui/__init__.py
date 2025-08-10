"""
Foxtrot TUI (Text User Interface) Package

A modern terminal-based interface for the Foxtrot trading platform,
built with Textual framework to provide the same functionality as the Qt GUI.
"""

# Lazy import to avoid circular dependencies at module level
__all__ = ["FoxtrotTUIApp", "main"]

def __getattr__(name):
    """Lazy import of TUI components to avoid circular dependencies."""
    if name == "FoxtrotTUIApp":
        from .main_app import FoxtrotTUIApp
        return FoxtrotTUIApp
    elif name == "main":
        from .main_app import main
        return main
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
