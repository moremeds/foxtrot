"""
Specific monitor implementations for different data types.
"""

from foxtrot.core.event import (
    EVENT_ACCOUNT,
    EVENT_LOG,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_QUOTE,
    EVENT_TICK,
    EVENT_TRADE,
)
from foxtrot.core.event_engine import Event
from foxtrot.util.object import CancelRequest, OrderData, QuoteData

from .base_widget import BaseMonitor
from .cell_widget import (
    AskCell,
    BaseCell,
    BidCell,
    DirectionCell,
    EnumCell,
    MsgCell,
    PnlCell,
    TimeCell,
)


class TickMonitor(BaseMonitor):
    """
    Monitor for tick data.
    """

    event_type: str = EVENT_TICK
    data_key: str = "vt_symbol"
    sorting: bool = True

    headers: dict = {
        "symbol": {"display": "Code", "cell": BaseCell, "update": False},
        "exchange": {"display": "Exchange", "cell": EnumCell, "update": False},
        "name": {"display": "Name", "cell": BaseCell, "update": True},
        "last_price": {"display": "Latest Price", "cell": BaseCell, "update": True},
        "volume": {"display": "Volume", "cell": BaseCell, "update": True},
        "open_price": {"display": "Open Price", "cell": BaseCell, "update": True},
        "high_price": {"display": "High Price", "cell": BaseCell, "update": True},
        "low_price": {"display": "Low Price", "cell": BaseCell, "update": True},
        "bid_price_1": {"display": "Bid Price 1", "cell": BidCell, "update": True},
        "bid_volume_1": {"display": "Bid Volume 1", "cell": BidCell, "update": True},
        "ask_price_1": {"display": "Ask Price 1", "cell": AskCell, "update": True},
        "ask_volume_1": {"display": "Ask Volume 1", "cell": AskCell, "update": True},
        "datetime": {"display": "Time", "cell": TimeCell, "update": True},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }


class LogMonitor(BaseMonitor):
    """
    Monitor for log data.
    """

    event_type: str = EVENT_LOG
    data_key: str = ""
    sorting: bool = False

    headers: dict = {
        "time": {"display": "Time", "cell": TimeCell, "update": False},
        "msg": {"display": "Message", "cell": MsgCell, "update": False},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }


class TradeMonitor(BaseMonitor):
    """
    Monitor for trade data.
    """

    event_type: str = EVENT_TRADE
    data_key: str = ""
    sorting: bool = True

    headers: dict = {
        "tradeid": {"display": "Trade ID", "cell": BaseCell, "update": False},
        "orderid": {"display": "Order ID", "cell": BaseCell, "update": False},
        "symbol": {"display": "Code", "cell": BaseCell, "update": False},
        "exchange": {"display": "Exchange", "cell": EnumCell, "update": False},
        "direction": {"display": "Direction", "cell": DirectionCell, "update": False},
        "offset": {"display": "Offset", "cell": EnumCell, "update": False},
        "price": {"display": "Price", "cell": BaseCell, "update": False},
        "volume": {"display": "Volume", "cell": BaseCell, "update": False},
        "datetime": {"display": "Time", "cell": TimeCell, "update": False},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }


class OrderMonitor(BaseMonitor):
    """
    Monitor for order data.
    """

    event_type: str = EVENT_ORDER
    data_key: str = "vt_orderid"
    sorting: bool = True

    headers: dict = {
        "orderid": {"display": "Order ID", "cell": BaseCell, "update": False},
        "reference": {"display": "Reference", "cell": BaseCell, "update": False},
        "symbol": {"display": "Code", "cell": BaseCell, "update": False},
        "exchange": {"display": "Exchange", "cell": EnumCell, "update": False},
        "type": {"display": "Type", "cell": EnumCell, "update": False},
        "direction": {"display": "Direction", "cell": DirectionCell, "update": False},
        "offset": {"display": "Offset", "cell": EnumCell, "update": False},
        "price": {"display": "Price", "cell": BaseCell, "update": False},
        "volume": {"display": "Volume", "cell": BaseCell, "update": True},
        "traded": {"display": "Traded", "cell": BaseCell, "update": True},
        "status": {"display": "Status", "cell": EnumCell, "update": True},
        "datetime": {"display": "Time", "cell": TimeCell, "update": True},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }

    def init_ui(self) -> None:
        """
        Connect signal.
        """
        super().init_ui()

        self.setToolTip("Double click to cancel order")
        self.itemDoubleClicked.connect(self.cancel_order)

    def cancel_order(self, cell: BaseCell) -> None:
        """
        Cancel order if cell double clicked.
        """
        order: OrderData = cell.get_data()
        req: CancelRequest = order.create_cancel_request()
        self.main_engine.cancel_order(req, order.adapter_name)


class PositionMonitor(BaseMonitor):
    """
    Monitor for position data.
    """

    event_type: str = EVENT_POSITION
    data_key: str = "vt_positionid"
    sorting: bool = True

    headers: dict = {
        "symbol": {"display": "Code", "cell": BaseCell, "update": False},
        "exchange": {"display": "Exchange", "cell": EnumCell, "update": False},
        "direction": {"display": "Direction", "cell": DirectionCell, "update": False},
        "volume": {"display": "Volume", "cell": BaseCell, "update": True},
        "yd_volume": {"display": "Yesterday Volume", "cell": BaseCell, "update": True},
        "frozen": {"display": "Frozen", "cell": BaseCell, "update": True},
        "price": {"display": "Average Price", "cell": BaseCell, "update": True},
        "pnl": {"display": "PnL", "cell": PnlCell, "update": True},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }


class AccountMonitor(BaseMonitor):
    """
    Monitor for account data.
    """

    event_type: str = EVENT_ACCOUNT
    data_key: str = "vt_accountid"
    sorting: bool = True

    headers: dict = {
        "accountid": {"display": "Account ID", "cell": BaseCell, "update": False},
        "balance": {"display": "Balance", "cell": BaseCell, "update": True},
        "frozen": {"display": "Frozen", "cell": BaseCell, "update": True},
        "available": {"display": "Available", "cell": BaseCell, "update": True},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }


class QuoteMonitor(BaseMonitor):
    """
    Monitor for quote data.
    """

    event_type: str = EVENT_QUOTE
    data_key: str = "vt_quoteid"
    sorting: bool = True

    headers: dict = {
        "quoteid": {"display": "Quote ID", "cell": BaseCell, "update": False},
        "reference": {"display": "Reference", "cell": BaseCell, "update": False},
        "symbol": {"display": "Code", "cell": BaseCell, "update": False},
        "exchange": {"display": "Exchange", "cell": EnumCell, "update": False},
        "bid_offset": {"display": "Buy Open Close", "cell": EnumCell, "update": False},
        "bid_volume": {"display": "Buy Volume", "cell": BidCell, "update": False},
        "bid_price": {"display": "Buy Price", "cell": BidCell, "update": False},
        "ask_price": {"display": "Ask Price", "cell": AskCell, "update": False},
        "ask_volume": {"display": "Ask Volume", "cell": AskCell, "update": False},
        "ask_offset": {"display": "Sell Open Close", "cell": EnumCell, "update": False},
        "status": {"display": "Status", "cell": EnumCell, "update": True},
        "datetime": {"display": "Time", "cell": TimeCell, "update": True},
        "adapter_name": {"display": "Adapter", "cell": BaseCell, "update": False},
    }

    def init_ui(self) -> None:
        """
        Connect signal.
        """
        super().init_ui()

        self.setToolTip("Double click to cancel quote")
        self.itemDoubleClicked.connect(self.cancel_quote)

    def cancel_quote(self, cell: BaseCell) -> None:
        """
        Cancel quote if cell double clicked.
        """
        quote: QuoteData = cell.get_data()
        req: CancelRequest = quote.create_cancel_request()
        self.main_engine.cancel_quote(req, quote.adapter_name)


class ActiveOrderMonitor(OrderMonitor):
    """
    Monitor which shows active order only.
    """

    def process_event(self, event: Event) -> None:
        """
        Hides the row if order is not active.
        """
        super().process_event(event)

        order: OrderData = event.data
        row_cells: dict = self.cells[order.vt_orderid]
        row: int = self.row(row_cells["volume"])

        if order.is_active():
            self.showRow(row)
        else:
            self.hideRow(row)