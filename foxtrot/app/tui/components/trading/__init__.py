"""
Trading components package with backward compatibility.

This package provides modular trading components that replace the monolithic
trading_panel.py file. All components are designed to work together while
maintaining single responsibility and testability.
"""

# Import all components for backward compatibility
from .common import (
    OrderAction,
    TradingConstants,
    TradingFormData,
    format_order_impact,
    get_symbol_suggestions
)

from .input_widgets import (
    SymbolInput,
    PriceInput,
    VolumeInput
)

from .order_preview import OrderPreviewPanel
from .market_data_panel import MarketDataPanel

# Import new modular components  
from .form import TradingFormManager
from .trading_actions import TradingActionHandler, OrderSubmissionMessage, OrderValidationMessage
from .trading_controller import TradingController

# NOTE: TUITradingPanel is available at foxtrot.app.tui.components.trading_panel 
# Removed import to avoid circular dependency

# Export main components
__all__ = [
    # Common utilities
    'OrderAction',
    'TradingConstants', 
    'TradingFormData',
    'format_order_impact',
    'get_symbol_suggestions',
    
    # Input widgets
    'SymbolInput',
    'PriceInput', 
    'VolumeInput',
    
    # Main panels
    'OrderPreviewPanel',
    'MarketDataPanel',
    
    # Modular architecture components
    'TradingFormManager',
    'TradingActionHandler',
    'OrderSubmissionMessage',
    'OrderValidationMessage',
    
    # Main trading controller (business logic)
    'TradingController'
]