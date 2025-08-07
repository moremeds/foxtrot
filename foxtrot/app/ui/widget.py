"""
Basic widgets for UI - backward compatibility module.

All widgets have been reorganized into the widgets/ subdirectory:
- widgets/cells.py: Table cell classes
- widgets/base_monitor.py: Base monitor class
- widgets/monitors.py: Specific monitor classes
- widgets/dialogs.py: Dialog windows
- widgets/trading.py: Trading-related widgets
"""

# Re-export everything for backward compatibility
from .widgets import (
    COLOR_ASK,
    COLOR_BID,
    COLOR_BLACK,
    COLOR_LONG,
    COLOR_SHORT,
    AboutDialog,
    AccountMonitor,
    ActiveOrderMonitor,
    AskCell,
    BaseCell,
    BaseMonitor,
    BidCell,
    ConnectDialog,
    ContractManager,
    DateCell,
    DirectionCell,
    EnumCell,
    GlobalDialog,
    LogMonitor,
    MsgCell,
    OrderMonitor,
    PnlCell,
    PositionMonitor,
    QuoteMonitor,
    TickMonitor,
    TimeCell,
    TradeMonitor,
    TradingWidget,
)

__all__ = [
    "BaseMonitor",
    "BaseCell",
    "EnumCell",
    "DirectionCell",
    "BidCell",
    "AskCell",
    "PnlCell",
    "TimeCell",
    "DateCell",
    "MsgCell",
    "TickMonitor",
    "LogMonitor",
    "TradeMonitor",
    "OrderMonitor",
    "PositionMonitor",
    "AccountMonitor",
    "QuoteMonitor",
    "ConnectDialog",
    "TradingWidget",
    "ActiveOrderMonitor",
    "ContractManager",
    "AboutDialog",
    "GlobalDialog",
    "COLOR_LONG",
    "COLOR_SHORT",
    "COLOR_BID",
    "COLOR_ASK",
    "COLOR_BLACK",
]