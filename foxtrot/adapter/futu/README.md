# Futu Trading Adapter for Foxtrot

This directory contains the Futu trading adapter implementation for the Foxtrot trading platform, providing integration with Futu Securities for trading across Hong Kong, US, and China markets using the official Futu OpenAPI.

## Architecture Overview

The adapter follows the **OpenD Gateway Pattern** with the official Futu Python SDK:

```
Foxtrot Application
       ↓
   FutuAdapter  
       ↓
   futu Python SDK
       ↓
   OpenD Gateway (Local)
       ↓
   Futu Servers (Remote)
```

### Key Features

- **Multi-Market Support**: Hong Kong (SEHK), US (NASDAQ/NYSE), China (SZSE/SSE)
- **OpenD Gateway**: Local gateway at 127.0.0.1:11111 for all communications
- **RSA Authentication**: Secure key-based authentication instead of API key/secret
- **Callback-Driven**: Real-time data processing via SDK callbacks
- **Thread-Safe**: All operations designed for concurrent access
- **Existing Exchange Integration**: Uses existing VT exchanges instead of creating new ones

## Directory Structure

```
foxtrot/adapter/futu/
├── __init__.py              # Module initialization
├── futu.py                  # Main adapter facade (BaseAdapter implementation)
├── api_client.py            # OpenD connection coordinator and context manager
├── account_manager.py       # Account queries, balances, and positions
├── order_manager.py         # Order placement, cancellation, and tracking
├── market_data.py          # Real-time market data subscriptions via callbacks
├── historical_data.py      # Historical OHLCV data queries
├── contract_manager.py     # Symbol/contract information management
├── futu_mappings.py        # Data format conversions (Futu SDK ↔ VT)
├── futu_callbacks.py       # SDK callback handlers for events
└── README.md               # This file
```

## Implementation Status

### ✅ Phase 1: Foundation and OpenD Setup (COMPLETED)

**Deliverables Completed:**
- [x] **FutuAdapter Class**: BaseAdapter interface implementation with OpenD integration
- [x] **FutuApiClient**: OpenD connection coordinator with context management
- [x] **Data Mappings**: Comprehensive conversion functions between Futu SDK and VT formats
- [x] **Callback Handlers**: SDK callback processors for real-time data
- [x] **Manager Architecture**: All specialized managers (market data, orders, accounts, etc.)
- [x] **Basic Testing**: Adapter instantiation and mapping validation tests
- [x] **Configuration Structure**: Complete default settings for OpenD gateway

**Key Achievements:**
- ✅ Adapter successfully instantiates and integrates with EventEngine
- ✅ All BaseAdapter abstract methods implemented
- ✅ OpenD gateway architecture properly configured
- ✅ Symbol mapping functions validated for all supported markets
- ✅ Thread-safe manager delegation pattern established
- ✅ RSA key authentication framework in place

### ✅ Phase 2: Authentication and Context Management (COMPLETED)

**Deliverables Completed:**
- [x] **RSA Key Authentication**: Comprehensive RSA key validation and encryption setup
- [x] **Enhanced Connection Management**: Robust connection initialization with retry logic
- [x] **Health Monitoring System**: Real-time connection health checks with heartbeat tracking
- [x] **Automatic Reconnection**: Intelligent reconnection with exponential backoff and state recovery
- [x] **Thread Safety**: Thread-safe operations with proper locking mechanisms
- [x] **Error Handling**: Graceful error handling and connection cleanup
- [x] **Status Monitoring**: Comprehensive connection status and health reporting

**Key Achievements:**
- ✅ RSA key file validation with proper format checking
- ✅ Multi-context initialization (Quote, HK Trade, US Trade) with unlock sequences
- ✅ Background health monitoring thread with configurable intervals
- ✅ Automatic subscription restoration after reconnection
- ✅ Thread-safe connection operations with RLock protection
- ✅ Comprehensive status APIs for monitoring and debugging
- ✅ Connection timeout and retry logic with configurable parameters

### 🚧 Next Phases (TO BE IMPLEMENTED)

#### Phase 3: Market Data Subscriptions
- [ ] Real-time market data subscriptions
- [ ] Multi-market subscription management
- [ ] TickData conversion and event firing
- [ ] Subscription recovery after reconnection

#### Phase 4: Order Management and Execution
- [ ] Order placement via SDK
- [ ] Order status tracking with callbacks
- [ ] Multi-market order routing
- [ ] Order cancellation functionality

#### Phase 5: Account and Position Management
- [ ] Multi-currency account balance queries
- [ ] Cross-market position consolidation
- [ ] Real-time account/position updates

#### Phase 6: Historical Data and Contract Information
- [ ] Historical OHLCV data queries
- [ ] Contract information loading
- [ ] Symbol validation and discovery

#### Phase 7: Error Handling and Resilience
- [ ] Comprehensive error classification
- [ ] Connection recovery mechanisms
- [ ] Subscription and state recovery

#### Phase 8: Testing and Validation
- [ ] Unit test suite (>90% coverage)
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] End-to-end testing

## Configuration

### Default Settings

```python
default_setting = {
    # OpenD Gateway Settings
    "Host": "127.0.0.1",                    # Local OpenD gateway
    "Port": 11111,                          # Standard OpenD port
    "RSA Key File": "conn_key.txt",         # RSA private key file
    "Connection ID": "",                    # Unique connection identifier
    
    # Trading Settings
    "Environment": "SIMULATE",              # REAL/SIMULATE
    "Trading Password": "",                 # For trade context unlock
    "Paper Trading": True,
    
    # Market Access
    "HK Market Access": True,
    "US Market Access": True, 
    "CN Market Access": False,             # May require special permissions
    
    # Connection Management
    "Connect Timeout": 30,
    "Reconnect Interval": 10,
    "Max Reconnect Attempts": 5,
    "Keep Alive Interval": 30,
    
    # Market Data
    "Market Data Level": "L1",
    "Max Subscriptions": 200,
    "Enable Push": True,
}
```

### Supported Exchanges

The adapter integrates with existing Foxtrot exchanges:
- **SEHK**: Hong Kong Stock Exchange
- **NASDAQ**: NASDAQ Stock Exchange
- **NYSE**: New York Stock Exchange
- **SZSE**: Shenzhen Stock Exchange
- **SSE**: Shanghai Stock Exchange

## Symbol Format

### VT Symbol Convention
All symbols follow the standard VT format: `{symbol}.{exchange}`

**Examples:**
- Hong Kong: `"0700.SEHK"` (Tencent Holdings)
- US NASDAQ: `"AAPL.NASDAQ"` (Apple Inc.)
- US NYSE: `"SPY.NYSE"` (SPDR S&P 500 ETF)
- China SZSE: `"000001.SZSE"` (Ping An Bank)
- China SSE: `"600036.SSE"` (China Merchants Bank)

### Futu SDK Format Conversion
The adapter automatically converts between VT and Futu SDK formats:

```python
VT Format      →  Futu SDK Format
"0700.SEHK"    →  ("HK", "HK.00700")
"AAPL.NASDAQ"  →  ("US", "US.AAPL")
"000001.SZSE"  →  ("CN", "CN.000001")
```

## Prerequisites

### Software Requirements
1. **OpenD Gateway**: Must be installed and running locally
2. **Futu API SDK**: Already integrated via `futu-api` package
3. **RSA Keys**: Required for authentication
4. **Market Access**: Appropriate permissions for desired markets

### Setup Steps (For Production Use)
1. Install and configure OpenD gateway
2. Generate RSA key pair for authentication
3. Configure Futu account with required market permissions
4. Set up paper trading environment for testing
5. Configure adapter settings in Foxtrot

## Usage Example

```python
from foxtrot.core.event_engine import EventEngine
from foxtrot.adapter.futu import FutuAdapter

# Create event engine
event_engine = EventEngine()

# Create adapter
adapter = FutuAdapter(event_engine, "FUTU")

# Configure settings
settings = {
    "Host": "127.0.0.1",
    "Port": 11111,
    "RSA Key File": "path/to/conn_key.txt",
    "Trading Password": "your_password",
    "Paper Trading": True,
    # ... other settings
}

# Connect to OpenD gateway
adapter.connect(settings)

# Subscribe to market data
from foxtrot.util.object import SubscribeRequest
from foxtrot.util.constants import Exchange

req = SubscribeRequest(
    symbol="0700",
    exchange=Exchange.SEHK
)
adapter.subscribe(req)

# Place an order
from foxtrot.util.object import OrderRequest
from foxtrot.util.constants import Direction, OrderType

order_req = OrderRequest(
    symbol="0700",
    exchange=Exchange.SEHK,
    direction=Direction.LONG,
    type=OrderType.LIMIT,
    volume=100,
    price=500.0
)
adapter.send_order(order_req)
```

## Performance Targets

Based on OpenD gateway architecture:
- **Market Data Latency**: <100ms (adjusted for gateway overhead)
- **Order Latency**: <200ms (SDK + gateway processing)
- **Connection Recovery**: <60s (OpenD restart time)
- **Memory Usage**: <150MB (SDK overhead included)
- **Subscription Capacity**: >200 symbols

## Development Notes

### Thread Safety
All manager operations are designed to be thread-safe with proper locking mechanisms for callback synchronization.

### Error Handling
Comprehensive error classification and recovery mechanisms are planned for Phase 7, with graceful degradation patterns.

### Testing Strategy
The adapter includes unit tests for all components, with mock SDK integration for consistent testing environments.

## Contributing

When extending the adapter:
1. Follow existing manager delegation patterns
2. Maintain thread safety in all operations
3. Use proper VT data object conversions
4. Include comprehensive error handling
5. Add appropriate unit tests

## References

- [Official Futu OpenAPI Documentation](https://openapi.futunn.com/futu-api-doc/en/)
- [Foxtrot BaseAdapter Interface](../base_adapter.py)
- [VT Data Objects](../../util/object.py)
- [Futu Python SDK on GitHub](https://github.com/futunnopen/py-futu-api)

---

**Last Updated**: January 31, 2025  
**Implementation Phase**: 2 of 8 (Authentication and Context Management Complete)  
**Next Milestone**: Phase 3 - Market Data Subscriptions