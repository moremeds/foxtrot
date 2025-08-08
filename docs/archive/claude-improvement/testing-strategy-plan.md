# Foxtrot Testing Strategy Plan

**Document Version:** 1.0  
**Date:** August 6, 2025

## Overview

This document outlines a comprehensive testing infrastructure overhaul inspired by Nautilus Trader's multi-layered testing strategy, adapted for Foxtrot's Python-native environment. The plan transforms Foxtrot's basic test structure into a production-grade testing framework.

---

## Current State Assessment

**Existing Testing Infrastructure:**
- Basic unit tests in `tests/unit/`
- Limited integration tests
- Manual testing processes
- No performance benchmarking
- Minimal test fixtures

**Key Gaps:**
- Lack of performance testing framework
- Limited acceptance/system testing
- No property-based testing
- Insufficient mock infrastructure
- Missing continuous benchmarking

---

## Test Organization Enhancement

### Target Test Structure

```
tests/
├── unit/              # Enhanced unit tests with better coverage
├── integration/       # Enhanced integration test coverage  
├── performance/       # NEW - Performance benchmarking framework
├── acceptance/        # NEW - Black-box system tests
├── fixtures/          # Enhanced comprehensive test data
│   ├── market_data/   # Market data fixtures
│   ├── adapters/      # Adapter mock data
│   └── strategies/    # Strategy test scenarios
├── mocks/             # Enhanced professional mock infrastructure
├── benchmarks/        # Performance benchmark suite
└── conftest.py        # Enhanced test configuration
```

### Phase 1: Test Infrastructure Foundation (2 weeks)

#### 1.1 Reorganize Test Structure

```bash
# Create new test directories
mkdir -p tests/{performance,acceptance,benchmarks}
mkdir -p tests/fixtures/{market_data,adapters,strategies}
mkdir -p tests/mocks/{adapters,engines,data_sources}
```

#### 1.2 Enhanced conftest.py

```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from foxtrot.fixtures import create_test_engine, create_mock_adapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine

@pytest.fixture(scope="session")
def test_event_engine():
    """Shared test event engine for integration tests"""
    engine = EventEngine()
    yield engine
    engine.stop()

@pytest.fixture
def test_main_engine(test_event_engine):
    """Test MainEngine with mocked dependencies"""
    engine = MainEngine(test_event_engine)
    yield engine
    engine.close()

@pytest.fixture
def mock_binance_adapter():
    """Mock Binance adapter with realistic responses"""
    return create_mock_adapter("binance")

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    from tests.fixtures.market_data import generate_sample_data
    return generate_sample_data()
```

#### 1.3 Professional Mock Infrastructure

```python
# tests/fixtures/mock_adapter.py
from foxtrot.adapter.base_adapter import BaseAdapter, AdapterStatus
from foxtrot.util.object import TickData, OrderData, TradeData
import time
import threading
from typing import Dict, List

class MockBinanceAdapter(BaseAdapter):
    """Professional mock with realistic market data simulation"""
    
    def __init__(self):
        super().__init__()
        self.market_data_simulator = MarketDataSimulator()
        self.order_responses = OrderResponseSimulator()
        self.latency_simulator = LatencySimulator(min_latency=0.001, max_latency=0.01)
    
    def connect(self):
        # Simulate connection with realistic latency
        self.latency_simulator.simulate_delay()
        self.status = AdapterStatus.CONNECTED
        self.write_log("Mock Binance adapter connected")
    
    def subscribe(self, req: SubscribeRequest):
        # Simulate realistic market data feed
        threading.Thread(
            target=self._simulate_market_data, 
            args=(req.symbol,), 
            daemon=True
        ).start()
    
    def _simulate_market_data(self, symbol: str):
        """Generate realistic tick data"""
        base_price = 50000.0
        while self.status == AdapterStatus.CONNECTED:
            tick = self.market_data_simulator.generate_tick(symbol, base_price)
            self.on_tick(tick)
            time.sleep(0.1)  # 10 ticks per second

class MarketDataSimulator:
    """Generates realistic market data for testing"""
    
    def __init__(self):
        self.price_generator = RandomWalkPriceGenerator()
    
    def generate_tick(self, symbol: str, base_price: float) -> TickData:
        price = self.price_generator.next_price(base_price)
        return TickData(
            symbol=symbol,
            exchange="BINANCE",
            datetime=datetime.now(),
            last_price=price,
            volume=random.uniform(0.1, 10.0),
            bid_price_1=price - 0.01,
            ask_price_1=price + 0.01,
            bid_volume_1=random.uniform(1.0, 100.0),
            ask_volume_1=random.uniform(1.0, 100.0)
        )
```

---

## Property-Based Testing Integration

### Python Hypothesis Integration

Replace Nautilus's Rust proptest with Python's hypothesis library for property-based testing.

#### Implementation

```python
# tests/unit/util/test_object_properties.py
from hypothesis import given, strategies as st, assume
from foxtrot.util.object import OrderData, TickData
from foxtrot.util.constants import Direction, OrderType

@given(
    quantity=st.floats(min_value=0.01, max_value=1000000),
    price=st.floats(min_value=0.01, max_value=1000000)
)
def test_order_quantity_price_always_positive(quantity, price):
    """Property: Order quantities and prices must always be positive"""
    order = OrderData(
        symbol="BTCUSDT.BINANCE",
        quantity=quantity,
        price=price,
        direction=Direction.LONG,
        type=OrderType.LIMIT
    )
    assert order.quantity > 0
    assert order.price > 0

@given(st.text(min_size=5, max_size=50))
def test_symbol_parsing_idempotent(symbol_str):
    """Property: Symbol parsing should be idempotent"""
    assume("." in symbol_str and symbol_str.count(".") == 1)
    assume(not any(char in symbol_str for char in " \t\n\r"))
    
    from foxtrot.util.utility import parse_vt_symbol
    parsed = parse_vt_symbol(symbol_str)
    reparsed = parse_vt_symbol(str(parsed))
    assert parsed == reparsed

@given(
    prices=st.lists(st.floats(min_value=1.0, max_value=100000.0), min_size=1, max_size=1000)
)
def test_tick_data_ordering_preserved(prices):
    """Property: Tick data processing should preserve chronological ordering"""
    from foxtrot.util.object import TickData
    from datetime import datetime, timedelta
    
    ticks = []
    base_time = datetime.now()
    
    for i, price in enumerate(prices):
        tick = TickData(
            symbol="BTCUSDT.BINANCE",
            exchange="BINANCE", 
            datetime=base_time + timedelta(microseconds=i),
            last_price=price,
            volume=1.0
        )
        ticks.append(tick)
    
    # Property: timestamps should be monotonically increasing
    timestamps = [tick.datetime for tick in ticks]
    assert timestamps == sorted(timestamps)
```

#### Property-Based Test Configuration

```python
# tests/property_test_config.py
from hypothesis import settings, Verbosity

# Configure hypothesis for trading-specific testing
settings.register_profile("fast", max_examples=50, verbosity=Verbosity.normal)
settings.register_profile("thorough", max_examples=1000, verbosity=Verbosity.verbose)
settings.register_profile("ci", max_examples=100, verbosity=Verbosity.normal)

# Load profile based on environment
import os
profile = os.getenv("HYPOTHESIS_PROFILE", "fast")
settings.load_profile(profile)
```

---

## Performance Testing Framework

### Continuous Benchmarking System

Inspired by Nautilus's performance-focused development, implement comprehensive benchmarking.

#### pytest-benchmark Integration

```python
# tests/performance/test_event_engine_performance.py
import pytest
import time
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import Event, TickData

class TestEventEnginePerformance:
    
    @pytest.mark.benchmark(group="event_processing")
    def test_event_processing_throughput(self, benchmark):
        """Benchmark event processing throughput"""
        engine = EventEngine()
        engine.start()
        
        def create_test_events():
            return [Event(EVENT_TICK, self._create_tick()) for _ in range(1000)]
        
        events = create_test_events()
        
        def process_events():
            for event in events:
                engine.put(event)
            # Wait for processing to complete
            time.sleep(0.1)
        
        result = benchmark(process_events)
        engine.stop()
        
        # Assert minimum performance requirements
        assert result.stats.mean < 0.1  # Less than 100ms for 1000 events
    
    @pytest.mark.benchmark(group="memory_usage")
    def test_memory_usage_under_load(self, benchmark):
        """Test memory usage doesn't grow unbounded"""
        import tracemalloc
        import gc
        
        def memory_test():
            tracemalloc.start()
            engine = EventEngine()
            engine.start()
            
            # Simulate heavy load
            for i in range(10000):
                event = Event(EVENT_TICK, self._create_tick())
                engine.put(event)
            
            time.sleep(1)  # Let events process
            gc.collect()  # Force garbage collection
            
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            engine.stop()
            return peak
        
        peak_memory = benchmark(memory_test)
        assert peak_memory < 50 * 1024 * 1024  # Less than 50MB
    
    def _create_tick(self):
        return TickData(
            symbol="BTCUSDT.BINANCE",
            exchange="BINANCE",
            datetime=datetime.now(),
            last_price=50000.0,
            volume=1.0
        )

# tests/performance/test_adapter_performance.py
class TestAdapterPerformance:
    
    @pytest.mark.benchmark(group="order_processing")
    def test_order_submission_latency(self, benchmark, mock_binance_adapter):
        """Benchmark order submission latency"""
        adapter = mock_binance_adapter
        adapter.connect()
        
        def submit_order():
            order = OrderData(
                symbol="BTCUSDT.BINANCE",
                quantity=0.01,
                price=50000.0,
                direction=Direction.LONG,
                type=OrderType.LIMIT
            )
            adapter.send_order(order)
        
        result = benchmark(submit_order)
        # Target: less than 10ms order processing
        assert result.stats.mean < 0.01
```

#### Performance Regression Testing

```python
# tests/performance/conftest.py
import pytest
import json
import os
from pathlib import Path

@pytest.fixture
def performance_baseline():
    """Load performance baseline metrics"""
    baseline_file = Path("tests/performance/baseline.json")
    if baseline_file.exists():
        return json.loads(baseline_file.read_text())
    return {}

@pytest.fixture(autouse=True)
def check_performance_regression(request, benchmark, performance_baseline):
    """Check for performance regressions"""
    if hasattr(request.node, 'benchmark') and request.node.benchmark:
        yield
        
        test_name = request.node.name
        if test_name in performance_baseline:
            baseline = performance_baseline[test_name]
            current = benchmark.stats.mean
            
            # Alert if performance degraded by more than 20%
            if current > baseline * 1.2:
                pytest.fail(f"Performance regression: {current:.4f}s vs baseline {baseline:.4f}s")
```

---

## Acceptance Testing Framework

### End-to-End System Testing

Black-box testing inspired by Nautilus's comprehensive system tests.

#### Implementation

```python
# tests/acceptance/test_trading_workflow.py
import pytest
from foxtrot.server.engine import MainEngine
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Direction, OrderType, OrderStatus

class TestTradingWorkflowAcceptance:
    """End-to-end trading workflow acceptance tests"""
    
    @pytest.fixture
    def trading_system(self):
        """Complete trading system setup for acceptance testing"""
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        
        # Add mock adapters
        from tests.fixtures.mock_adapter import MockBinanceAdapter
        adapter = MockBinanceAdapter()
        main_engine.add_adapter(adapter)
        
        # Start system
        main_engine.init_engines()
        adapter.connect()
        
        yield main_engine
        
        # Cleanup
        main_engine.close()
    
    @pytest.mark.acceptance
    def test_complete_trading_cycle(self, trading_system):
        """Test complete order lifecycle from submission to position update"""
        system = trading_system
        oms = system.get_engine("oms")
        
        # Given: System is running with connected adapters
        assert len(system.adapters) > 0
        assert system.adapters["binance"].status == "connected"
        
        # When: Submit a limit order
        order_req = {
            "symbol": "BTCUSDT.BINANCE",
            "quantity": 0.01,
            "price": 50000.0,
            "direction": Direction.LONG,
            "type": OrderType.LIMIT
        }
        
        order_id = system.submit_order(order_req)
        
        # Then: Order is accepted and tracked
        order = oms.get_order(order_id)
        assert order is not None
        assert order.status in [OrderStatus.SUBMITTED, OrderStatus.ACCEPTED]
        
        # When: Order fills (simulated by mock adapter)
        system.simulate_order_fill(order_id, quantity=0.01, price=50000.0)
        
        # Then: Position and account are updated
        position = oms.get_position("BTCUSDT.BINANCE")
        assert position is not None
        assert position.quantity == 0.01
        
        # Account balance should reflect the trade
        account = system.get_account("binance")
        assert account.available_balance < account.initial_balance
    
    @pytest.mark.acceptance
    def test_risk_management_integration(self, trading_system):
        """Test risk management prevents oversized orders"""
        system = trading_system
        
        # Given: Risk limits are configured
        risk_engine = system.get_engine("risk")
        risk_engine.set_position_limit("BTCUSDT.BINANCE", max_quantity=0.1)
        
        # When: Submit order exceeding position limit
        large_order_req = {
            "symbol": "BTCUSDT.BINANCE",
            "quantity": 0.5,  # Exceeds limit
            "price": 50000.0,
            "direction": Direction.LONG,
            "type": OrderType.LIMIT
        }
        
        # Then: Order should be rejected
        with pytest.raises(RiskViolationException):
            system.submit_order(large_order_req)
    
    @pytest.mark.acceptance 
    def test_market_data_integration(self, trading_system):
        """Test market data flows through system correctly"""
        system = trading_system
        received_ticks = []
        
        def tick_handler(event):
            received_ticks.append(event.data)
        
        # Given: Subscribe to market data
        system.subscribe_tick_data("BTCUSDT.BINANCE")
        system.event_engine.register(EVENT_TICK, tick_handler)
        
        # When: Market data is generated (by mock adapter)
        import time
        time.sleep(2)  # Allow time for tick generation
        
        # Then: Ticks are received and processed
        assert len(received_ticks) > 0
        assert all(tick.symbol == "BTCUSDT.BINANCE" for tick in received_ticks)
        assert all(tick.last_price > 0 for tick in received_ticks)
```

---

## Test Execution Strategy

### Continuous Integration Integration

```yaml
# .github/workflows/test.yml
name: Comprehensive Testing

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          uv sync
          uv pip install pytest-benchmark pytest-cov hypothesis
      
      - name: Run unit tests with coverage
        run: uv run pytest tests/unit/ --cov=foxtrot --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run integration tests
        run: uv run pytest tests/integration/ -v
  
  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run performance benchmarks
        run: |
          uv run pytest tests/performance/ --benchmark-json=performance.json
      
      - name: Check for regressions
        run: |
          # Compare with baseline and fail if regression > 20%
          python scripts/check_performance_regression.py performance.json
  
  acceptance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python  
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run acceptance tests
        run: uv run pytest tests/acceptance/ -v --tb=short
```

### Local Development Testing

```bash
# Makefile additions
test:
	@echo "Running comprehensive test suite..."
	uv run pytest tests/unit/ --cov=foxtrot
	uv run pytest tests/integration/ -v
	uv run pytest tests/performance/ --benchmark-skip
	uv run pytest tests/acceptance/ -v

test-performance:
	@echo "Running performance benchmarks..."
	uv run pytest tests/performance/ --benchmark-json=benchmarks.json

test-property:
	@echo "Running property-based tests..."
	HYPOTHESIS_PROFILE=thorough uv run pytest tests/unit/ -k "property" -v

test-acceptance:
	@echo "Running acceptance tests..."
	uv run pytest tests/acceptance/ -v --tb=short
```

---

## Success Metrics

### Test Coverage Targets
- **Unit Tests**: 95% coverage minimum
- **Integration Tests**: 90% critical path coverage
- **Performance Tests**: 100% critical performance path coverage
- **Acceptance Tests**: 100% major workflow coverage

### Performance Benchmarks
- Event processing: < 100ms for 1000 events
- Order processing: < 10ms average latency
- Memory usage: < 50MB under load
- No memory leaks in 24-hour stress tests

### Quality Gates
- All tests pass before merge
- No performance regressions > 20%
- Property tests pass with 1000+ examples
- Acceptance tests validate end-to-end workflows

This comprehensive testing strategy transforms Foxtrot's testing from basic unit tests to a production-grade testing framework that ensures reliability, performance, and maintainability while remaining accessible to Python developers.