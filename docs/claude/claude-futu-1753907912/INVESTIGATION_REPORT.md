# Foxtrot Trading Platform Architecture Investigation Report

## Executive Summary

This report provides a comprehensive analysis of the Foxtrot trading platform's adapter architecture, analyzing the existing Binance, Interactive Brokers (IB), and Crypto implementations to understand the patterns, interfaces, and architectural decisions required for implementing a new Futu adapter.

**USE OFFICIAL OPENAPI FUTU from OFFICIAL WEBSITE:**
- https://openapi.futunn.com/futu-api-doc/en/ftapi/init.html      
- https://openapi.futunn.com/futu-api-doc/en/quote/overview.html  
- https://openapi.futunn.com/futu-api-doc/en/trade/overview.html  

## 1. BaseAdapter Interface Analysis

### Core Contract Requirements

The `BaseAdapter` abstract class defines the fundamental contract that all adapters must implement:

```python
# Required Abstract Methods
def connect(setting: dict) -> None
def close() -> None  
def subscribe(req: SubscribeRequest) -> None
def send_order(req: OrderRequest) -> str
def cancel_order(req: CancelRequest) -> None
def query_account() -> None
def query_position() -> None

# Optional Methods (with default implementations)
def send_quote(req: QuoteRequest) -> str
def cancel_quote(req: CancelRequest) -> None  
def query_history(req: HistoryRequest) -> list[BarData]
```

### Thread Safety Requirements

The BaseAdapter documentation explicitly states critical requirements:

- **All methods must be thread-safe**
- **No mutable shared properties between objects**
- **All methods should be non-blocking**
- **Must automatically reconnect if connection lost**
- **Data objects passed to callbacks must be immutable (constant)**

### Event System Integration

The BaseAdapter provides standardized event callbacks:

```python
# Core event methods that fire events through EventEngine
def on_tick(tick: TickData) -> None
def on_trade(trade: TradeData) -> None  
def on_order(order: OrderData) -> None
def on_position(position: PositionData) -> None
def on_account(account: AccountData) -> None
def on_contract(contract: ContractData) -> None
def on_quote(quote: QuoteData) -> None
def on_log(log: LogData) -> None
```

**Key Pattern**: Each event is fired both generally and with symbol/ID-specific suffixes:
- `EVENT_TICK` + `EVENT_TICK + tick.vt_symbol`
- `EVENT_ORDER` + `EVENT_ORDER + order.vt_orderid`

## 2. VT Data Object Standards

### VT Symbol Convention

All symbols follow the format: `{symbol}.{exchange.value}`

Examples:
- `"BTCUSDT.BINANCE"`
- `"SPY.SMART"`
- `"0700.SEHK"` (for Hong Kong stocks)

### VT ID Convention

Objects have adapter-prefixed identifiers:
- `vt_orderid = f"{adapter_name}.{orderid}"`
- `vt_tradeid = f"{adapter_name}.{tradeid}"`
- `vt_accountid = f"{adapter_name}.{accountid}"`

### Data Object Immutability

All data objects use `@dataclass` with `__post_init__` methods:

```python
@dataclass
class TickData(BaseData):
    symbol: str
    exchange: Exchange
    datetime: Datetime
    # ... fields
    
    def __post_init__(self) -> None:
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"
```

### Comprehensive Market Data Structure

The `TickData` object provides extensive market data support:

- **5-level order book** (bid_price_1-5, ask_price_1-5, bid_volume_1-5, ask_volume_1-5)
- **OHLC data** (open_price, high_price, low_price, last_price)
- **Volume and turnover** statistics
- **Limit up/down** prices
- **Open interest** for derivatives

## 3. Binance Adapter Architecture (CCXT-Based)

### Manager Delegation Pattern

The Binance adapter follows a clean separation of concerns:

```
BinanceAdapter (Facade)
    ↓
BinanceApiClient (Coordinator)
    ↓
Specialized Managers:
    - BinanceAccountManager
    - BinanceOrderManager  
    - BinanceMarketData
    - BinanceHistoricalData
    - BinanceContractManager
```

### Key Implementation Patterns

#### 1. Facade Pattern
```python
class BinanceAdapter(BaseAdapter):
    def __init__(self, event_engine: EventEngine, adapter_name: str):
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)
        self.api_client = BinanceApiClient(event_engine, adapter_name)
    
    def send_order(self, req: OrderRequest) -> str:
        if not self.api_client.order_manager:
            return ""
        return self.api_client.order_manager.send_order(req)
```

#### 2. CCXT Integration
```python
class BinanceApiClient:
    def connect(self, settings: dict) -> bool:
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
        })
        self.exchange.set_sandbox_mode(sandbox)
        self.initialize_managers()
```

#### 3. Data Mapping Layer
The `binance_mappings.py` provides centralized conversions:

```python
def convert_symbol_to_ccxt(vt_symbol: str) -> str:
    """Convert BTCUSDT.BINANCE -> BTC/USDT"""
    
def convert_direction_to_ccxt(direction: Direction) -> str:
    """Convert Direction.LONG -> 'buy'"""
    
def convert_status_from_ccxt(ccxt_status: str) -> Status:
    """Convert 'open' -> Status.NOTTRADED"""
```

#### 4. Error Handling Strategy
```python
def classify_error(error: Exception) -> str:
    """Classify errors into categories: network_error, auth_error, rate_limit, etc."""
    
def should_retry_error(error_category: str, attempt: int) -> bool:
    """Determine retry logic based on error type"""
    
def get_retry_delay(error_category: str, attempt: int) -> float:
    """Exponential backoff with category-specific delays"""
```

### Manager Responsibilities

#### Order Manager
- **Thread-safe order tracking** with locks
- **Local order ID generation** for tracking
- **CCXT order conversion** and execution
- **Status synchronization** between local and exchange

#### Account Manager  
- **Balance queries** and position tracking
- **Real-time portfolio updates**
- **Account information caching**

#### Market Data Manager
- **WebSocket subscription management**
- **Real-time tick data processing**
- **Symbol subscription tracking**

## 4. Crypto Adapter Architecture (Multi-Exchange CCXT)

### Universal Crypto Trading Support

The recently added Crypto adapter provides a unified interface for multiple cryptocurrency exchanges:

```python
class CryptoAdapter(BaseAdapter):
    default_name: str = "CRYPTO"
    
    exchanges: list[Exchange] = [
        Exchange.BINANCE, Exchange.BYBIT, Exchange.OKX,
        Exchange.BITGET, Exchange.MEXC, Exchange.GATE, Exchange.KUCOIN
    ]
```

### Exchange-Agnostic Pattern

Unlike the Binance adapter which is exchange-specific, the Crypto adapter dynamically selects exchanges:

```python
def connect(self, setting: dict[str, Any]) -> bool:
    self.exchange_name = setting.get("Exchange", "binance")
    exchange_class = getattr(ccxt, self.exchange_name)
    self.exchange = exchange_class({
        "apiKey": api_key,
        "secret": secret,
        "enableRateLimit": True,
    })
```

### Simplified Architecture

The Crypto adapter uses a flatter structure compared to Binance:

```
CryptoAdapter (Facade)
    ↓
Direct Manager Integration:
    - AccountManager
    - OrderManager
    - MarketData
```

## 5. Interactive Brokers Adapter Architecture (Native API)

### EWrapper Integration Pattern

The IB adapter uses native ibapi with EWrapper callbacks:

```python
class IbApi(EWrapper):
    def __init__(self, adapter):
        super().__init__()
        self.adapter = adapter
        
        # Initialize managers
        self.contract_manager = ContractManager(self.adapter_name)
        self.market_data_manager = MarketDataManager(self.adapter_name)
        self.order_manager = OrderManager(self.adapter_name)
        # ...
        
        self.client: EClient = EClient(self)
```

### Threading Model

```python
def connect(self, host: str, port: int, clientid: int, account: str):
    self.client.connect(host, port, clientid)
    self.thread = Thread(target=self.client.run)
    self.thread.start()
```

### Callback-Driven Architecture

Unlike Binance's polling approach, IB uses native callbacks:

```python
def orderStatus(self, orderId: OrderId, status: str, filled, remaining, 
               avgFillPrice: float, ...):
    """Native IB callback for order status updates"""
    self.order_manager.process_order_status(
        orderId, status, filled, remaining, avgFillPrice, self.adapter.on_order
    )

def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, 
             attrib: TickAttrib):
    """Native IB callback for tick price updates"""
    self.market_data_manager.process_tick_price(
        reqId, tickType, price, attrib, self.contract_manager,
        self.adapter.on_tick, self.adapter.write_log
    )
```

### Request ID Management

IB requires careful request ID coordination:

```python
def get_next_reqid(self) -> int:
    """Centralized request ID generation"""
    self.reqid += 1
    return self.reqid

# Manager methods use temporary request ID injection
def subscribe(self, req) -> None:
    def get_reqid():
        return self.get_next_reqid()
    
    original_method = self.market_data_manager._get_next_reqid
    self.market_data_manager._get_next_reqid = get_reqid
    try:
        self.market_data_manager.subscribe(req, self.client, ...)
    finally:
        self.market_data_manager._get_next_reqid = original_method
```

### IB-Specific Challenges

#### 1. Connection State Management
```python
def check_connection(self) -> None:
    """Periodic connection health checks"""
    if self.client.isConnected():
        return
    
    if self.status:
        self.close()
    # Reconnect logic
```

#### 2. Complex Contract System
IB requires detailed contract specifications:

```python
def generate_ib_contract(symbol: str, exchange: Exchange) -> Contract:
    """Generate IB Contract from VT symbol/exchange"""
    # Complex logic for different product types
```

#### 3. Market Data Synchronization
```python
def error(self, reqId: TickerId, errorCode: int, errorString: str):
    # Market data server connected (code 2104)
    if errorCode == 2104 and not self.data_ready:
        self.data_ready = True
        self.market_data_manager.resubscribe_on_ready(self.client)
```

## 6. Event System Architecture

### EventEngine Core

The event system uses a thread-safe queue-based approach:

```python
class EventEngine:
    def __init__(self, interval: float = 1.0):
        self._queue: Queue[Event] = Queue()
        self._handlers: defaultdict[str, list[HandlerType]] = defaultdict(list)
        self._thread: Thread = Thread(target=self._run)
        self._timer: Thread = Thread(target=self._run_timer)
```

### Enhanced Event Types (Recent Updates)

Standard event types with dot notation for symbol-specific events:

```python
EVENT_TICK = "eTick."
EVENT_TRADE = "eTrade."  
EVENT_ORDER = "eOrder."
EVENT_POSITION = "ePosition."
EVENT_ACCOUNT = "eAccount."
EVENT_CONTRACT = "eContract."
EVENT_QUOTE = "eQuote."
EVENT_LOG = "eLog"
EVENT_TIMER = "eTimer"

# Recently Added Event Types
EVENT_ORDER_CANCEL = "eOrderCancel."
EVENT_ORDER_CANCEL_ALL = "eOrderCancelAll."
EVENT_ACCOUNT_REQUEST = "eAccountRequest."
EVENT_POSITION_REQUEST = "ePositionRequest."
```

### Event Distribution Pattern

Events are distributed both generally and specifically:

```python  
def on_tick(self, tick: TickData) -> None:
    self.on_event(EVENT_TICK, tick)                     # General
    self.on_event(EVENT_TICK + tick.vt_symbol, tick)    # Symbol-specific
```

### Robust Error Handling

The EventEngine includes sophisticated error handling:

```python
def _process(self, event: Event) -> None:
    if event.type in self._handlers:
        for handler in self._handlers[event.type]:
            try:
                handler(event)
            except Exception as e:
                # Don't hold reference to exception object to prevent memory leaks
                error_msg = (
                    f"Handler failed for event {event.type}: {type(e).__name__}: {str(e)}"
                )
                print(error_msg)
```

## 7. MainEngine Integration Architecture

### Component Orchestration

The MainEngine acts as the central coordinator:

```python
class MainEngine:
    def __init__(self, event_engine: EventEngine | None = None):
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine()
        self.event_engine.start()

        self.adapters: dict[str, BaseAdapter] = {}
        self.engines: dict[str, BaseEngine] = {}
        self.apps: dict[str, BaseApp] = {}
        self.exchanges: list[Exchange] = []
```

### Adapter Registration Pattern

```python
def add_adapter(self, adapter_class: type[BaseAdapter], adapter_name: str = "") -> BaseAdapter:
    # Create adapter instance
    # Register with MainEngine
    # Track supported exchanges
    # Initialize OMS integration
```

### OMS (Order Management System) Integration

The MainEngine maintains centralized order/position/account state:

- **Order tracking** across all adapters
- **Position aggregation** from multiple sources
- **Account balance consolidation**
- **Contract/symbol registry**

## 8. Common Architectural Patterns

### 1. Manager Coordination Pattern

All adapters use specialized managers:

```python
# Common Manager Types:
- AccountManager: Balance and position queries
- OrderManager: Order lifecycle management  
- MarketDataManager: Real-time data subscriptions
- ContractManager: Symbol/contract information
- HistoricalDataManager: Historical data queries
```

### 2. Data Mapping Layer

All adapters provide centralized data transformation:

```python
# Binance: binance_mappings.py
# IB: ib_mappings.py
# Crypto: crypto_mappings.py

# Common mapping functions:
def convert_symbol_to_native(vt_symbol: str) -> str
def convert_symbol_from_native(native_symbol: str) -> str  
def convert_direction_to_native(direction: Direction) -> str
def convert_status_from_native(native_status: str) -> Status
```

### 3. Thread Safety Patterns

Adapters implement thread safety differently:

**Binance/Crypto**: Uses explicit locks in managers
```python
class BinanceOrderManager:
    def __init__(self, api_client):
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()
    
    def send_order(self, req: OrderRequest) -> str:
        with self._order_lock:
            self._local_order_id += 1
```

**IB**: Relies on single-threaded callback processing and immutable data

### 4. Error Handling Strategies

**Binance/Crypto**: Sophisticated error classification and retry logic
**IB**: Callback-based error handling with reconnection logic

### 5. Connection Management

**Binance/Crypto**: Simple connect/disconnect with CCXT
**IB**: Complex connection state management with threading

## 9. Futu Adapter Implementation Recommendations

### Required Components

Based on the analysis, a Futu adapter should implement:

#### 1. Core Structure Options

**Option A: Dedicated Futu Adapter (Recommended)**
```python
FutuAdapter (BaseAdapter facade)
    ↓
FutuApiClient (Coordinator)
    ↓
Specialized Managers:
    - FutuAccountManager
    - FutuOrderManager
    - FutuMarketData  
    - FutuHistoricalData
    - FutuContractManager
```

**Option B: Multi-Broker Integration**
```python
# Extend the Crypto adapter pattern for multiple brokers
MultiBrokerAdapter (BaseAdapter facade)
    ↓
BrokerApiClient (Coordinator)
    ↓
Broker-Specific Implementations:
    - FutuImplementation
    - TigerImplementation
    - etc.
```

#### 2. Integration Approach

**Option A: Native Futu OpenAPI**
- Similar to IB pattern with native callbacks
- Direct integration with Futu's WebSocket/REST APIs
- Custom threading and connection management
- Full control over API features

**Option B: Wrapper Library**
- Similar to Binance/Crypto pattern with library
- Use futu-api Python library if available
- Simpler integration but less control

#### 3. Data Mapping Requirements

Create `futu_mappings.py` with functions for:

```python
def convert_symbol_to_futu(vt_symbol: str) -> str:
    """Convert SPY.SMART -> US.SPY or 0700.SEHK -> HK.00700"""

def convert_market_from_futu(futu_market: str) -> Exchange:
    """Convert HK -> Exchange.SEHK, US -> Exchange.NASDAQ/NYSE"""

def convert_order_type_to_futu(order_type: OrderType) -> str:
    """Convert OrderType.LIMIT -> Futu order type"""

def convert_status_from_futu(futu_status: str) -> Status:
    """Convert Futu status -> VT Status enum"""
```

#### 4. Exchange Support

Add Futu-specific exchanges to `constants.py`:
```python
class Exchange(Enum):
    # Existing exchanges...
    FUTU_HK = "FUTU_HK"    # Hong Kong market via Futu
    FUTU_US = "FUTU_US"    # US market via Futu  
    FUTU_CN = "FUTU_CN"    # A-Share market via Futu
```

#### 5. Thread Safety Considerations

Follow the IB pattern for callback-driven APIs or Binance pattern for polling APIs:

```python
class FutuOrderManager:
    def __init__(self, api_client):
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()  # If needed for thread safety
```

#### 6. Connection Management

Implement robust connection handling:

```python
class FutuApiClient:
    def connect(self, settings: dict) -> bool:
        # Initialize Futu API connection
        # Handle authentication
        # Set up callback handlers (if callback-based)
        # Test connection and load initial data
        
    def check_connection(self) -> None:
        # Periodic health checks
        # Automatic reconnection logic
```

#### 7. Market Data Considerations

Futu supports multiple markets, so implement market-specific handling:

```python
class FutuMarketData:
    def subscribe(self, req: SubscribeRequest) -> bool:
        # Parse symbol to determine market (HK/US/CN)
        # Use appropriate Futu subscription method
        # Handle different data formats per market
```

### Implementation Priorities

1. **Start with Order Management**: Core trading functionality
2. **Add Account/Position Queries**: Portfolio management
3. **Implement Market Data**: Real-time price feeds
4. **Add Contract Management**: Symbol/instrument data
5. **Implement Historical Data**: Backtesting support

### Testing Strategy

Follow existing patterns:
- **Unit tests** for each manager component
- **Integration tests** with mock Futu API
- **End-to-end tests** with paper trading account
- **Thread safety tests** for concurrent operations

## 10. Key Implementation Guidelines

### Data Immutability
Ensure all data objects are immutable after creation:
```python
# Create copies before passing to callbacks
contract_copy = ContractData(
    symbol=contract.symbol,
    exchange=contract.exchange,
    # ... all fields
    adapter_name=contract.adapter_name,
)
self.on_contract(contract_copy)
```

### Error Handling
Implement comprehensive error handling:
```python
def classify_futu_error(error: Exception) -> str:
    """Classify Futu API errors for retry logic"""
    
def should_retry_futu_error(error_category: str, attempt: int) -> bool:
    """Determine retry strategy"""
```

### Logging Integration
Use the adapter's logging system:
```python
self.write_log("Connection established")  # Info
self.write_log(f"Error: {error_msg}")     # Error
```

### Configuration
Define default settings:
```python
class FutuAdapter(BaseAdapter):
    default_name: str = "FUTU"
    
    default_setting: dict[str, Any] = {
        "Host": "127.0.0.1",
        "Port": 11111,
        "Unlock Password": "",
        "Trading Password": "",
        "Environment": "SIMULATE",  # REAL/SIMULATE
    }
    
    exchanges: list[Exchange] = [Exchange.FUTU_HK, Exchange.FUTU_US, Exchange.FUTU_CN]
```

### Event Integration
Leverage the enhanced event system:
```python
# Use new event types for enhanced functionality
self.on_event(EVENT_ORDER_CANCEL, cancel_data)
self.on_event(EVENT_ACCOUNT_REQUEST, request_data)
```

## 11. Recent Platform Enhancements

### TUI (Terminal User Interface) Integration

Recent developments include a comprehensive TUI interface:
- **Interactive trading panels** with real-time updates
- **Validation framework** for trading operations
- **Monitor components** for accounts, orders, positions, trades
- **Event-driven updates** through EventEngine integration

### Enhanced Event System

New event types provide more granular control:
- **ORDER_CANCEL events** for cancellation tracking
- **ACCOUNT_REQUEST/POSITION_REQUEST** for query tracking
- **Improved error handling** with memory leak prevention

### Multi-Exchange Crypto Support

The Crypto adapter demonstrates the platform's flexibility:
- **Dynamic exchange selection** at runtime
- **Unified interface** across multiple crypto exchanges
- **CCXT integration** for rapid multi-exchange support

## Conclusion

The Foxtrot trading platform follows consistent architectural patterns across adapters:

1. **BaseAdapter facade** providing clean interface
2. **ApiClient coordinator** managing connections and managers
3. **Specialized managers** handling domain-specific operations
4. **Data mapping layer** for format conversions
5. **Event-driven communication** via EventEngine
6. **Thread-safe implementations** with proper synchronization
7. **Comprehensive error handling** with retry logic
8. **Enhanced event system** with granular event types
9. **Multi-exchange flexibility** demonstrated by Crypto adapter
10. **TUI integration capability** for real-time interfaces

A Futu adapter should follow these established patterns while adapting to Futu's specific API characteristics, whether callback-driven (like IB) or polling-based (like Binance/Crypto). The key is maintaining the clean separation of concerns and thread-safe operation while providing the complete BaseAdapter interface.

The recent enhancements show the platform's continued evolution toward more sophisticated trading interfaces and better multi-exchange support, providing excellent foundation patterns for Futu integration.

---

*Investigation completed: 2025-01-31*
*Files analyzed: 25+ core architecture files*
*Patterns identified: 10 key architectural patterns*
*Recommendations: Complete implementation roadmap with recent enhancements*
*Status: Platform ready for Futu adapter integration*