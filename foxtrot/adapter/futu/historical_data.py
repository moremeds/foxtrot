"""
Futu historical data manager for OHLCV data queries.

This module handles historical market data queries via the Futu OpenD gateway.
"""

from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING

from foxtrot.util.constants import Interval
from foxtrot.util.object import BarData, HistoryRequest
import futu as ft

from .futu_mappings import convert_symbol_to_futu_market

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuHistoricalData:
    """
    Historical data management for Futu OpenD gateway.

    Handles historical OHLCV data queries with intelligent caching,
    performance optimization, and resource management.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the historical data manager with enhanced caching."""
        self.api_client = api_client

        # Enhanced caching system
        self._cache: dict[str, tuple[list[BarData], float]] = {}  # data, timestamp
        self._cache_timeout = 300  # 5 minutes default
        self._cache_lock = threading.RLock()
        self._max_cache_size = 1000  # Maximum cache entries

        # Performance optimization settings
        self._request_throttle = 0.1  # Minimum time between requests (seconds)
        self._last_request_time = 0.0
        self._request_lock = threading.Lock()

        # Cache statistics for monitoring
        self._cache_hits = 0
        self._cache_misses = 0
        self._total_requests = 0

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """
        Query historical data via SDK with enhanced caching and performance optimization.

        Args:
            req: History request

        Returns:
            List of bar data
        """
        with self._request_lock:
            self._total_requests += 1

        try:
            # Generate cache key with improved granularity
            cache_key = self._generate_cache_key(req)

            # Check cache first with thread safety
            cached_data = self._get_cached_data(cache_key)
            if cached_data is not None:
                self._cache_hits += 1
                return cached_data

            self._cache_misses += 1

            # Apply request throttling to avoid overwhelming the SDK
            self._apply_request_throttle()

            # Convert VT parameters to SDK format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)
            kl_type = self._convert_interval_to_ktype(req.interval)

            # Query quote context with validation
            if not self.api_client.quote_ctx:
                self.api_client._log_error("Quote context not available for historical data")
                return []

            # Determine optimal number of records based on interval
            num_records = self._calculate_optimal_record_count(req.interval)

            # Query from SDK with enhanced error handling
            ret, data = self.api_client.quote_ctx.get_cur_kline(
                code=code,
                num=num_records,
                kl_type=kl_type,
                autype=ft.AuType.QFQ  # Forward adjusted
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Historical data query failed for {req.vt_symbol}: {data}")
                return []

            # Convert to BarData objects with improved error handling
            bars = self._convert_kline_data_to_bars(req, data)

            # Cache results with intelligent cache management
            self._cache_data(cache_key, bars)

            return bars

        except Exception as e:
            self.api_client._log_error(f"Historical data error for {req.vt_symbol}: {e}")
            return []

    def _generate_cache_key(self, req: HistoryRequest) -> str:
        """
        Generate intelligent cache key with time-based granularity.

        Args:
            req: History request

        Returns:
            Cache key string
        """
        # For real-time data, include current minute to ensure freshness
        current_time = datetime.now()
        if req.interval == Interval.MINUTE:
            time_grain = current_time.strftime("%Y%m%d%H%M")
        elif req.interval == Interval.HOUR:
            time_grain = current_time.strftime("%Y%m%d%H")
        else:  # Daily and above
            time_grain = current_time.strftime("%Y%m%d")

        return f"{req.vt_symbol}_{req.interval}_{req.start}_{req.end}_{time_grain}"

    def _get_cached_data(self, cache_key: str) -> list[BarData] | None:
        """
        Retrieve data from cache with expiration checking.

        Args:
            cache_key: Cache key to look up

        Returns:
            Cached data if valid, None otherwise
        """
        with self._cache_lock:
            if cache_key not in self._cache:
                return None

            data, timestamp = self._cache[cache_key]
            current_time = time.time()

            # Check if cache entry has expired
            if current_time - timestamp > self._cache_timeout:
                del self._cache[cache_key]
                return None

            return data

    def _cache_data(self, cache_key: str, data: list[BarData]) -> None:
        """
        Cache data with intelligent cache management.

        Args:
            cache_key: Key to store data under
            data: Bar data to cache
        """
        with self._cache_lock:
            current_time = time.time()

            # Implement LRU eviction if cache is full
            if len(self._cache) >= self._max_cache_size:
                self._evict_oldest_cache_entries()

            self._cache[cache_key] = (data, current_time)

    def _evict_oldest_cache_entries(self) -> None:
        """Remove oldest cache entries to make room for new data."""
        # Sort by timestamp and remove oldest 20% of entries
        entries_to_remove = len(self._cache) // 5
        if entries_to_remove == 0:
            entries_to_remove = 1

        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1][1])

        for i in range(entries_to_remove):
            del self._cache[sorted_entries[i][0]]

    def _apply_request_throttle(self) -> None:
        """Apply request throttling to avoid overwhelming the SDK."""
        with self._request_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self._request_throttle:
                sleep_time = self._request_throttle - time_since_last
                time.sleep(sleep_time)

            self._last_request_time = time.time()

    def _calculate_optimal_record_count(self, interval: Interval) -> int:
        """
        Calculate optimal number of records to request based on interval.

        Args:
            interval: Data interval

        Returns:
            Optimal number of records
        """
        # Optimize based on typical usage patterns
        if interval == Interval.MINUTE:
            return 1440  # 1 day of minute data
        if interval == Interval.HOUR:
            return 168   # 1 week of hourly data
        if interval == Interval.DAILY:
            return 252   # ~1 year of daily data
        if interval == Interval.WEEKLY:
            return 104   # ~2 years of weekly data
        return 1000  # Default maximum

    def _convert_kline_data_to_bars(self, req: HistoryRequest, data: any) -> list[BarData]:
        """
        Convert SDK kline data to BarData objects with enhanced error handling.

        Args:
            req: Original history request
            data: K-line data from SDK

        Returns:
            List of BarData objects
        """
        bars = []

        if not isinstance(data, list):
            return bars

        for kline_data in data:
            try:
                bar = self._convert_kline_to_bar(req, kline_data)
                if bar:
                    bars.append(bar)
            except Exception as e:
                self.api_client._log_error(f"Error converting kline data: {e}")
                continue  # Skip invalid data but continue processing

        return bars

    def get_cache_statistics(self) -> dict[str, any]:
        """
        Get cache performance statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            hit_rate = (self._cache_hits / max(self._total_requests, 1)) * 100

            return {
                "cache_size": len(self._cache),
                "max_cache_size": self._max_cache_size,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "total_requests": self._total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_timeout_seconds": self._cache_timeout,
            }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        with self._cache_lock:
            self._cache.clear()
            self.api_client._log_info("Historical data cache cleared")

    def _convert_interval_to_ktype(self, interval: Interval) -> ft.KLType:
        """
        Convert VT interval to Futu KLType.

        Args:
            interval: VT interval

        Returns:
            Corresponding Futu KLType
        """
        mapping = {
            Interval.MINUTE: ft.KLType.K_1M,
            Interval.HOUR: ft.KLType.K_60M,
            Interval.DAILY: ft.KLType.K_DAY,
            Interval.WEEKLY: ft.KLType.K_WEEK,
        }
        return mapping.get(interval, ft.KLType.K_DAY)

    def _convert_kline_to_bar(self, req: HistoryRequest, kline_data: dict) -> BarData:
        """
        Convert SDK kline data to VT BarData.

        Args:
            req: Original history request
            kline_data: K-line data from SDK

        Returns:
            BarData object
        """
        try:
            # Parse timestamp
            time_key = kline_data.get("time_key", "")
            dt = datetime.strptime(time_key, "%Y-%m-%d %H:%M:%S") if time_key else datetime.now()

            return BarData(
                symbol=req.symbol,
                exchange=req.exchange,
                datetime=dt,
                interval=req.interval,
                volume=float(kline_data.get("volume", 0)),
                turnover=float(kline_data.get("turnover", 0)),
                open_price=float(kline_data.get("open", 0)),
                high_price=float(kline_data.get("high", 0)),
                low_price=float(kline_data.get("low", 0)),
                close_price=float(kline_data.get("close", 0)),
                adapter_name=self.api_client.adapter_name,
            )


        except Exception as e:
            self.api_client._log_error(f"K-line conversion error: {e}")
            return None
