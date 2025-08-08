"""
Abstract interfaces for core components.

This module defines abstract base classes that enable dependency injection
and break circular dependencies between Engine and Adapter components.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..util.constants import Exchange
    from ..util.object import (
        AccountData,
        BarData,
        CancelRequest,
        ContractData,
        HistoryRequest,
        LogData,
        OrderData,
        OrderRequest,
        PositionData,
        QuoteData,
        QuoteRequest,
        SubscribeRequest,
        TickData,
        TradeData,
    )
    from .event_engine import EventEngine


class IAdapter(ABC):
    """
    Interface for trading system adapters.
    
    Defines the contract for all trading system adapters without
    creating circular dependencies with the Engine.
    """

    # Default name for the adapter
    default_name: str

    # Fields required in setting dict for connect function
    default_setting: dict[str, str | int | float | bool]

    # Exchanges supported in the adapter
    exchanges: list["Exchange"]

    @abstractmethod
    def connect(self, setting: dict[str, str | int | float | bool]) -> None:
        """Start adapter connection."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close adapter connection."""
        pass

    @abstractmethod
    def subscribe(self, req: "SubscribeRequest") -> None:
        """Subscribe to tick data updates."""
        pass

    @abstractmethod
    def send_order(self, req: "OrderRequest") -> str:
        """Send new order request."""
        pass

    @abstractmethod
    def cancel_order(self, req: "CancelRequest") -> None:
        """Cancel existing order."""
        pass

    @abstractmethod
    def query_account(self) -> None:
        """Query account balance."""
        pass

    @abstractmethod
    def query_position(self) -> None:
        """Query holding positions."""
        pass

    def send_quote(self, req: "QuoteRequest") -> str:
        """Send new quote request (optional)."""
        return ""

    def cancel_quote(self, req: "CancelRequest") -> None:
        """Cancel existing quote (optional)."""
        pass

    def query_history(self, req: "HistoryRequest") -> list["BarData"]:
        """Query historical bar data (optional)."""
        return []


class IEngine(ABC):
    """
    Interface for the main trading engine.
    
    Defines the contract for engine functionality without
    creating circular dependencies with adapters.
    """

    @abstractmethod
    def write_log(self, msg: str, source: str = "") -> None:
        """Write log event with specific message."""
        pass

    @abstractmethod
    def add_adapter(self, adapter_class: type["IAdapter"], adapter_name: str = "") -> "IAdapter":
        """Add adapter to the engine."""
        pass

    @abstractmethod
    def get_adapter(self, adapter_name: str) -> "IAdapter" | None:
        """Get adapter by name."""
        pass

    @abstractmethod
    def connect(self, setting: dict[str, str | bool | int | float], adapter_name: str) -> None:
        """Connect to a specific adapter."""
        pass

    @abstractmethod
    def subscribe(self, req: "SubscribeRequest", adapter_name: str) -> None:
        """Subscribe to tick data via adapter."""
        pass

    @abstractmethod
    def send_order(self, req: "OrderRequest", adapter_name: str) -> str:
        """Send order via adapter."""
        pass

    @abstractmethod
    def cancel_order(self, req: "CancelRequest", adapter_name: str) -> None:
        """Cancel order via adapter."""
        pass

    # Optional data access methods
    def get_tick(self, vt_symbol: str) -> "TickData" | None:
        """Get tick data by symbol (optional)."""
        return None

    def get_order(self, vt_orderid: str) -> "OrderData" | None:
        """Get order data by order id (optional)."""
        return None

    def get_trade(self, vt_tradeid: str) -> "TradeData" | None:
        """Get trade data by trade id (optional)."""
        return None

    def get_position(self, vt_positionid: str) -> "PositionData" | None:
        """Get position data by position id (optional)."""
        return None

    def get_account(self, vt_accountid: str) -> "AccountData" | None:
        """Get account data by account id (optional)."""
        return None

    def get_contract(self, vt_symbol: str) -> "ContractData" | None:
        """Get contract data by symbol (optional)."""
        return None


class IEventEngine(ABC):
    """
    Interface for event processing engine.
    
    Defines the contract for event handling without creating
    dependencies on specific implementations.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the event engine."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the event engine."""
        pass

    @abstractmethod
    def put(self, event: object) -> None:
        """Put event into the processing queue."""
        pass

    @abstractmethod
    def register(self, type: str, handler: Callable) -> None:
        """Register event handler for specific event type."""
        pass

    @abstractmethod
    def unregister(self, type: str, handler: Callable) -> None:
        """Unregister event handler."""
        pass