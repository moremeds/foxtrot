# Foxtrot Trading Platform - Print Statement to Loguru Migration Plan

**Plan Version:** 1.0  
**Created:** 2025-01-02  
**Target Completion:** 4 weeks  
**Total Print Statements to Migrate:** 39 (core foxtrot/ codebase)

## Executive Summary

This comprehensive migration plan addresses the systematic replacement of 39 print() statements in the Foxtrot trading platform core codebase with proper loguru logging. The plan prioritizes performance-critical paths, maintains thread safety, and preserves user experience while establishing a robust, scalable logging architecture.

### Key Success Metrics
- **Zero performance regression** in EventEngine hot paths (target: <2% impact)
- **100% migration** of core print statements (39 total)
- **Thread-safe logging** across all components
- **Structured log format** with component context
- **Preserved user experience** in TUI and test environments

---

## 1. Migration Strategy Overview

### 1.1 High-Level Approach

**Incremental Migration Strategy:**
- **Phase-based implementation** with validation at each stage
- **Performance-first approach** for critical paths
- **Context-aware logging** with component-specific loggers
- **Selective preservation** of user-facing print statements
- **Comprehensive testing** at each phase

**Core Principles:**
1. **No breaking changes** to existing functionality
2. **Performance optimization** for high-frequency paths
3. **Thread safety** across all logging operations
4. **Structured logging** for operational monitoring
5. **Backward compatibility** with existing codebase patterns

### 1.2 Risk Mitigation Strategies

| Risk Category | Mitigation Strategy | Validation Method |
|---------------|-------------------|-------------------|
| **Performance Regression** | Conditional logging, async I/O, benchmarking | EventEngine throughput tests |
| **Thread Safety Issues** | Loguru thread-safe defaults, concurrent testing | Multi-threaded integration tests |
| **User Experience Impact** | Selective migration, preserve console output | Manual testing of TUI workflows |
| **System Integration Failure** | Robust fallback mechanisms, feature flags | End-to-end system testing |
| **Data Loss** | Gradual migration, comprehensive context preservation | Log output validation |

### 1.3 Success Criteria and Validation Methods

**Functional Success Criteria:**
- ✅ All 39 core print statements migrated to appropriate log levels
- ✅ Log files created with correct structure and rotation
- ✅ Component context preserved in all log entries
- ✅ Error handling maintains full stack trace information

**Performance Success Criteria:**
- ✅ EventEngine throughput regression <2%
- ✅ Memory usage increase <10MB
- ✅ Log I/O operations don't block critical paths
- ✅ Startup time increase <500ms

**Operational Success Criteria:**
- ✅ Log aggregation ready for production monitoring
- ✅ Debug information accessible for development
- ✅ Test output preserved for developer workflow
- ✅ Configuration management through settings

---

## 2. Logging Architecture Design

### 2.1 Directory Structure

```
foxtrot_cache/logs/
├── main/
│   ├── foxtrot-{YYYY-MM-DD}.log              # Main application logs (INFO+)
│   └── foxtrot-debug-{YYYY-MM-DD}.log        # Debug level logs
├── adapters/
│   ├── binance-{YYYY-MM-DD}.log              # Binance adapter specific
│   ├── ibrokers-{YYYY-MM-DD}.log             # IB adapter specific
│   └── crypto-{YYYY-MM-DD}.log               # Crypto adapter specific
├── performance/
│   ├── events-{YYYY-MM-DD}.log               # Event processing metrics
│   └── adapters-{YYYY-MM-DD}.log             # Adapter performance data
└── errors/
    └── errors-{YYYY-MM-DD}.log               # ERROR level only aggregation
```

### 2.2 Context-Aware Logging Configuration

**Enhanced Logger Format:**
```
2025-01-02 10:30:45.123 | INFO     | EventEngine  | Handler registered for EVENT_TICK
2025-01-02 10:30:45.124 | ERROR    | Adapter.BIN  | Connection failed: Network timeout
2025-01-02 10:30:45.125 | DEBUG    | OrderManager | Order validation passed for SPY.SMART
```

**Context Fields:**
- **Timestamp:** Millisecond precision for event correlation
- **Level:** Standard loguru levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Component:** Hierarchical component identification (Engine.EventEngine, Adapter.Binance)
- **Message:** Human-readable message with structured context
- **Extra Fields:** event_type, adapter_name, correlation_id, performance_metrics

### 2.3 Log File Naming and Rotation Strategy

**Naming Convention:**
- `{component}-{YYYY-MM-DD}.log` for component-specific logs
- `{category}-{YYYY-MM-DD}.log` for functional category logs

**Rotation Policy:**
- **Daily rotation** at midnight local time
- **Size-based rotation** at 100MB per file
- **Retention period** of 30 days (configurable)
- **Compression** of archived logs older than 7 days

**Configuration:**
```python
# Log rotation settings
SETTINGS = {
    "log.max_file_size": "100MB",
    "log.retention_days": 30,
    "log.compression": True,
    "log.rotation_time": "00:00"
}
```

### 2.4 Performance Optimization Considerations

**Hot Path Optimization:**
```python
# Conditional logging for performance-critical paths
if logger.level <= DEBUG:
    logger.debug("High-frequency event", extra=context)

# Async logging for non-blocking I/O
logger.add("async_sink.log", enqueue=True, serialize=True)

# Context caching to avoid repeated bind() calls
class ComponentLogger:
    def __init__(self, component_name: str):
        self._logger = logger.bind(component=component_name)
```

**Memory Management:**
- **Structured logging** to avoid string formatting overhead
- **Context object reuse** for high-frequency events
- **Buffer management** for async logging queues
- **Memory-mapped files** for high-throughput scenarios

---

## 3. Implementation Phases

### 3.1 Phase 1: Foundation & Critical Paths (Week 1)

**Objective:** Establish logging infrastructure and migrate performance-critical components

**Entry Criteria:**
- ✅ Development environment setup complete
- ✅ Feature branch created (`feature/loguru-migration-phase1`)
- ✅ Baseline performance measurements taken

**Tasks:**

#### Task 1.1: Enhanced Logger Infrastructure (Day 1-2)
```bash
# File: foxtrot/util/logger.py (enhance existing)
```

**Implementation:**
```python
from loguru import logger
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .settings import SETTINGS

class FoxtrotLogger:
    """Enhanced logging system for Foxtrot trading platform."""
    
    def __init__(self):
        self._component_loggers: Dict[str, Any] = {}
        self._configure_loggers()
    
    def _configure_loggers(self):
        """Configure loguru with Foxtrot-specific settings."""
        # Remove default handler
        logger.remove()
        
        # Performance-optimized format
        format_template = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{extra[component]: <12}</cyan> "
            "| <level>{message}</level>"
        )
        
        # Add handlers based on configuration
        self._add_console_handler(format_template)
        self._add_file_handlers(format_template)
    
    def _add_console_handler(self, format_template: str):
        """Add console handler if enabled."""
        if SETTINGS.get("log.console", True):
            level = SETTINGS.get("log.level", 20)  # INFO level default
            logger.add(
                sink=sys.stdout,
                level=level,
                format=format_template,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
    
    def _add_file_handlers(self, format_template: str):
        """Add file handlers with rotation."""
        if not SETTINGS.get("log.file", True):
            return
            
        log_dir = Path(SETTINGS.get("log.dir", "foxtrot_cache/logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application log
        logger.add(
            sink=log_dir / "main" / "foxtrot-{time:YYYY-MM-DD}.log",
            level="INFO",
            format=format_template,
            rotation="1 day",
            retention=f"{SETTINGS.get('log.retention_days', 30)} days",
            compression="gz"
        )
        
        # Debug log
        logger.add(
            sink=log_dir / "main" / "foxtrot-debug-{time:YYYY-MM-DD}.log",
            level="DEBUG",
            format=format_template,
            rotation="100 MB",
            retention="7 days",
            compression="gz"
        )
        
        # Error aggregation log
        logger.add(
            sink=log_dir / "errors" / "errors-{time:YYYY-MM-DD}.log",
            level="ERROR",
            format=format_template,
            rotation="1 day",
            retention="90 days"
        )
    
    def get_component_logger(self, component_name: str):
        """Get a component-specific logger with context."""
        if component_name not in self._component_loggers:
            self._component_loggers[component_name] = logger.bind(
                component=component_name
            )
        return self._component_loggers[component_name]
    
    def get_performance_logger(self, component_name: str):
        """Get a high-performance logger for hot paths."""
        perf_enabled = SETTINGS.get("log.performance", False)
        return logger.bind(
            component=component_name,
            performance=perf_enabled
        )
    
    def get_adapter_logger(self, adapter_name: str):
        """Get an adapter-specific logger."""
        log_dir = Path(SETTINGS.get("log.dir", "foxtrot_cache/logs"))
        
        if SETTINGS.get("log.adapter_specific", True):
            adapter_log_path = log_dir / "adapters" / f"{adapter_name.lower()}-{{time:YYYY-MM-DD}}.log"
            logger.add(
                sink=str(adapter_log_path),
                level="DEBUG",
                format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                rotation="1 day",
                retention="14 days",
                filter=lambda record: record["extra"].get("adapter") == adapter_name
            )
        
        return logger.bind(component=f"Adapter.{adapter_name}", adapter=adapter_name)

# Global logger instance
_foxtrot_logger = None

def get_foxtrot_logger() -> FoxtrotLogger:
    """Get the global Foxtrot logger instance."""
    global _foxtrot_logger
    if _foxtrot_logger is None:
        _foxtrot_logger = FoxtrotLogger()
    return _foxtrot_logger

# Convenience functions for backward compatibility
def get_component_logger(component_name: str):
    """Get a component-specific logger."""
    return get_foxtrot_logger().get_component_logger(component_name)

def get_performance_logger(component_name: str):
    """Get a performance-optimized logger."""
    return get_foxtrot_logger().get_performance_logger(component_name)

def get_adapter_logger(adapter_name: str):
    """Get an adapter-specific logger."""
    return get_foxtrot_logger().get_adapter_logger(adapter_name)
```

#### Task 1.2: EventEngine Critical Path Migration (Day 2-3)
**Priority: CRITICAL - Performance hot path**

**Files to modify:**
- `foxtrot/core/event_engine.py` (lines 82, 91, 146, 151)

**Implementation:**
```python
# File: foxtrot/core/event_engine.py

from foxtrot.util.logger import get_performance_logger
from typing import Dict, List, Callable, Any
import threading
import queue
from datetime import datetime

class EventEngine:
    """Event-driven engine for Foxtrot trading platform."""
    
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._active: bool = False
        self._thread: threading.Thread = None
        self._timer_thread: threading.Thread = None
        self._handlers: Dict[str, List[Callable]] = {}
        self._general_handlers: List[Callable] = []
        
        # Performance-optimized logger for hot path
        self.logger = get_performance_logger("EventEngine")
        
        self.logger.info("EventEngine initialized")
    
    def _process(self, event: Event) -> None:
        """
        Process event with optimized error handling.
        
        CRITICAL PERFORMANCE PATH - processes 1000+ events/sec
        """
        # Process specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    # MIGRATION: Replace print with structured logging
                    # OLD: print(f"Handler failed for event {event.type}: {type(e).__name__}: {str(e)}")
                    self.logger.error(
                        "Event handler failed",
                        extra={
                            "event_type": event.type,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                            "handler_name": getattr(handler, '__name__', 'unknown'),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
        
        # Process general handlers
        for handler in self._general_handlers:
            try:
                handler(event)
            except Exception as e:
                # MIGRATION: Replace print with structured logging
                # OLD: print(f"General handler failed for event {event.type}: {type(e).__name__}: {str(e)}")
                self.logger.error(
                    "General event handler failed",
                    extra={
                        "event_type": event.type,
                        "error_type": type(e).__name__,
                        "error_msg": str(e),
                        "handler_name": getattr(handler, '__name__', 'unknown'),
                        "handler_type": "general",
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    def stop(self) -> None:
        """Stop event engine with proper shutdown logging."""
        self.logger.info("EventEngine shutdown initiated")
        self._active = False
        
        # Wait for main thread with timeout
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                # MIGRATION: Replace print with WARNING logging
                # OLD: print("Warning: Main thread didn't terminate within timeout")
                self.logger.warning(
                    "Main thread shutdown timeout",
                    extra={
                        "timeout_seconds": 5.0,
                        "thread_alive": True,
                        "shutdown_phase": "main_thread"
                    }
                )
        
        # Wait for timer thread with timeout
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=5.0)
            if self._timer_thread.is_alive():
                # MIGRATION: Replace print with WARNING logging
                # OLD: print("Warning: Timer thread didn't terminate within timeout")
                self.logger.warning(
                    "Timer thread shutdown timeout",
                    extra={
                        "timeout_seconds": 5.0,
                        "thread_alive": True,
                        "shutdown_phase": "timer_thread"
                    }
                )
        
        self.logger.info("EventEngine shutdown completed")
```

#### Task 1.3: Performance Baseline Testing (Day 3-4)
**Create performance validation suite**

```python
# File: tests/performance/test_logging_performance.py

import pytest
import time
import threading
from foxtrot.core.event_engine import EventEngine, Event
from foxtrot.util.logger import get_performance_logger
import statistics

class TestLoggingPerformance:
    """Performance tests for logging migration."""
    
    def test_event_engine_throughput_baseline(self):
        """Measure EventEngine throughput with new logging."""
        engine = EventEngine()
        engine.start()
        
        # Test event handler that triggers error logging
        def failing_handler(event):
            if event.data.get("trigger_error"):
                raise ValueError("Test error for logging performance")
        
        engine.register(handler=failing_handler, event_type="TEST_EVENT")
        
        # Measure processing time for batch of events
        event_count = 1000
        error_events = 100  # 10% error rate
        
        start_time = time.perf_counter()
        
        for i in range(event_count):
            event = Event(
                type="TEST_EVENT",
                data={"trigger_error": i < error_events, "sequence": i}
            )
            engine.put(event)
        
        # Wait for processing to complete
        time.sleep(2.0)
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        throughput = event_count / processing_time
        
        engine.stop()
        
        # Performance assertion: minimum 500 events/sec
        assert throughput > 500, f"Throughput {throughput:.2f} events/sec below minimum"
        
        return {
            "throughput": throughput,
            "processing_time": processing_time,
            "event_count": event_count,
            "error_rate": error_events / event_count
        }
    
    def test_concurrent_logging_performance(self):
        """Test logging performance under concurrent load."""
        logger = get_performance_logger("ConcurrencyTest")
        thread_count = 10
        messages_per_thread = 100
        
        def logging_worker(thread_id: int, results: list):
            start_time = time.perf_counter()
            
            for i in range(messages_per_thread):
                logger.info(
                    f"Concurrent message {i}",
                    extra={
                        "thread_id": thread_id,
                        "message_seq": i,
                        "test_type": "concurrency"
                    }
                )
            
            end_time = time.perf_counter()
            results.append(end_time - start_time)
        
        threads = []
        results = []
        
        overall_start = time.perf_counter()
        
        # Start all threads
        for thread_id in range(thread_count):
            thread = threading.Thread(
                target=logging_worker,
                args=(thread_id, results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        overall_end = time.perf_counter()
        
        total_messages = thread_count * messages_per_thread
        overall_throughput = total_messages / (overall_end - overall_start)
        avg_thread_time = statistics.mean(results)
        
        # Performance assertions
        assert overall_throughput > 1000, f"Concurrent throughput {overall_throughput:.2f} msg/sec too low"
        assert avg_thread_time < 2.0, f"Average thread time {avg_thread_time:.2f}s too high"
        
        return {
            "overall_throughput": overall_throughput,
            "avg_thread_time": avg_thread_time,
            "total_messages": total_messages,
            "thread_count": thread_count
        }
```

**Exit Criteria:**
- ✅ Enhanced logger infrastructure implemented and tested
- ✅ EventEngine critical path migrated with no performance regression
- ✅ Performance baseline established (>500 events/sec throughput)
- ✅ Unit tests passing for new logging functionality
- ✅ Integration tests validate thread safety

**Rollback Plan:**
- Git revert to pre-migration state
- Re-enable print statements with feature flag
- Performance regression triggers immediate rollback

### 3.2 Phase 2: Infrastructure Components (Week 2)

**Objective:** Migrate initialization and configuration logging

**Entry Criteria:**
- ✅ Phase 1 completed and validated
- ✅ Performance tests passing
- ✅ Feature branch created (`feature/loguru-migration-phase2`)

**Tasks:**

#### Task 2.1: Database Initialization Logging (Day 5-6)
**Files to modify:**
- `foxtrot/server/database.py` (line 126)

**Implementation:**
```python
# File: foxtrot/server/database.py

from foxtrot.util.logger import get_component_logger

class DatabaseManager:
    def __init__(self):
        self.logger = get_component_logger("Database")
    
    def init_database_driver(self, module_name: str):
        """Initialize database driver with proper logging."""
        try:
            # Attempt to import custom driver
            driver_module = __import__(module_name)
            self.logger.info(
                "Database driver loaded successfully",
                extra={
                    "driver_name": module_name,
                    "driver_type": "custom"
                }
            )
            return driver_module
        except ImportError:
            # MIGRATION: Replace print with INFO logging
            # OLD: print(f"Can't find database driver {module_name}, using default SQLite database")
            self.logger.info(
                "Custom database driver not found, using SQLite fallback",
                extra={
                    "requested_driver": module_name,
                    "fallback_driver": "sqlite",
                    "fallback_reason": "import_error"
                }
            )
            return self._get_sqlite_driver()
```

#### Task 2.2: Datafeed Configuration Logging (Day 6-7)
**Files to modify:**
- `foxtrot/server/datafeed.py` (lines 55-57, 71-73)

**Implementation:**
```python
# File: foxtrot/server/datafeed.py

from foxtrot.util.logger import get_component_logger

class DatafeedManager:
    def __init__(self):
        self.logger = get_component_logger("Datafeed")
    
    def check_datafeed_configuration(self):
        """Check datafeed configuration with structured logging."""
        if not self._has_datafeed_config():
            # MIGRATION: Replace multi-line print with WARNING logging
            # OLD: print("No datafeed configuration found...")
            self.logger.warning(
                "No datafeed configuration found",
                extra={
                    "configuration_file": "vt_setting.json",
                    "required_fields": ["datafeed.name", "datafeed.username", "datafeed.password"],
                    "action_required": "configure_datafeed_settings",
                    "documentation": "https://docs.foxtrot.trading/datafeed"
                }
            )
            return False
        return True
    
    def load_datafeed_module(self, module_name: str):
        """Load datafeed module with error handling."""
        try:
            module = __import__(f"foxtrot.adapter.{module_name}")
            self.logger.info(
                "Datafeed module loaded successfully",
                extra={
                    "module_name": module_name,
                    "module_path": f"foxtrot.adapter.{module_name}"
                }
            )
            return module
        except ImportError as e:
            # MIGRATION: Replace multi-line print with WARNING logging
            # OLD: print("Failed to import datafeed module...")
            self.logger.warning(
                "Failed to import datafeed module",
                extra={
                    "module_name": module_name,
                    "error_type": type(e).__name__,
                    "error_msg": str(e),
                    "suggested_action": f"pip install {module_name}",
                    "alternative": "check module availability"
                }
            )
            return None
```

#### Task 2.3: Infrastructure Testing (Day 7-8)
**Create comprehensive infrastructure tests**

```python
# File: tests/unit/server/test_database_logging.py

import pytest
from unittest.mock import patch, MagicMock
from foxtrot.server.database import DatabaseManager

class TestDatabaseLogging:
    """Test database logging functionality."""
    
    def test_successful_driver_loading_logs(self, caplog):
        """Test successful driver loading creates appropriate logs."""
        db_manager = DatabaseManager()
        
        with patch('builtins.__import__') as mock_import:
            mock_module = MagicMock()
            mock_import.return_value = mock_module
            
            result = db_manager.init_database_driver("custom_driver")
            
            # Verify log entry
            assert "Database driver loaded successfully" in caplog.text
            assert "custom_driver" in caplog.text
            assert result == mock_module
    
    def test_driver_fallback_logs(self, caplog):
        """Test driver fallback creates appropriate logs."""
        db_manager = DatabaseManager()
        
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            with patch.object(db_manager, '_get_sqlite_driver') as mock_sqlite:
                mock_sqlite.return_value = MagicMock()
                
                result = db_manager.init_database_driver("missing_driver")
                
                # Verify log entry
                assert "using SQLite fallback" in caplog.text
                assert "missing_driver" in caplog.text
                assert mock_sqlite.called
```

**Exit Criteria:**
- ✅ Database initialization logging implemented
- ✅ Datafeed configuration logging implemented
- ✅ Structured log context includes all relevant information
- ✅ Unit tests validate log output and content
- ✅ Integration tests confirm startup process logging

### 3.3 Phase 3: Adapter Components (Week 2-3)

**Objective:** Migrate adapter logging to structured format

**Entry Criteria:**
- ✅ Phase 2 completed and validated
- ✅ Infrastructure logging working correctly
- ✅ Feature branch created (`feature/loguru-migration-phase3`)

**Tasks:**

#### Task 3.1: Binance Adapter Logging (Day 8-10)
**Files to modify:**
- `foxtrot/adapter/binance/api_client.py` (lines 133, 137)

**Implementation:**
```python
# File: foxtrot/adapter/binance/api_client.py

from foxtrot.util.logger import get_adapter_logger

class BinanceApiClient:
    """Binance API client with structured logging."""
    
    def __init__(self, event_engine, adapter_name: str):
        self.event_engine = event_engine
        self.adapter_name = adapter_name
        self.logger = get_adapter_logger("Binance")
        
        self.logger.info(
            "Binance API client initialized",
            extra={
                "adapter_name": adapter_name,
                "initialization_time": datetime.now().isoformat()
            }
        )
    
    def log_info(self, message: str, **context) -> None:
        """Log info message with adapter context."""
        # MIGRATION: Replace print with structured logging
        # OLD: print(f"[{self.adapter_name}] INFO: {message}")
        self.logger.info(
            message,
            extra={
                "adapter_name": self.adapter_name,
                "log_type": "info",
                **context
            }
        )
    
    def log_error(self, message: str, error: Exception = None, **context) -> None:
        """Log error message with adapter context."""
        # MIGRATION: Replace print with structured logging
        # OLD: print(f"[{self.adapter_name}] ERROR: {message}")
        error_context = {
            "adapter_name": self.adapter_name,
            "log_type": "error",
            **context
        }
        
        if error:
            error_context.update({
                "error_type": type(error).__name__,
                "error_msg": str(error),
                "error_traceback": format_exc() if self.logger.level <= DEBUG else None
            })
        
        self.logger.error(message, extra=error_context)
    
    def connect(self):
        """Connect to Binance with connection logging."""
        try:
            self.logger.info(
                "Attempting Binance connection",
                extra={
                    "adapter_name": self.adapter_name,
                    "connection_type": "ccxt",
                    "exchange": "binance"
                }
            )
            
            # Connection logic here
            result = self._establish_connection()
            
            self.logger.info(
                "Binance connection established",
                extra={
                    "adapter_name": self.adapter_name,
                    "connection_status": "connected",
                    "account_type": result.get("account_type", "unknown")
                }
            )
            
            return result
            
        except Exception as e:
            self.log_error(
                "Binance connection failed",
                error=e,
                connection_attempt=1,
                retry_available=True
            )
            raise
```

#### Task 3.2: Crypto Adapter Components Migration (Day 10-12)
**Files to modify:**
- `foxtrot/adapter/crypto/crypto_adapter.py`
- `foxtrot/adapter/crypto/account_manager.py`
- `foxtrot/adapter/crypto/market_data.py`
- `foxtrot/adapter/crypto/order_manager.py`

**Pattern for all crypto adapter components:**
```python
# Template for crypto adapter component migration

from foxtrot.util.logger import get_adapter_logger

class CryptoComponent:
    """Base pattern for crypto adapter components."""
    
    def __init__(self, adapter_name: str, component_type: str):
        self.adapter_name = adapter_name
        self.component_type = component_type
        self.logger = get_adapter_logger(f"Crypto.{component_type}")
    
    def log_operation(self, operation: str, status: str, **context):
        """Log component operation with structured context."""
        log_level = "info" if status == "success" else "error"
        
        log_context = {
            "adapter_name": self.adapter_name,
            "component_type": self.component_type,
            "operation": operation,
            "status": status,
            **context
        }
        
        getattr(self.logger, log_level)(
            f"{operation} {status}",
            extra=log_context
        )

# Example: Market Data Component
class MarketDataManager(CryptoComponent):
    def __init__(self, adapter_name: str):
        super().__init__(adapter_name, "MarketData")
    
    def subscribe_ticker(self, symbol: str):
        """Subscribe to ticker with logging."""
        try:
            # MIGRATION: Replace debug print statements
            self.log_operation(
                operation="subscribe_ticker",
                status="attempting",
                symbol=symbol,
                subscription_type="ticker"
            )
            
            # Subscription logic here
            result = self._perform_subscription(symbol)
            
            self.log_operation(
                operation="subscribe_ticker",
                status="success",
                symbol=symbol,
                subscription_id=result.get("subscription_id")
            )
            
        except Exception as e:
            self.log_operation(
                operation="subscribe_ticker",
                status="failed",
                symbol=symbol,
                error_type=type(e).__name__,
                error_msg=str(e)
            )
            raise
```

#### Task 3.3: Adapter Testing and Validation (Day 12-13)
**Create adapter-specific logging tests**

```python
# File: tests/unit/adapter/test_adapter_logging.py

import pytest
from unittest.mock import MagicMock, patch
from foxtrot.adapter.binance.api_client import BinanceApiClient

class TestAdapterLogging:
    """Test adapter logging functionality."""
    
    def test_binance_connection_success_logging(self, caplog):
        """Test successful Binance connection logging."""
        event_engine = MagicMock()
        client = BinanceApiClient(event_engine, "TEST_BINANCE")
        
        with patch.object(client, '_establish_connection') as mock_connect:
            mock_connect.return_value = {"account_type": "spot"}
            
            client.connect()
            
            # Verify log entries
            assert "Attempting Binance connection" in caplog.text
            assert "Binance connection established" in caplog.text
            assert "TEST_BINANCE" in caplog.text
    
    def test_binance_connection_failure_logging(self, caplog):
        """Test failed Binance connection logging."""
        event_engine = MagicMock()
        client = BinanceApiClient(event_engine, "TEST_BINANCE")
        
        with patch.object(client, '_establish_connection') as mock_connect:
            mock_connect.side_effect = ConnectionError("Network timeout")
            
            with pytest.raises(ConnectionError):
                client.connect()
            
            # Verify error log entry
            assert "Binance connection failed" in caplog.text
            assert "Network timeout" in caplog.text
            assert "ConnectionError" in caplog.text
```

**Exit Criteria:**
- ✅ Binance adapter logging migrated and tested
- ✅ Crypto adapter components migrated (12 print statements)
- ✅ Adapter-specific log files created correctly
- ✅ Connection lifecycle logging implemented
- ✅ Error context preserved in adapter logs

### 3.4 Phase 4: TUI Components (Week 3)

**Objective:** Selective migration of TUI components while preserving user experience

**Entry Criteria:**
- ✅ Phase 3 completed and validated
- ✅ Adapter logging working correctly
- ✅ Feature branch created (`feature/loguru-migration-phase4`)

**Tasks:**

#### Task 4.1: Monitor Component Logging (Day 13-14)
**Files to modify:**
- `foxtrot/app/tui/components/base_monitor.py` (lines 356, 433)

**Implementation:**
```python
# File: foxtrot/app/tui/components/base_monitor.py

from foxtrot.util.logger import get_component_logger

class BaseMonitor:
    """Base monitor with structured logging."""
    
    def __init__(self, monitor_name: str):
        self.monitor_name = monitor_name
        self.logger = get_component_logger(f"TUI.Monitor.{monitor_name}")
    
    def log_monitor_event(self, level: str, message: str, **context):
        """Log monitor event with context."""
        # MIGRATION: Replace print statements
        # OLD: print(f"ERROR/INFO [{self.monitor_name}]: {message}")
        
        log_context = {
            "monitor_name": self.monitor_name,
            "monitor_type": "base",
            **context
        }
        
        getattr(self.logger, level.lower())(message, extra=log_context)
    
    def handle_error(self, error: Exception, context: str = ""):
        """Handle monitor error with structured logging."""
        self.log_monitor_event(
            level="error",
            message=f"Monitor error in {context}",
            error_type=type(error).__name__,
            error_msg=str(error),
            context=context
        )
    
    def log_info(self, message: str, **context):
        """Log monitor info message."""
        self.log_monitor_event(
            level="info",
            message=message,
            **context
        )
```

#### Task 4.2: TUI Main App Selective Migration (Day 14-15)
**Files to modify:**
- `foxtrot/app/tui/main_app.py` (selective migration of 18 statements)

**Strategy:**
- **Migrate internal logging** (debug fallback on line 284)
- **Keep user-facing output** (startup messages, ASCII banner)
- **Migrate error handling** (import errors, startup failures)

**Implementation:**
```python
# File: foxtrot/app/tui/main_app.py

from foxtrot.util.logger import get_component_logger

class TUIMainApp:
    """TUI Main Application with selective logging migration."""
    
    def __init__(self):
        self.logger = get_component_logger("TUI.MainApp")
    
    def debug_log_fallback(self, level: str, message: str):
        """Debug logging fallback - MIGRATE THIS."""
        # MIGRATION: Replace print fallback with robust logging
        # OLD: print(f"[{level}] {message}")
        try:
            getattr(self.logger, level.lower())(
                message,
                extra={
                    "fallback": True,
                    "original_level": level
                }
            )
        except Exception:
            # Last resort fallback to console
            print(f"[FALLBACK-{level}] {message}")
    
    def display_startup_banner(self):
        """Display startup banner - KEEP AS CONSOLE OUTPUT."""
        # KEEP: User-facing ASCII banner and instructions
        banner = """
╔══════════════════════════════════════╗
║          Foxtrot Trading             ║
║        Event-Driven Platform         ║
╚══════════════════════════════════════╝
        """
        print(banner)  # KEEP: User interface
        
        # MIGRATE: Internal startup logging
        self.logger.info(
            "TUI application started",
            extra={
                "startup_time": datetime.now().isoformat(),
                "display_mode": "console"
            }
        )
    
    def handle_startup_error(self, error: Exception, component: str):
        """Handle startup errors with dual output."""
        # MIGRATE: Internal error logging
        self.logger.error(
            "TUI startup component failed",
            extra={
                "component": component,
                "error_type": type(error).__name__,
                "error_msg": str(error),
                "startup_phase": "initialization"
            }
        )
        
        # KEEP: User-friendly error message
        print(f"❌ Error starting {component}: {str(error)}")
        print("   Please check the logs for detailed information.")
    
    def handle_import_error(self, module_name: str, error: Exception):
        """Handle import errors with user guidance."""
        # MIGRATE: Internal error logging
        self.logger.error(
            "Module import failed",
            extra={
                "module_name": module_name,
                "error_type": type(error).__name__,
                "error_msg": str(error),
                "import_phase": "startup"
            }
        )
        
        # KEEP: User-friendly guidance
        print(f"❌ Failed to import {module_name}")
        print(f"   Suggestion: pip install {module_name}")
        print("   Falling back to basic functionality...")
```

**Exit Criteria:**
- ✅ Monitor component logging migrated
- ✅ TUI internal logging migrated while preserving user interface
- ✅ User-facing console output preserved
- ✅ Error handling provides both logging and user feedback
- ✅ Manual testing confirms TUI user experience unchanged

### 3.5 Phase 5: Validation & Optimization (Week 4)

**Objective:** Comprehensive validation, performance optimization, and documentation

**Entry Criteria:**
- ✅ All previous phases completed
- ✅ Core print statement migration complete (39 statements)
- ✅ Feature branch created (`feature/loguru-migration-validation`)

**Tasks:**

#### Task 5.1: Comprehensive Performance Benchmarking (Day 15-16)
**Create complete performance validation suite**

```python
# File: tests/performance/test_migration_performance.py

import pytest
import time
import threading
import statistics
from pathlib import Path
from foxtrot.core.event_engine import EventEngine
from foxtrot.adapter.binance.api_client import BinanceApiClient
from foxtrot.util.logger import get_foxtrot_logger

class TestMigrationPerformance:
    """Comprehensive performance tests for migration validation."""
    
    def test_system_throughput_benchmark(self):
        """Test complete system throughput with logging."""
        # Initialize system components
        event_engine = EventEngine()
        event_engine.start()
        
        binance_client = BinanceApiClient(event_engine, "PERF_TEST")
        
        # Simulate high-frequency trading scenario
        event_count = 5000
        error_rate = 0.05  # 5% error rate
        
        start_time = time.perf_counter()
        
        # Generate mixed event load
        for i in range(event_count):
            # Simulate market data events
            if i % 10 == 0:
                event = Event(type="EVENT_TICK", data={"symbol": "BTCUSDT"})
                event_engine.put(event)
            
            # Simulate order events with some errors
            if i % 20 == 0:
                try:
                    if i < (event_count * error_rate):
                        raise ValueError(f"Simulated order error {i}")
                    else:
                        binance_client.log_info("Order processed", order_id=f"order_{i}")
                except Exception as e:
                    binance_client.log_error("Order failed", error=e, order_id=f"order_{i}")
        
        # Wait for processing
        time.sleep(3.0)
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        throughput = event_count / processing_time
        
        event_engine.stop()
        
        # Performance assertions
        assert throughput > 1000, f"System throughput {throughput:.2f} events/sec too low"
        assert processing_time < 10.0, f"Processing time {processing_time:.2f}s too high"
        
        return {
            "system_throughput": throughput,
            "processing_time": processing_time,
            "event_count": event_count,
            "error_rate": error_rate
        }
    
    def test_memory_usage_validation(self):
        """Validate memory usage stays within acceptable bounds."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create multiple logger instances
        loggers = []
        for i in range(100):
            logger = get_component_logger(f"TestComponent_{i}")
            loggers.append(logger)
            
            # Generate log messages
            for j in range(50):
                logger.info(
                    f"Test message {j}",
                    extra={
                        "component_id": i,
                        "message_id": j,
                        "test_data": f"data_{i}_{j}"
                    }
                )
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - baseline_memory
        
        # Memory usage assertion
        assert memory_increase < 50, f"Memory increase {memory_increase:.2f}MB too high"
        
        return {
            "baseline_memory_mb": baseline_memory,
            "peak_memory_mb": peak_memory,
            "memory_increase_mb": memory_increase
        }
    
    def test_log_file_creation_validation(self):
        """Validate log files are created with correct structure."""
        logger_system = get_foxtrot_logger()
        
        # Generate logs across different components
        components = ["EventEngine", "Adapter.Binance", "TUI.Monitor"]
        
        for component in components:
            logger = logger_system.get_component_logger(component)
            
            logger.debug("Debug message for validation")
            logger.info("Info message for validation")
            logger.warning("Warning message for validation")
            logger.error("Error message for validation")
        
        # Wait for file writing
        time.sleep(1.0)
        
        # Validate log files exist
        log_dir = Path("foxtrot_cache/logs")
        
        expected_files = [
            log_dir / "main" / f"foxtrot-{datetime.now().strftime('%Y-%m-%d')}.log",
            log_dir / "main" / f"foxtrot-debug-{datetime.now().strftime('%Y-%m-%d')}.log",
            log_dir / "errors" / f"errors-{datetime.now().strftime('%Y-%m-%d')}.log"
        ]
        
        for log_file in expected_files:
            assert log_file.exists(), f"Log file {log_file} not created"
            assert log_file.stat().st_size > 0, f"Log file {log_file} is empty"
        
        return {"validated_files": [str(f) for f in expected_files]}
```

#### Task 5.2: Integration Testing (Day 16-17)
**Create end-to-end integration tests**

```python
# File: tests/integration/test_logging_integration.py

import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from foxtrot.server.engine import MainEngine
from foxtrot.adapter.binance.binance import BinanceAdapter

class TestLoggingIntegration:
    """Integration tests for complete logging system."""
    
    def test_main_engine_lifecycle_logging(self, caplog):
        """Test MainEngine lifecycle with logging."""
        # Create MainEngine instance
        main_engine = MainEngine()
        
        # Verify initialization logging
        assert "MainEngine initialized" in caplog.text
        
        # Test adapter addition
        with patch('foxtrot.adapter.binance.binance.BinanceAdapter') as MockAdapter:
            mock_adapter = MockAdapter.return_value
            main_engine.add_adapter(mock_adapter)
            
            # Verify adapter logging
            assert "Adapter added" in caplog.text
        
        # Test shutdown
        main_engine.close()
        
        # Verify shutdown logging
        assert "MainEngine shutdown" in caplog.text
    
    def test_cross_component_logging_correlation(self, caplog):
        """Test logging correlation across components."""
        main_engine = MainEngine()
        
        # Simulate event flow with logging
        event_engine = main_engine.event_engine
        
        # Create test event
        test_event = Event(
            type="EVENT_ORDER",
            data={"symbol": "BTCUSDT", "price": 50000}
        )
        
        # Process event (should trigger logging)
        event_engine.put(test_event)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify event processing logged
        assert "EVENT_ORDER" in caplog.text
        
        main_engine.close()
    
    def test_error_propagation_and_logging(self, caplog):
        """Test error propagation maintains logging context."""
        main_engine = MainEngine()
        
        # Create failing event handler
        def failing_handler(event):
            raise RuntimeError("Test error for logging validation")
        
        main_engine.event_engine.register(
            handler=failing_handler,
            event_type="TEST_ERROR_EVENT"
        )
        
        # Trigger error
        error_event = Event(type="TEST_ERROR_EVENT", data={})
        main_engine.event_engine.put(error_event)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Verify error logged with context
        assert "Event handler failed" in caplog.text
        assert "RuntimeError" in caplog.text
        assert "Test error for logging validation" in caplog.text
        
        main_engine.close()
```

#### Task 5.3: Documentation and Final Validation (Day 17-18)
**Create comprehensive documentation**

```markdown
# File: docs/LOGGING_MIGRATION_GUIDE.md

# Foxtrot Logging Migration Guide

## Overview
This guide documents the migration from print() statements to structured loguru logging in the Foxtrot trading platform.

## Logging Architecture

### Directory Structure
```
foxtrot_cache/logs/
├── main/                    # Main application logs
├── adapters/               # Adapter-specific logs
├── performance/            # Performance monitoring logs
└── errors/                # Error aggregation logs
```

### Logger Types

#### Component Logger
```python
from foxtrot.util.logger import get_component_logger

logger = get_component_logger("EventEngine")
logger.info("Component started", extra={"startup_time": "..."})
```

#### Performance Logger
```python
from foxtrot.util.logger import get_performance_logger

logger = get_performance_logger("EventEngine")
# Optimized for high-frequency logging
```

#### Adapter Logger
```python
from foxtrot.util.logger import get_adapter_logger

logger = get_adapter_logger("Binance")
# Creates adapter-specific log files
```

### Best Practices

1. **Use structured logging with context**
   ```python
   logger.error(
       "Operation failed",
       extra={
           "component": "OrderManager",
           "operation": "place_order",
           "symbol": "BTCUSDT",
           "error_type": "ValidationError"
       }
   )
   ```

2. **Include component context**
   - Always bind logger with component name
   - Include operation context in log messages
   - Add correlation IDs for request tracking

3. **Performance considerations**
   - Use appropriate log levels
   - Avoid expensive string formatting in hot paths
   - Consider async logging for high-frequency events

4. **Error handling**
   - Include full error context
   - Preserve stack traces for debugging
   - Add actionable information for operations

### Configuration

#### Settings (vt_setting.json)
```json
{
  "log.level": 20,
  "log.console": true,
  "log.file": true,
  "log.performance": false,
  "log.adapter_specific": true,
  "log.max_file_size": "100MB",
  "log.retention_days": 30
}
```

#### Environment Variables
- `FOXTROT_LOG_DIR`: Custom log directory
- `FOXTROT_LOG_LEVEL`: Runtime log level override
- `FOXTROT_ENV`: Environment detection (development/production/test)

### Migration Results

#### Performance Impact
- EventEngine throughput: <2% regression
- Memory usage: <10MB increase
- Startup time: <500ms increase

#### Migration Coverage
- ✅ 39/39 core print statements migrated
- ✅ Thread-safe logging implemented
- ✅ Structured context preserved
- ✅ User experience maintained
```

**Exit Criteria:**
- ✅ All performance benchmarks passing
- ✅ Integration tests validate cross-component logging
- ✅ Log file structure and rotation working correctly
- ✅ Documentation complete and accurate
- ✅ Final code review completed
- ✅ Migration ready for production deployment

---

## 4. Module-Specific Migration Plans

### 4.1 Core Module (foxtrot/core/)

**EventEngine (foxtrot/core/event_engine.py)**
- **Priority:** CRITICAL (performance hot path)
- **Print Statements:** 4 (lines 82, 91, 146, 151)
- **Migration Strategy:** Performance-optimized logging with conditional execution
- **Context Requirements:** event_type, error_type, handler_name, thread_context

**Implementation Pattern:**
```python
# High-frequency exception handling (lines 82, 91)
if self.logger.level <= ERROR:
    self.logger.error(
        "Event handler failed",
        extra={
            "event_type": event.type,
            "error_type": type(e).__name__,
            "error_msg": str(e),
            "handler_name": getattr(handler, '__name__', 'unknown'),
            "performance_critical": True
        }
    )

# Thread termination warnings (lines 146, 151)
self.logger.warning(
    "Thread shutdown timeout",
    extra={
        "thread_type": "main|timer",
        "timeout_seconds": 5.0,
        "thread_alive": True
    }
)
```

**Special Considerations:**
- **Performance Impact:** Monitor EventEngine throughput during migration
- **Thread Safety:** Ensure logging doesn't introduce contention
- **Error Context:** Preserve full error information for debugging

### 4.2 Server Module (foxtrot/server/)

**Database (foxtrot/server/database.py)**
- **Priority:** HIGH (initialization critical path)
- **Print Statements:** 1 (line 126)
- **Migration Strategy:** INFO level with fallback context
- **Context Requirements:** driver_name, fallback_reason, alternative_action

**Datafeed (foxtrot/server/datafeed.py)**
- **Priority:** HIGH (initialization critical path)
- **Print Statements:** 2 (lines 55-57, 71-73)
- **Migration Strategy:** WARNING level with configuration guidance
- **Context Requirements:** configuration_file, required_fields, documentation_links

### 4.3 Adapter Module (foxtrot/adapter/)

**Binance Adapter (foxtrot/adapter/binance/)**
- **Priority:** HIGH (trading operations)
- **Print Statements:** 2 (api_client.py lines 133, 137)
- **Migration Strategy:** Adapter-specific logger with connection context
- **Context Requirements:** adapter_name, connection_status, operation_type

**Crypto Adapter (foxtrot/adapter/crypto/)**
- **Priority:** MEDIUM (multiple files)
- **Print Statements:** 12 (across 4 files)
- **Migration Strategy:** Component-specific loggers with operation tracking
- **Context Requirements:** component_type, operation, status, symbol, error_details

**Implementation Pattern for Adapters:**
```python
class AdapterComponent:
    def __init__(self, adapter_name: str):
        self.logger = get_adapter_logger(adapter_name)
    
    def log_operation(self, operation: str, status: str, **context):
        level = "info" if status == "success" else "error"
        self.logger.__getattribute__(level)(
            f"{operation} {status}",
            extra={
                "adapter_name": self.adapter_name,
                "operation": operation,
                "status": status,
                **context
            }
        )
```

### 4.4 TUI Module (foxtrot/app/tui/)

**Main App (foxtrot/app/tui/main_app.py)**
- **Priority:** LOW (user interface)
- **Print Statements:** 18 (selective migration)
- **Migration Strategy:** Dual output - logging for internal, console for user
- **Preservation:** ASCII banner, user instructions, status messages

**Monitor Components (foxtrot/app/tui/components/base_monitor.py)**
- **Priority:** MEDIUM (operational monitoring)
- **Print Statements:** 2 (lines 356, 433)
- **Migration Strategy:** Structured logging with monitor context
- **Context Requirements:** monitor_name, monitor_type, event_context

**Selective Migration Rules:**
- **Migrate:** Internal status, debug information, error handling
- **Preserve:** User-facing messages, interactive prompts, ASCII art
- **Dual Output:** Error messages (log + user notification)

### 4.5 Test Preservation Strategy

**Performance Tests (tests/unit/core/test_event_engine_performance.py)**
- **Action:** PRESERVE (47 print statements)
- **Rationale:** Developer needs visible benchmark output
- **Alternative:** Consider adding log capture for CI/CD

**Integration Tests (tests/integration/)**
- **Action:** SELECTIVE PRESERVATION
- **Migrate:** Internal test logging, error handling
- **Preserve:** Test progress reporting, result summaries

**Examples (examples/)**
- **Action:** PRESERVE (50 print statements)
- **Rationale:** Educational value requires visible console output
- **Enhancement:** Add logging alongside prints for debugging

---

## 5. Technical Implementation Details

### 5.1 Loguru Configuration Code

**Enhanced Logger Factory (foxtrot/util/logger.py)**
```python
from loguru import logger
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from .settings import SETTINGS

class FoxtrotLogger:
    """Enhanced logging system for Foxtrot trading platform."""
    
    def __init__(self):
        self._component_loggers: Dict[str, Any] = {}
        self._performance_loggers: Dict[str, Any] = {}
        self._adapter_loggers: Dict[str, Any] = {}
        self._initialized = False
        self._configure_loggers()
    
    def _configure_loggers(self):
        """Configure loguru with Foxtrot-specific settings."""
        if self._initialized:
            return
        
        # Remove default handler
        logger.remove()
        
        # Enhanced format with component hierarchy
        format_template = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <cyan>{extra[component]: <16}</cyan> "
            "| <yellow>{extra[correlation_id]: <12}</yellow> "
            "| <level>{message}</level>"
        )
        
        # Performance-optimized format for hot paths
        perf_format = (
            "<green>{time:HH:mm:ss.SSS}</green> "
            "| <level>{level: <5}</level> "
            "| <cyan>{extra[component]: <12}</cyan> "
            "| <level>{message}</level>"
        )
        
        self._add_console_handler(format_template)
        self._add_file_handlers(format_template, perf_format)
        self._add_adapter_handlers()
        
        self._initialized = True
    
    def _add_console_handler(self, format_template: str):
        """Add console handler if enabled."""
        if not SETTINGS.get("log.console", True):
            return
        
        level = SETTINGS.get("log.level", 20)  # INFO level default
        logger.add(
            sink=sys.stdout,
            level=level,
            format=format_template,
            colorize=True,
            backtrace=True,
            diagnose=True,
            filter=self._console_filter
        )
    
    def _add_file_handlers(self, format_template: str, perf_format: str):
        """Add file handlers with rotation and categorization."""
        if not SETTINGS.get("log.file", True):
            return
        
        log_dir = Path(SETTINGS.get("log.dir", "foxtrot_cache/logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["main", "adapters", "performance", "errors"]:
            (log_dir / subdir).mkdir(exist_ok=True)
        
        # Main application log
        logger.add(
            sink=str(log_dir / "main" / "foxtrot-{time:YYYY-MM-DD}.log"),
            level="INFO",
            format=format_template,
            rotation="1 day",
            retention=f"{SETTINGS.get('log.retention_days', 30)} days",
            compression="gz",
            serialize=False,
            filter=lambda record: not record["extra"].get("performance", False)
        )
        
        # Debug log with size rotation
        logger.add(
            sink=str(log_dir / "main" / "foxtrot-debug-{time:YYYY-MM-DD}.log"),
            level="DEBUG",
            format=format_template,
            rotation=SETTINGS.get("log.max_file_size", "100 MB"),
            retention="7 days",
            compression="gz",
            serialize=False
        )
        
        # Performance log
        if SETTINGS.get("log.performance", False):
            logger.add(
                sink=str(log_dir / "performance" / "perf-{time:YYYY-MM-DD}.log"),
                level="DEBUG",
                format=perf_format,
                rotation="1 day",
                retention="14 days",
                filter=lambda record: record["extra"].get("performance", False),
                enqueue=True  # Async logging for performance
            )
        
        # Error aggregation log
        logger.add(
            sink=str(log_dir / "errors" / "errors-{time:YYYY-MM-DD}.log"),
            level="ERROR",
            format=format_template,
            rotation="1 day",
            retention="90 days",
            backtrace=True,
            diagnose=True
        )
    
    def _add_adapter_handlers(self):
        """Add adapter-specific handlers if enabled."""
        if not SETTINGS.get("log.adapter_specific", True):
            return
        
        log_dir = Path(SETTINGS.get("log.dir", "foxtrot_cache/logs"))
        
        # Adapter handlers will be added dynamically when adapters are created
        # This method sets up the infrastructure
    
    def _console_filter(self, record):
        """Filter console output to avoid noise."""
        # Skip performance logs on console
        if record["extra"].get("performance", False):
            return False
        
        # Skip debug logs in production
        if self._detect_environment() == "production" and record["level"].no < 20:
            return False
        
        return True
    
    def _detect_environment(self) -> str:
        """Detect execution environment."""
        if 'pytest' in sys.modules:
            return 'test'
        elif os.getenv('FOXTROT_ENV') == 'production':
            return 'production'
        else:
            return 'development'
    
    def get_component_logger(self, component_name: str):
        """Get a component-specific logger with context."""
        if component_name not in self._component_loggers:
            self._component_loggers[component_name] = logger.bind(
                component=component_name,
                correlation_id="",
                performance=False
            )
        return self._component_loggers[component_name]
    
    def get_performance_logger(self, component_name: str):
        """Get a high-performance logger for hot paths."""
        if component_name not in self._performance_loggers:
            perf_enabled = SETTINGS.get("log.performance", False)
            self._performance_loggers[component_name] = logger.bind(
                component=component_name,
                correlation_id="",
                performance=True
            )
        return self._performance_loggers[component_name]
    
    def get_adapter_logger(self, adapter_name: str):
        """Get an adapter-specific logger with file routing."""
        if adapter_name not in self._adapter_loggers:
            log_dir = Path(SETTINGS.get("log.dir", "foxtrot_cache/logs"))
            
            if SETTINGS.get("log.adapter_specific", True):
                # Add adapter-specific file handler
                adapter_log_path = log_dir / "adapters" / f"{adapter_name.lower()}-{{time:YYYY-MM-DD}}.log"
                
                handler_id = logger.add(
                    sink=str(adapter_log_path),
                    level="DEBUG",
                    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                    rotation="1 day",
                    retention="14 days",
                    filter=lambda record, adapter=adapter_name: record["extra"].get("adapter") == adapter
                )
            
            self._adapter_loggers[adapter_name] = logger.bind(
                component=f"Adapter.{adapter_name}",
                adapter=adapter_name,
                correlation_id=""
            )
        
        return self._adapter_loggers[adapter_name]
    
    def add_correlation_id(self, component_logger, correlation_id: str):
        """Add correlation ID to logger for request tracking."""
        return component_logger.bind(correlation_id=correlation_id)

# Global singleton instance
_foxtrot_logger: Optional[FoxtrotLogger] = None

def get_foxtrot_logger() -> FoxtrotLogger:
    """Get the global Foxtrot logger instance."""
    global _foxtrot_logger
    if _foxtrot_logger is None:
        _foxtrot_logger = FoxtrotLogger()
    return _foxtrot_logger

# Convenience functions for easy usage
def get_component_logger(component_name: str):
    """Get a component-specific logger."""
    return get_foxtrot_logger().get_component_logger(component_name)

def get_performance_logger(component_name: str):
    """Get a performance-optimized logger."""
    return get_foxtrot_logger().get_performance_logger(component_name)

def get_adapter_logger(adapter_name: str):
    """Get an adapter-specific logger."""
    return get_foxtrot_logger().get_adapter_logger(adapter_name)

def add_correlation_context(logger_instance, correlation_id: str):
    """Add correlation context to any logger."""
    return get_foxtrot_logger().add_correlation_id(logger_instance, correlation_id)
```

### 5.2 Logger Factory Implementation

**Component Logger Factory Pattern:**
```python
# Factory pattern for consistent logger creation
class ComponentLoggerFactory:
    """Factory for creating component-specific loggers."""
    
    @staticmethod
    def create_event_engine_logger():
        """Create optimized logger for EventEngine."""
        return get_performance_logger("EventEngine")
    
    @staticmethod
    def create_adapter_logger(adapter_name: str, manager_type: str = None):
        """Create adapter and manager specific logger."""
        component_name = f"Adapter.{adapter_name}"
        if manager_type:
            component_name += f".{manager_type}"
        
        return get_adapter_logger(adapter_name).bind(
            manager_type=manager_type or "main"
        )
    
    @staticmethod
    def create_tui_logger(component_name: str):
        """Create TUI component logger."""
        return get_component_logger(f"TUI.{component_name}")
    
    @staticmethod
    def create_server_logger(component_name: str):
        """Create server component logger."""
        return get_component_logger(f"Server.{component_name}")

# Usage examples:
event_logger = ComponentLoggerFactory.create_event_engine_logger()
binance_order_logger = ComponentLoggerFactory.create_adapter_logger("Binance", "OrderManager")
tui_monitor_logger = ComponentLoggerFactory.create_tui_logger("Monitor")
```

### 5.3 Context Detection Mechanisms

**Execution Context Detection:**
```python
import sys
import os
import threading
from typing import Dict, Any

class ExecutionContextDetector:
    """Detect and manage execution context for logging."""
    
    @staticmethod
    def detect_environment() -> str:
        """Detect the execution environment."""
        if 'pytest' in sys.modules:
            return 'test'
        elif os.getenv('FOXTROT_ENV') == 'production':
            return 'production'
        elif os.getenv('FOXTROT_ENV') == 'development':
            return 'development'
        else:
            # Auto-detect based on other indicators
            if __debug__:
                return 'development'
            else:
                return 'production'
    
    @staticmethod
    def detect_component_context() -> Dict[str, Any]:
        """Detect current component context from call stack."""
        import inspect
        
        frame = inspect.currentframe()
        context = {
            "thread_name": threading.current_thread().name,
            "thread_id": threading.get_ident(),
        }
        
        # Walk up the stack to find component information
        try:
            while frame:
                frame = frame.f_back
                if not frame:
                    break
                
                # Look for class information
                if 'self' in frame.f_locals:
                    obj = frame.f_locals['self']
                    class_name = obj.__class__.__name__
                    
                    # Identify component type
                    if 'Engine' in class_name:
                        context['component_type'] = 'engine'
                        context['component_name'] = class_name
                    elif 'Adapter' in class_name:
                        context['component_type'] = 'adapter'
                        context['component_name'] = getattr(obj, 'adapter_name', class_name)
                    elif 'Manager' in class_name:
                        context['component_type'] = 'manager'
                        context['component_name'] = class_name
                    
                    break
        finally:
            del frame
        
        return context
    
    @staticmethod
    def create_correlation_id(operation: str = None) -> str:
        """Create correlation ID for request tracking."""
        import uuid
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        
        if operation:
            return f"{operation}_{timestamp}_{short_uuid}"
        else:
            return f"{timestamp}_{short_uuid}"

# Usage in components:
def enhanced_logging_wrapper(func):
    """Decorator to add automatic context detection."""
    def wrapper(*args, **kwargs):
        context = ExecutionContextDetector.detect_component_context()
        correlation_id = ExecutionContextDetector.create_correlation_id(func.__name__)
        
        # Add context to logger if available
        if hasattr(args[0], 'logger'):
            logger = args[0].logger.bind(
                correlation_id=correlation_id,
                **context
            )
            args[0].logger = logger
        
        return func(*args, **kwargs)
    
    return wrapper
```

### 5.4 Integration with Existing Code Patterns

**BaseAdapter Integration:**
```python
# Enhanced BaseAdapter with logging integration
from foxtrot.util.logger import get_adapter_logger
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Enhanced base adapter with integrated logging."""
    
    def __init__(self, event_engine, adapter_name: str):
        self.event_engine = event_engine
        self.adapter_name = adapter_name
        
        # Initialize adapter-specific logger
        self.logger = get_adapter_logger(adapter_name)
        
        self.logger.info(
            "Adapter initialized",
            extra={
                "adapter_name": adapter_name,
                "adapter_type": self.__class__.__name__,
                "initialization_time": datetime.now().isoformat()
            }
        )
    
    def write_log(self, message: str, level: str = "info"):
        """Enhanced write_log method with structured logging."""
        # Legacy compatibility
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(
            message,
            extra={
                "adapter_name": self.adapter_name,
                "legacy_method": True
            }
        )
        
        # Also send LOG event for backward compatibility
        from foxtrot.core.event import Event
        from foxtrot.util.event_type import EVENT_LOG
        
        log_event = Event(
            type=EVENT_LOG,
            data={
                "message": message,
                "level": level,
                "gateway_name": self.adapter_name
            }
        )
        self.event_engine.put(log_event)
    
    def log_connection_status(self, status: str, **context):
        """Log connection status with standardized format."""
        level = "info" if status == "connected" else "warning"
        
        self.logger.__getattribute__(level)(
            f"Connection {status}",
            extra={
                "adapter_name": self.adapter_name,
                "connection_status": status,
                "timestamp": datetime.now().isoformat(),
                **context
            }
        )
    
    def log_operation(self, operation: str, status: str, **context):
        """Log operation with standardized format."""
        level = "info" if status == "success" else "error"
        
        self.logger.__getattribute__(level)(
            f"{operation} {status}",
            extra={
                "adapter_name": self.adapter_name,
                "operation": operation,
                "status": status,
                "timestamp": datetime.now().isoformat(),
                **context
            }
        )
```

**Event System Integration:**
```python
# Enhanced Event class with logging context
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime

@dataclass
class Event:
    """Enhanced Event with logging correlation."""
    
    type: str
    data: Any = None
    correlation_id: Optional[str] = field(default_factory=lambda: ExecutionContextDetector.create_correlation_id())
    timestamp: datetime = field(default_factory=datetime.now)
    source_component: Optional[str] = None
    
    def with_logging_context(self, logger):
        """Bind event correlation to logger."""
        return logger.bind(
            correlation_id=self.correlation_id,
            event_type=self.type,
            source_component=self.source_component
        )
```

---

## 6. Quality Assurance Plan

### 6.1 Testing Strategy for Each Phase

**Phase 1: Critical Path Testing**
```python
# Performance regression testing
class TestCriticalPathPerformance:
    
    def test_event_engine_throughput_regression(self):
        """Ensure no significant performance regression in EventEngine."""
        # Baseline measurement
        baseline_throughput = self.measure_baseline_throughput()
        
        # Current implementation throughput
        current_throughput = self.measure_current_throughput()
        
        # Allow max 2% regression
        regression_threshold = 0.02
        assert current_throughput >= baseline_throughput * (1 - regression_threshold)
    
    def test_exception_handling_performance(self):
        """Test exception handling performance in EventEngine."""
        event_count = 1000
        error_rate = 0.1  # 10% errors
        
        start_time = time.perf_counter()
        
        # Generate events with errors
        for i in range(event_count):
            # Implementation here
            pass
        
        end_time = time.perf_counter()
        processing_time = end_time - start_time
        
        # Assert maximum processing time
        assert processing_time < 5.0  # 5 seconds max for 1000 events
```

**Phase 2: Infrastructure Testing**
```python
# Infrastructure component testing
class TestInfrastructureLogging:
    
    def test_database_fallback_logging(self, caplog):
        """Test database fallback logging is correct."""
        db_manager = DatabaseManager()
        
        # Simulate missing driver
        with patch('builtins.__import__', side_effect=ImportError("Driver not found")):
            result = db_manager.init_database_driver("missing_driver")
            
            # Verify log content
            assert "using SQLite fallback" in caplog.text
            assert "missing_driver" in caplog.text
    
    def test_datafeed_configuration_warnings(self, caplog):
        """Test datafeed configuration warning logging."""
        datafeed_manager = DatafeedManager()
        
        # Simulate missing configuration
        with patch.object(datafeed_manager, '_has_datafeed_config', return_value=False):
            result = datafeed_manager.check_datafeed_configuration()
            
            # Verify warning logged
            assert "No datafeed configuration found" in caplog.text
            assert not result
```

**Phase 3: Adapter Testing**
```python
# Adapter logging testing
class TestAdapterLogging:
    
    def test_binance_connection_logging(self, caplog):
        """Test Binance adapter connection logging."""
        event_engine = MagicMock()
        client = BinanceApiClient(event_engine, "TEST_BINANCE")
        
        # Test successful connection
        with patch.object(client, '_establish_connection') as mock_connect:
            mock_connect.return_value = {"account_type": "spot"}
            client.connect()
            
            assert "Attempting Binance connection" in caplog.text
            assert "Binance connection established" in caplog.text
    
    def test_adapter_error_context_preservation(self, caplog):
        """Test adapter error context is preserved."""
        client = BinanceApiClient(MagicMock(), "TEST")
        
        test_error = ConnectionError("Network timeout")
        client.log_error("Connection failed", error=test_error, retry_count=3)
        
        # Verify error context
        assert "Connection failed" in caplog.text
        assert "ConnectionError" in caplog.text
        assert "Network timeout" in caplog.text
```

**Phase 4: TUI Testing**
```python
# TUI component testing
class TestTUILogging:
    
    def test_monitor_component_logging(self, caplog):
        """Test monitor component logging."""
        monitor = BaseMonitor("TestMonitor")
        
        monitor.log_info("Monitor started", component_status="active")
        
        # Verify structured logging
        assert "Monitor started" in caplog.text
        assert "TestMonitor" in caplog.text
    
    def test_user_interface_preservation(self, capsys):
        """Test user interface output is preserved."""
        app = TUIMainApp()
        
        app.display_startup_banner()
        
        captured = capsys.readouterr()
        # Verify banner is still printed to console
        assert "Foxtrot Trading" in captured.out
```

### 6.2 Performance Benchmarking Approach

**Benchmark Test Suite:**
```python
class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmarking for logging migration."""
    
    def benchmark_event_engine_throughput(self):
        """Benchmark EventEngine throughput with logging."""
        test_scenarios = [
            {"event_count": 1000, "error_rate": 0.0},
            {"event_count": 1000, "error_rate": 0.05},
            {"event_count": 1000, "error_rate": 0.10},
            {"event_count": 5000, "error_rate": 0.05},
        ]
        
        results = []
        for scenario in test_scenarios:
            result = self._run_throughput_test(**scenario)
            results.append(result)
        
        return results
    
    def benchmark_memory_usage(self):
        """Benchmark memory usage with logging."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        baseline_memory = process.memory_info().rss
        
        # Create logger instances and generate logs
        for i in range(100):
            logger = get_component_logger(f"BenchmarkComponent{i}")
            for j in range(100):
                logger.info(f"Benchmark message {j}", extra={"component_id": i})
        
        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - baseline_memory
        
        return {
            "baseline_mb": baseline_memory / 1024 / 1024,
            "peak_mb": peak_memory / 1024 / 1024,
            "increase_mb": memory_increase / 1024 / 1024
        }
    
    def benchmark_concurrent_logging(self):
        """Benchmark concurrent logging performance."""
        import threading
        import queue
        
        result_queue = queue.Queue()
        thread_count = 10
        messages_per_thread = 100
        
        def logging_worker(thread_id):
            logger = get_component_logger(f"ConcurrentTest{thread_id}")
            start_time = time.perf_counter()
            
            for i in range(messages_per_thread):
                logger.info(
                    f"Concurrent message {i}",
                    extra={"thread_id": thread_id, "message_id": i}
                )
            
            end_time = time.perf_counter()
            result_queue.put(end_time - start_time)
        
        # Start all threads
        threads = []
        overall_start = time.perf_counter()
        
        for thread_id in range(thread_count):
            thread = threading.Thread(target=logging_worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        overall_end = time.perf_counter()
        
        # Collect results
        thread_times = []
        while not result_queue.empty():
            thread_times.append(result_queue.get())
        
        return {
            "overall_time": overall_end - overall_start,
            "avg_thread_time": sum(thread_times) / len(thread_times),
            "total_messages": thread_count * messages_per_thread,
            "throughput": (thread_count * messages_per_thread) / (overall_end - overall_start)
        }
```

### 6.3 Validation of Log File Generation

**Log File Validation Tests:**
```python
class TestLogFileGeneration:
    """Test log file creation and structure."""
    
    def test_log_directory_creation(self):
        """Test log directory structure is created correctly."""
        logger_system = get_foxtrot_logger()
        
        # Generate some logs
        component_logger = logger_system.get_component_logger("TestComponent")
        adapter_logger = logger_system.get_adapter_logger("TestAdapter")
        
        component_logger.info("Test component message")
        adapter_logger.info("Test adapter message")
        
        # Wait for file I/O
        time.sleep(1.0)
        
        # Verify directory structure
        log_dir = Path("foxtrot_cache/logs")
        assert log_dir.exists()
        assert (log_dir / "main").exists()
        assert (log_dir / "adapters").exists()
        assert (log_dir / "errors").exists()
    
    def test_log_file_content_structure(self):
        """Test log file content has correct structure."""
        logger = get_component_logger("StructureTest")
        
        test_message = "Test structured logging"
        test_context = {
            "operation": "test_operation",
            "status": "success",
            "data": {"key": "value"}
        }
        
        logger.info(test_message, extra=test_context)
        
        # Wait for file write
        time.sleep(1.0)
        
        # Read log file and verify structure
        log_dir = Path("foxtrot_cache/logs/main")
        log_files = list(log_dir.glob("foxtrot-*.log"))
        assert len(log_files) > 0
        
        with open(log_files[0], 'r') as f:
            content = f.read()
            
        # Verify content structure
        assert test_message in content
        assert "StructureTest" in content
        assert "INFO" in content
        # Timestamp format verification
        import re
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}'
        assert re.search(timestamp_pattern, content)
    
    def test_log_rotation_functionality(self):
        """Test log rotation works correctly."""
        # This test requires time-based testing or size-based rotation
        # Implementation depends on specific rotation strategy
        pass
    
    def test_adapter_specific_log_files(self):
        """Test adapter-specific log files are created."""
        adapters = ["Binance", "IB", "Crypto"]
        
        for adapter_name in adapters:
            logger = get_adapter_logger(adapter_name)
            logger.info(f"Test message from {adapter_name}")
        
        # Wait for file I/O
        time.sleep(1.0)
        
        # Verify adapter log files
        log_dir = Path("foxtrot_cache/logs/adapters")
        for adapter_name in adapters:
            adapter_files = list(log_dir.glob(f"{adapter_name.lower()}-*.log"))
            assert len(adapter_files) > 0, f"No log file found for {adapter_name}"
```

### 6.4 Regression Testing Plan

**Automated Regression Test Suite:**
```python
class RegressionTestSuite:
    """Comprehensive regression testing for migration."""
    
    def test_no_print_statements_remaining(self):
        """Verify all target print statements have been migrated."""
        import ast
        from pathlib import Path
        
        # List of files that should have no print statements
        target_files = [
            "foxtrot/core/event_engine.py",
            "foxtrot/server/database.py",
            "foxtrot/server/datafeed.py",
            "foxtrot/adapter/binance/api_client.py",
            "foxtrot/app/tui/components/base_monitor.py"
        ]
        
        for file_path in target_files:
            self._verify_no_prints_in_file(file_path)
    
    def _verify_no_prints_in_file(self, file_path: str):
        """Verify specific file has no print statements."""
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    # Check if this is an allowed print (comments should indicate)
                    line_num = node.lineno
                    raise AssertionError(f"Unexpected print statement in {file_path}:{line_num}")
    
    def test_backward_compatibility(self):
        """Test backward compatibility with existing code."""
        # Test that existing logging calls still work
        from foxtrot.util.logger import logger
        
        # Old-style logging should still work
        logger.info("Backward compatibility test")
        
        # Test legacy write_log method
        event_engine = EventEngine()
        adapter = BinanceAdapter(event_engine, "TEST")
        adapter.write_log("Legacy log test")
    
    def test_settings_integration(self):
        """Test settings integration works correctly."""
        # Test different settings configurations
        test_settings = [
            {"log.console": True, "log.file": True},
            {"log.console": False, "log.file": True},
            {"log.console": True, "log.file": False},
        ]
        
        for settings in test_settings:
            with patch.dict('foxtrot.util.settings.SETTINGS', settings):
                logger_system = FoxtrotLogger()
                # Verify logger system respects settings
                # Implementation depends on specific settings logic
    
    def test_thread_safety_regression(self):
        """Test thread safety hasn't regressed."""
        import threading
        import queue
        
        error_queue = queue.Queue()
        
        def concurrent_logging_worker(worker_id):
            try:
                logger = get_component_logger(f"ThreadTest{worker_id}")
                for i in range(100):
                    logger.info(f"Message {i} from worker {worker_id}")
            except Exception as e:
                error_queue.put(e)
        
        # Start multiple threads
        threads = []
        for worker_id in range(10):
            thread = threading.Thread(target=concurrent_logging_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        assert len(errors) == 0, f"Thread safety errors: {errors}"
```

---

## 7. Risk Analysis and Mitigation

### 7.1 Identified Risks and Their Mitigation Strategies

| Risk Category | Risk Description | Probability | Impact | Mitigation Strategy | Detection Method |
|---------------|------------------|-------------|--------|-------------------|------------------|
| **Performance** | EventEngine throughput regression >5% | Medium | High | Conditional logging, async I/O, performance testing | Automated benchmarks |
| **Thread Safety** | Race conditions in concurrent logging | Low | High | Loguru thread-safe defaults, concurrency testing | Multi-threaded stress tests |
| **User Experience** | Loss of immediate TUI feedback | Medium | Medium | Selective migration, dual output strategy | Manual testing workflows |
| **System Stability** | Logging system failure causing crashes | Low | Critical | Robust fallback mechanisms, error handling | Exception monitoring |
| **Data Loss** | Important debug information lost | Medium | Medium | Gradual migration, context preservation | Log content validation |
| **Integration** | Breaking changes to existing APIs | Low | High | Backward compatibility, comprehensive testing | API compatibility tests |
| **Configuration** | Invalid logging configuration preventing startup | Medium | High | Configuration validation, safe defaults | Startup sequence testing |
| **Disk Space** | Log files consuming excessive disk space | Medium | Low | Log rotation, size limits, monitoring | Disk usage monitoring |

### 7.2 Performance Impact Assessment

**Critical Performance Paths Analysis:**

**EventEngine Hot Path (Highest Risk):**
```python
# Risk Assessment: EventEngine._process() method
# Current: 1000+ events/sec processing capability
# Risk: Logging overhead in exception handling (lines 82, 91)

# Mitigation Strategy:
class EventEnginePerformanceOptimization:
    def __init__(self):
        self.logger = get_performance_logger("EventEngine")
        self.error_count = 0
        self.last_error_log = 0
        
    def optimized_error_logging(self, event, error, handler):
        """Optimized error logging with rate limiting."""
        current_time = time.time()
        
        # Rate limiting: max 10 errors/second logged
        if current_time - self.last_error_log < 0.1:
            self.error_count += 1
            return
        
        # Reset counter and log
        if self.error_count > 0:
            self.logger.error(
                f"Suppressed {self.error_count} similar errors",
                extra={"suppressed_count": self.error_count}
            )
            self.error_count = 0
        
        # Log current error with full context
        self.logger.error(
            "Event handler failed",
            extra={
                "event_type": event.type,
                "error_type": type(error).__name__,
                "error_msg": str(error)[:200],  # Truncate long messages
                "handler_name": getattr(handler, '__name__', 'unknown')
            }
        )
        
        self.last_error_log = current_time
```

**Memory Usage Assessment:**
```python
# Memory impact analysis
class MemoryImpactAnalysis:
    def estimate_memory_impact(self):
        """Estimate memory impact of logging migration."""
        
        # Logger instance overhead
        component_loggers = 20  # Estimated number of components
        logger_overhead_per_instance = 1024  # bytes
        total_logger_overhead = component_loggers * logger_overhead_per_instance
        
        # Log message buffering
        message_buffer_size = 1024 * 1024  # 1MB buffer
        
        # File handle overhead
        log_files = 8  # Estimated number of log files
        file_handle_overhead = log_files * 8192  # bytes per file handle
        
        total_estimated_overhead = (
            total_logger_overhead +
            message_buffer_size +
            file_handle_overhead
        )
        
        return {
            "total_overhead_mb": total_estimated_overhead / 1024 / 1024,
            "logger_overhead_kb": total_logger_overhead / 1024,
            "buffer_overhead_mb": message_buffer_size / 1024 / 1024,
            "file_overhead_kb": file_handle_overhead / 1024
        }
```

### 7.3 Breaking Change Prevention

**API Compatibility Strategy:**
```python
# Maintain backward compatibility for existing code
class BackwardCompatibilityLayer:
    """Ensure existing code continues to work during migration."""
    
    @staticmethod
    def legacy_write_log_support():
        """Support for existing write_log() calls."""
        # BaseAdapter.write_log() method maintained
        # LOG events still processed by LogEngine
        # Gradual migration without breaking existing adapters
    
    @staticmethod
    def settings_compatibility():
        """Maintain compatibility with existing settings."""
        # Existing log.level, log.console, log.file settings supported
        # New settings added with sensible defaults
        # No breaking changes to vt_setting.json format
    
    @staticmethod
    def event_system_compatibility():
        """Maintain EVENT_LOG compatibility."""
        # LogEngine still processes EVENT_LOG events
        # Existing event handlers continue to work
        # New structured logging runs in parallel
```

**Migration Safety Checks:**
```python
class MigrationSafetyChecks:
    """Safety checks to prevent breaking changes."""
    
    def validate_settings_compatibility(self):
        """Validate settings file compatibility."""
        required_settings = ["log.level", "log.console", "log.file"]
        
        for setting in required_settings:
            if setting not in SETTINGS:
                raise ConfigurationError(f"Required setting {setting} missing")
    
    def validate_logger_initialization(self):
        """Validate logger system initializes correctly."""
        try:
            logger_system = FoxtrotLogger()
            test_logger = logger_system.get_component_logger("ValidationTest")
            test_logger.info("Validation test message")
            return True
        except Exception as e:
            raise LoggerInitializationError(f"Logger initialization failed: {e}")
    
    def validate_file_permissions(self):
        """Validate log directory can be created and written."""
        log_dir = Path("foxtrot_cache/logs")
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            test_file = log_dir / "permission_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception as e:
            raise PermissionError(f"Cannot write to log directory: {e}")
```

### 7.4 Edge Cases and Special Considerations

**Edge Case Handling:**

**1. Logging System Initialization Failure:**
```python
class LoggingFailureFallback:
    """Handle logging system initialization failures gracefully."""
    
    @staticmethod
    def create_fallback_logger():
        """Create fallback logger when main system fails."""
        import logging
        
        # Use standard library logging as fallback
        fallback_logger = logging.getLogger("foxtrot_fallback")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | FALLBACK | %(message)s'
        )
        handler.setFormatter(formatter)
        fallback_logger.addHandler(handler)
        fallback_logger.setLevel(logging.INFO)
        
        return fallback_logger
    
    @staticmethod
    def safe_logger_get(component_name: str):
        """Safely get logger with fallback on failure."""
        try:
            return get_component_logger(component_name)
        except Exception:
            # Fall back to print statements in critical failure
            class PrintFallbackLogger:
                def info(self, msg, **kwargs):
                    print(f"[INFO] {component_name}: {msg}")
                def error(self, msg, **kwargs):
                    print(f"[ERROR] {component_name}: {msg}")
                def warning(self, msg, **kwargs):
                    print(f"[WARNING] {component_name}: {msg}")
                def debug(self, msg, **kwargs):
                    if __debug__:
                        print(f"[DEBUG] {component_name}: {msg}")
            
            return PrintFallbackLogger()
```

**2. High-Frequency Event Scenarios:**
```python
class HighFrequencyEventHandling:
    """Special handling for high-frequency events."""
    
    def __init__(self):
        self.event_counts = {}
        self.last_logged = {}
        self.suppression_threshold = 100  # events
        self.time_window = 60  # seconds
    
    def should_log_event(self, event_type: str) -> bool:
        """Determine if high-frequency event should be logged."""
        current_time = time.time()
        
        # Initialize counters
        if event_type not in self.event_counts:
            self.event_counts[event_type] = 0
            self.last_logged[event_type] = current_time
        
        self.event_counts[event_type] += 1
        
        # Reset counter if time window expired
        if current_time - self.last_logged[event_type] > self.time_window:
            self.event_counts[event_type] = 1
            self.last_logged[event_type] = current_time
            return True
        
        # Log every Nth event or at the end of suppression period
        if (self.event_counts[event_type] % self.suppression_threshold == 0 or
            current_time - self.last_logged[event_type] > self.time_window):
            self.last_logged[event_type] = current_time
            return True
        
        return False
```

**3. Test Environment Isolation:**
```python
class TestEnvironmentIsolation:
    """Ensure test environment doesn't interfere with production logging."""
    
    @staticmethod
    def setup_test_logging():
        """Setup isolated logging for tests."""
        if 'pytest' in sys.modules:
            # Use temporary directory for test logs
            import tempfile
            test_log_dir = tempfile.mkdtemp(prefix="foxtrot_test_logs_")
            
            # Override log directory setting
            import foxtrot.util.settings
            foxtrot.util.settings.SETTINGS["log.dir"] = test_log_dir
            
            # Use memory-only logging for tests
            test_logger = logger.bind(test_mode=True)
            return test_logger
        
        return get_foxtrot_logger()
    
    @staticmethod
    def cleanup_test_logging():
        """Cleanup test logging artifacts."""
        if 'pytest' in sys.modules:
            import tempfile
            import shutil
            
            test_log_dir = SETTINGS.get("log.dir")
            if test_log_dir and "foxtrot_test_logs_" in test_log_dir:
                shutil.rmtree(test_log_dir, ignore_errors=True)
```

---

## 8. Configuration and Setup

### 8.1 Dependencies to Add (loguru)

**Current Dependency Status:**
```bash
# Verify loguru is already included in project dependencies
grep -i loguru pyproject.toml
grep -i loguru requirements.txt
```

**Loguru Version Requirements:**
```toml
# pyproject.toml - ensure minimum version for async support
[tool.poetry.dependencies]
loguru = "^0.7.0"  # Minimum version for async logging and structured format

# Additional development dependencies for testing
[tool.poetry.group.dev.dependencies]
pytest-loguru = "^0.4.0"  # For testing log output
```

**Version Verification Command:**
```bash
# Check loguru features available
python -c "import loguru; print(f'Loguru version: {loguru.__version__}')"
python -c "from loguru import logger; print('Async support:', hasattr(logger, 'complete'))"
```

### 8.2 Git Configuration Changes (.gitignore)

**Enhanced .gitignore:**
```gitignore
# Existing entries (preserve)
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# NEW: Logging-related entries
foxtrot_cache/logs/
*.log
logs/
/logs
.logs/

# NEW: Log-related temporary files
*.log.*
*.log.gz
*.log.bz2
*.log.zip

# NEW: Test log artifacts
test_logs/
/tmp/foxtrot_test_logs_*
**/test_log_output/

# NEW: Performance test outputs
performance_results/
benchmark_logs/

# NEW: Log configuration backups
vt_setting.json.backup
logging_config.backup
```

### 8.3 Project Structure Modifications

**New Directory Structure:**
```
foxtrot/                           # Existing
├── util/
│   ├── logger.py                  # ENHANCED: Extended with new logging system
│   └── ...                       # Existing files
├── ...                           # Existing structure

foxtrot_cache/                     # Existing
├── logs/                         # NEW: Log file directory
│   ├── main/                     # NEW: Main application logs
│   │   ├── foxtrot-2025-01-02.log
│   │   └── foxtrot-debug-2025-01-02.log
│   ├── adapters/                 # NEW: Adapter-specific logs
│   │   ├── binance-2025-01-02.log
│   │   ├── ibrokers-2025-01-02.log
│   │   └── crypto-2025-01-02.log
│   ├── performance/              # NEW: Performance monitoring
│   │   ├── events-2025-01-02.log
│   │   └── adapters-2025-01-02.log
│   └── errors/                   # NEW: Error aggregation
│       └── errors-2025-01-02.log
└── ...                          # Existing cache structure

tests/                            # Existing
├── unit/
│   ├── util/
│   │   └── test_logger.py        # NEW: Logger unit tests
│   └── ...
├── integration/
│   └── test_logging_integration.py # NEW: Integration tests
├── performance/
│   ├── test_logging_performance.py # NEW: Performance tests
│   └── test_migration_validation.py # NEW: Migration validation
└── ...                          # Existing tests

docs/                            # NEW: Documentation directory
├── LOGGING_MIGRATION_GUIDE.md   # NEW: Logging guide
├── LOGGING_BEST_PRACTICES.md    # NEW: Best practices
└── TROUBLESHOOTING_LOGGING.md   # NEW: Troubleshooting guide
```

**Directory Creation Script:**
```bash
#!/bin/bash
# create_log_directories.sh

echo "Creating logging directory structure..."

# Create main log directories
mkdir -p foxtrot_cache/logs/{main,adapters,performance,errors}

# Create test directories
mkdir -p tests/{unit/util,integration,performance}

# Create documentation directory
mkdir -p docs

# Set appropriate permissions
chmod 755 foxtrot_cache/logs
chmod 755 foxtrot_cache/logs/*

echo "Directory structure created successfully"
echo "Log directories:"
find foxtrot_cache/logs -type d -exec ls -ld {} \;
```

### 8.4 Documentation Updates Needed

**1. README.md Updates:**
```markdown
# NEW: Add to README.md

## Logging

Foxtrot uses structured logging with [loguru](https://loguru.readthedocs.io/) for comprehensive operational monitoring.

### Log Files Location
- **Main logs:** `foxtrot_cache/logs/main/`
- **Adapter logs:** `foxtrot_cache/logs/adapters/`
- **Performance logs:** `foxtrot_cache/logs/performance/`
- **Error logs:** `foxtrot_cache/logs/errors/`

### Configuration
Logging is configured via `vt_setting.json`:

```json
{
  "log.level": 20,          // INFO level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR)
  "log.console": true,      // Enable console output
  "log.file": true,         // Enable file logging
  "log.adapter_specific": true,  // Create adapter-specific log files
  "log.retention_days": 30, // Log file retention period
  "log.max_file_size": "100MB"  // Maximum log file size before rotation
}
```

### Usage in Components
```python
from foxtrot.util.logger import get_component_logger

class MyComponent:
    def __init__(self):
        self.logger = get_component_logger("MyComponent")
    
    def process_data(self, data):
        self.logger.info("Processing data", extra={"data_size": len(data)})
```

For detailed logging documentation, see [docs/LOGGING_MIGRATION_GUIDE.md](docs/LOGGING_MIGRATION_GUIDE.md).
```

**2. CHANGELOG.md Entry:**
```markdown
# NEW: Add to CHANGELOG.md

## [Unreleased] - Logging Migration

### Added
- Structured logging with loguru replacing print() statements
- Component-specific loggers with contextual information
- Adapter-specific log files for better debugging
- Performance-optimized logging for high-frequency events
- Log file rotation and retention management
- Comprehensive logging configuration via settings

### Changed
- Migrated 39 print() statements to structured logging
- Enhanced error handling with detailed context preservation
- Improved thread safety in logging operations
- Better debugging information for adapter operations

### Technical Details
- Enhanced `foxtrot/util/logger.py` with factory pattern
- Added log directory structure under `foxtrot_cache/logs/`
- Implemented performance benchmarking for EventEngine
- Added comprehensive test suite for logging functionality

### Migration Notes
- All existing functionality preserved
- No breaking changes to public APIs
- Performance impact <2% in critical paths
- User interface output unchanged
```

**3. Development Guide Updates:**
```markdown
# NEW: docs/DEVELOPMENT_LOGGING_GUIDE.md

# Logging Best Practices for Foxtrot Development

## Quick Start

### Creating Component Loggers
```python
from foxtrot.util.logger import get_component_logger

class NewEngine:
    def __init__(self):
        self.logger = get_component_logger("NewEngine")
        self.logger.info("Engine initialized")
```

### Adapter Development
```python
from foxtrot.util.logger import get_adapter_logger

class NewAdapter:
    def __init__(self, adapter_name):
        self.logger = get_adapter_logger(adapter_name)
        
    def connect(self):
        try:
            # Connection logic
            self.logger.info("Connected successfully", extra={"endpoint": "..."})
        except Exception as e:
            self.logger.error("Connection failed", extra={"error": str(e)})
```

### Performance-Critical Components
```python
from foxtrot.util.logger import get_performance_logger

class HighFrequencyComponent:
    def __init__(self):
        self.logger = get_performance_logger("HighFrequency")
        
    def process_event(self, event):
        # Use conditional logging for hot paths
        if self.logger.level <= DEBUG:
            self.logger.debug("Processing event", extra={"event_type": event.type})
```

## Logging Levels

- **DEBUG (10):** Detailed diagnostic information
- **INFO (20):** General operational information
- **WARNING (30):** Warning conditions that don't prevent operation
- **ERROR (40):** Error conditions that may affect functionality
- **CRITICAL (50):** Critical errors that may cause system failure

## Context Best Practices

Always include relevant context in log messages:

```python
# Good
self.logger.error(
    "Order placement failed",
    extra={
        "symbol": "BTCUSDT",
        "order_type": "LIMIT",
        "price": 50000,
        "quantity": 0.1,
        "error_code": "INSUFFICIENT_BALANCE"
    }
)

# Avoid
self.logger.error("Order failed")
```

## Testing Logging

```python
def test_component_logging(caplog):
    component = MyComponent()
    component.process_data([1, 2, 3])
    
    assert "Processing data" in caplog.text
    assert "data_size" in caplog.text
```

## Performance Considerations

1. **Use appropriate log levels** - avoid DEBUG in production hot paths
2. **Include context efficiently** - use structured logging over string formatting
3. **Consider async logging** - for high-frequency events
4. **Monitor log file sizes** - implement appropriate rotation

## Troubleshooting

### Common Issues

**Logger not initialized:**
```python
# Ensure logger system is initialized before use
from foxtrot.util.logger import get_foxtrot_logger
logger_system = get_foxtrot_logger()  # This initializes the system
```

**Missing log files:**
- Check `foxtrot_cache/logs/` directory exists and is writable
- Verify `log.file` setting is `true` in `vt_setting.json`
- Check file permissions

**Performance issues:**
- Use `get_performance_logger()` for hot paths
- Enable async logging with `enqueue=True`
- Consider log level filtering

See [TROUBLESHOOTING_LOGGING.md](TROUBLESHOOTING_LOGGING.md) for detailed troubleshooting.
```

### 8.5 Environment Variables

**Runtime Configuration Variables:**
```bash
# Environment variable configuration
export FOXTROT_LOG_DIR="/custom/log/path"          # Override default log directory
export FOXTROT_LOG_LEVEL="DEBUG"                   # Override log level (DEBUG/INFO/WARNING/ERROR)
export FOXTROT_ENV="production"                    # Environment type (development/production/test)
export FOXTROT_LOG_ASYNC="true"                    # Enable async logging
export FOXTROT_LOG_PERFORMANCE="true"              # Enable performance logging
export FOXTROT_LOG_CONSOLE="false"                 # Disable console logging in production
```

**Environment Detection Implementation:**
```python
# Enhanced environment detection
def get_environment_config():
    """Get environment-specific logging configuration."""
    env = os.getenv('FOXTROT_ENV', 'development').lower()
    
    configs = {
        'development': {
            'log.level': int(os.getenv('FOXTROT_LOG_LEVEL', '10')),  # DEBUG
            'log.console': os.getenv('FOXTROT_LOG_CONSOLE', 'true').lower() == 'true',
            'log.file': True,
            'log.performance': os.getenv('FOXTROT_LOG_PERFORMANCE', 'true').lower() == 'true',
            'log.async': os.getenv('FOXTROT_LOG_ASYNC', 'false').lower() == 'true'
        },
        'production': {
            'log.level': int(os.getenv('FOXTROT_LOG_LEVEL', '20')),  # INFO
            'log.console': os.getenv('FOXTROT_LOG_CONSOLE', 'false').lower() == 'true',
            'log.file': True,
            'log.performance': os.getenv('FOXTROT_LOG_PERFORMANCE', 'false').lower() == 'true',
            'log.async': os.getenv('FOXTROT_LOG_ASYNC', 'true').lower() == 'true'
        },
        'test': {
            'log.level': int(os.getenv('FOXTROT_LOG_LEVEL', '40')),  # ERROR
            'log.console': False,
            'log.file': False,  # Tests use memory logging
            'log.performance': False,
            'log.async': False
        }
    }
    
    return configs.get(env, configs['development'])
```

**Docker Environment Configuration:**
```dockerfile
# Dockerfile environment variables for logging
ENV FOXTROT_ENV=production
ENV FOXTROT_LOG_DIR=/app/logs
ENV FOXTROT_LOG_LEVEL=20
ENV FOXTROT_LOG_CONSOLE=false
ENV FOXTROT_LOG_ASYNC=true

# Create log directory
RUN mkdir -p /app/logs && \
    chmod 755 /app/logs

# Volume for log persistence
VOLUME ["/app/logs"]
```

---

## Implementation Commands and Sequences

### Phase 1 Commands:
```bash
# Phase 1: Foundation & Critical Paths
git checkout -b feature/loguru-migration-phase1

# 1. Enhance logger infrastructure
# Edit foxtrot/util/logger.py (implement FoxtrotLogger class)

# 2. Migrate EventEngine critical path
# Edit foxtrot/core/event_engine.py (lines 82, 91, 146, 151)

# 3. Create performance tests
# Create tests/performance/test_logging_performance.py

# 4. Run tests
python -m pytest tests/performance/test_logging_performance.py -v

# 5. Performance validation
python -m pytest tests/performance/ --benchmark-only

# 6. Commit phase 1
git add .
git commit -m "feat: Phase 1 - Critical path logging migration

- Enhanced foxtrot/util/logger.py with FoxtrotLogger class
- Migrated EventEngine exception handling to structured logging
- Added performance test suite
- Validated no performance regression in hot paths"

# Push and create PR
git push origin feature/loguru-migration-phase1
```

### Phase 2-5 Commands:
```bash
# Continue with subsequent phases following similar pattern
# Each phase: branch creation → implementation → testing → validation → commit → PR
```

### Final Validation Commands:
```bash
# Final migration validation
python -c "
import ast
import sys
from pathlib import Path

# Check no print statements remain in core files
core_files = [
    'foxtrot/core/event_engine.py',
    'foxtrot/server/database.py', 
    'foxtrot/server/datafeed.py',
    'foxtrot/adapter/binance/api_client.py'
]

for file_path in core_files:
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    prints = [node for node in ast.walk(tree) 
              if isinstance(node, ast.Call) and 
              isinstance(node.func, ast.Name) and 
              node.func.id == 'print']
    
    if prints:
        print(f'WARNING: {len(prints)} print statements remain in {file_path}')
        sys.exit(1)
    else:
        print(f'✅ {file_path} - no print statements')

print('✅ All core files migrated successfully')
"

# Test log file creation
python -c "
from foxtrot.util.logger import get_component_logger
import time
from pathlib import Path

logger = get_component_logger('ValidationTest')
logger.info('Migration validation test')
time.sleep(1)

log_dir = Path('foxtrot_cache/logs')
if log_dir.exists():
    print('✅ Log directory created')
    files = list(log_dir.rglob('*.log'))
    print(f'✅ {len(files)} log files found')
else:
    print('❌ Log directory not found')
"

# Performance regression test
python -m pytest tests/performance/ --verbose
```

---

## Complete Plan Location:
The plan has been saved to:
`/tmp/claude-instance-logging-migration/PLAN.md`