"""
Contract cache management for Futu adapter.

Handles contract caching, expiration, and LRU eviction with thread safety.
"""

import threading
import time
from typing import Dict, TYPE_CHECKING

from foxtrot.util.object import ContractData

if TYPE_CHECKING:
    from ..api_client import FutuApiClient


class ContractCacheManager:
    """Manages contract caching with thread safety and LRU eviction."""
    
    def __init__(self, api_client: "FutuApiClient"):
        """Initialize cache manager."""
        self.api_client = api_client
        
        # Thread-safe contract storage
        self._contracts: Dict[str, ContractData] = {}
        self._contracts_lock = threading.RLock()
        
        # Cache management
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_timeout = 3600  # 1 hour cache timeout
        self._max_cache_size = 10000  # Maximum cached contracts
        
        # Performance statistics
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_evictions": 0,
            "cache_cleanups": 0
        }
    
    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """Get contract from cache if available and valid."""
        with self._contracts_lock:
            if not self._is_cache_valid(vt_symbol):
                self._stats["cache_misses"] += 1
                return None
            
            self._stats["cache_hits"] += 1
            # Update access timestamp for LRU
            self._cache_timestamps[vt_symbol] = time.time()
            return self._contracts.get(vt_symbol)
    
    def store_contract(self, vt_symbol: str, contract: ContractData) -> None:
        """Store contract in cache."""
        with self._contracts_lock:
            self._contracts[vt_symbol] = contract
            self._cache_timestamps[vt_symbol] = time.time()
            
            # Trigger LRU eviction if needed
            if len(self._contracts) > self._max_cache_size:
                self._evict_lru_entries()
    
    def get_all_contracts(self) -> Dict[str, ContractData]:
        """Get all cached contracts."""
        with self._contracts_lock:
            # Cleanup expired entries first
            self._cleanup_expired_cache()
            return self._contracts.copy()
    
    def is_contract_cached(self, vt_symbol: str) -> bool:
        """Check if contract is cached and valid."""
        return self._is_cache_valid(vt_symbol)
    
    def _cleanup_expired_cache(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_symbols = []
        
        with self._contracts_lock:
            for vt_symbol, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._cache_timeout:
                    expired_symbols.append(vt_symbol)
            
            for vt_symbol in expired_symbols:
                if vt_symbol in self._contracts:
                    del self._contracts[vt_symbol]
                if vt_symbol in self._cache_timestamps:
                    del self._cache_timestamps[vt_symbol]
        
        if expired_symbols:
            self._stats["cache_cleanups"] += 1
            self.api_client._log_info(f"Cleaned up {len(expired_symbols)} expired contract entries")
    
    def _is_cache_valid(self, vt_symbol: str) -> bool:
        """Check if cached contract is still valid."""
        if vt_symbol not in self._contracts:
            return False
        
        timestamp = self._cache_timestamps.get(vt_symbol, 0)
        return (time.time() - timestamp) < self._cache_timeout
    
    def _evict_lru_entries(self) -> None:
        """Evict least recently used entries when cache is full."""
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
        
        self._stats["cache_evictions"] += 1
        self.api_client._log_info(f"Evicted {entries_to_remove} LRU contract entries")
    
    def get_statistics(self) -> Dict[str, float]:
        """Get cache performance statistics."""
        stats = self._stats.copy()
        stats["cached_contracts"] = len(self._contracts)
        
        # Calculate hit rate
        total_requests = self._stats["cache_hits"] + self._stats["cache_misses"]
        stats["cache_hit_rate"] = (
            self._stats["cache_hits"] / max(1, total_requests)
        )
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear all cached contracts."""
        with self._contracts_lock:
            self._contracts.clear()
            self._cache_timestamps.clear()
        
        self.api_client._log_info("Contract cache cleared")
    
    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self._contracts)