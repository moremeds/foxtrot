# End-to-End Tests

This directory contains comprehensive end-to-end tests for the Foxtrot trading platform that validate complete system integration with real brokers and exchanges.

## Overview

Unlike unit tests that test individual components in isolation, these e2e tests validate:

- **Complete System Integration**: MainEngine + Adapters + Event System + OMS
- **Real Broker Connectivity**: Actual API connections to exchanges
- **Event Flow Validation**: Events properly flowing through EventEngine to OMS
- **Order Lifecycle Management**: Complete order workflows through MainEngine
- **Error Handling**: Network failures, invalid credentials, timeout scenarios
- **Resource Management**: Proper cleanup and shutdown procedures

## Test Structure

### `test_binance_mainengine_e2e.py`

Comprehensive Binance adapter test using MainEngine architecture:

**Key Features:**
- Uses MainEngine as the core platform (not direct adapter calls)
- Tests event system integration with EventCollector pattern
- Validates OMS state management and data consistency
- Tests both spot and futures trading workflows
- Includes comprehensive error handling and edge cases
- Implements proper resource cleanup

**Test Coverage:**
- MainEngine setup and adapter connection
- Account/position queries through MainEngine interface
- Contract information flow through event system  
- Complete order lifecycle (place, track, cancel)
- Market data subscriptions with real-time tick data
- Futures adapter integration
- Error handling with invalid credentials
- Concurrent operations and thread safety
- State consistency across operations
- Resource cleanup and proper shutdown

## Prerequisites

### API Credentials

Set these environment variables for Binance testnet:

```bash
export BINANCE_TESTNET_SPOT_API_KEY="your_spot_api_key"
export BINANCE_TESTNET_SPOT_SECRET_KEY="your_spot_secret"
export BINANCE_TESTNET_FUTURES_API_KEY="your_futures_api_key" 
export BINANCE_TESTNET_FUTURES_SECRET_KEY="your_futures_secret"
```

Get testnet credentials from: https://testnet.binance.vision/

### Dependencies

```bash
# Install test dependencies
uv sync --dev

# Or with poetry
poetry install --with dev
```

## Running Tests

### Run All E2E Tests
```bash
# Using uv
uv run pytest tests/e2e/ -v -s

# Using poetry  
poetry run pytest tests/e2e/ -v -s
```

### Run Specific Test File
```bash
# Binance MainEngine E2E test
uv run pytest tests/e2e/test_binance_mainengine_e2e.py -v -s
```

### Run Specific Test Method
```bash
# Test only order lifecycle
uv run pytest tests/e2e/test_binance_mainengine_e2e.py::TestBinanceMainEngineE2E::test_order_lifecycle_through_main_engine -v -s
```

### Skip E2E Tests in Regular Runs
```bash
# Skip e2e tests during normal development
pytest tests/ -v --ignore=tests/e2e/
```

## Test Architecture

### EventCollector Pattern

Tests use an `EventCollector` class to capture and verify events:

```python
class EventCollector:
    def collect_event(self, event: Event) -> None:
        """Collect events for later verification."""
        
    def wait_for_events(self, event_type: str, count: int, timeout: float) -> bool:
        """Wait for specific number of events with timeout."""
        
    def get_events_by_type(self, event_type: str) -> List[Event]:
        """Get all events of a specific type."""
```

### MainEngine Integration

Tests use the complete MainEngine architecture:

```python
# Setup MainEngine with event collection
main_engine = MainEngine()
main_engine.event_engine.register(EVENT_ORDER, event_collector.collect_event)

# Add and connect adapter
adapter = main_engine.add_adapter(BinanceAdapter, "BINANCE_SPOT")
main_engine.connect(settings, "BINANCE_SPOT")

# Use MainEngine interface (not direct adapter calls)
order_id = main_engine.send_order(order_req, "BINANCE_SPOT")
account_data = main_engine.get_all_accounts()
```

### Resource Management

All tests implement proper cleanup:

```python
def teardown_method(self):
    """Clean up after each test."""
    # Cancel any remaining orders
    for order_id in self.test_orders:
        # ... cancel logic
    
    # Close main engine and adapters
    if self.main_engine:
        self.main_engine.close()
```

## Important Notes

### Test Environment

- **Testnet Only**: Tests use exchange testnets, never production
- **API Rate Limits**: May be slower due to testnet limitations
- **Network Dependencies**: Requires stable internet connection
- **Longer Execution**: E2E tests take significantly longer than unit tests

### Safety Measures

- All orders use minimal quantities
- Limit orders use very low prices to avoid execution
- Proper cleanup cancels remaining orders
- Uses sandbox/testnet environments only

### Troubleshooting

**Connection Issues:**
- Verify API credentials are correct
- Check testnet service status
- Ensure network connectivity

**Event Timeout Issues:**
- Increase timeout values for slower networks
- Check event registration is correct
- Verify adapter connection status

**Order Issues:**
- Check symbol formats match exchange requirements
- Verify minimum quantity requirements
- Ensure sufficient testnet balance

## Contributing

When adding new e2e tests:

1. **Follow the Pattern**: Use MainEngine + EventCollector pattern
2. **Proper Cleanup**: Always implement thorough cleanup in teardown
3. **Error Handling**: Test both success and failure scenarios  
4. **Documentation**: Document test purpose and requirements
5. **Safety First**: Use testnet environments and minimal quantities

## Comparison with Integration Tests

| Aspect | Integration Tests | E2E Tests |
|--------|------------------|-----------|
| **Scope** | Direct adapter usage | Complete MainEngine architecture |
| **Event Testing** | Limited | Full event system validation |
| **State Management** | Not tested | OMS integration verified |
| **Interface** | Adapter methods directly | MainEngine interface |
| **Complexity** | Moderate | High |
| **Execution Time** | Fast | Slow |
| **Network Dependencies** | Yes | Yes |

E2E tests provide the highest confidence that the complete system works correctly in real-world scenarios.