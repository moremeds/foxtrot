"""
Futu adapter facade - Clean interface implementing BaseAdapter.

This module provides a streamlined facade that delegates all operations
to the FutuApiClient using the official Futu OpenAPI and OpenD gateway.
"""

from typing import Any

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.object import (
    BarData,
    CancelRequest,
    HistoryRequest,
    OrderRequest,
    SubscribeRequest,
)

from .api_client import FutuApiClient


class FutuAdapter(BaseAdapter):
    """
    Futu trading adapter facade.

    This adapter provides a clean BaseAdapter interface while delegating
    all operations to the modular FutuApiClient system using official Futu OpenAPI.

    Architecture: OpenD Gateway Pattern
    - Uses local OpenD gateway (127.0.0.1:11111) as proxy to Futu servers
    - RSA key-based authentication instead of API key/secret
    - Callback-driven threading model for real-time data
    - Multi-market support: HK, US, CN (with appropriate permissions)
    """

    default_name: str = "FUTU"

    default_setting: dict[str, Any] = {
        # OpenD Gateway Settings
        "Host": "127.0.0.1",                    # Local OpenD gateway
        "Port": 11111,                          # Standard OpenD port
        "RSA Key File": "conn_key.txt",         # RSA private key file
        "Connection ID": "",                    # Unique connection identifier

        # Trading Settings
        "Environment": "SIMULATE",              # REAL/SIMULATE
        "Trading Password": "",                 # For trade context unlock
        "Paper Trading": True,

        # Market Access
        "HK Market Access": True,
        "US Market Access": True,
        "CN Market Access": False,             # May require special permissions

        # Connection Management
        "Connect Timeout": 30,
        "Reconnect Interval": 10,
        "Max Reconnect Attempts": 5,
        "Keep Alive Interval": 30,

        # Market Data
        "Market Data Level": "L1",
        "Max Subscriptions": 200,
        "Enable Push": True,
    }

    # Use existing exchanges instead of creating Futu-specific ones
    exchanges: list[Exchange] = [
        Exchange.SEHK,    # Hong Kong Stock Exchange
        Exchange.NASDAQ,  # NASDAQ
        Exchange.NYSE,    # New York Stock Exchange
        Exchange.SZSE,    # Shenzhen Stock Exchange
        Exchange.SSE,     # Shanghai Stock Exchange
    ]

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize the Futu adapter with OpenD gateway architecture."""
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)

        # Create the API client that coordinates all operations
        self.api_client = FutuApiClient(event_engine, adapter_name)
        self.api_client.set_adapter(self)

        # Connection status
        self.connected: bool = False

    def connect(self, setting: dict[str, Any]) -> None:
        """
        Connect to Futu OpenD gateway.

        Args:
            setting: Dictionary containing connection settings
        """
        if self.connected:
            self.write_log("Already connected to Futu OpenD")
            return

        self.write_log("Connecting to Futu OpenD gateway...")
        success = self.api_client.connect(setting)

        if success:
            self.connected = True
            self.write_log("Connected to Futu OpenD successfully")

            # Load initial data as required by BaseAdapter contract
            self._load_all_contracts()
            self.query_account()
            self.query_position()

        else:
            self.connected = False
            self.write_log("Failed to connect to Futu OpenD")

    def close(self) -> None:
        """Close OpenD connection and cleanup resources."""
        if self.connected:
            self.api_client.close()
            self.connected = False
            self.write_log("Futu OpenD connection closed")

    def subscribe(self, req: SubscribeRequest) -> None:
        """
        Subscribe to market data via OpenD gateway.

        Args:
            req: Subscription request with VT symbol format
        """
        if not self.api_client.market_data:
            self.write_log("Market data manager not available")
            return

        success = self.api_client.market_data.subscribe(req)
        if not success:
            self.write_log(f"Failed to subscribe to {req.vt_symbol}")

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order via Futu OpenD gateway.

        Args:
            req: Order request

        Returns:
            VT order ID if successful, empty string otherwise
        """
        if not self.api_client.order_manager:
            self.write_log("Order manager not available")
            return ""

        return self.api_client.order_manager.send_order(req)

    def cancel_order(self, req: CancelRequest) -> None:
        """
        Cancel an order via Futu OpenD gateway.

        Args:
            req: Cancel request
        """
        if not self.api_client.order_manager:
            self.write_log("Order manager not available")
            return

        self.api_client.order_manager.cancel_order(req)

    def query_account(self) -> None:
        """Query account information across all accessible markets."""
        if not self.api_client.account_manager:
            self.write_log("Account manager not available")
            return

        self.api_client.account_manager.query_account()

    def query_position(self) -> None:
        """Query position information across all accessible markets."""
        if not self.api_client.account_manager:
            self.write_log("Account manager not available")
            return

        self.api_client.account_manager.query_position()

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """
        Query historical data via Futu OpenD gateway.

        Args:
            req: History request

        Returns:
            List of bar data
        """
        if not self.api_client.historical_data:
            self.write_log("Historical data manager not available")
            return []

        return self.api_client.historical_data.query_history(req)

    def _load_all_contracts(self) -> None:
        """Load contract information for all accessible markets."""
        if not self.api_client.contract_manager:
            self.write_log("Contract manager not available")
            return

        self.api_client.contract_manager.load_all_contracts()

    def get_connection_status(self) -> dict[str, Any]:
        """
        Get comprehensive connection status information.

        Returns:
            Dictionary with connection status, health metrics, and OpenD info
        """
        return {
            "adapter_connected": self.connected,
            "api_client_status": self.api_client.get_opend_status(),
            "connection_health": self.api_client.get_connection_health(),
        }
