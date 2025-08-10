"""
Request objects for trading operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from .constants import Direction, Exchange, Interval, Offset, OrderType


if TYPE_CHECKING:
    # Imported only for static type checking to resolve forward references
    from foxtrot.util.trading_objects import OrderData
    from foxtrot.util.market_objects import QuoteData


@dataclass
class SubscribeRequest:
    """
    Request sending to specific adapter for subscribing tick data update.
    """

    symbol: str
    exchange: Exchange

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class OrderRequest:
    """
    Request sending to specific adapter for creating a new order.
    """

    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0
    offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_order_data(self, orderid: str, adapter_name: str) -> "OrderData":
        """
        Create order data from request.
        """
        from foxtrot.core.common import create_order_data_from_request
        return create_order_data_from_request(self, orderid, adapter_name)


@dataclass
class CancelRequest:
    """
    Request sending to specific adapter for canceling an existing order.
    """

    orderid: str
    symbol: str
    exchange: Exchange

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class HistoryRequest:
    """
    Request sending to specific adapter for querying history data.
    """

    symbol: str
    exchange: Exchange
    start: datetime
    end: datetime | None = None
    interval: Interval | None = None

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class QuoteRequest:
    """
    Request sending to specific adapter for creating a new quote.
    """

    symbol: str
    exchange: Exchange
    bid_price: float
    bid_volume: int
    ask_price: float
    ask_volume: int
    bid_offset: Offset = Offset.NONE
    ask_offset: Offset = Offset.NONE
    reference: str = ""

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"

    def create_quote_data(self, quoteid: str, adapter_name: str) -> "QuoteData":
        """
        Create quote data from request.
        """
        from foxtrot.core.common import create_quote_data_from_request
        return create_quote_data_from_request(self, quoteid, adapter_name)