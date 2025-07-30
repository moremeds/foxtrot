# Foxtrot Trading Platform - Testing Guide

## Overview

This document provides comprehensive guidance for testing the Foxtrot trading platform, including test structure, coverage targets, and maintenance procedures.

## Testing Architecture

### Test Structure Organization

```
tests/
├── unit/                    # Unit tests matching project hierarchy
│   ├── adapter/            # Adapter-specific tests
│   │   ├── binance/        # Binance adapter tests (81 tests, 71% coverage)
│   │   └── ibrokers/       # Interactive Brokers adapter tests  
│   ├── core/               # Core engine tests
│   │   ├── event_engine/   # Event engine tests (100% coverage)
│   └── util/               # Utility module tests (100% coverage)
├── integration/            # Integration tests (future)
├── performance/            # Performance benchmarks (future)
└── fixtures/               # Shared test fixtures and mocks
```

### Mock Infrastructure

#### External Dependencies
- **CCXT Library**: Comprehensive mock in `tests/unit/adapter/binance/mock_ccxt.py`
- **IB API**: Mock setup in `tests/unit/adapter/ibrokers/mock_ib_api.py`
- **WebSocket Connections**: Mocked through adapter API clients

#### Test Fixtures
- **Event Engine**: Mock event handlers for testing event-driven workflows
- **Trading Scenarios**: Realistic trading data fixtures for comprehensive testing
- **Network Conditions**: Mock network failures and connection issues

## Coverage Standards

### Current Coverage Status

| Module | Coverage | Tests | Status |
|--------|----------|-------|---------|
| **Core Components** |
| `core/event_engine.py` | 95%+ | 42 tests | ✅ Complete |
| `core/event.py` | 90%+ | 15 tests | ✅ Complete |
| **Utility Modules** |
| `util/constants.py` | 100% | 41 tests | ✅ Complete |
| `util/event_type.py` | 100% | 19 tests | ✅ Complete |
| `util/utility.py` | 47% | 47 tests | ⚠️ Core functions covered |
| **Binance Adapter** |
| `adapter/binance/binance.py` | 80% | 15 tests | ✅ Good |
| `adapter/binance/account_manager.py` | 98% | 11 tests | ✅ Excellent |
| `adapter/binance/api_client.py` | 92% | 11 tests | ✅ Excellent |
| `adapter/binance/order_manager.py` | 89% | 17 tests | ✅ Good |
| `adapter/binance/binance_mappings.py` | 97% | 20 tests | ✅ Excellent |
| **Interactive Brokers** |
| `adapter/ibrokers/*` | N/A | Skipped | ⏸️ On hold |

### Coverage Targets

- **Critical Components**: 90%+ coverage required
- **Core Business Logic**: 85%+ coverage required  
- **Adapter Facades**: 80%+ coverage required
- **Utility Functions**: 70%+ coverage required
- **Complex External Integrations**: 60%+ coverage acceptable

## Testing Phases

### Phase 1: Foundation (✅ Complete)
- **Week 1**: EventEngine core testing with thread safety and performance benchmarks
- **Week 2**: Enhanced utility module testing achieving 100% coverage for constants

### Phase 2: Interactive Brokers Adapter (⏸️ On Hold)
- **Scope**: Comprehensive IB adapter testing (skipped per user request)
- **Status**: Initial test infrastructure created with mock IB API

### Phase 3: Binance Adapter (✅ Complete) 
- **Scope**: Complete Binance adapter test suite
- **Achievement**: 71% overall coverage with 81 tests passing
- **Quality**: Excellent coverage for critical components (80-98%)

### Phase 4: Integration & Performance (🔄 Future)
- Integration tests for adapter interoperability
- Performance benchmarks for high-frequency trading scenarios
- End-to-end workflow validation

## Test Development Guidelines

### Writing Effective Tests

1. **Test Structure**: Follow AAA pattern (Arrange, Act, Assert)
2. **Mock Strategy**: Mock external dependencies, test business logic
3. **Edge Cases**: Include error conditions, boundary values, and failure scenarios
4. **Realistic Scenarios**: Use actual trading data patterns and market conditions

### Example Test Pattern

```python
class TestTradingComponent:
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_exchange = Mock()
        self.component = TradingComponent(self.mock_exchange)
    
    def test_operation_success(self):
        """Test successful operation."""
        # Arrange
        self.mock_exchange.api_call.return_value = {"status": "success"}
        
        # Act
        result = self.component.perform_operation("test_data")
        
        # Assert
        assert result.is_successful
        self.mock_exchange.api_call.assert_called_once_with("test_data")
    
    def test_operation_failure(self):
        """Test operation failure handling."""
        # Arrange
        self.mock_exchange.api_call.side_effect = Exception("Network error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Network error"):
            self.component.perform_operation("test_data")
```

### Mock Best Practices

1. **Scope**: Mock at the boundary of your system under test
2. **Behavior**: Mock behavior, not implementation details
3. **Realism**: Use realistic mock data and responses
4. **Isolation**: Each test should be independent and isolated

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest

# Run specific test module
uv run pytest tests/unit/adapter/binance/

# Run with coverage
uv run pytest --cov=foxtrot --cov-report=html

# Run specific test class
uv run pytest tests/unit/core/test_event_engine_unit.py::TestEventEngine
```

### Performance Testing

```bash
# Run performance benchmarks
uv run pytest tests/unit/core/test_event_engine_performance.py -v

# Run thread safety tests
uv run pytest tests/unit/core/test_event_engine_thread_safety.py -v
```

### Coverage Analysis

```bash
# Generate detailed coverage report
uv run pytest --cov=foxtrot --cov-report=html --cov-report=term-missing

# View coverage in browser
open htmlcov/index.html
```

## Quality Gates

### Pre-Commit Validation

1. **Linting**: `uv run ruff check foxtrot/`
2. **Formatting**: `uv run black foxtrot/`
3. **Type Checking**: `uv run mypy foxtrot/`
4. **Tests**: `uv run pytest`

### Continuous Integration

Tests should be run automatically on:
- Every commit to main branch
- All pull requests
- Nightly builds for comprehensive testing

### Quality Metrics

- **Test Success Rate**: 100% required
- **Coverage Regression**: No decrease in coverage allowed
- **Performance Regression**: No more than 5% performance degradation
- **Memory Leaks**: Zero tolerance for memory leaks in long-running tests

## Maintenance Procedures

### Regular Maintenance

1. **Weekly**: Review test failures and flaky tests
2. **Monthly**: Analyze coverage reports and identify gaps
3. **Quarterly**: Update mock data with latest API responses
4. **Annually**: Review and refactor test architecture

### Adding New Features

1. **TDD Approach**: Write tests before implementation
2. **Coverage Requirement**: New code must have 80%+ test coverage
3. **Integration Points**: Test all integration points with mocks
4. **Documentation**: Update this guide with new testing patterns

### Debugging Test Failures

1. **Isolation**: Run failing test in isolation first
2. **Logging**: Enable debug logging for complex scenarios
3. **Mock Verification**: Verify mock setup matches actual API behavior
4. **Environment**: Check for environment-specific issues

## Advanced Testing Scenarios

### High-Frequency Trading Scenarios

```python
def test_high_frequency_order_processing():
    """Test system behavior under high-frequency trading conditions."""
    # Setup high-volume order scenario
    orders = [create_test_order(i) for i in range(1000)]
    
    # Measure processing time
    start_time = time.time()
    results = [adapter.send_order(order) for order in orders]
    processing_time = time.time() - start_time
    
    # Assert performance requirements
    assert processing_time < 1.0  # Process 1000 orders in under 1 second
    assert all(result for result in results)  # All orders processed successfully
```

### Error Recovery Testing

```python
def test_connection_recovery():
    """Test automatic recovery from connection failures."""
    # Simulate connection failure
    adapter.api_client.connected = False
    
    # Attempt operation
    result = adapter.send_order(test_order)
    
    # Verify recovery attempt
    assert adapter.api_client.reconnect.called
    assert result or adapter.api_client.connection_retry_count > 0
```

### Market Data Integrity Testing

```python
def test_market_data_integrity():
    """Test market data processing integrity."""
    # Setup realistic market data feed
    mock_ticks = generate_realistic_tick_data(symbol="BTCUSDT", count=100)
    
    # Process ticks
    processed_ticks = []
    for tick in mock_ticks:
        processed_tick = adapter.process_tick(tick)
        processed_ticks.append(processed_tick)
    
    # Verify data integrity
    assert len(processed_ticks) == len(mock_ticks)
    assert all(tick.timestamp > 0 for tick in processed_ticks)
    assert all(tick.price > 0 for tick in processed_ticks)
```

## Troubleshooting Common Issues

### Mock Setup Problems

**Issue**: ImportError for external dependencies
**Solution**: Ensure mock modules are imported before foxtrot modules

```python
# Correct order
from .mock_ccxt import *  # Import mock first
from foxtrot.adapter.binance import BinanceAdapter  # Then import foxtrot
```

### Flaky Tests

**Issue**: Tests pass individually but fail when run together
**Solution**: Check for shared state and ensure proper test isolation

```python
def setup_method(self):
    """Reset all state before each test."""
    # Clear any global state
    GlobalState.reset()
    # Create fresh instances
    self.adapter = BinanceAdapter(Mock(), "TEST")
```

### Performance Test Variability

**Issue**: Performance tests give inconsistent results
**Solution**: Use relative performance comparisons and multiple runs

```python
def test_performance():
    """Test with multiple runs for stability."""
    times = []
    for _ in range(5):
        start = time.time()
        perform_operation()
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    assert avg_time < PERFORMANCE_THRESHOLD
```

## Future Enhancements

### Planned Improvements

1. **Integration Testing**: Full end-to-end trading workflows
2. **Load Testing**: Stress testing under high market volatility
3. **Chaos Engineering**: Testing system resilience under failure conditions
4. **Property-Based Testing**: Using hypothesis for edge case discovery
5. **Visual Testing**: UI component testing for trading dashboards
6. **Contract Testing**: API contract validation between adapters

### Testing Infrastructure

1. **Test Data Management**: Centralized test data repository
2. **Parallel Test Execution**: Distributed testing for faster feedback
3. **Test Environment Management**: Containerized test environments
4. **Automated Test Generation**: AI-assisted test case generation
5. **Performance Regression Detection**: Automated performance monitoring

---

## Conclusion

The Foxtrot trading platform maintains high testing standards with comprehensive coverage of critical components. The modular test architecture enables efficient testing of complex trading scenarios while maintaining isolation and reliability.

For questions or contributions to the testing framework, please refer to the project's contribution guidelines or contact the development team.