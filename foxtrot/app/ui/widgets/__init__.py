"""
UI widget components for Foxtrot trading platform.

This package contains modularized widget components split from the original
monolithic widget.py file to maintain proper file size limits and separation of concerns.
"""

# Re-export commonly used components for backward compatibility
from .base_widget import BaseMonitor
from .cell_widget import (
    BaseCell,
    EnumCell,
    DirectionCell,
    BidCell,
    AskCell,
    PnlCell,
    TimeCell,
    DateCell,
    MsgCell,
)
from .monitor_widget import (
    TickMonitor,
    LogMonitor,
    TradeMonitor,
    OrderMonitor,
    PositionMonitor,
    AccountMonitor,
    QuoteMonitor,
    ActiveOrderMonitor,
)
from .trading_widget import TradingWidget
from .dialog_widget import ConnectDialog, AboutDialog, GlobalDialog
from .contract_widget import ContractManager

__all__ = [
    # Base
    "BaseMonitor",
    # Cells
    "BaseCell",
    "EnumCell",
    "DirectionCell",
    "BidCell",
    "AskCell",
    "PnlCell",
    "TimeCell",
    "DateCell",
    "MsgCell",
    # Monitors
    "TickMonitor",
    "LogMonitor",
    "TradeMonitor",
    "OrderMonitor",
    "PositionMonitor",
    "AccountMonitor",
    "QuoteMonitor",
    "ActiveOrderMonitor",
    # Main widgets
    "TradingWidget",
    "ContractManager",
    # Dialogs
    "ConnectDialog",
    "AboutDialog",
    "GlobalDialog",
]