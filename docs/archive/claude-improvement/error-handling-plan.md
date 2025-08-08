# Foxtrot Error Handling & Recovery Plan

**Document Version:** 1.0  
**Date:** August 6, 2025

## Overview

This document outlines an advanced error handling and recovery system inspired by Nautilus Trader's comprehensive error management, adapted for Foxtrot's Python-native environment. The plan transforms Foxtrot's basic error handling into a production-grade resilience framework.

---

## Current State Assessment

**Existing Error Handling:**
- Basic exception handling in adapters
- Simple logging for errors
- No structured error recovery
- Limited error classification
- Manual error investigation

**Key Gaps:**
- No error severity classification
- Lack of automated recovery mechanisms
- Missing circuit breaker patterns
- No retry logic with backoff
- Limited error context preservation

---

## Structured Error Hierarchy

### Enhanced Error Classification System

```python
# foxtrot/util/errors.py
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

class ErrorSeverity(Enum):
    LOW = "low"           # Info/warning level, system continues normally
    MEDIUM = "medium"     # Degraded functionality, manual intervention recommended
    HIGH = "high"         # System component failure, automatic recovery attempted
    CRITICAL = "critical" # System-wide failure, immediate attention required

class ErrorCategory(Enum):
    CONNECTION = "connection"       # Network/adapter connection issues
    VALIDATION = "validation"       # Data validation failures
    AUTHENTICATION = "authentication"  # Auth/credential issues
    RATE_LIMIT = "rate_limit"      # API rate limiting
    MARKET_DATA = "market_data"    # Market data feed issues
    ORDER_EXECUTION = "order_execution"  # Order processing failures
    SYSTEM = "system"              # Internal system errors

class FoxtrotError(Exception):
    """Base error class with enhanced context and recovery guidance"""
    
    def __init__(
        self, 
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_after: Optional[float] = None,
        suggested_action: Optional[str] = None
    ):
        super().__init__(message)
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.suggested_action = suggested_action
        self.timestamp = datetime.utcnow()
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        import hashlib
        import time
        
        content = f"{self.category.value}:{self.severity.value}:{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize error for logging/persistence"""
        return {
            "error_id": self.error_id,
            "message": str(self),
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
            "suggested_action": self.suggested_action,
            "timestamp": self.timestamp.isoformat()
        }

# Specific error types
class AdapterConnectionError(FoxtrotError):
    """Adapter connection failures with recovery guidance"""
    
    def __init__(self, adapter_name: str, reason: str, **kwargs):
        super().__init__(
            f"Adapter {adapter_name} connection failed: {reason}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONNECTION,
            context={"adapter": adapter_name, "reason": reason},
            retry_after=5.0,
            suggested_action=f"Check {adapter_name} credentials and network connectivity",
            **kwargs
        )

class OrderRejectionError(FoxtrotError):
    """Order rejection with detailed context"""
    
    def __init__(self, order_id: str, venue_reason: str, **kwargs):
        super().__init__(
            f"Order {order_id} rejected: {venue_reason}",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.ORDER_EXECUTION,
            context={"order_id": order_id, "venue_reason": venue_reason},
            recoverable=False,  # Order rejections typically not auto-recoverable
            suggested_action="Review order parameters and account status",
            **kwargs
        )

class RateLimitError(FoxtrotError):
    """API rate limiting with backoff guidance"""
    
    def __init__(self, adapter_name: str, retry_after: float = 60.0, **kwargs):
        super().__init__(
            f"Rate limit exceeded for {adapter_name}",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RATE_LIMIT,
            context={"adapter": adapter_name},
            retry_after=retry_after,
            suggested_action=f"Wait {retry_after} seconds before retrying",
            **kwargs
        )

class MarketDataError(FoxtrotError):
    """Market data feed issues"""
    
    def __init__(self, symbol: str, issue: str, **kwargs):
        super().__init__(
            f"Market data issue for {symbol}: {issue}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.MARKET_DATA,
            context={"symbol": symbol, "issue": issue},
            retry_after=1.0,
            suggested_action="Check market data feed connectivity",
            **kwargs
        )
```

---

## Circuit Breaker Pattern

### Intelligent Failure Protection

```python
# foxtrot/util/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import logging
from foxtrot.util.structured_logger import StructuredLogger

class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failing, blocking calls
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreakerOpenError(FoxtrotError):
    """Exception raised when circuit breaker is open"""
    
    def __init__(self, service_name: str, failure_count: int):
        super().__init__(
            f"Circuit breaker open for {service_name} after {failure_count} failures",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONNECTION,
            context={"service": service_name, "failure_count": failure_count},
            suggested_action=f"Service {service_name} is temporarily unavailable"
        )

class CircuitBreaker:
    """Circuit breaker for service protection with advanced features"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,  # Successes needed to close from half-open
        timeout: timedelta = timedelta(minutes=1),
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        # State tracking
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
        
        # Logging
        self.logger = StructuredLogger(f"circuit_breaker.{name}")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self._log_blocked_call()
                raise CircuitBreakerOpenError(self.name, self.failure_count)
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure(e)
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (
            self.last_failure_time and
            datetime.utcnow() - self.last_failure_time > self.timeout
        )
    
    def _transition_to_half_open(self):
        """Transition to half-open state for testing"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.logger.info(
            "Circuit breaker transitioning to half-open",
            previous_state="open",
            failure_count=self.failure_count
        )
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0  # Reset failure count on successful call
    
    def _close_circuit(self):
        """Close circuit after successful recovery"""
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.logger.info(
            "Circuit breaker closed - service recovered",
            recovery_time=(datetime.utcnow() - self.last_failure_time).total_seconds()
        )
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self._open_circuit(exception)
        
        self.logger.error(
            "Circuit breaker recorded failure",
            failure_count=self.failure_count,
            exception=str(exception),
            state=self.state.value
        )
    
    def _open_circuit(self, last_exception: Exception):
        """Open circuit due to failures"""
        self.state = CircuitState.OPEN
        self.logger.error(
            "Circuit breaker opened due to repeated failures",
            failure_count=self.failure_count,
            threshold=self.failure_threshold,
            last_exception=str(last_exception),
            retry_after=self.timeout.total_seconds()
        )
    
    def _log_blocked_call(self):
        """Log blocked call while circuit is open"""
        self.logger.warning(
            "Call blocked by open circuit breaker",
            time_until_retry=(
                self.last_failure_time + self.timeout - datetime.utcnow()
            ).total_seconds() if self.last_failure_time else 0
        )

# Usage example in adapter:
class BinanceAdapter(BaseAdapter):
    
    def __init__(self):
        super().__init__()
        self.connection_breaker = CircuitBreaker(
            name="binance_connection",
            failure_threshold=3,
            timeout=timedelta(minutes=2)
        )
    
    def connect(self):
        """Connect with circuit breaker protection"""
        return self.connection_breaker.call(self._connect_impl)
```

---

## Retry Logic with Exponential Backoff

### Intelligent Retry Mechanisms

```python
# foxtrot/util/retry.py
import asyncio
import random
import time
from typing import Optional, Callable, Any, Tuple, Union
from functools import wraps
from foxtrot.util.errors import FoxtrotError, ErrorSeverity
from foxtrot.util.structured_logger import StructuredLogger

class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_range: Tuple[float, float] = (0.5, 1.5),
        exceptions: Tuple[type, ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_range = jitter_range
        self.exceptions = exceptions

def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    **config_kwargs
):
    """Decorator for retry logic with exponential backoff and jitter"""
    
    if config is None:
        config = RetryConfig(**config_kwargs)
    
    def decorator(func: Callable) -> Callable:
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            logger = StructuredLogger(f"retry.{func.__name__}")
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    # Execute function
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except config.exceptions as e:
                    last_exception = e
                    
                    # Don't retry on final attempt
                    if attempt == config.max_retries:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            final_exception=str(e)
                        )
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        jitter_factor = random.uniform(*config.jitter_range)
                        delay *= jitter_factor
                    
                    # Use retry_after from FoxtrotError if available
                    if isinstance(e, FoxtrotError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    logger.warning(
                        "Retry attempt after failure",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_attempts=config.max_retries + 1,
                        delay_seconds=delay,
                        exception=str(e)
                    )
                    
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    # Unexpected exception type - don't retry
                    logger.error(
                        "Non-retryable exception encountered",
                        function=func.__name__,
                        exception=type(e).__name__,
                        message=str(e)
                    )
                    raise e
            
            # Re-raise the last exception if all retries failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            """Synchronous version of retry wrapper"""
            logger = StructuredLogger(f"retry.{func.__name__}")
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                        
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            final_exception=str(e)
                        )
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        jitter_factor = random.uniform(*config.jitter_range)
                        delay *= jitter_factor
                    
                    if isinstance(e, FoxtrotError) and e.retry_after:
                        delay = max(delay, e.retry_after)
                    
                    logger.warning(
                        "Retry attempt after failure",
                        function=func.__name__,
                        attempt=attempt + 1,
                        delay_seconds=delay,
                        exception=str(e)
                    )
                    
                    time.sleep(delay)
                
                except Exception as e:
                    logger.error(
                        "Non-retryable exception encountered",
                        function=func.__name__,
                        exception=type(e).__name__,
                        message=str(e)
                    )
                    raise e
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Usage examples:
class BinanceAdapter(BaseAdapter):
    
    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        exceptions=(ConnectionError, TimeoutError, RateLimitError)
    )
    async def connect(self):
        """Connect with automatic retry logic"""
        # Connection logic that may fail
        if not self._test_connection():
            raise AdapterConnectionError("binance", "Connection test failed")
        
        self.status = "connected"
    
    @retry_with_backoff(
        max_retries=2,
        base_delay=0.5,
        max_delay=5.0,
        exceptions=(OrderRejectionError,)
    )
    def submit_order(self, order: OrderData):
        """Submit order with retry for transient failures"""
        try:
            return self._submit_order_impl(order)
        except Exception as e:
            if "insufficient funds" in str(e).lower():
                # Don't retry insufficient funds - not transient
                raise OrderRejectionError(order.vt_orderid, str(e), recoverable=False)
            raise e
```

---

## Error Recovery Automation

### Automated Recovery Strategies

```python
# foxtrot/util/recovery.py
from typing import Dict, Callable, Optional, List
from abc import ABC, abstractmethod
from enum import Enum
import asyncio
from foxtrot.util.errors import FoxtrotError, ErrorSeverity, ErrorCategory
from foxtrot.util.structured_logger import StructuredLogger

class RecoveryAction(Enum):
    RETRY = "retry"
    RECONNECT = "reconnect"  
    RESTART_COMPONENT = "restart_component"
    SWITCH_ADAPTER = "switch_adapter"
    ALERT_OPERATOR = "alert_operator"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"

class RecoveryStrategy(ABC):
    """Abstract base for recovery strategies"""
    
    @abstractmethod
    async def can_handle(self, error: FoxtrotError) -> bool:
        """Check if this strategy can handle the error"""
        pass
    
    @abstractmethod
    async def execute_recovery(self, error: FoxtrotError, context: Dict) -> bool:
        """Execute recovery action, return True if successful"""
        pass

class ConnectionRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for connection failures"""
    
    async def can_handle(self, error: FoxtrotError) -> bool:
        return error.category == ErrorCategory.CONNECTION
    
    async def execute_recovery(self, error: FoxtrotError, context: Dict) -> bool:
        adapter_name = error.context.get("adapter")
        if not adapter_name:
            return False
        
        try:
            # Get adapter from context
            adapter = context.get("adapters", {}).get(adapter_name)
            if not adapter:
                return False
            
            # Attempt reconnection
            await adapter.disconnect()
            await asyncio.sleep(2)  # Brief pause
            await adapter.connect()
            
            return adapter.status == "connected"
            
        except Exception:
            return False

class RateLimitRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy for rate limiting"""
    
    async def can_handle(self, error: FoxtrotError) -> bool:
        return error.category == ErrorCategory.RATE_LIMIT
    
    async def execute_recovery(self, error: FoxtrotError, context: Dict) -> bool:
        # Wait for the specified retry_after period
        if error.retry_after:
            await asyncio.sleep(error.retry_after)
            return True
        return False

class ErrorRecoveryManager:
    """Manages automated error recovery"""
    
    def __init__(self):
        self.strategies: List[RecoveryStrategy] = [
            ConnectionRecoveryStrategy(),
            RateLimitRecoveryStrategy(),
        ]
        self.logger = StructuredLogger("error_recovery")
        self.recovery_history: List[Dict] = []
    
    async def handle_error(
        self, 
        error: FoxtrotError, 
        context: Dict,
        max_recovery_attempts: int = 3
    ) -> bool:
        """Attempt to recover from error automatically"""
        
        # Check if error is marked as recoverable
        if not error.recoverable:
            self.logger.info(
                "Error marked as non-recoverable, skipping recovery",
                error_id=error.error_id,
                category=error.category.value
            )
            return False
        
        # Find appropriate recovery strategy
        recovery_strategy = None
        for strategy in self.strategies:
            if await strategy.can_handle(error):
                recovery_strategy = strategy
                break
        
        if not recovery_strategy:
            self.logger.warning(
                "No recovery strategy found for error",
                error_id=error.error_id,
                category=error.category.value,
                severity=error.severity.value
            )
            return False
        
        # Attempt recovery
        for attempt in range(max_recovery_attempts):
            self.logger.info(
                "Attempting error recovery",
                error_id=error.error_id,
                strategy=recovery_strategy.__class__.__name__,
                attempt=attempt + 1,
                max_attempts=max_recovery_attempts
            )
            
            try:
                success = await recovery_strategy.execute_recovery(error, context)
                
                if success:
                    self.logger.info(
                        "Error recovery successful",
                        error_id=error.error_id,
                        strategy=recovery_strategy.__class__.__name__,
                        attempts_used=attempt + 1
                    )
                    
                    self._record_recovery(error, recovery_strategy, True, attempt + 1)
                    return True
                
            except Exception as recovery_error:
                self.logger.error(
                    "Recovery attempt failed",
                    error_id=error.error_id,
                    strategy=recovery_strategy.__class__.__name__,
                    attempt=attempt + 1,
                    recovery_error=str(recovery_error)
                )
        
        self.logger.error(
            "All recovery attempts failed",
            error_id=error.error_id,
            strategy=recovery_strategy.__class__.__name__,
            total_attempts=max_recovery_attempts
        )
        
        self._record_recovery(error, recovery_strategy, False, max_recovery_attempts)
        return False
    
    def _record_recovery(
        self, 
        error: FoxtrotError, 
        strategy: RecoveryStrategy, 
        success: bool, 
        attempts: int
    ):
        """Record recovery attempt for analysis"""
        record = {
            "error_id": error.error_id,
            "category": error.category.value,
            "severity": error.severity.value,
            "strategy": strategy.__class__.__name__,
            "success": success,
            "attempts": attempts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.recovery_history.append(record)
        
        # Keep only last 1000 records
        if len(self.recovery_history) > 1000:
            self.recovery_history = self.recovery_history[-1000:]

# Integration with MainEngine
class MainEngine:
    
    def __init__(self, event_engine):
        super().__init__(event_engine)
        self.error_recovery = ErrorRecoveryManager()
    
    async def handle_adapter_error(self, adapter_name: str, error: Exception):
        """Handle adapter errors with recovery"""
        
        # Convert to FoxtrotError if needed
        if not isinstance(error, FoxtrotError):
            foxtrot_error = AdapterConnectionError(adapter_name, str(error))
        else:
            foxtrot_error = error
        
        # Attempt recovery
        context = {
            "adapters": self.adapters,
            "engines": self.engines,
            "main_engine": self
        }
        
        recovery_success = await self.error_recovery.handle_error(
            foxtrot_error, 
            context
        )
        
        if not recovery_success:
            # Escalate to operator attention
            await self._escalate_error(foxtrot_error)
    
    async def _escalate_error(self, error: FoxtrotError):
        """Escalate unrecoverable errors"""
        self.write_log(
            f"ESCALATION REQUIRED: {error}",
            level=logging.CRITICAL
        )
        
        # Could integrate with alerting system
        # await self.alert_system.send_alert(error)
```

---

## Success Metrics

### Error Handling Quality Indicators
- **Error Classification Coverage**: 100% of errors properly categorized
- **Recovery Success Rate**: >80% of recoverable errors automatically resolved
- **Mean Time to Recovery**: <30 seconds for connection issues
- **Error Context Completeness**: 95% of errors include actionable context

### Resilience Metrics
- **Circuit Breaker Effectiveness**: >90% protection against cascading failures
- **Retry Success Rate**: >70% of retries succeed within max attempts
- **Error Escalation Rate**: <10% of errors require manual intervention

This comprehensive error handling system transforms Foxtrot's error management from reactive to proactive, providing production-grade resilience while maintaining Python accessibility.