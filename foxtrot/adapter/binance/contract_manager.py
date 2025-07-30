"""
Binance Contract Manager - Handles contract and instrument management.

This module manages contract information including symbol discovery,
contract specifications, and symbol validation.
"""

from typing import TYPE_CHECKING

from foxtrot.util.constants import Exchange, Product
from foxtrot.util.object import ContractData

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


class BinanceContractManager:
    """
    Manager for Binance contract operations.

    Handles symbol discovery, contract specifications, and symbol validation.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the contract manager."""
        self.api_client = api_client
        self._contracts: dict[str, ContractData] = {}
        self._markets_loaded = False

    def query_contract(self, symbol: str) -> ContractData | None:
        """
        Query contract information for a symbol.

        Args:
            symbol: Symbol to query (in VT format)

        Returns:
            ContractData if found, None otherwise
        """
        try:
            # Ensure markets are loaded
            if not self._markets_loaded:
                self._load_markets()

            # Return cached contract if available
            contract = self._contracts.get(symbol)
            if contract:
                return contract

            # Try to find contract by base symbol
            base_symbol = symbol.split(".")[0]
            for contract_symbol, contract_data in self._contracts.items():
                if contract_symbol.startswith(base_symbol):
                    return contract_data

            return None

        except Exception as e:
            self.api_client._log_error(f"Failed to query contract {symbol}: {str(e)}")
            return None

    def get_available_contracts(self) -> list[ContractData]:
        """
        Get all available contracts.

        Returns:
            List of all available ContractData objects
        """
        try:
            # Ensure markets are loaded
            if not self._markets_loaded:
                self._load_markets()

            return list(self._contracts.values())

        except Exception as e:
            self.api_client._log_error(f"Failed to get available contracts: {str(e)}")
            return []

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is available for trading.

        Args:
            symbol: Symbol to validate (in VT format)

        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            contract = self.query_contract(symbol)
            return contract is not None

        except Exception as e:
            self.api_client._log_error(f"Failed to validate symbol {symbol}: {str(e)}")
            return False

    def _load_markets(self) -> None:
        """Load market information from Binance."""
        try:
            if not self.api_client.exchange:
                return

            # Load markets from exchange
            markets = self.api_client.exchange.load_markets()

            if not markets:
                self.api_client._log_error("No markets loaded from exchange")
                return

            # Convert markets to contracts
            for market_id, market_info in markets.items():
                try:
                    # Create VT symbol format
                    base = market_info.get("base", "")
                    quote = market_info.get("quote", "")
                    vt_symbol = f"{base}{quote}.{Exchange.BINANCE.value}"

                    # Create contract data
                    contract = ContractData(
                        symbol=vt_symbol,
                        exchange=Exchange.BINANCE,
                        name=market_info.get("id", market_id),
                        product=Product.SPOT,  # Binance spot products
                        size=1,  # Standard lot size
                        pricetick=market_info.get("precision", {}).get("price", 0.01),
                        min_volume=market_info.get("limits", {})
                        .get("amount", {})
                        .get("min", 0.001),
                        stop_supported=True,  # Binance supports stop orders
                        net_position=True,  # Spot trading uses net positions
                        history_data=True,  # Historical data available
                        adapter_name=self.api_client.adapter_name,
                    )

                    self._contracts[vt_symbol] = contract

                except Exception as e:
                    self.api_client._log_error(f"Failed to process market {market_id}: {str(e)}")
                    continue

            self._markets_loaded = True
            self.api_client._log_info(f"Loaded {len(self._contracts)} contracts from Binance")

        except Exception as e:
            self.api_client._log_error(f"Failed to load markets: {str(e)}")

    def get_contract_count(self) -> int:
        """
        Get the number of loaded contracts.

        Returns:
            Number of contracts loaded
        """
        return len(self._contracts)
