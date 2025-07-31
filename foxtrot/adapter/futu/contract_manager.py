"""
Futu contract manager for symbol information and contract loading.

This module handles contract information queries and symbol validation
with enhanced caching, batch processing, and performance optimization.
"""

import threading
import time
from typing import TYPE_CHECKING

from foxtrot.util.constants import Exchange, Product
from foxtrot.util.object import ContractData
import futu as ft

from .futu_mappings import convert_futu_to_vt_symbol

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuContractManager:
    """
    Enhanced contract information management for Futu OpenD gateway.

    Handles contract loading and symbol validation across multiple markets
    with intelligent caching, batch processing, and performance optimization.

    Features:
    - Thread-safe contract caching with expiration
    - Batch processing for efficient contract loading
    - Smart retry logic for failed queries
    - Memory management with LRU eviction
    - Performance statistics and monitoring
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the enhanced contract manager."""
        self.api_client = api_client

        # Thread-safe contract storage
        self._contracts: dict[str, ContractData] = {}
        self._contracts_lock = threading.RLock()

        # Cache management
        self._cache_timestamps: dict[str, float] = {}
        self._cache_timeout = 3600  # 1 hour cache timeout
        self._max_cache_size = 10000  # Maximum cached contracts

        # Performance optimization
        self._batch_size = 500  # Contracts per batch
        self._query_timeout = 30.0  # Query timeout in seconds
        self._retry_delay = 2.0  # Initial retry delay
        self._max_retries = 3

        # Statistics tracking
        self._stats = {
            "contracts_loaded": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_queries": 0,
            "total_query_time": 0.0,
            "last_update": 0.0,
        }

    def load_all_contracts(self) -> None:
        """Load contract information for all accessible markets with optimized processing."""
        start_time = time.time()

        try:
            # Clean expired cache entries first
            self._cleanup_expired_cache()

            markets = []
            if self.api_client.hk_access:
                markets.append("HK")
            if self.api_client.us_access:
                markets.append("US")
            if self.api_client.cn_access:
                markets.append("CN")

            if not markets:
                self.api_client._log_error("No market access enabled for contract loading")
                return

            self.api_client._log_info(f"Loading contracts for {len(markets)} markets: {markets}")

            total_loaded = 0
            for market in markets:
                loaded_count = self._load_market_contracts_optimized(market)
                total_loaded += loaded_count

            # Update statistics
            load_time = time.time() - start_time
            self._stats["total_query_time"] += load_time
            self._stats["last_update"] = time.time()

            self.api_client._log_info(
                f"Contract loading completed: {total_loaded} contracts loaded in {load_time:.2f}s"
            )

        except Exception as e:
            self.api_client._log_error(f"Contract loading error: {e}")
            self._stats["failed_queries"] += 1

    def _load_market_contracts(self, market: str) -> None:
        """
        Load contracts for specific market.

        Args:
            market: Market identifier (HK, US, CN)
        """
        try:
            if not self.api_client.quote_ctx:
                self.api_client._log_error("Quote context not available for contract loading")
                return

            # Get market enum
            market_enum = self._get_market_enum(market)

            # Query stock list for market
            ret, data = self.api_client.quote_ctx.get_stock_basicinfo(
                market=market_enum,
                stock_type=ft.SecurityType.STOCK
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Contract loading failed for {market}: {data}")
                return

            # Process contract data
            if isinstance(data, list):
                contract_count = 0
                for stock_info in data:
                    if self._process_contract_info(market, stock_info):
                        contract_count += 1

                self.api_client._log_info(f"Loaded {contract_count} contracts for {market} market")

        except Exception as e:
            self.api_client._log_error(f"Contract loading error for {market}: {e}")

    def _process_contract_info(self, market: str, stock_info: dict) -> bool:
        """
        Process individual contract information.

        Args:
            market: Market identifier
            stock_info: Stock information from SDK

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            code = stock_info.get("code", "")
            if not code:
                return False

            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")

            contract = ContractData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                name=stock_info.get("name", ""),
                product=Product.EQUITY,
                size=1.0,
                pricetick=self._get_price_tick(market),
                min_volume=1.0,
                stop_supported=False,
                net_position=True,
                history_data=True,
                adapter_name=self.api_client.adapter_name,
            )

            self._contracts[vt_symbol] = contract

            # Fire contract event
            self.api_client.adapter.on_contract(contract)
            return True

        except Exception as e:
            self.api_client._log_error(f"Contract processing error: {e}")
            return False

    def _get_market_enum(self, market: str) -> ft.Market:
        """
        Get Futu Market enum for market identifier.

        Args:
            market: Market identifier

        Returns:
            Futu Market enum
        """
        mapping = {
            "HK": ft.Market.HK,
            "US": ft.Market.US,
            "CN": ft.Market.CN_SH,  # Simplified
        }
        return mapping.get(market, ft.Market.HK)

    def _get_price_tick(self, market: str) -> float:
        """
        Get default price tick for market.

        Args:
            market: Market identifier

        Returns:
            Default price tick
        """
        # Simplified price ticks - in production, this should be per-symbol
        mapping = {
            "HK": 0.001,  # HK stocks
            "US": 0.01,   # US stocks
            "CN": 0.01,   # CN stocks
        }
        return mapping.get(market, 0.01)

    def get_contract(self, vt_symbol: str) -> ContractData:
        """
        Get contract by VT symbol.

        Args:
            vt_symbol: VT symbol

        Returns:
            Contract data or None if not found
        """
        return self._contracts.get(vt_symbol)

    def get_all_contracts(self) -> dict[str, ContractData]:
        """Get all loaded contracts."""
        return self._contracts.copy()

    def validate_symbol(self, vt_symbol: str) -> bool:
        """
        Validate if symbol exists in loaded contracts with cache optimization.

        Args:
            vt_symbol: VT symbol to validate

        Returns:
            True if symbol exists, False otherwise
        """
        with self._contracts_lock:
            if vt_symbol in self._contracts:
                # Check if cache entry is still valid
                if self._is_cache_valid(vt_symbol):
                    self._stats["cache_hits"] += 1
                    return True
                # Remove expired entry
                del self._contracts[vt_symbol]
                if vt_symbol in self._cache_timestamps:
                    del self._cache_timestamps[vt_symbol]

            self._stats["cache_misses"] += 1
            return False

    def _load_market_contracts_optimized(self, market: str) -> int:
        """
        Load contracts for specific market with enhanced processing.

        Args:
            market: Market identifier (HK, US, CN)

        Returns:
            Number of contracts loaded
        """
        try:
            if not self.api_client.quote_ctx:
                self.api_client._log_error("Quote context not available for contract loading")
                return 0

            self.api_client._log_info(f"Loading contracts for {market} market...")
            start_time = time.time()

            # Get market enum with retry logic
            market_enum = self._get_market_enum_with_fallback(market)

            # Query with retry logic
            contracts_data = self._query_contracts_with_retry(market_enum, market)
            if not contracts_data:
                return 0

            # Process in batches for memory efficiency
            processed_count = self._process_contracts_batch(market, contracts_data)

            load_time = time.time() - start_time
            self.api_client._log_info(
                f"Loaded {processed_count} contracts for {market} market in {load_time:.2f}s"
            )

            return processed_count

        except Exception as e:
            self.api_client._log_error(f"Optimized contract loading error for {market}: {e}")
            return 0

    def _query_contracts_with_retry(self, market_enum: ft.Market, market: str) -> list | None:
        """
        Query contracts with intelligent retry logic.

        Args:
            market_enum: Futu market enum
            market: Market identifier string

        Returns:
            List of contract data or None if failed
        """
        retry_delay = self._retry_delay

        for attempt in range(self._max_retries):
            try:
                ret, data = self.api_client.quote_ctx.get_stock_basicinfo(
                    market=market_enum,
                    stock_type=ft.SecurityType.STOCK
                )

                if ret == ft.RET_OK and isinstance(data, list):
                    return data

                self.api_client._log_error(
                    f"Contract query attempt {attempt + 1} failed for {market}: {data}"
                )

                if attempt < self._max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

            except Exception as e:
                self.api_client._log_error(
                    f"Contract query attempt {attempt + 1} error for {market}: {e}"
                )

                if attempt < self._max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2

        return None

    def _process_contracts_batch(self, market: str, contracts_data: list) -> int:
        """
        Process contracts in batches for memory efficiency.

        Args:
            market: Market identifier
            contracts_data: List of contract information

        Returns:
            Number of contracts processed successfully
        """
        processed_count = 0
        batch_count = 0

        for i in range(0, len(contracts_data), self._batch_size):
            batch = contracts_data[i:i + self._batch_size]
            batch_count += 1

            batch_processed = 0
            for stock_info in batch:
                if self._process_contract_info_enhanced(market, stock_info):
                    batch_processed += 1
                    processed_count += 1

            self.api_client._log_info(
                f"Processed batch {batch_count}: {batch_processed}/{len(batch)} contracts"
            )

            # Memory management - enforce cache size limit
            if len(self._contracts) > self._max_cache_size:
                self._evict_lru_entries()

        return processed_count

    def _process_contract_info_enhanced(self, market: str, stock_info: dict) -> bool:
        """
        Process individual contract information with enhanced validation.

        Args:
            market: Market identifier
            stock_info: Stock information from SDK

        Returns:
            True if processed successfully, False otherwise
        """
        try:
            code = stock_info.get("code", "")
            if not code:
                return False

            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")

            # Enhanced contract creation with more fields
            contract = ContractData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                name=stock_info.get("name", ""),
                product=Product.EQUITY,
                size=1.0,
                pricetick=self._get_price_tick_advanced(market, stock_info),
                min_volume=self._get_min_volume(market, stock_info),
                stop_supported=self._supports_stop_orders(market),
                net_position=True,
                history_data=True,
                adapter_name=self.api_client.adapter_name,
            )

            with self._contracts_lock:
                self._contracts[vt_symbol] = contract
                self._cache_timestamps[vt_symbol] = time.time()

            # Fire contract event
            self.api_client.adapter.on_contract(contract)
            self._stats["contracts_loaded"] += 1
            return True

        except Exception as e:
            self.api_client._log_error(f"Enhanced contract processing error: {e}")
            return False

    def _get_market_enum_with_fallback(self, market: str) -> ft.Market:
        """
        Get Futu Market enum with fallback handling.

        Args:
            market: Market identifier

        Returns:
            Futu Market enum with fallback
        """
        mapping = {
            "HK": ft.Market.HK,
            "US": ft.Market.US,
        }

        # CN market with fallback
        if market == "CN":
            if hasattr(ft.Market, 'CN_SH'):
                return ft.Market.CN_SH
            if hasattr(ft.Market, 'CN'):
                return ft.Market.CN
            self.api_client._log_error("CN market not supported in this SDK version")
            return ft.Market.HK  # Fallback

        return mapping.get(market, ft.Market.HK)

    def _get_price_tick_advanced(self, market: str, stock_info: dict) -> float:
        """
        Get advanced price tick based on stock price and market rules.

        Args:
            market: Market identifier
            stock_info: Stock information

        Returns:
            Price tick for the stock
        """
        # Try to get actual price tick from stock info
        if "price_tick" in stock_info:
            return float(stock_info["price_tick"])

        # Fallback to market defaults with price-based logic
        if market == "HK":
            # HK has price-based tick sizes
            price = float(stock_info.get("cur_price", 0))
            if price < 0.25:
                return 0.001
            if price < 0.5:
                return 0.005
            if price < 10.0:
                return 0.01
            if price < 20.0:
                return 0.02
            return 0.05
        if market == "US" or market == "CN":
            return 0.01

        return 0.01  # Default

    def _get_min_volume(self, market: str, stock_info: dict) -> float:
        """
        Get minimum trading volume for the stock.

        Args:
            market: Market identifier
            stock_info: Stock information

        Returns:
            Minimum trading volume
        """
        # Try to get from stock info
        if "lot_size" in stock_info:
            return float(stock_info["lot_size"])

        # Market defaults
        if market == "HK":
            return 100.0  # HK stocks typically trade in lots of 100
        return 1.0  # US and CN default to 1

    def _supports_stop_orders(self, market: str) -> bool:
        """
        Check if market supports stop orders.

        Args:
            market: Market identifier

        Returns:
            True if stop orders supported
        """
        # Most markets support stop orders
        return market in ["HK", "US", "CN"]

    def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries to free memory."""
        current_time = time.time()
        expired_symbols = []

        with self._contracts_lock:
            for vt_symbol, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._cache_timeout:
                    expired_symbols.append(vt_symbol)

            for symbol in expired_symbols:
                del self._contracts[symbol]
                del self._cache_timestamps[symbol]

        if expired_symbols:
            self.api_client._log_info(f"Cleaned up {len(expired_symbols)} expired contract entries")

    def _is_cache_valid(self, vt_symbol: str) -> bool:
        """
        Check if cache entry is still valid.

        Args:
            vt_symbol: Symbol to check

        Returns:
            True if cache entry is valid
        """
        if vt_symbol not in self._cache_timestamps:
            return False

        return time.time() - self._cache_timestamps[vt_symbol] < self._cache_timeout

    def _evict_lru_entries(self) -> None:
        """Evict least recently used cache entries to maintain size limit."""
        if len(self._contracts) <= self._max_cache_size:
            return

        # Sort by timestamp and remove oldest entries
        sorted_entries = sorted(
            self._cache_timestamps.items(),
            key=lambda x: x[1]
        )

        entries_to_remove = len(self._contracts) - self._max_cache_size + 100  # Remove extra

        with self._contracts_lock:
            for i in range(entries_to_remove):
                if i < len(sorted_entries):
                    symbol_to_remove = sorted_entries[i][0]
                    if symbol_to_remove in self._contracts:
                        del self._contracts[symbol_to_remove]
                    if symbol_to_remove in self._cache_timestamps:
                        del self._cache_timestamps[symbol_to_remove]

        self.api_client._log_info(f"Evicted {entries_to_remove} LRU contract entries")

    def get_statistics(self) -> dict[str, float]:
        """
        Get contract manager performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        stats = self._stats.copy()
        stats["cached_contracts"] = len(self._contracts)
        stats["cache_hit_rate"] = (
            self._stats["cache_hits"] /
            max(1, self._stats["cache_hits"] + self._stats["cache_misses"])
        )
        return stats
