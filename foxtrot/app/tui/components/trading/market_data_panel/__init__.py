"""
Market data panel modular package.

This package provides a modular market data system with the following components:
- Data handler for fetching and validation logic
- Display manager for UI presentation and formatting
- Main controller for orchestration and public interface

The package maintains backward compatibility by exporting the main MarketDataPanel
class which provides the same interface as the original monolithic implementation.
"""

# Main controller class for backward compatibility
from .panel_controller import MarketDataPanel

# Core component classes
from .data_handler import MarketDataHandler
from .display_manager import MarketDataDisplayManager
from .ui_layout import MarketDataUILayout

# Version info
__version__ = "2.0.0"
__author__ = "Foxtrot Trading Platform"

__all__ = [
    # Main classes
    "MarketDataPanel",
    
    # Component classes (available for advanced usage)
    "MarketDataHandler",
    "MarketDataDisplayManager",
    "MarketDataUILayout",
    
    # Package metadata
    "__version__",
    "__author__"
]