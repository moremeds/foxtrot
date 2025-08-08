"""
Trade monitor modular components package.

Provides focused components for trade monitoring functionality:
    - trade_controller: Business logic coordination
    - trade_filters_actions: Filtering and action handling
    - trade_statistics: Statistics calculation and tracking
    - trade_export: CSV and other export formats
    - trade_ui_components: UI formatting and display logic

All components work together through the TradeController coordinator.
"""

from .trade_controller import TradeController
from .trade_filters_actions import TradeFiltersActions
from .trade_statistics import TradeStatistics
from .trade_export import TradeExport
from .trade_ui_components import TradeUIComponents

def create_trade_monitor(main_engine, event_engine):
    """Create a configured trade monitor instance."""
    # Lazy import to avoid circular dependency
    from ..trade_monitor import create_trade_monitor as _create_trade_monitor
    return _create_trade_monitor(main_engine, event_engine)

__all__ = [
    "TradeController",
    "TradeFiltersActions", 
    "TradeStatistics",
    "TradeExport",
    "TradeUIComponents",
    "create_trade_monitor",
]

__version__ = "1.0.0"
__author__ = "Foxtrot Trading Platform"