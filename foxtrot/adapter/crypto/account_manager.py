"""
Crypto Account Manager - Handles account information, balances, and positions.
"""

from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import PositionData
from foxtrot.util.logger import get_adapter_logger

from .account_object import CryptoAccountData

if TYPE_CHECKING:
    from .crypto_adapter import CryptoAdapter


class AccountManager:
    """
    Manager for Crypto account operations.
    """

    def __init__(self, adapter: "CryptoAdapter"):
        """Initialize the account manager."""
        self.adapter = adapter
        self._account_cache: dict | None = None
        
        # Adapter-specific logger
        self._logger = get_adapter_logger("CryptoAccount")

    def query_account(self) -> CryptoAccountData | None:
        """
        Query account information from the exchange.
        """
        try:
            if not self.adapter.exchange:
                return None

            account_info = self.adapter.exchange.fetch_balance()

            if not account_info:
                return None

            self._account_cache = account_info

            return CryptoAccountData(
                adapter_name=self.adapter.adapter_name,
                accountid=self.adapter.adapter_name,
                balance=account_info.get("USDT", {}).get("total", 0.0),
                frozen=account_info.get("USDT", {}).get("used", 0.0),
                **account_info.get("info", {}),
            )

        except Exception as e:
            # MIGRATION: Replace print with ERROR logging
            self._logger.error(
                "Failed to query account information",
                extra={
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            return None

    def query_position(self) -> list[PositionData]:
        """
        Query position information from the exchange.
        """
        positions = []

        try:
            if not self.adapter.exchange:
                return positions

            balance_info = self.adapter.exchange.fetch_balance()

            for symbol, balance in balance_info.items():
                if isinstance(balance, dict) and balance.get("total", 0) > 0:
                    position = PositionData(
                        adapter_name=self.adapter.adapter_name,
                        symbol=f"{symbol}.{self.adapter.default_name}",
                        exchange=Exchange[self.adapter.exchange_name.upper()],
                        direction=Direction.NET,
                        volume=balance.get("total", 0),
                        frozen=balance.get("used", 0),
                        price=0.0,
                        pnl=0.0,
                    )
                    positions.append(position)

        except Exception as e:
            # MIGRATION: Replace print with ERROR logging
            self._logger.error(
                "Failed to query position information", 
                extra={
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )

        return positions

    def get_cached_account(self) -> dict | None:
        """
        Get cached account information.
        """
        return self._account_cache

    def clear_cache(self) -> None:
        """Clear cached account data."""
        self._account_cache = None
