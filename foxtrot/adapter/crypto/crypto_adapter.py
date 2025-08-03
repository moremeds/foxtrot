"""
Crypto adapter facade - Clean interface implementing BaseAdapter.
"""

from typing import Any

import ccxt

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.logger import get_adapter_logger
from foxtrot.util.object import (
    BarData,
    CancelRequest,
    ContractData,
    HistoryRequest,
    OrderRequest,
    SubscribeRequest,
)

from .account_manager import AccountManager
from .market_data import MarketData
from .order_manager import OrderManager


class CryptoAdapter(BaseAdapter):
    """
    Crypto trading adapter facade.
    """

    default_name: str = "CRYPTO"

    default_setting: dict[str, Any] = {
        "Exchange": "binance",
        "API Key": "",
        "Secret": "",
        "Sandbox": False,
        "Proxy Host": "",
        "Proxy Port": 0,
    }

    exchanges: list[Exchange] = [
        Exchange.BINANCE,
        Exchange.BYBIT,
        Exchange.OKX,
        Exchange.BITGET,
        Exchange.MEXC,
        Exchange.GATE,
        Exchange.KUCOIN,
    ]

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize the Crypto adapter."""
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)

        self.exchange: ccxt.Exchange = None
        self.account_manager: AccountManager = None
        self.market_data: MarketData = None
        self.order_manager: OrderManager = None
        
        # Adapter-specific logger
        self._logger = get_adapter_logger(f"Crypto{adapter_name}")

    def connect(self, setting: dict[str, Any]) -> bool:
        """
        Connect to Crypto API.
        """
        self.exchange_name = setting.get("Exchange", "binance")
        api_key = setting.get("API Key", "")
        secret = setting.get("Secret", "")
        sandbox = setting.get("Sandbox", False)
        proxy_host = setting.get("Proxy Host", "")
        proxy_port = setting.get("Proxy Port", 0)

        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
            }
        )

        if sandbox:
            self.exchange.set_sandbox_mode(True)

        if proxy_host and proxy_port:
            self.exchange.proxies = {
                "http": f"http://{proxy_host}:{proxy_port}",
                "https": f"https://{proxy_host}:{proxy_port}",
            }

        try:
            self.exchange.load_markets()
        except Exception as e:
            # MIGRATION: Replace print with ERROR logging
            self._logger.error(
                "Failed to connect to exchange",
                extra={
                    "exchange_name": self.exchange_name,
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            return False

        self.account_manager = AccountManager(self)
        self.market_data = MarketData(self)
        self.order_manager = OrderManager(self)

        return True

    def close(self) -> None:
        """Close connection and cleanup resources."""

    def subscribe(self, req: SubscribeRequest) -> bool:
        """
        Subscribe to market data.
        """
        if not self.market_data:
            return False
        return self.market_data.subscribe(req)

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order.
        """
        if not self.order_manager:
            return ""
        return self.order_manager.send_order(req)

    def cancel_order(self, req: CancelRequest) -> bool:
        """
        Cancel an order.
        """
        if not self.order_manager:
            return False
        return self.order_manager.cancel_order(req)

    def query_account(self) -> None:
        """Query account information."""
        if not self.account_manager:
            return

        account_data = self.account_manager.query_account()
        if account_data:
            self.on_account(account_data)

    def query_position(self) -> None:
        """Query position information."""
        if not self.account_manager:
            return

        positions = self.account_manager.query_position()
        for position in positions:
            self.on_position(position)

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """
        Query historical data.
        """
        if not self.market_data:
            return []
        return self.market_data.query_history(req)

    def query_contract(self, symbol: str) -> ContractData:
        """
        Query contract information.
        """
        if not self.market_data:
            return None
        return self.market_data.query_contract(symbol)

    def get_available_contracts(self) -> list[ContractData]:
        """
        Get all available contracts.
        """
        if not self.market_data:
            return []
        return self.market_data.get_available_contracts()

    @property
    def connected(self) -> bool:
        """Check if adapter is connected."""
        return self.exchange is not None
