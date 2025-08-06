# Foxtrot State Management & Persistence Plan

**Document Version:** 1.0  
**Date:** August 6, 2025

## Overview

This document outlines an enhanced state management and persistence system building upon the existing SQLite plan in `./docs/gemini/plans/`, inspired by Nautilus Trader's cache-centric architecture and advanced persistence patterns, adapted for Foxtrot's Python-native environment.

---

## Current State Assessment

**Existing Architecture:**
- Basic in-memory state in OmsEngine  
- Simple SQLite persistence proposal in existing plans
- No caching layer optimization
- Limited state recovery capabilities
- Manual state management

**Key Gaps:**
- No high-performance caching layer
- Limited state versioning and migration
- Missing transaction support
- No state compression or optimization
- Lack of state consistency guarantees

---

## Enhanced Cache System

### High-Performance Cache Architecture

Building on Nautilus's cache-centric approach with Python-optimized patterns:

```python
# foxtrot/server/cache/cache_manager.py
from typing import Dict, Any, Optional, List, TypeVar, Generic, Callable
from abc import ABC, abstractmethod
import pickle
import threading
from collections import OrderedDict
from enum import Enum
import time
import json

T = TypeVar('T')

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"       # Fastest access, limited size
    L2_COMPRESSED = "l2_compressed"  # Compressed memory cache
    L3_PERSISTENT = "l3_persistent"  # Disk-based persistence

class CacheInterface(ABC):
    """Abstract cache interface for different storage levels"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    def clear(self) -> None:
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

class MemoryCache(CacheInterface):
    """High-performance in-memory cache with LRU eviction"""
    
    def __init__(self, max_size: int = 10000, default_ttl: Optional[int] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            # Check expiry
            if key in self._expiry and time.time() > self._expiry[key]:
                self._remove_expired(key)
                return None
            
            if key in self._cache:
                # Move to end (most recently used)
                value = self._cache.pop(key)
                self._cache[key] = value
                return value
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            # Remove if exists
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                # Remove least recently used
                lru_key, _ = self._cache.popitem(last=False)
                if lru_key in self._expiry:
                    del self._expiry[lru_key]
            
            # Add new item
            self._cache[key] = value
            
            # Set expiry if specified
            effective_ttl = ttl or self.default_ttl
            if effective_ttl:
                self._expiry[key] = time.time() + effective_ttl
    
    def delete(self, key: str) -> bool:
        with self._lock:
            deleted = key in self._cache
            if deleted:
                del self._cache[key]
                if key in self._expiry:
                    del self._expiry[key]
            return deleted
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
    
    def exists(self, key: str) -> bool:
        return self.get(key) is not None
    
    def _remove_expired(self, key: str):
        """Remove expired key"""
        if key in self._cache:
            del self._cache[key]
        if key in self._expiry:
            del self._expiry[key]
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if current_time > expiry
        ]
        
        for key in expired_keys:
            self._remove_expired(key)
        
        return len(expired_keys)

class CompressedCache(CacheInterface):
    """Compressed memory cache for larger datasets"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                compressed_data = self._cache.pop(key)
                self._cache[key] = compressed_data  # Move to end
                return pickle.loads(compressed_data)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            compressed_data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            
            if key in self._cache:
                self._cache.pop(key)
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[key] = compressed_data
    
    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

class MultiLevelCacheManager:
    """Multi-level cache system with automatic data promotion/demotion"""
    
    def __init__(
        self,
        l1_size: int = 1000,      # L1: Hot data
        l2_size: int = 5000,      # L2: Warm data 
        l3_cache: Optional[CacheInterface] = None  # L3: Cold data (persistent)
    ):
        self.l1_cache = MemoryCache(max_size=l1_size, default_ttl=300)  # 5 min TTL
        self.l2_cache = CompressedCache(max_size=l2_size)
        self.l3_cache = l3_cache
        
        # Access tracking for intelligent promotion/demotion
        self._access_counts: Dict[str, int] = {}
        self._last_access: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get with automatic promotion from lower levels"""
        self._update_access_stats(key)
        
        # Try L1 first (fastest)
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 (compressed memory)
        value = self.l2_cache.get(key)
        if value is not None:
            # Promote to L1 if accessed frequently
            if self._should_promote_to_l1(key):
                self.l1_cache.set(key, value)
            return value
        
        # Try L3 (persistent)
        if self.l3_cache:
            value = self.l3_cache.get(key)
            if value is not None:
                # Promote to L2
                self.l2_cache.set(key, value)
                if self._should_promote_to_l1(key):
                    self.l1_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any, level: CacheLevel = CacheLevel.L1_MEMORY) -> None:
        """Set value at specified cache level"""
        self._update_access_stats(key)
        
        if level == CacheLevel.L1_MEMORY:
            self.l1_cache.set(key, value)
        elif level == CacheLevel.L2_COMPRESSED:
            self.l2_cache.set(key, value)
        elif level == CacheLevel.L3_PERSISTENT and self.l3_cache:
            self.l3_cache.set(key, value)
        
        # Also set in higher levels if frequently accessed
        if self._is_hot_data(key):
            self.l1_cache.set(key, value)
            self.l2_cache.set(key, value)
    
    def delete(self, key: str) -> bool:
        """Delete from all cache levels"""
        deleted = False
        deleted |= self.l1_cache.delete(key)
        deleted |= self.l2_cache.delete(key)
        if self.l3_cache:
            deleted |= self.l3_cache.delete(key)
        
        # Clean up access stats
        with self._lock:
            self._access_counts.pop(key, None)
            self._last_access.pop(key, None)
        
        return deleted
    
    def _update_access_stats(self, key: str):
        """Update access statistics for cache level decisions"""
        current_time = time.time()
        with self._lock:
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            self._last_access[key] = current_time
    
    def _should_promote_to_l1(self, key: str) -> bool:
        """Determine if key should be promoted to L1"""
        with self._lock:
            access_count = self._access_counts.get(key, 0)
            last_access = self._last_access.get(key, 0)
            
            # Promote if accessed >3 times in last 5 minutes
            return (access_count > 3 and 
                    time.time() - last_access < 300)
    
    def _is_hot_data(self, key: str) -> bool:
        """Determine if data is 'hot' and should be in multiple levels"""
        with self._lock:
            access_count = self._access_counts.get(key, 0)
            return access_count > 10

class TradingDataCacheManager:
    """Specialized cache manager for trading data types"""
    
    def __init__(self, persistent_cache: Optional[CacheInterface] = None):
        self.cache = MultiLevelCacheManager(
            l1_size=1000,
            l2_size=5000, 
            l3_cache=persistent_cache
        )
        
        # Specialized accessors for trading data
        self._lock = threading.RLock()
    
    # Order management
    def cache_order(self, order: 'OrderData') -> None:
        """Cache order with automatic level selection"""
        key = f"order:{order.vt_orderid}"
        
        # Active orders go to L1, completed orders to L2
        if order.is_active():
            level = CacheLevel.L1_MEMORY
        else:
            level = CacheLevel.L2_COMPRESSED
        
        self.cache.set(key, order, level)
    
    def get_order(self, vt_orderid: str) -> Optional['OrderData']:
        """Get order with fast lookup"""
        return self.cache.get(f"order:{vt_orderid}")
    
    def get_all_orders(self, status_filter: Optional[str] = None) -> List['OrderData']:
        """Get orders with optional status filtering"""
        # This would need to be implemented with an index
        # For now, simplified version
        orders = []
        # Implementation would maintain status indexes
        return orders
    
    # Position management  
    def cache_position(self, position: 'PositionData') -> None:
        """Cache position data"""
        key = f"position:{position.vt_positionid}"
        
        # All positions are hot data
        self.cache.set(key, position, CacheLevel.L1_MEMORY)
    
    def get_position(self, vt_positionid: str) -> Optional['PositionData']:
        """Get position with fast lookup"""
        return self.cache.get(f"position:{vt_positionid}")
    
    # Market data management
    def cache_tick(self, tick: 'TickData', max_ticks: int = 1000) -> None:
        """Cache market data with size limits"""
        symbol_key = f"ticks:{tick.symbol}"
        
        # Get or create tick list for symbol
        tick_list = self.cache.get(symbol_key)
        if tick_list is None:
            from collections import deque
            tick_list = deque(maxlen=max_ticks)
        
        tick_list.append(tick)
        self.cache.set(symbol_key, tick_list, CacheLevel.L1_MEMORY)
        
        # Also cache latest tick for fast access
        self.cache.set(f"latest_tick:{tick.symbol}", tick, CacheLevel.L1_MEMORY)
    
    def get_latest_tick(self, symbol: str) -> Optional['TickData']:
        """Get latest tick for symbol"""
        return self.cache.get(f"latest_tick:{symbol}")
    
    def get_recent_ticks(self, symbol: str, count: int = 100) -> List['TickData']:
        """Get recent ticks for symbol"""
        tick_list = self.cache.get(f"ticks:{symbol}")
        if tick_list:
            return list(tick_list)[-count:]
        return []
```

---

## Advanced Persistent Storage

### Enhanced SQLite Implementation

Building upon the existing SQLite plan with advanced features:

```python
# foxtrot/server/persistence/advanced_persistence.py
import sqlite3
import json
import pickle
import gzip
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass
import threading
from enum import Enum

class CompressionLevel(Enum):
    NONE = 0
    LIGHT = 1
    MEDIUM = 6
    HIGH = 9

@dataclass
class MigrationScript:
    """Database migration script"""
    version: int
    description: str
    up_script: str
    down_script: Optional[str] = None

class AdvancedSqlitePersistence:
    """Enhanced SQLite persistence with versioning, compression, and transactions"""
    
    def __init__(
        self, 
        db_path: str = "foxtrot_state.db",
        compression_level: CompressionLevel = CompressionLevel.LIGHT,
        enable_wal: bool = True,
        connection_pool_size: int = 5
    ):
        self.db_path = db_path
        self.compression_level = compression_level
        self.enable_wal = enable_wal
        self.schema_version = 3  # Incremented from existing plan
        
        # Connection pooling for better performance
        self._connection_pool = []
        self._pool_lock = threading.Lock()
        self._pool_size = connection_pool_size
        
        # Migration scripts
        self._migrations = self._get_migration_scripts()
        
        self._init_database()
    
    def _init_database(self):
        """Initialize database with comprehensive schema and optimizations"""
        with self._get_connection() as conn:
            # Enable WAL mode for better concurrent access
            if self.enable_wal:
                conn.execute("PRAGMA journal_mode=WAL")
            
            # Performance optimizations
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # Create comprehensive schema
            conn.executescript("""
                -- Enhanced orders table with compression support
                CREATE TABLE IF NOT EXISTS orders (
                    vt_orderid TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    offset TEXT NOT NULL,
                    type TEXT NOT NULL,
                    volume REAL NOT NULL,
                    price REAL,
                    status TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    reference TEXT,
                    data_json TEXT,
                    data_compressed BLOB,
                    compression_level INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );
                
                -- Optimized indexes
                CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON orders(symbol, status);
                CREATE INDEX IF NOT EXISTS idx_orders_datetime_desc ON orders(datetime DESC);
                CREATE INDEX IF NOT EXISTS idx_orders_status_updated ON orders(status, updated_at);
                
                -- Enhanced positions table
                CREATE TABLE IF NOT EXISTS positions (
                    vt_positionid TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    volume REAL NOT NULL,
                    frozen REAL DEFAULT 0,
                    price REAL NOT NULL,
                    pnl REAL DEFAULT 0,
                    data_json TEXT,
                    data_compressed BLOB,
                    compression_level INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
                CREATE INDEX IF NOT EXISTS idx_positions_updated ON positions(updated_at DESC);
                
                -- Enhanced trades table with better normalization
                CREATE TABLE IF NOT EXISTS trades (
                    vt_tradeid TEXT PRIMARY KEY,
                    vt_orderid TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    offset TEXT NOT NULL,
                    volume REAL NOT NULL,
                    price REAL NOT NULL,
                    commission REAL DEFAULT 0,
                    datetime TEXT NOT NULL,
                    data_json TEXT,
                    data_compressed BLOB,
                    compression_level INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    FOREIGN KEY (vt_orderid) REFERENCES orders (vt_orderid)
                );
                
                CREATE INDEX IF NOT EXISTS idx_trades_orderid ON trades(vt_orderid);
                CREATE INDEX IF NOT EXISTS idx_trades_symbol_datetime ON trades(symbol, datetime DESC);
                CREATE INDEX IF NOT EXISTS idx_trades_datetime_desc ON trades(datetime DESC);
                
                -- Account snapshots for balance history
                CREATE TABLE IF NOT EXISTS account_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    balance REAL NOT NULL,
                    available REAL NOT NULL,
                    frozen REAL DEFAULT 0,
                    currency TEXT NOT NULL,
                    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_json TEXT,
                    data_compressed BLOB
                );
                
                CREATE INDEX IF NOT EXISTS idx_account_snapshots_time ON account_snapshots(account_id, snapshot_time DESC);
                
                -- Migration tracking
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Configuration storage
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Performance monitoring
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    tags TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time ON performance_metrics(metric_name, recorded_at DESC);
            """)
            
            # Apply any pending migrations
            self._apply_migrations(conn)
            
            # Insert current schema version
            conn.execute(
                "INSERT OR REPLACE INTO schema_migrations (version, description) VALUES (?, ?)",
                (self.schema_version, "Advanced persistence with compression and performance optimizations")
            )
    
    @contextmanager
    def _get_connection(self):
        """Get database connection from pool or create new one"""
        conn = None
        try:
            # Try to get from pool
            with self._pool_lock:
                if self._connection_pool:
                    conn = self._connection_pool.pop()
                else:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
            
            yield conn
            
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            # Return to pool or close
            if conn:
                try:
                    conn.commit()
                    with self._pool_lock:
                        if len(self._connection_pool) < self._pool_size:
                            self._connection_pool.append(conn)
                        else:
                            conn.close()
                except:
                    conn.close()
    
    def _compress_data(self, data: Any) -> tuple[bytes, int]:
        """Compress data based on compression level"""
        if self.compression_level == CompressionLevel.NONE:
            return pickle.dumps(data), 0
        
        pickled_data = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        compressed_data = gzip.compress(pickled_data, compresslevel=self.compression_level.value)
        
        return compressed_data, self.compression_level.value
    
    def _decompress_data(self, data: bytes, compression_level: int) -> Any:
        """Decompress data"""
        if compression_level == 0:
            return pickle.loads(data)
        
        decompressed = gzip.decompress(data)
        return pickle.loads(decompressed)
    
    def save_order(self, order: 'OrderData') -> None:
        """Save order with compression and versioning"""
        compressed_data, compression_level = self._compress_data(order)
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders (
                    vt_orderid, symbol, exchange, direction, offset, type,
                    volume, price, status, datetime, reference, 
                    data_compressed, compression_level, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
                          COALESCE((SELECT version FROM orders WHERE vt_orderid = ?) + 1, 1))
            """, (
                order.vt_orderid, order.symbol, order.exchange.value,
                order.direction.value, order.offset.value, order.type.value,
                order.volume, order.price, order.status.value,
                order.datetime.isoformat(), order.reference,
                compressed_data, compression_level, order.vt_orderid
            ))
    
    def load_order(self, vt_orderid: str) -> Optional['OrderData']:
        """Load order with decompression"""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT data_compressed, compression_level, data_json 
                FROM orders 
                WHERE vt_orderid = ?
            """, (vt_orderid,)).fetchone()
            
            if row:
                if row['data_compressed']:
                    return self._decompress_data(row['data_compressed'], row['compression_level'])
                elif row['data_json']:
                    # Fallback to JSON for legacy data
                    import json
                    from foxtrot.util.object import OrderData
                    data = json.loads(row['data_json'])
                    return OrderData(**data)
        
        return None
    
    def get_orders_by_status(self, status: str, limit: int = 100) -> List['OrderData']:
        """Get orders by status with limit"""
        orders = []
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT data_compressed, compression_level, data_json
                FROM orders 
                WHERE status = ? 
                ORDER BY updated_at DESC 
                LIMIT ?
            """, (status, limit)).fetchall()
            
            for row in rows:
                if row['data_compressed']:
                    order = self._decompress_data(row['data_compressed'], row['compression_level'])
                    orders.append(order)
                elif row['data_json']:
                    import json
                    from foxtrot.util.object import OrderData
                    data = json.loads(row['data_json'])
                    orders.append(OrderData(**data))
        
        return orders
    
    def save_position(self, position: 'PositionData') -> None:
        """Save position with versioning"""
        compressed_data, compression_level = self._compress_data(position)
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO positions (
                    vt_positionid, symbol, exchange, direction,
                    volume, frozen, price, pnl,
                    data_compressed, compression_level, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP,
                          COALESCE((SELECT version FROM positions WHERE vt_positionid = ?) + 1, 1))
            """, (
                position.vt_positionid, position.symbol, position.exchange.value,
                position.direction.value, position.volume, position.frozen,
                position.price, position.pnl,
                compressed_data, compression_level, position.vt_positionid
            ))
    
    def cleanup_old_data(self, days: int = 30) -> Dict[str, int]:
        """Advanced cleanup with detailed reporting"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        cleanup_results = {}
        
        with self._get_connection() as conn:
            # Clean up old trades (keep referenced by active orders)
            cursor = conn.execute("""
                DELETE FROM trades 
                WHERE datetime < ? AND vt_orderid NOT IN (
                    SELECT vt_orderid FROM orders WHERE status IN ('Active', 'PartTraded', 'Submitted')
                )
            """, (cutoff_date,))
            cleanup_results['trades_deleted'] = cursor.rowcount
            
            # Clean up old account snapshots (keep last 100 per account)
            cursor = conn.execute("""
                DELETE FROM account_snapshots WHERE id NOT IN (
                    SELECT id FROM account_snapshots a1 WHERE (
                        SELECT COUNT(*) FROM account_snapshots a2 
                        WHERE a2.account_id = a1.account_id AND a2.snapshot_time > a1.snapshot_time
                    ) < 100
                )
            """)
            cleanup_results['snapshots_deleted'] = cursor.rowcount
            
            # Clean up old performance metrics
            cursor = conn.execute("""
                DELETE FROM performance_metrics 
                WHERE recorded_at < ?
            """, (cutoff_date,))
            cleanup_results['metrics_deleted'] = cursor.rowcount
            
            # Vacuum to reclaim space
            conn.execute("VACUUM")
            cleanup_results['vacuum_performed'] = True
        
        return cleanup_results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        stats = {}
        
        with self._get_connection() as conn:
            # Table row counts
            tables = ['orders', 'positions', 'trades', 'account_snapshots', 'performance_metrics']
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()['count']
            
            # Database size
            cursor = conn.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor = conn.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            stats['database_size_bytes'] = page_count * page_size
            
            # Compression efficiency
            cursor = conn.execute("""
                SELECT 
                    AVG(CASE WHEN compression_level > 0 THEN LENGTH(data_compressed) ELSE LENGTH(data_json) END) as avg_size,
                    compression_level
                FROM orders 
                GROUP BY compression_level
            """)
            stats['compression_stats'] = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Schema version
            cursor = conn.execute("SELECT MAX(version) as version FROM schema_migrations")
            stats['schema_version'] = cursor.fetchone()['version']
        
        return stats
    
    def _get_migration_scripts(self) -> List[MigrationScript]:
        """Define database migration scripts"""
        return [
            MigrationScript(
                version=2,
                description="Add compression support",
                up_script="""
                    ALTER TABLE orders ADD COLUMN data_compressed BLOB;
                    ALTER TABLE orders ADD COLUMN compression_level INTEGER DEFAULT 0;
                    ALTER TABLE positions ADD COLUMN data_compressed BLOB;
                    ALTER TABLE positions ADD COLUMN compression_level INTEGER DEFAULT 0;
                    ALTER TABLE trades ADD COLUMN data_compressed BLOB;
                    ALTER TABLE trades ADD COLUMN compression_level INTEGER DEFAULT 0;
                """
            ),
            MigrationScript(
                version=3,
                description="Add versioning and performance monitoring",
                up_script="""
                    ALTER TABLE orders ADD COLUMN version INTEGER DEFAULT 1;
                    ALTER TABLE positions ADD COLUMN version INTEGER DEFAULT 1;
                    ALTER TABLE trades ADD COLUMN version INTEGER DEFAULT 1;
                    
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        tags TEXT,
                        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time 
                    ON performance_metrics(metric_name, recorded_at DESC);
                """
            )
        ]
    
    def _apply_migrations(self, conn: sqlite3.Connection):
        """Apply pending database migrations"""
        # Get current version
        try:
            cursor = conn.execute("SELECT MAX(version) as version FROM schema_migrations")
            current_version = cursor.fetchone()['version'] or 0
        except sqlite3.OperationalError:
            current_version = 0
        
        # Apply pending migrations
        for migration in self._migrations:
            if migration.version > current_version:
                try:
                    conn.executescript(migration.up_script)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                        (migration.version, migration.description)
                    )
                    print(f"Applied migration {migration.version}: {migration.description}")
                except Exception as e:
                    print(f"Migration {migration.version} failed: {e}")
                    raise
```

---

## State Management Integration

### Enhanced OmsEngine Integration

```python
# foxtrot/server/engines/enhanced_oms_engine.py
from foxtrot.server.engines.base_engine import BaseEngine
from foxtrot.server.cache.cache_manager import TradingDataCacheManager
from foxtrot.server.persistence.advanced_persistence import AdvancedSqlitePersistence
from foxtrot.util.event_type import *
from foxtrot.util.structured_logger import StructuredLogger
import threading
import time

class EnhancedOmsEngine(BaseEngine):
    """Enhanced OMS Engine with advanced caching and persistence"""
    
    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine, "oms")
        
        # Initialize persistence and caching
        self.persistence = AdvancedSqlitePersistence()
        self.cache_manager = TradingDataCacheManager(
            persistent_cache=self.persistence
        )
        
        # Logger
        self.logger = StructuredLogger("foxtrot.oms")
        
        # Background tasks
        self._background_thread = None
        self._stop_event = threading.Event()
        
        # Load initial state
        self._load_state()
        
        # Register event handlers
        self._register_handlers()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _register_handlers(self):
        """Register event handlers"""
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
    
    def _load_state(self):
        """Load state from persistence on startup"""
        with self.logger.timer("oms_state_loading"):
            try:
                # Load active orders
                active_orders = self.persistence.get_orders_by_status("Active")
                for order in active_orders:
                    self.cache_manager.cache_order(order)
                
                self.logger.info(
                    "OMS state loaded successfully",
                    active_orders_count=len(active_orders)
                )
                
            except Exception as e:
                self.logger.error(
                    "Failed to load OMS state",
                    error=str(e)
                )
                raise
    
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        self._background_thread = threading.Thread(
            target=self._background_worker,
            name="oms_background",
            daemon=True
        )
        self._background_thread.start()
    
    def _background_worker(self):
        """Background worker for maintenance tasks"""
        while not self._stop_event.wait(30):  # Run every 30 seconds
            try:
                # Cleanup expired cache entries
                self.cache_manager.cache.l1_cache.cleanup_expired()
                
                # Periodic database maintenance (every 5 minutes)
                if int(time.time()) % 300 == 0:
                    stats = self.persistence.get_database_stats()
                    self.logger.info(
                        "Database statistics",
                        **stats
                    )
                
            except Exception as e:
                self.logger.error(
                    "Background task error",
                    error=str(e)
                )
    
    def process_order_event(self, event):
        """Process order events with caching and persistence"""
        order = event.data
        
        with self.logger.timer("order_processing", order_id=order.vt_orderid):
            try:
                # Update cache first (fastest access)
                self.cache_manager.cache_order(order)
                
                # Persist to database
                self.persistence.save_order(order)
                
                self.logger.info(
                    "Order processed successfully",
                    order_id=order.vt_orderid,
                    symbol=order.symbol,
                    status=order.status.value
                )
                
            except Exception as e:
                self.logger.error(
                    "Failed to process order event",
                    order_id=order.vt_orderid,
                    error=str(e)
                )
                raise
    
    def process_position_event(self, event):
        """Process position events"""
        position = event.data
        
        with self.logger.timer("position_processing", position_id=position.vt_positionid):
            try:
                # Update cache and persistence
                self.cache_manager.cache_position(position)
                self.persistence.save_position(position)
                
                self.logger.info(
                    "Position processed successfully",
                    position_id=position.vt_positionid,
                    symbol=position.symbol,
                    volume=position.volume
                )
                
            except Exception as e:
                self.logger.error(
                    "Failed to process position event",
                    position_id=position.vt_positionid,
                    error=str(e)
                )
                raise
    
    def get_order(self, vt_orderid: str) -> Optional['OrderData']:
        """Get order with optimized cache lookup"""
        with self.logger.timer("order_lookup"):
            return self.cache_manager.get_order(vt_orderid)
    
    def get_all_orders(self) -> List['OrderData']:
        """Get all orders (implementation would use proper indexing)"""
        # This would be implemented with proper cache indexing
        # For now, simplified version
        return []
    
    def get_position(self, vt_positionid: str) -> Optional['PositionData']:
        """Get position with optimized lookup"""
        return self.cache_manager.get_position(vt_positionid)
    
    def close(self):
        """Clean shutdown of OMS engine"""
        with self.logger.timer("oms_shutdown"):
            # Stop background tasks
            self._stop_event.set()
            if self._background_thread:
                self._background_thread.join(timeout=5)
            
            # Final state save
            # Implementation would save all cached state
            
            self.logger.info("OMS Engine shutdown completed")
```

---

## Success Metrics

### State Management Quality Indicators
- **Cache Hit Rate**: >95% for frequently accessed data (orders, positions)
- **Persistence Reliability**: Zero data loss events, 100% crash recovery
- **Query Performance**: <1ms cache lookups, <10ms database queries
- **Storage Efficiency**: >50% space savings through compression

### Operational Benefits
- **Startup Performance**: <5 seconds to load complete state
- **Memory Efficiency**: 70% reduction in memory usage vs naive approach
- **Persistence Reliability**: Guaranteed state consistency across restarts
- **Scalability**: Support for 100K+ orders with consistent performance

This enhanced state management system transforms Foxtrot's data handling from basic in-memory storage to a production-grade persistence and caching framework, enabling reliable operation at scale while maintaining Python simplicity.