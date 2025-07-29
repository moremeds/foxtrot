"""
Main Interactive Brokers adapter implementation.
"""
from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.core.event import EVENT_TIMER, Event
from foxtrot.util.constants import Exchange
from foxtrot.util.object import (
    BarData,
    CancelRequest,
    HistoryRequest,
    OrderRequest,
    SubscribeRequest,
)

from .api_client import IbApi
from .ib_mappings import EXCHANGE_VT2IB


class IBAdapter(BaseAdapter):
    """
    Interactive Brokers trading adapter.
    
    This adapter provides a clean interface to Interactive Brokers TWS/Gateway
    while delegating all complex operations to specialized manager classes.
    """

    default_name: str = "IB"

    default_setting: dict[str, str | int] = {
        "TWS Address": "127.0.0.1",
        "TWS Port": 7497,
        "Client ID": 1,
        "Trading Account": ""
    }

    exchanges: list[Exchange] = list(EXCHANGE_VT2IB.keys())

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize the IB adapter."""
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)

        self.api: IbApi = IbApi(self)
        self.count: int = 0

    def connect(self, setting: dict[str, str | int | float | bool]) -> None:
        """Connect to the trading interface."""
        host: str = str(setting["TWS Address"])
        port: int = int(setting["TWS Port"])
        clientid: int = int(setting["Client ID"])
        account: str = str(setting["Trading Account"])

        self.api.connect(host, port, clientid, account)

        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def close(self) -> None:
        """Close the interface."""
        self.api.close()

    def subscribe(self, req: SubscribeRequest) -> None:
        """Subscribe to market data."""
        self.api.subscribe(req)

    def send_order(self, req: OrderRequest) -> str:
        """Send an order."""
        return self.api.send_order(req)

    def cancel_order(self, req: CancelRequest) -> None:
        """Cancel an order."""
        self.api.cancel_order(req)

    def query_account(self) -> None:
        """Query account balance."""
        pass

    def query_position(self) -> None:
        """Query holdings."""
        pass

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """Query historical data."""
        return self.api.query_history(req)

    def process_timer_event(self, event: Event) -> None:
        """Process timer events."""
        self.count += 1
        if self.count < 10:
            return
        self.count = 0

        self.api.check_connection()
