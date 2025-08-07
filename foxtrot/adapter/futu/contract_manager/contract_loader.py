"""
Contract loading functionality for Futu adapter.

Handles contract information queries and loading from Futu OpenD API
with batch processing and retry logic.
"""

import time
from typing import Dict, List, Optional, TYPE_CHECKING

import futu as ft

from foxtrot.util.constants import Exchange, Product
from foxtrot.util.object import ContractData
from ..futu_mappings import convert_futu_to_vt_symbol

if TYPE_CHECKING:
    from ..api_client import FutuApiClient
    from .cache_manager import ContractCacheManager


class ContractLoader:
    """Handles contract loading from Futu API."""
    
    def __init__(self, api_client: "FutuApiClient", cache_manager: "ContractCacheManager"):
        """Initialize contract loader."""
        self.api_client = api_client
        self.cache_manager = cache_manager
        
        # Loading configuration
        self._batch_size = 100  # Process contracts in batches
        self._retry_delay = 1.0  # Delay between retries
        self._max_retries = 3  # Maximum retry attempts
        
        # Supported markets for contract loading
        self._supported_markets = [
            "HK", "US", "SH", "SZ", "HK_FUTURE", "CN_FUTURE"
        ]
    
    def load_all_contracts(self) -> None:
        """
        Load all contracts from supported markets.
        
        This method loads contracts for all supported markets and stores them
        in the cache for quick access.
        """
        self.api_client._log_info("Starting to load all contracts...")
        
        total_loaded = 0
        start_time = time.time()
        
        for market in self._supported_markets:
            try:
                count = self._load_market_contracts_optimized(market)
                total_loaded += count
                self.api_client._log_info(f"Loaded {count} contracts from {market}")
                
                # Small delay between markets to avoid overwhelming the API
                time.sleep(0.5)
                
            except Exception as e:
                self.api_client._log_error(f"Failed to load contracts from {market}: {e}")
        
        end_time = time.time()
        self.api_client._log_info(
            f"Contract loading completed: {total_loaded} contracts in "
            f"{end_time - start_time:.2f} seconds"
        )
    
    def _load_market_contracts_optimized(self, market: str) -> int:
        """
        Load contracts for a specific market with optimization.
        
        Args:
            market: Market code (e.g., 'HK', 'US', 'SH')
            
        Returns:
            Number of contracts loaded
        """
        try:
            market_enum = self._get_market_enum_with_fallback(market)
            if not market_enum:
                self.api_client._log_warning(f"Unsupported market: {market}")
                return 0
            
            # Query contracts with retry logic
            contracts_data = self._query_contracts_with_retry(market_enum, market)
            if not contracts_data:
                return 0
            
            # Process contracts in batches
            return self._process_contracts_batch(market, contracts_data)
            
        except Exception as e:
            self.api_client._log_error(f"Error loading {market} contracts: {e}")
            return 0
    
    def _query_contracts_with_retry(
        self, 
        market_enum: ft.Market, 
        market: str
    ) -> Optional[List]:
        """
        Query contracts with retry logic.
        
        Args:
            market_enum: Futu market enum
            market: Market string identifier
            
        Returns:
            List of contract data or None if failed
        """
        for attempt in range(self._max_retries):
            try:
                if not self.api_client.api or not self.api_client.api.is_connected:
                    self.api_client._log_error("API not connected for contract query")
                    return None
                
                # Query stock basic info
                ret_code, ret_data = self.api_client.api.get_stock_basicinfo(
                    market=market_enum,
                    stock_type=ft.SecurityType.STOCK
                )
                
                if ret_code != ft.RET_OK:
                    self.api_client._log_error(f"Failed to get {market} contracts: {ret_data}")
                    if attempt < self._max_retries - 1:
                        time.sleep(self._retry_delay * (attempt + 1))
                        continue
                    return None
                
                return ret_data.to_dict('records') if hasattr(ret_data, 'to_dict') else []
                
            except Exception as e:
                self.api_client._log_error(f"Exception querying {market} contracts: {e}")
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
                    continue
                return None
        
        return None
    
    def _process_contracts_batch(self, market: str, contracts_data: List) -> int:
        """
        Process contracts in batches for better performance.
        
        Args:
            market: Market identifier
            contracts_data: List of contract data dictionaries
            
        Returns:
            Number of contracts processed
        """
        processed_count = 0
        
        # Process in batches to avoid memory issues
        for i in range(0, len(contracts_data), self._batch_size):
            batch = contracts_data[i:i + self._batch_size]
            
            for stock_info in batch:
                try:
                    if self._process_contract_info_enhanced(market, stock_info):
                        processed_count += 1
                except Exception as e:
                    # Log but continue processing other contracts
                    symbol = stock_info.get('code', 'unknown')
                    self.api_client._log_warning(f"Failed to process {symbol}: {e}")
        
        return processed_count
    
    def _process_contract_info_enhanced(self, market: str, stock_info: Dict) -> bool:
        """
        Process individual contract info with enhanced data extraction.
        
        Args:
            market: Market identifier
            stock_info: Contract information dictionary
            
        Returns:
            True if processing was successful
        """
        try:
            # Extract basic contract information
            code = stock_info.get("code", "")
            name = stock_info.get("name", "")
            
            if not code or not name:
                return False
            
            # Convert to VT symbol format
            vt_symbol = convert_futu_to_vt_symbol(code, market)
            if not vt_symbol:
                return False
            
            # Get exchange enum
            exchange = self._get_exchange_from_market(market)
            if not exchange:
                return False
            
            # Create contract data
            contract = ContractData(
                symbol=code,
                exchange=exchange,
                name=name,
                product=Product.EQUITY,
                size=1.0,
                pricetick=self._get_price_tick_advanced(market, stock_info),
                min_volume=self._get_min_volume(market, stock_info),
                stop_supported=self._supports_stop_orders(market),
                net_position=True,
                history_data=True,
                gateway_name="FUTU",
                vt_symbol=vt_symbol
            )
            
            # Store in cache
            self.cache_manager.store_contract(vt_symbol, contract)
            return True
            
        except Exception as e:
            self.api_client._log_error(f"Error processing contract info: {e}")
            return False
    
    def _get_market_enum_with_fallback(self, market: str) -> Optional[ft.Market]:
        """Get Futu market enum with fallback handling."""
        market_mapping = {
            "HK": ft.Market.HK,
            "US": ft.Market.US,
            "SH": ft.Market.SH,
            "SZ": ft.Market.SZ,
            "HK_FUTURE": ft.Market.HK_FUTURE,
            "CN_FUTURE": ft.Market.CN_FUTURE,
        }
        
        return market_mapping.get(market.upper())
    
    def _get_exchange_from_market(self, market: str) -> Optional[Exchange]:
        """Map market to exchange enum."""
        market_to_exchange = {
            "HK": Exchange.HKEX,
            "US": Exchange.NASDAQ,  # Default to NASDAQ for US
            "SH": Exchange.SSE,
            "SZ": Exchange.SZSE,
            "HK_FUTURE": Exchange.HKEX,
            "CN_FUTURE": Exchange.CFFEX,  # Default to CFFEX for CN futures
        }
        
        return market_to_exchange.get(market.upper())
    
    def _get_price_tick_advanced(self, market: str, stock_info: Dict) -> float:
        """Get price tick with advanced logic based on market and stock info."""
        # Try to get from stock info if available
        if "lot_size" in stock_info and stock_info["lot_size"]:
            try:
                lot_size = float(stock_info["lot_size"])
                if lot_size > 0:
                    return 1.0 / lot_size
            except (ValueError, TypeError):
                pass
        
        # Fallback to market defaults
        return self._get_price_tick_default(market)
    
    def _get_price_tick_default(self, market: str) -> float:
        """Get default price tick for market."""
        default_ticks = {
            "HK": 0.01,
            "US": 0.01,
            "SH": 0.01,
            "SZ": 0.01,
            "HK_FUTURE": 0.01,
            "CN_FUTURE": 0.01,
        }
        
        return default_ticks.get(market.upper(), 0.01)
    
    def _get_min_volume(self, market: str, stock_info: Dict) -> float:
        """Get minimum trading volume."""
        # Try to extract from stock info
        if "board_lot" in stock_info:
            try:
                return float(stock_info["board_lot"])
            except (ValueError, TypeError):
                pass
        
        # Market defaults
        market_min_volumes = {
            "HK": 100.0,  # HK stocks typically trade in lots of 100
            "US": 1.0,    # US stocks can trade 1 share
            "SH": 100.0,  # A-shares trade in lots of 100
            "SZ": 100.0,  # A-shares trade in lots of 100
        }
        
        return market_min_volumes.get(market.upper(), 1.0)
    
    def _supports_stop_orders(self, market: str) -> bool:
        """Check if market supports stop orders."""
        stop_supported_markets = {"US", "HK"}  # Generally US and HK support stop orders
        return market.upper() in stop_supported_markets