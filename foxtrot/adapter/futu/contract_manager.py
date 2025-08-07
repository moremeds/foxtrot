"""
Futu contract manager for symbol information and contract loading.

Simplified facade that coordinates contract management functionality
through specialized components for caching and loading.
"""

from typing import TYPE_CHECKING, Dict, Optional
import futu as ft

from foxtrot.util.constants import Exchange, Product
from foxtrot.util.object import ContractData
from .futu_mappings import convert_futu_to_vt_symbol

# Import specialized components
from .contract_manager.cache_manager import ContractCacheManager
from .contract_manager.contract_loader import ContractLoader

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuContractManager:
    """
    Contract information management facade for Futu OpenD gateway.
    
    Coordinates contract loading and caching through specialized components
    while maintaining backward compatibility.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the contract manager facade."""
        self.api_client = api_client
        
        # Initialize specialized components
        self._init_components()

    def _init_components(self) -> None:
        """Initialize specialized contract management components."""
        # Cache management component
        self.cache_manager = ContractCacheManager(self.api_client)
        
        # Contract loading component
        self.contract_loader = ContractLoader(self.api_client, self.cache_manager)

    def load_all_contracts(self) -> None:
        """
        Load all contracts from supported markets.
        
        Delegates to contract loader component for efficient batch loading.
        """
        self.contract_loader.load_all_contracts()

    def get_contract(self, vt_symbol: str) -> Optional[ContractData]:
        """
        Get contract information for a specific VT symbol.
        
        Args:
            vt_symbol: VT format symbol (e.g., "AAPL.NASDAQ")
            
        Returns:
            ContractData if found, None otherwise
        """
        # Try cache first
        contract = self.cache_manager.get_contract(vt_symbol)
        if contract:
            return contract
        
        # If not in cache, try to load dynamically
        try:
            # Extract symbol and exchange
            if "." not in vt_symbol:
                return None
            
            symbol, exchange_str = vt_symbol.split(".", 1)
            
            # Try to determine market from exchange
            market = self._get_market_from_exchange(exchange_str)
            if not market:
                return None
            
            # Load specific contract
            contract = self._load_single_contract(symbol, market)
            if contract:
                self.cache_manager.store_contract(vt_symbol, contract)
            
            return contract
            
        except Exception as e:
            self.api_client._log_error(f"Error getting contract {vt_symbol}: {e}")
            return None

    def get_all_contracts(self) -> Dict[str, ContractData]:
        """Get all cached contracts."""
        return self.cache_manager.get_all_contracts()

    def validate_symbol(self, vt_symbol: str) -> bool:
        """
        Validate if a VT symbol exists and is tradeable.
        
        Args:
            vt_symbol: VT format symbol to validate
            
        Returns:
            True if symbol is valid and tradeable
        """
        try:
            # Check cache first
            if self.cache_manager.is_contract_cached(vt_symbol):
                return True
            
            # Try to get contract info
            contract = self.get_contract(vt_symbol)
            return contract is not None
            
        except Exception as e:
            self.api_client._log_error(f"Error validating symbol {vt_symbol}: {e}")
            return False

    def get_statistics(self) -> Dict[str, float]:
        """Get contract manager performance statistics."""
        return self.cache_manager.get_statistics()

    # Helper methods for market/exchange mapping
    def _get_market_from_exchange(self, exchange_str: str) -> Optional[str]:
        """Map exchange string to market identifier."""
        exchange_to_market = {
            "HKEX": "HK",
            "NASDAQ": "US",
            "NYSE": "US", 
            "AMEX": "US",
            "SSE": "SH",
            "SZSE": "SZ",
        }
        
        return exchange_to_market.get(exchange_str.upper())

    def _load_single_contract(self, symbol: str, market: str) -> Optional[ContractData]:
        """
        Load a single contract from Futu API.
        
        Args:
            symbol: Symbol code
            market: Market identifier
            
        Returns:
            ContractData if found, None otherwise
        """
        try:
            market_enum = self.contract_loader._get_market_enum_with_fallback(market)
            if not market_enum:
                return None
            
            if not self.api_client.api or not self.api_client.api.is_connected:
                return None
            
            # Query specific stock info
            ret_code, ret_data = self.api_client.api.get_stock_basicinfo(
                market=market_enum,
                stock_type=ft.SecurityType.STOCK,
                code_list=[symbol]
            )
            
            if ret_code != ft.RET_OK or ret_data.empty:
                return None
            
            # Process the first (and should be only) result
            stock_info = ret_data.iloc[0].to_dict()
            
            # Use contract loader's processing method
            if self.contract_loader._process_contract_info_enhanced(market, stock_info):
                vt_symbol = convert_futu_to_vt_symbol(symbol, market)
                return self.cache_manager.get_contract(vt_symbol)
            
            return None
            
        except Exception as e:
            self.api_client._log_error(f"Error loading single contract {symbol}: {e}")
            return None

    # Legacy methods for backward compatibility
    def _load_market_contracts(self, market: str) -> None:
        """Legacy method - delegates to contract loader."""
        self.contract_loader._load_market_contracts_optimized(market)

    def _get_market_enum(self, market: str) -> ft.Market:
        """Legacy method - delegates to contract loader."""
        return self.contract_loader._get_market_enum_with_fallback(market)

    def _get_price_tick(self, market: str) -> float:
        """Legacy method - delegates to contract loader."""
        return self.contract_loader._get_price_tick_default(market)