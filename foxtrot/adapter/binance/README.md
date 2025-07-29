# Binance Adapter - Modular Architecture

## Overview

The Binance adapter provides trading functionality for the Binance exchange using a modular architecture pattern. This implementation uses the CCXT library for exchange communication and follows the proven design patterns from the ibrokers adapter.

## Architecture

### Modular Design

The adapter is split into specialized managers, each handling a specific aspect of trading operations:

```
foxtrot/adapter/binance/
├── __init__.py                 # Module initialization and exports
├── binance.py                  # Main adapter facade (BaseAdapter implementation)
├── api_client.py               # Central coordinator for all operations
├── account_manager.py          # Account and position management
├── order_manager.py            # Order lifecycle management
├── market_data.py              # Real-time market data streaming
├── historical_data.py          # Historical data queries
├── contract_manager.py         # Contract and symbol management
├── binance_mappings.py         # Data transformation utilities
└── README.md                   # This file
```

### Component Responsibilities

#### `BinanceAdapter` (binance.py)
- **Purpose**: Main facade implementing BaseAdapter interface
- **Responsibilities**: 
  - Coordinate with BinanceApiClient
  - Implement standard adapter interface methods
  - Handle adapter lifecycle (connect, close)

#### `BinanceApiClient` (api_client.py)
- **Purpose**: Central coordinator for all Binance operations
- **Responsibilities**:
  - Manage CCXT exchange instance
  - Initialize and coordinate all managers
  - Provide callback interfaces for events
  - Handle cross-cutting concerns (logging, error handling)

#### `BinanceAccountManager` (account_manager.py)
- **Purpose**: Account and position management
- **Responsibilities**:
  - Query account balance and information
  - Track positions and portfolio state
  - Cache account data for performance

#### `BinanceOrderManager` (order_manager.py)
- **Purpose**: Order lifecycle management
- **Responsibilities**:
  - Send orders to exchange
  - Track order status and updates
  - Handle order cancellation
  - Generate trade events

#### `BinanceMarketData` (market_data.py)
- **Purpose**: Real-time market data streaming
- **Responsibilities**:
  - Manage WebSocket connections
  - Subscribe to market data feeds
  - Process and distribute tick data
  - Handle connection recovery

#### `BinanceHistoricalData` (historical_data.py)
- **Purpose**: Historical data queries
- **Responsibilities**:
  - Fetch historical OHLCV data
  - Handle different timeframes
  - Implement data caching for performance
  - Respect exchange rate limits

#### `BinanceContractManager` (contract_manager.py)
- **Purpose**: Contract and symbol management
- **Responsibilities**:
  - Load and cache contract information
  - Validate trading symbols
  - Provide contract specifications
  - Handle symbol format conversions

#### `BinanceMappings` (binance_mappings.py)
- **Purpose**: Data transformation utilities
- **Responsibilities**:
  - Convert between CCXT and VT data formats
  - Map order types, statuses, and directions
  - Classify and handle exchange errors
  - Provide retry logic for different error types

## Key Features

### Enhanced Error Handling
- **Error Classification**: Automatic categorization of errors (network, auth, rate limit, etc.)
- **Retry Logic**: Intelligent retry with exponential backoff
- **Graceful Degradation**: Continues operation when possible during errors

### Thread Safety
- **Manager Coordination**: Thread-safe operations across all managers
- **Connection Management**: Safe WebSocket connection handling
- **Order Tracking**: Thread-safe order state management

### Performance Optimizations
- **Connection Pooling**: Efficient WebSocket connection reuse
- **Data Caching**: Smart caching for frequently accessed data
- **Rate Limiting**: Respect exchange rate limits automatically

### Symbol Management
- **Dynamic Discovery**: Automatic symbol loading from exchange
- **Format Conversion**: Seamless conversion between VT and CCXT formats
- **Validation**: Symbol validation before trading operations

## Configuration

### Basic Configuration
```python
settings = {
    "API Key": "your_binance_api_key",
    "Secret": "your_binance_secret_key", 
    "Sandbox": True,  # Use sandbox for testing
    "Proxy Host": "",  # Optional proxy settings
    "Proxy Port": 0,
}
```

### Advanced Configuration (Future)
```python
settings = {
    "API Key": "your_binance_api_key",
    "Secret": "your_binance_secret_key",
    "Sandbox": False,
    "Enable Futures": True,          # Enable futures trading
    "Futures API Key": "futures_key", # Separate futures credentials
    "Futures Secret": "futures_secret",
    "Rate Limit Buffer": 0.1,        # Safety buffer for rate limits
    "Reconnect Delay": 5,            # WebSocket reconnection delay
    "Max Retry Attempts": 3,         # Maximum retry attempts
}
```

## Usage

### Basic Usage
```python
from foxtrot.core.event_engine import EventEngine
from foxtrot.adapter.binance import BinanceAdapter

# Create event engine
event_engine = EventEngine()

# Create adapter
adapter = BinanceAdapter(event_engine, "BINANCE")

# Configure settings
settings = {
    "API Key": "your_api_key",
    "Secret": "your_secret", 
    "Sandbox": True
}

# Connect to exchange
if adapter.connect(settings):
    print("Connected successfully")
    
    # Query account
    adapter.query_account()
    
    # Subscribe to market data
    from foxtrot.util.object import SubscribeRequest
    req = SubscribeRequest("BTCUSDT.BINANCE", Exchange.BINANCE)
    adapter.subscribe(req)
    
    # Send order
    from foxtrot.util.object import OrderRequest
    from foxtrot.util.constants import Direction, OrderType
    
    order_req = OrderRequest(
        symbol="BTCUSDT.BINANCE",
        exchange=Exchange.BINANCE,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=0.001,
        price=30000
    )
    adapter.send_order(order_req)
```

## Development Status

### Phase 1: Foundation (Current)
- ✅ Fixed critical import issue
- ✅ Created modular file structure  
- ✅ Implemented basic manager classes
- 🔄 Need to implement basic facade
- 🔄 Need to create test framework

### Phase 2: Core Implementation (Next)
- ⏳ Complete manager implementations
- ⏳ Add comprehensive error handling
- ⏳ Implement thread-safe operations
- ⏳ Achieve >80% test coverage

### Phase 3: Advanced Features (Future)
- ⏳ Add futures trading support
- ⏳ Implement advanced error recovery
- ⏳ Add performance optimizations
- ⏳ Create integration test suite

### Phase 4: Production Readiness (Future)
- ⏳ Complete documentation
- ⏳ Add monitoring and observability
- ⏳ Production testing and validation
- ⏳ Deployment preparation

## Testing

### Unit Tests
```bash
# Run all Binance adapter tests
pytest tests/unit/adapter/binance/ -v

# Run specific manager tests
pytest tests/unit/adapter/binance/test_order_manager.py -v

# Run with coverage
pytest tests/unit/adapter/binance/ -v --cov=foxtrot.adapter.binance
```

### Integration Tests
```bash
# Run integration tests (requires sandbox credentials)
pytest tests/integration/binance/ -v
```

## Contributing

When contributing to the Binance adapter:

1. **Follow the modular pattern**: Keep functionality separated by concern
2. **Add comprehensive tests**: Both unit and integration tests required
3. **Document changes**: Update this README for architectural changes
4. **Error handling**: Use the error classification system in binance_mappings
5. **Thread safety**: Ensure all operations are thread-safe
6. **Performance**: Consider caching and rate limiting impacts

## Troubleshooting

### Common Issues

**Import Error**: If you get import errors, ensure the `__init__.py` file correctly imports from `.binance`

**Connection Failed**: Check API credentials and sandbox settings. Ensure network connectivity to Binance.

**Rate Limit Errors**: The adapter automatically handles rate limiting with exponential backoff. Check your API usage.

**Symbol Format Issues**: Use VT format symbols (e.g., "BTCUSDT.BINANCE"). The adapter handles conversion automatically.

### Debug Mode
Enable debug logging to see detailed operation logs:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```