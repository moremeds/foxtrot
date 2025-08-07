"""
Market data panel for displaying real-time trading information.

This module provides a comprehensive market data display with real-time updates,
market depth information, and formatted price/volume data.

REFACTORED: This file now imports from the modular market_data_panel package
while maintaining complete backward compatibility.
"""

# Import from the modular package for backward compatibility
from .market_data_panel import MarketDataPanel

# Also export for advanced usage
from .market_data_panel import MarketDataHandler, MarketDataDisplayManager

# Backward compatibility - ensure all original imports continue to work
__all__ = ["MarketDataPanel", "MarketDataHandler", "MarketDataDisplayManager"]