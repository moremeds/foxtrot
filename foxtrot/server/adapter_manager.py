"""
Adapter management functionality for MainEngine.
"""

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.object import (
    CancelRequest,
    HistoryRequest,
    OrderRequest,
    QuoteRequest,
    SubscribeRequest,
)


class AdapterManager:
    """
    Manages adapter lifecycle and operations.
    """

    def __init__(self, event_engine: EventEngine, write_log_func) -> None:
        """Initialize adapter manager."""
        self.event_engine: EventEngine = event_engine
        self.write_log = write_log_func
        self.adapters: dict[str, BaseAdapter] = {}
        self.exchanges: list[Exchange] = []

    def add_adapter(self, adapter_class: type[BaseAdapter], adapter_name: str = "") -> BaseAdapter:
        """
        Add adapter.
        """
        # Use default name if adapter_name not passed
        if not adapter_name:
            adapter_name = adapter_class.default_name

        adapter: BaseAdapter = adapter_class(self.event_engine, adapter_name)
        self.adapters[adapter_name] = adapter

        # Add adapter supported exchanges into engine
        for exchange in adapter.exchanges:
            if exchange not in self.exchanges:
                self.exchanges.append(exchange)

        return adapter

    def get_adapter(self, adapter_name: str) -> BaseAdapter | None:
        """
        Return adapter object by name.
        """
        adapter: BaseAdapter | None = self.adapters.get(adapter_name, None)
        if not adapter:
            self.write_log(f"Adapter not found: {adapter_name}")
        return adapter

    def get_default_setting(self, adapter_name: str) -> dict[str, str | bool | int | float] | None:
        """
        Get default setting dict of a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            return adapter.get_default_setting()  # type: ignore
        return None

    def get_all_gateway_names(self) -> list[str]:
        """
        Get all names of gateway added in main engine.
        """
        return list(self.adapters.keys())

    def get_all_exchanges(self) -> list[Exchange]:
        """
        Get all exchanges.
        """
        return self.exchanges

    def connect(self, setting: dict[str, str | bool | int | float], adapter_name: str) -> None:
        """
        Start connection of a specific adapter.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            adapter.connect(setting)

    def subscribe(self, req: SubscribeRequest, adapter_name: str) -> None:
        """
        Subscribe tick data update of a specific adapter.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            adapter.subscribe(req)

    def send_order(self, req: OrderRequest, adapter_name: str) -> str:
        """
        Send new order request to a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            return adapter.send_order(req)  # type: ignore
        return ""

    def cancel_order(self, req: CancelRequest, adapter_name: str) -> None:
        """
        Send cancel order request to a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            adapter.cancel_order(req)

    def send_quote(self, req: QuoteRequest, adapter_name: str) -> str:
        """
        Send new quote request to a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            return adapter.send_quote(req)  # type: ignore
        return ""

    def cancel_quote(self, req: CancelRequest, adapter_name: str) -> None:
        """
        Send cancel quote request to a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            adapter.cancel_quote(req)

    def query_history(self, req: HistoryRequest, adapter_name: str) -> list:
        """
        Send query history data request to a specific gateway.
        """
        adapter: BaseAdapter | None = self.get_adapter(adapter_name)
        if adapter:
            return adapter.query_history(req)  # type: ignore
        return []

    def close(self) -> None:
        """
        Close all adapter connections.
        """
        for adapter in self.adapters.values():
            adapter.close()