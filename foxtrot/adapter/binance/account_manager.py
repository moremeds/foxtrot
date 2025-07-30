"""
Binance Account Manager - Handles account information, balances, and positions.

This module manages account-related operations including balance queries,
position tracking, and account state management.
"""

from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import AccountData, PositionData

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


class BinanceAccountManager:
    """
    Manager for Binance account operations.

    Handles account balance queries, position tracking, and account state caching.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the account manager."""
        self.api_client = api_client
        self._account_cache: dict | None = None

    def query_account(self) -> AccountData | None:
        """
        Query account information from Binance.

        Returns:
            AccountData object if successful, None otherwise
        """
        try:
            if not self.api_client.exchange:
                return None

            # Fetch account information
            account_info = self.api_client.exchange.fetch_balance()

            if not account_info:
                return None

            # Cache the account info
            self._account_cache = account_info

            # Convert to AccountData
            account_data = AccountData(
                adapter_name=self.api_client.adapter_name,
                accountid=self.api_client.adapter_name,
                balance=account_info.get("USDT", {}).get("total", 0.0),
                frozen=account_info.get("USDT", {}).get("used", 0.0),
            )

            return account_data

        except Exception as e:
            self.api_client._log_error(f"Failed to query account: {str(e)}")
            return None

    def query_position(self) -> list[PositionData]:
        """
        Query position information from Binance.

        Returns:
            List of PositionData objects
        """
        positions = []

        try:
            if not self.api_client.exchange:
                return positions

            # For spot trading, positions are essentially balances
            balance_info = self.api_client.exchange.fetch_balance()

            if not balance_info:
                return positions

            # Convert non-zero balances to positions
            for symbol, balance in balance_info.items():
                if isinstance(balance, dict) and balance.get("total", 0) > 0:
                    position = PositionData(
                        adapter_name=self.api_client.adapter_name,
                        symbol=f"{symbol}.{Exchange.BINANCE.value}",
                        exchange=Exchange.BINANCE,
                        direction=Direction.NET,  # Spot positions use NET direction
                        volume=balance.get("total", 0),
                        frozen=balance.get("used", 0),
                        price=0.0,  # Price not available for positions
                        pnl=0.0,  # PnL calculation would require additional data
                    )
                    positions.append(position)

        except Exception as e:
            self.api_client._log_error(f"Failed to query positions: {str(e)}")

        return positions

    def get_cached_account(self) -> dict | None:
        """
        Get cached account information.

        Returns:
            Cached account data if available, None otherwise
        """
        return self._account_cache

    def clear_cache(self) -> None:
        """Clear cached account data."""
        self._account_cache = None
