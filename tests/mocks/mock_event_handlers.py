"""
Mock event handlers for testing EventEngine and trading components.

Provides configurable mock handlers that simulate realistic trading
scenarios and event processing patterns.
"""

from collections import defaultdict, deque
import random
import threading
import time
from typing import Any

from foxtrot.core.event_engine import Event


class MockEventHandler:
    """Base class for mock event handlers with configurable behavior."""

    def __init__(self, name: str = "MockHandler"):
        self.name = name
        self.call_count = 0
        self.received_events = []
        self.processing_times = []
        self.errors = []
        self.lock = threading.Lock()
        self.fail_rate = 0.0  # Probability of failure (0.0 - 1.0)
        self.processing_delay = 0.0  # Seconds to sleep during processing
        self.enabled = True

    def __call__(self, event: Event) -> None:
        """Make handler callable."""
        with self.lock:
            if not self.enabled:
                return

            start_time = time.time()
            self.call_count += 1
            self.received_events.append(event)

            # Simulate processing delay
            if self.processing_delay > 0:
                time.sleep(self.processing_delay)

            # Simulate random failures
            if self.fail_rate > 0 and random.random() < self.fail_rate:
                error = Exception(f"Simulated failure in {self.name}")
                self.errors.append(error)
                raise error

            end_time = time.time()
            self.processing_times.append(end_time - start_time)

            # Call custom processing logic
            self._process_event(event)

    def _process_event(self, event: Event) -> None:
        """Override this method for custom processing logic."""

    def reset(self) -> None:
        """Reset handler state."""
        with self.lock:
            self.call_count = 0
            self.received_events.clear()
            self.processing_times.clear()
            self.errors.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get handler statistics."""
        with self.lock:
            avg_processing_time = (
                sum(self.processing_times) / len(self.processing_times)
                if self.processing_times
                else 0.0
            )

            return {
                "name": self.name,
                "call_count": self.call_count,
                "events_received": len(self.received_events),
                "errors": len(self.errors),
                "avg_processing_time": avg_processing_time,
                "enabled": self.enabled,
            }

    def configure(
        self, fail_rate: float = 0.0, processing_delay: float = 0.0, enabled: bool = True
    ):
        """Configure handler behavior."""
        self.fail_rate = fail_rate
        self.processing_delay = processing_delay
        self.enabled = enabled


class RecordingHandler(MockEventHandler):
    """Handler that records all events for inspection."""

    def __init__(self, name: str = "RecordingHandler"):
        super().__init__(name)
        self.event_types = defaultdict(int)
        self.event_data = []

    def _process_event(self, event: Event) -> None:
        """Record event details."""
        self.event_types[event.type] += 1
        self.event_data.append({"type": event.type, "data": event.data, "timestamp": time.time()})

    def get_events_by_type(self, event_type: str) -> list[Event]:
        """Get all events of a specific type."""
        return [event for event in self.received_events if event.type == event_type]

    def get_latest_event(self, event_type: str = None) -> Event | None:
        """Get the most recent event, optionally filtered by type."""
        if not self.received_events:
            return None

        if event_type is None:
            return self.received_events[-1]

        for event in reversed(self.received_events):
            if event.type == event_type:
                return event

        return None


class CountingHandler(MockEventHandler):
    """Handler that counts events by type and provides statistics."""

    def __init__(self, name: str = "CountingHandler"):
        super().__init__(name)
        self.counts = defaultdict(int)
        self.first_event_time = None
        self.last_event_time = None

    def _process_event(self, event: Event) -> None:
        """Count events by type."""
        self.counts[event.type] += 1

        current_time = time.time()
        if self.first_event_time is None:
            self.first_event_time = current_time
        self.last_event_time = current_time

    def get_count(self, event_type: str) -> int:
        """Get count for specific event type."""
        return self.counts.get(event_type, 0)

    def get_rate(self, event_type: str = None) -> float:
        """Get events per second rate."""
        if self.first_event_time is None or self.last_event_time is None:
            return 0.0

        duration = self.last_event_time - self.first_event_time
        if duration <= 0:
            return 0.0

        if event_type is None:
            return self.call_count / duration
        return self.counts[event_type] / duration


class TradingEventHandler(MockEventHandler):
    """Handler that simulates realistic trading event processing."""

    def __init__(self, name: str = "TradingHandler"):
        super().__init__(name)
        self.positions = defaultdict(float)
        self.orders = {}
        self.trades = []
        self.account_balance = 100000.0
        self.processing_stats = defaultdict(list)

    def _process_event(self, event: Event) -> None:
        """Process trading events with realistic logic."""
        processing_start = time.time()

        if event.type.startswith("eTick"):
            self._process_tick(event)
        elif event.type.startswith("eOrder"):
            self._process_order(event)
        elif event.type.startswith("eTrade"):
            self._process_trade(event)
        elif event.type.startswith("ePosition"):
            self._process_position(event)
        elif event.type.startswith("eAccount"):
            self._process_account(event)

        processing_time = time.time() - processing_start
        self.processing_stats[event.type].append(processing_time)

    def _process_tick(self, event: Event) -> None:
        """Process market tick data."""
        # Simulate price analysis
        if hasattr(event.data, "last_price"):
            price = event.data.last_price
            # Simple moving average calculation simulation
            if random.random() < 0.1:  # 10% chance of generating signal
                signal = "BUY" if random.random() < 0.5 else "SELL"
                # Could trigger order placement logic here

    def _process_order(self, event: Event) -> None:
        """Process order events."""
        if hasattr(event.data, "orderid"):
            order_id = event.data.orderid
            self.orders[order_id] = event.data

    def _process_trade(self, event: Event) -> None:
        """Process trade execution events."""
        if hasattr(event.data, "volume") and hasattr(event.data, "price"):
            trade_info = {
                "volume": event.data.volume,
                "price": event.data.price,
                "timestamp": time.time(),
            }
            self.trades.append(trade_info)

            # Update position simulation
            if hasattr(event.data, "symbol"):
                symbol = event.data.symbol
                self.positions[symbol] += event.data.volume

    def _process_position(self, event: Event) -> None:
        """Process position updates."""
        if hasattr(event.data, "symbol") and hasattr(event.data, "volume"):
            self.positions[event.data.symbol] = event.data.volume

    def _process_account(self, event: Event) -> None:
        """Process account balance updates."""
        if hasattr(event.data, "balance"):
            self.account_balance = event.data.balance

    def get_trading_stats(self) -> dict[str, Any]:
        """Get comprehensive trading statistics."""
        return {
            "positions": dict(self.positions),
            "order_count": len(self.orders),
            "trade_count": len(self.trades),
            "account_balance": self.account_balance,
            "avg_processing_times": {
                event_type: sum(times) / len(times) if times else 0.0
                for event_type, times in self.processing_stats.items()
            },
        }


class LatencyMeasuringHandler(MockEventHandler):
    """Handler that measures end-to-end event latency."""

    def __init__(self, name: str = "LatencyHandler"):
        super().__init__(name)
        self.latencies = []
        self.latency_stats = {}

    def _process_event(self, event: Event) -> None:
        """Measure latency if timestamp is provided in event data."""
        current_time = time.time()

        # Try to extract timestamp from event data
        timestamp = None
        if hasattr(event.data, "timestamp"):
            timestamp = event.data.timestamp
        elif isinstance(event.data, dict) and "timestamp" in event.data:
            timestamp = event.data["timestamp"]
        elif isinstance(event.data, str):
            try:
                timestamp = float(event.data)
            except (ValueError, TypeError):
                pass

        if timestamp is not None:
            latency = (current_time - timestamp) * 1000  # Convert to milliseconds
            self.latencies.append(latency)

    def get_latency_stats(self) -> dict[str, float]:
        """Get comprehensive latency statistics."""
        if not self.latencies:
            return {}

        latencies_sorted = sorted(self.latencies)
        n = len(latencies_sorted)

        return {
            "count": n,
            "min": min(latencies_sorted),
            "max": max(latencies_sorted),
            "mean": sum(latencies_sorted) / n,
            "median": latencies_sorted[n // 2],
            "p95": latencies_sorted[int(0.95 * n)],
            "p99": latencies_sorted[int(0.99 * n)],
        }


class LoadTestingHandler(MockEventHandler):
    """Handler designed for load testing with configurable processing characteristics."""

    def __init__(self, name: str = "LoadTestingHandler", cpu_intensive: bool = False):
        super().__init__(name)
        self.cpu_intensive = cpu_intensive
        self.throughput_samples = deque(maxlen=1000)
        self.last_sample_time = time.time()
        self.events_since_sample = 0

    def _process_event(self, event: Event) -> None:
        """Process event with configurable CPU load."""
        if self.cpu_intensive:
            # Simulate CPU-intensive processing
            result = 0
            for i in range(1000):
                result += i**2
                if i % 100 == 0:
                    # Prevent optimization
                    str(result)

        # Update throughput sampling
        self.events_since_sample += 1
        current_time = time.time()

        if current_time - self.last_sample_time >= 1.0:  # Sample every second
            throughput = self.events_since_sample / (current_time - self.last_sample_time)
            self.throughput_samples.append(throughput)
            self.events_since_sample = 0
            self.last_sample_time = current_time

    def get_throughput_stats(self) -> dict[str, float]:
        """Get throughput statistics."""
        if not self.throughput_samples:
            return {}

        samples = list(self.throughput_samples)
        return {
            "current_throughput": samples[-1] if samples else 0.0,
            "avg_throughput": sum(samples) / len(samples),
            "max_throughput": max(samples),
            "min_throughput": min(samples),
        }


class HandlerFactory:
    """Factory for creating and managing mock handlers."""

    @staticmethod
    def create_recording_handler(name: str = None) -> RecordingHandler:
        """Create a recording handler."""
        return RecordingHandler(name or f"RecordingHandler_{id(object())}")

    @staticmethod
    def create_counting_handler(name: str = None) -> CountingHandler:
        """Create a counting handler."""
        return CountingHandler(name or f"CountingHandler_{id(object())}")

    @staticmethod
    def create_trading_handler(name: str = None) -> TradingEventHandler:
        """Create a trading event handler."""
        return TradingEventHandler(name or f"TradingHandler_{id(object())}")

    @staticmethod
    def create_latency_handler(name: str = None) -> LatencyMeasuringHandler:
        """Create a latency measuring handler."""
        return LatencyMeasuringHandler(name or f"LatencyHandler_{id(object())}")

    @staticmethod
    def create_load_testing_handler(
        name: str = None, cpu_intensive: bool = False
    ) -> LoadTestingHandler:
        """Create a load testing handler."""
        return LoadTestingHandler(name or f"LoadTestingHandler_{id(object())}", cpu_intensive)

    @staticmethod
    def create_failing_handler(name: str = None, fail_rate: float = 0.1) -> MockEventHandler:
        """Create a handler that fails randomly."""
        handler = MockEventHandler(name or f"FailingHandler_{id(object())}")
        handler.configure(fail_rate=fail_rate)
        return handler

    @staticmethod
    def create_slow_handler(name: str = None, delay: float = 0.01) -> MockEventHandler:
        """Create a handler with processing delay."""
        handler = MockEventHandler(name or f"SlowHandler_{id(object())}")
        handler.configure(processing_delay=delay)
        return handler

    @staticmethod
    def create_handler_suite(prefix: str = "Test") -> dict[str, MockEventHandler]:
        """Create a suite of different handler types for comprehensive testing."""
        return {
            "recording": HandlerFactory.create_recording_handler(f"{prefix}_Recording"),
            "counting": HandlerFactory.create_counting_handler(f"{prefix}_Counting"),
            "trading": HandlerFactory.create_trading_handler(f"{prefix}_Trading"),
            "latency": HandlerFactory.create_latency_handler(f"{prefix}_Latency"),
            "load_testing": HandlerFactory.create_load_testing_handler(f"{prefix}_Load"),
            "failing": HandlerFactory.create_failing_handler(f"{prefix}_Failing", 0.05),
            "slow": HandlerFactory.create_slow_handler(f"{prefix}_Slow", 0.001),
        }


class HandlerGroup:
    """Manages a group of handlers for coordinated testing."""

    def __init__(self, name: str = "HandlerGroup"):
        self.name = name
        self.handlers: dict[str, MockEventHandler] = {}
        self.lock = threading.Lock()

    def add_handler(self, key: str, handler: MockEventHandler) -> None:
        """Add a handler to the group."""
        with self.lock:
            self.handlers[key] = handler

    def remove_handler(self, key: str) -> MockEventHandler | None:
        """Remove and return a handler from the group."""
        with self.lock:
            return self.handlers.pop(key, None)

    def get_handler(self, key: str) -> MockEventHandler | None:
        """Get a handler by key."""
        return self.handlers.get(key)

    def reset_all(self) -> None:
        """Reset all handlers in the group."""
        with self.lock:
            for handler in self.handlers.values():
                handler.reset()

    def configure_all(self, **kwargs) -> None:
        """Configure all handlers in the group."""
        with self.lock:
            for handler in self.handlers.values():
                if hasattr(handler, "configure"):
                    handler.configure(**kwargs)

    def get_group_stats(self) -> dict[str, Any]:
        """Get statistics for all handlers in the group."""
        with self.lock:
            return {
                key: handler.get_stats() if hasattr(handler, "get_stats") else {}
                for key, handler in self.handlers.items()
            }

    def get_total_call_count(self) -> int:
        """Get total call count across all handlers."""
        return sum(handler.call_count for handler in self.handlers.values())

    def get_total_error_count(self) -> int:
        """Get total error count across all handlers."""
        return sum(
            len(handler.errors) for handler in self.handlers.values() if hasattr(handler, "errors")
        )


# Convenience functions for quick handler creation
def quick_recording_handler() -> RecordingHandler:
    """Quick creation of recording handler."""
    return HandlerFactory.create_recording_handler()


def quick_counting_handler() -> CountingHandler:
    """Quick creation of counting handler."""
    return HandlerFactory.create_counting_handler()


def quick_trading_handler() -> TradingEventHandler:
    """Quick creation of trading handler."""
    return HandlerFactory.create_trading_handler()
