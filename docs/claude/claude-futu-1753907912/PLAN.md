# Futu Trading Adapter Implementation Plan - Refined

## Executive Summary

This document provides a comprehensive, refined implementation plan for developing a Futu trading adapter for the Foxtrot trading platform. The plan is based on detailed analysis of existing adapter architectures, official Futu OpenAPI documentation, and comprehensive flow analysis of the platform's event-driven architecture.

**Key Refinements from Investigation:**
- **Connection Architecture**: OpenD gateway pattern instead of direct REST API
- **Authentication Method**: RSA key management instead of API key/secret  
- **Integration Approach**: Official `futu` Python SDK instead of custom implementation
- **Threading Model**: Callback-driven (IB pattern) due to push notification architecture
- **VT Symbol Strategy**: Use existing exchanges (SEHK, NASDAQ, NYSE, SZSE, SSE) instead of creating Futu-specific exchanges

**Estimated Timeline**: 10-12 weeks (reduced from original 14 weeks due to official SDK)  
**Complexity**: High (multi-market support, OpenD gateway management)  
**Priority**: High (extends platform to Asian markets with proven architecture)

---

## 1. Architecture Design - Corrected

### 1.1 Connection Architecture (Corrected)

**Official Futu API Architecture:**
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

**Key Architectural Corrections:**
- **Local Gateway Required**: OpenD must run locally (127.0.0.1:11111)
- **WebSocket Protocol**: Uses WebSocket to local OpenD, not direct REST
- **Push Notifications**: Real-time data via callbacks, not polling
- **RSA Encryption**: Requires RSA key files for security
- **Multi-Context**: Separate contexts for quotes and trading

### 1.2 Directory Structure

```
foxtrot/adapter/futu/
├── futu.py                    # Main adapter facade (BaseAdapter implementation)
├── api_client.py             # OpenD connection coordinator and context manager
├── account_manager.py        # Account queries, balances, and positions
├── order_manager.py          # Order placement, cancellation, and tracking
├── market_data.py           # Real-time market data subscriptions via callbacks
├── historical_data.py       # Historical OHLCV data queries
├── contract_manager.py      # Symbol/contract information management
├── futu_mappings.py         # Data format conversions (Futu SDK ↔ VT)
├── futu_callbacks.py        # SDK callback handlers for events
└── __init__.py              # Module initialization
```

### 1.3 Manager Architecture (Refined)

#### FutuAdapter (Main Facade)
```python
class FutuAdapter(BaseAdapter):
    """Main adapter implementing BaseAdapter interface with OpenD integration"""
    default_name: str = "FUTU"
    exchanges: list[Exchange] = [Exchange.SEHK, Exchange.NASDAQ, Exchange.NYSE, 
                                Exchange.SZSE, Exchange.SSE]  # Use existing exchanges
    
    # Threading model: Callback-driven (IB pattern)
    # Connection: OpenD gateway via futu SDK
    # Authentication: RSA key-based
```

#### FutuApiClient (Coordinator) - Updated
- **OpenD Connection Management**: Start/stop OpenD gateway connection
- **Context Coordination**: Manage separate quote and trade contexts
- **RSA Key Management**: Load and manage encryption keys
- **Callback Registration**: Register SDK callbacks with managers
- **Multi-Market Routing**: Route requests to appropriate market contexts
- **Health Monitoring**: Monitor OpenD gateway health and connectivity

#### Manager Responsibilities (Refined)

**FutuAccountManager**
- **Multi-Currency Balances**: HKD, USD, CNY balance tracking via SDK
- **Cross-Market Positions**: Position consolidation across HK/US/CN markets
- **Account Permissions**: Trading permissions and market access verification
- **Real-time Updates**: Account change callbacks via SDK

**FutuOrderManager**  
- **SDK Order Placement**: Use official order placement APIs
- **Callback-Driven Updates**: Order status via SDK callbacks
- **Multi-Market Orders**: Handle different order types per market
- **Thread-Safe Tracking**: Maintain order state with callback synchronization

**FutuMarketData**
- **SDK Subscriptions**: Use official subscription APIs
- **Callback Processing**: Handle tick data callbacks efficiently  
- **Multi-Market Support**: Separate market data contexts
- **Subscription Recovery**: Resubscribe after OpenD reconnection

### 1.4 VT Symbol Mapping Strategy (Corrected)

**Use Existing Exchanges Instead of Creating New Ones:**

```python
# Hong Kong Market - Use existing SEHK
VT_FORMAT: "0700.SEHK"      # Tencent Holdings
FUTU_SDK: ("HK", "00700")   # SDK market and code

# US Market - Use existing NASDAQ/NYSE
VT_FORMAT: "AAPL.NASDAQ"    # Apple Inc.
FUTU_SDK: ("US", "AAPL")    # SDK market and code

# China A-Shares - Use existing SZSE/SSE  
VT_FORMAT: "000001.SZSE"    # Ping An Bank
FUTU_SDK: ("CN", "000001")  # SDK market and code
```

**Benefits of Using Existing Exchanges:**
- Maintains compatibility with existing platform components
- Avoids fragmenting the exchange ecosystem
- Leverages existing exchange-specific logic
- Simplifies multi-adapter integration

---

## 2. Technical Specifications - Updated

### 2.1 Official SDK Integration

**Dependencies (Updated):**
```python
# pyproject.toml additions
[tool.poetry.dependencies]
futu-api = "^6.0.0"  # Official Futu Python SDK
cryptography = "^3.4.8"  # For RSA key management
```

**Connection Configuration (Corrected):**
```python
class FutuAdapter(BaseAdapter):
    default_setting: dict[str, Any] = {
        # OpenD Gateway Settings (Corrected)
        "Host": "127.0.0.1",     # Local OpenD gateway
        "Port": 11111,           # Standard OpenD port
        "RSA Key File": "conn_key.txt",  # RSA private key file
        "Connection ID": "",     # Unique connection identifier
        
        # Trading Settings
        "Environment": "SIMULATE",  # REAL/SIMULATE
        "Trading Password": "",     # For trade context unlock
        "Paper Trading": True,
        
        # Market Access
        "HK Market Access": True,
        "US Market Access": True, 
        "CN Market Access": False,  # May require special permissions
        
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

### 2.2 Threading Model - Callback-Driven (IB Pattern)

**Architecture Choice: Callback-Driven**
Based on SDK architecture analysis, Futu SDK provides push notifications via callbacks, similar to Interactive Brokers. This requires the IB threading pattern:

```python
class FutuApiClient:
    """Single-threaded callback processing similar to IB pattern"""
    
    def __init__(self, event_engine: EventEngine, adapter_name: str):
        # SDK contexts initialized on connect
        self.quote_ctx: Optional[OpenQuoteContext] = None
        self.trade_ctx: Optional[OpenSecTradeContext] = None
        
        # Callback handlers
        self.quote_handler = FutuQuoteHandler(self)
        self.trade_handler = FutuTradeHandler(self)
    
    def connect(self, settings: dict) -> bool:
        """Initialize SDK contexts with callback handlers"""
        try:
            # Initialize quote context
            self.quote_ctx = OpenQuoteContext(
                host=settings["Host"], 
                port=settings["Port"]
            )
            self.quote_ctx.set_handler(self.quote_handler)
            
            # Initialize trade context  
            self.trade_ctx = OpenSecTradeContext(
                host=settings["Host"],
                port=settings["Port"]
            )
            self.trade_ctx.set_handler(self.trade_handler)
            
            # Set RSA encryption
            SysConfig.set_init_rsa_file(settings["RSA Key File"])
            SysConfig.enable_proto_encrypt(True)
            
            return True
            
        except Exception as e:
            self.adapter.write_log(f"Connection failed: {e}")
            return False
```

### 2.3 Data Mapping Functions (SDK-Based)

```python
# futu_mappings.py - Updated for SDK integration
from futu import *

def convert_symbol_to_futu_market(vt_symbol: str) -> tuple[str, str]:
    """Convert VT symbol to Futu SDK market and code
    
    Returns:
        (market, code) - e.g., ("HK", "00700"), ("US", "AAPL")
    """
    symbol, exchange = vt_symbol.split(".")
    
    if exchange == "SEHK":
        return ("HK", symbol.zfill(5))  # Pad with zeros for HK stocks
    elif exchange in ["NASDAQ", "NYSE"]:
        return ("US", symbol)
    elif exchange in ["SZSE", "SSE"]:
        return ("CN", symbol)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")

def convert_futu_to_vt_symbol(market: str, code: str) -> str:
    """Convert Futu SDK format to VT symbol"""
    if market == "HK":
        return f"{code.lstrip('0')}.SEHK"  # Remove leading zeros
    elif market == "US":
        # Determine specific US exchange (simplified - use NASDAQ as default)
        return f"{code}.NASDAQ"
    elif market == "CN":
        # Determine specific CN exchange (simplified - use SZSE as default)
        return f"{code}.SZSE"
    else:
        raise ValueError(f"Unsupported market: {market}")

def convert_order_type_to_futu(order_type: OrderType) -> OrderType:
    """Convert VT OrderType to Futu SDK OrderType"""
    mapping = {
        OrderType.LIMIT: OrderType.NORMAL,      # Regular limit order
        OrderType.MARKET: OrderType.MARKET,     # Market order
        OrderType.STOP: OrderType.STOP,         # Stop order
    }
    return mapping.get(order_type, OrderType.NORMAL)

def convert_futu_order_status(futu_status: OrderStatus) -> Status:
    """Convert Futu SDK order status to VT Status"""
    mapping = {
        OrderStatus.NONE: Status.SUBMITTING,
        OrderStatus.UNSUBMITTED: Status.NOTTRADED,
        OrderStatus.WAITING_SUBMIT: Status.SUBMITTING,
        OrderStatus.SUBMITTING: Status.SUBMITTING,
        OrderStatus.SUBMITTED: Status.NOTTRADED,
        OrderStatus.FILLED_PART: Status.PARTTRADED,
        OrderStatus.FILLED_ALL: Status.ALLTRADED,
        OrderStatus.CANCELLED_PART: Status.PARTTRADED,
        OrderStatus.CANCELLED_ALL: Status.CANCELLED,
        OrderStatus.FAILED: Status.REJECTED,
        OrderStatus.DISABLED: Status.REJECTED,
        OrderStatus.DELETED: Status.CANCELLED,
    }
    return mapping.get(futu_status, Status.SUBMITTING)
```

---

## 3. Implementation Phases - Refined

### Phase 1: Foundation and OpenD Setup (Week 1)
**Priority**: Highest - Infrastructure foundation  
**Dependencies**: None

#### Deliverables
- [ ] **FutuAdapter Class**: BaseAdapter interface implementation
- [ ] **OpenD Integration**: Basic OpenD gateway connection setup  
- [ ] **SDK Installation**: Official futu-api package integration
- [ ] **RSA Key Management**: Encryption key loading and configuration
- [ ] **Basic Logging**: Integration with adapter logging framework
- [ ] **Configuration Validation**: Settings structure and validation

#### Success Criteria
- FutuAdapter successfully instantiated and registered with MainEngine
- OpenD gateway connection attempt returns clear success/failure status
- RSA key loading functional (with test keys)
- SDK contexts can be initialized
- Logging properly integrated with existing system

#### Key Implementation Details
```python
class FutuAdapter(BaseAdapter):
    default_name: str = "FUTU"
    
    def __init__(self, event_engine: EventEngine, adapter_name: str):
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)
        self.api_client = FutuApiClient(event_engine, adapter_name)
        
    def connect(self, setting: dict) -> None:
        """Connect to OpenD gateway via SDK"""
        if self.connected:
            self.write_log("Already connected to Futu OpenD")
            return
            
        self.write_log("Connecting to Futu OpenD gateway...")
        success = self.api_client.connect(setting)
        
        if success:
            self.connected = True
            self.write_log("Connected to Futu OpenD successfully")
            # Initialize contract loading, account queries
            self.api_client.load_initial_data()
        else:
            self.write_log("Failed to connect to Futu OpenD")
```

#### Files Created/Modified
- `foxtrot/adapter/futu/futu.py` - Main adapter facade
- `foxtrot/adapter/futu/api_client.py` - OpenD connection coordinator
- `foxtrot/adapter/futu/__init__.py` - Module initialization
- `pyproject.toml` - Add futu-api dependency
- `foxtrot/util/constants.py` - No new exchanges needed (use existing)

---

### Phase 2: Authentication and Context Management (Week 2)
**Priority**: Highest - Required for all operations  
**Dependencies**: Phase 1 complete

#### Deliverables
- [ ] **RSA Key Authentication**: Full RSA key-based authentication
- [ ] **Context Management**: Quote and trade context coordination
- [ ] **Connection Health Monitoring**: OpenD gateway health checks
- [ ] **Reconnection Logic**: Automatic reconnection with state recovery
- [ ] **Error Classification**: OpenD-specific error handling

#### Success Criteria
- Successful authentication with valid RSA keys and trading password
- Both quote and trade contexts properly initialized
- Connection state accurately tracked and reported
- Automatic reconnection functional after OpenD restart
- Clear error messages for authentication and connection failures

#### Key Implementation Details
```python
class FutuApiClient:
    def connect(self, settings: dict) -> bool:
        try:
            # Configure RSA encryption
            rsa_file = settings.get("RSA Key File", "conn_key.txt")
            if not os.path.exists(rsa_file):
                raise FileNotFoundError(f"RSA key file not found: {rsa_file}")
                
            SysConfig.set_init_rsa_file(rsa_file)
            SysConfig.enable_proto_encrypt(True)
            
            # Initialize quote context
            self.quote_ctx = OpenQuoteContext(
                host=settings["Host"],
                port=settings["Port"]
            )
            
            # Test quote connection
            ret, data = self.quote_ctx.get_global_state()
            if ret != RET_OK:
                raise ConnectionError(f"Quote context failed: {data}")
            
            # Initialize trade context
            self.trade_ctx = OpenSecTradeContext(
                host=settings["Host"],
                port=settings["Port"]
            )
            
            # Unlock trading if password provided
            trading_pwd = settings.get("Trading Password")
            if trading_pwd:
                ret, data = self.trade_ctx.unlock_trade(trading_pwd)
                if ret != RET_OK:
                    raise AuthenticationError(f"Trading unlock failed: {data}")
            
            # Set up callback handlers
            self.setup_callback_handlers()
            
            self.connected = True
            self.adapter.write_log("Futu OpenD connected and authenticated")
            return True
            
        except Exception as e:
            self.adapter.write_log(f"Connection failed: {e}")
            return False
    
    def setup_callback_handlers(self):
        """Register SDK callback handlers"""
        self.quote_handler = FutuQuoteHandler(self)
        self.trade_handler = FutuTradeHandler(self)
        
        self.quote_ctx.set_handler(self.quote_handler)
        self.trade_ctx.set_handler(self.trade_handler)
```

#### Files Created/Modified
- `foxtrot/adapter/futu/api_client.py` - Enhanced with authentication
- `foxtrot/adapter/futu/futu_callbacks.py` - SDK callback handlers
- Configuration examples and RSA key setup documentation

---

### Phase 3: Market Data Subscriptions (Weeks 3-4)
**Priority**: High - Real-time data foundation  
**Dependencies**: Phase 2 complete

#### Deliverables
- [ ] **FutuMarketData Manager**: Real-time market data via SDK callbacks
- [ ] **Multi-Market Subscriptions**: HK, US, CN market data support
- [ ] **TickData Conversion**: SDK data to VT TickData objects
- [ ] **Subscription Management**: Track and recover subscriptions
- [ ] **Callback Processing**: Efficient tick data callback handling

#### Success Criteria
- Successfully subscribe to real-time market data across all markets
- TickData objects properly formatted with all required fields
- Events properly fired through EventEngine (general + symbol-specific)
- Multi-market subscriptions working simultaneously
- Subscription recovery after OpenD reconnection
- Performance: <100ms latency from market to application (adjusted for gateway)

#### Key Implementation Details
```python
class FutuMarketData:
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        self.subscriptions: dict[str, dict] = {}  # Track active subscriptions
        
    def subscribe(self, req: SubscribeRequest) -> bool:
        """Subscribe to real-time market data via SDK"""
        try:
            # Convert VT symbol to Futu format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)
            
            # Validate symbol exists
            if not self._validate_symbol(market, code):
                self.api_client.adapter.write_log(f"Invalid symbol: {req.vt_symbol}")
                return False
            
            # Subscribe via SDK
            ret, data = self.api_client.quote_ctx.subscribe(
                code_list=[code],
                subtype_list=[SubType.QUOTE, SubType.ORDER_BOOK]
            )
            
            if ret != RET_OK:
                self.api_client.adapter.write_log(f"Subscription failed: {data}")
                return False
            
            # Track subscription
            self.subscriptions[req.vt_symbol] = {
                "market": market,
                "code": code,
                "subtype": [SubType.QUOTE, SubType.ORDER_BOOK],
                "timestamp": datetime.now()
            }
            
            self.api_client.adapter.write_log(f"Subscribed to {req.vt_symbol}")
            return True
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Subscription error: {e}")
            return False

class FutuQuoteHandler(StockQuoteHandlerBase):
    """SDK callback handler for market data"""
    
    def __init__(self, api_client: FutuApiClient):
        super().__init__()
        self.api_client = api_client
        
    def on_recv_rsp(self, rsp_pb):
        """Handle real-time quote data callbacks"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            return RET_ERROR, content
            
        # Convert SDK data to TickData
        for quote_data in content:
            tick = self._convert_to_tick_data(quote_data)
            if tick:
                # Fire events through adapter
                self.api_client.adapter.on_tick(tick)
                
        return RET_OK, content
        
    def _convert_to_tick_data(self, quote_data) -> Optional[TickData]:
        """Convert SDK quote data to VT TickData object"""
        try:
            # Determine VT symbol from market and code
            vt_symbol = convert_futu_to_vt_symbol(
                quote_data.get("market", ""),
                quote_data.get("code", "")
            )
            
            # Extract exchange from VT symbol
            symbol, exchange_str = vt_symbol.split(".")
            exchange = Exchange(exchange_str)
            
            # Create TickData object
            tick = TickData(
                symbol=symbol,
                exchange=exchange,
                datetime=datetime.now(),
                last_price=float(quote_data.get("last_price", 0)),
                volume=float(quote_data.get("volume", 0)),
                open_price=float(quote_data.get("open_price", 0)),
                high_price=float(quote_data.get("high_price", 0)),
                low_price=float(quote_data.get("low_price", 0)),
                # Order book data (5 levels)
                bid_price_1=float(quote_data.get("bid_price_1", 0)),
                ask_price_1=float(quote_data.get("ask_price_1", 0)),
                bid_volume_1=float(quote_data.get("bid_volume_1", 0)),
                ask_volume_1=float(quote_data.get("ask_volume_1", 0)),
                # Additional fields as available
                adapter_name=self.api_client.adapter_name,
            )
            
            return tick
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Tick conversion failed: {e}")
            return None
```

#### Files Created/Modified
- `foxtrot/adapter/futu/market_data.py` - Market data manager
- `foxtrot/adapter/futu/futu_callbacks.py` - Enhanced with quote handler
- `foxtrot/adapter/futu/futu_mappings.py` - Symbol conversion functions

---

### Phase 4: Order Management and Execution (Weeks 5-6)
**Priority**: High - Core trading functionality  
**Dependencies**: Phase 2 complete (Phase 3 recommended)

#### Deliverables
- [ ] **FutuOrderManager**: Order placement via SDK
- [ ] **Order Status Tracking**: Callback-driven order status updates
- [ ] **Multi-Market Orders**: Order routing across HK/US/CN markets
- [ ] **Order Cancellation**: Cancel functionality with proper status updates
- [ ] **Thread-Safe State Management**: Order tracking with callback synchronization

#### Success Criteria
- Successfully place and cancel orders across all supported markets
- Order status updates received via callbacks and processed correctly
- Order tracking remains consistent under concurrent operations
- Orders properly tracked in OMS with correct VT identifiers
- Multi-market order routing functional
- Performance: <200ms order latency (adjusted for OpenD gateway)

#### Key Implementation Details
```python
class FutuOrderManager:
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()  # Callback synchronization
        self._local_order_id = 0
        
    def send_order(self, req: OrderRequest) -> str:
        """Send order via Futu SDK"""
        try:
            # Convert VT request to SDK format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)
            futu_order_type = convert_order_type_to_futu(req.type)
            futu_trd_side = TrdSide.BUY if req.direction == Direction.LONG else TrdSide.SELL
            
            # Generate local order ID
            with self._order_lock:
                self._local_order_id += 1
                local_orderid = f"FUTU.{self._local_order_id}"
            
            # Create initial OrderData
            order = OrderData(
                symbol=req.symbol,
                exchange=req.exchange,
                orderid=local_orderid,
                type=req.type,
                direction=req.direction,
                volume=req.volume,
                price=req.price,
                status=Status.SUBMITTING,
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )
            
            # Store order before submission
            with self._order_lock:
                self._orders[local_orderid] = order
            
            # Submit to SDK
            ret, data = self.api_client.trade_ctx.place_order(
                price=req.price,
                qty=int(req.volume),
                code=code,
                trd_side=futu_trd_side,
                order_type=futu_order_type,
                trd_env=TrdEnv.SIMULATE if self.api_client.paper_trading else TrdEnv.REAL,
            )
            
            if ret != RET_OK:
                # Update order as rejected
                order.status = Status.REJECTED
                with self._order_lock:
                    self._orders[local_orderid] = order
                self.api_client.adapter.on_order(order)
                self.api_client.adapter.write_log(f"Order submission failed: {data}")
                return ""
            
            # Update order with exchange ID
            exchange_orderid = str(data["order_id"])
            order.orderid = exchange_orderid
            order.status = Status.NOTTRADED
            
            with self._order_lock:
                # Keep both local and exchange ID mapping
                self._orders[local_orderid] = order
                self._orders[exchange_orderid] = order
            
            # Fire order event
            self.api_client.adapter.on_order(order)
            self.api_client.adapter.write_log(f"Order submitted: {exchange_orderid}")
            
            return local_orderid
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Order submission error: {e}")
            return ""
    
    def cancel_order(self, req: CancelRequest) -> None:
        """Cancel order via SDK"""
        try:
            # Find order by VT order ID
            order = self._orders.get(req.vt_orderid)
            if not order:
                self.api_client.adapter.write_log(f"Order not found: {req.vt_orderid}")
                return
            
            # Cancel via SDK
            ret, data = self.api_client.trade_ctx.modify_order(
                ModifyOrderOp.CANCEL,
                order_id=int(order.orderid),
                qty=0,
                price=0
            )
            
            if ret != RET_OK:
                self.api_client.adapter.write_log(f"Order cancellation failed: {data}")
            else:
                self.api_client.adapter.write_log(f"Order cancellation requested: {order.orderid}")
                
        except Exception as e:
            self.api_client.adapter.write_log(f"Cancel order error: {e}")

class FutuTradeHandler(TradeOrderHandlerBase):
    """SDK callback handler for order and trade updates"""
    
    def __init__(self, api_client: FutuApiClient):
        super().__init__()
        self.api_client = api_client
        
    def on_recv_rsp(self, rsp_pb):
        """Handle order status update callbacks"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            return RET_ERROR, content
            
        # Process order updates
        for order_data in content:
            self._process_order_update(order_data)
            
        return RET_OK, content
        
    def _process_order_update(self, order_data):
        """Convert SDK order data to VT OrderData and fire events"""
        try:
            # Convert SDK order to VT format
            vt_symbol = convert_futu_to_vt_symbol(
                order_data.get("market", ""),
                order_data.get("code", "")
            )
            symbol, exchange_str = vt_symbol.split(".")
            
            order = OrderData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                orderid=str(order_data["order_id"]),
                type=convert_futu_to_vt_order_type(order_data["order_type"]),
                direction=Direction.LONG if order_data["trd_side"] == TrdSide.BUY else Direction.SHORT,
                volume=float(order_data["qty"]),
                price=float(order_data["price"]),
                traded=float(order_data.get("dealt_qty", 0)),
                status=convert_futu_order_status(order_data["order_status"]),
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )
            
            # Update order manager state
            order_manager = self.api_client.order_manager
            if order_manager:
                with order_manager._order_lock:
                    order_manager._orders[order.orderid] = order
            
            # Fire order event
            self.api_client.adapter.on_order(order)
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Order update processing failed: {e}")
```

#### Files Created/Modified
- `foxtrot/adapter/futu/order_manager.py` - Order management with SDK
- `foxtrot/adapter/futu/futu_callbacks.py` - Enhanced with trade handler  
- `foxtrot/adapter/futu/futu_mappings.py` - Order type conversions

---

### Phase 5: Account and Position Management (Week 7)
**Priority**: Medium - Portfolio management  
**Dependencies**: Phase 2 complete

#### Deliverables
- [ ] **FutuAccountManager**: Account balance queries via SDK
- [ ] **Multi-Currency Support**: HKD, USD, CNY balance tracking
- [ ] **Position Management**: Cross-market position consolidation
- [ ] **Real-time Updates**: Account/position change callbacks
- [ ] **Portfolio Synchronization**: Integration with OMS state management

#### Success Criteria
- Account balances accurately retrieved across all currencies
- Positions properly tracked and updated across all markets
- Multi-currency balances properly converted and reported
- Account/position events properly fired and processed by OMS
- Real-time account updates functional (if supported by SDK)

#### Key Implementation Details
```python
class FutuAccountManager:
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        
    def query_account(self) -> None:
        """Query account information via SDK"""
        try:
            # Query account info for each supported market
            markets = ["HK", "US", "CN"] if self.api_client.cn_access else ["HK", "US"]
            
            for market in markets:
                ret, data = self.api_client.trade_ctx.accinfo_query(
                    trd_env=TrdEnv.SIMULATE if self.api_client.paper_trading else TrdEnv.REAL,
                    trd_market=self._get_trd_market(market)
                )
                
                if ret != RET_OK:
                    self.api_client.adapter.write_log(f"Account query failed for {market}: {data}")
                    continue
                
                # Process account data for this market
                for acc_data in data:
                    account = AccountData(
                        accountid=f"FUTU.{market}.{acc_data['acc_id']}",
                        balance=float(acc_data["total_assets"]),
                        frozen=float(acc_data["frozen_cash"]),
                        available=float(acc_data["avl_withdrawal_cash"]),
                        commission=float(acc_data.get("total_fee", 0)),
                        margin=float(acc_data.get("margin_call_req", 0)),
                        datetime=datetime.now(),
                        adapter_name=self.api_client.adapter_name,
                    )
                    
                    # Fire account event
                    self.api_client.adapter.on_account(account)
                    
        except Exception as e:
            self.api_client.adapter.write_log(f"Account query error: {e}")
    
    def query_position(self) -> None:
        """Query position information via SDK"""
        try:
            # Query positions for each market
            markets = ["HK", "US", "CN"] if self.api_client.cn_access else ["HK", "US"]
            
            for market in markets:
                ret, data = self.api_client.trade_ctx.position_list_query(
                    trd_env=TrdEnv.SIMULATE if self.api_client.paper_trading else TrdEnv.REAL,
                    trd_market=self._get_trd_market(market)
                )
                
                if ret != RET_OK:
                    self.api_client.adapter.write_log(f"Position query failed for {market}: {data}")
                    continue
                
                # Process position data
                for pos_data in data:
                    # Convert to VT symbol
                    vt_symbol = convert_futu_to_vt_symbol(market, pos_data["code"])
                    symbol, exchange_str = vt_symbol.split(".")
                    
                    # Determine position direction
                    qty = float(pos_data["qty"])
                    direction = Direction.LONG if qty > 0 else Direction.SHORT
                    
                    position = PositionData(
                        symbol=symbol,
                        exchange=Exchange(exchange_str),
                        direction=direction,
                        volume=abs(qty),
                        frozen=float(pos_data.get("frozen_qty", 0)),
                        price=float(pos_data["cost_price"]),
                        pnl=float(pos_data["unrealized_pl"]),
                        yd_volume=float(pos_data.get("yesterday_qty", 0)),
                        datetime=datetime.now(),
                        adapter_name=self.api_client.adapter_name,
                    )
                    
                    # Fire position event
                    self.api_client.adapter.on_position(position)
                    
        except Exception as e:
            self.api_client.adapter.write_log(f"Position query error: {e}")
    
    def _get_trd_market(self, market: str) -> TrdMarket:
        """Convert market string to SDK TrdMarket enum"""
        mapping = {
            "HK": TrdMarket.HK,
            "US": TrdMarket.US,
            "CN": TrdMarket.CN_SH,  # Simplified - may need both SH/SZ
        }
        return mapping.get(market, TrdMarket.HK)
```

#### Files Created/Modified
- `foxtrot/adapter/futu/account_manager.py` - Account/position management
- `foxtrot/adapter/futu/api_client.py` - Enhanced with account manager integration

---

### Phase 6: Historical Data and Contract Information (Week 8)
**Priority**: Low - Enhancement features  
**Dependencies**: Phase 2 complete

#### Deliverables
- [ ] **FutuHistoricalData**: Historical OHLCV data queries via SDK
- [ ] **FutuContractManager**: Contract information and symbol validation
- [ ] **Multi-Market Support**: Historical data across HK/US/CN markets
- [ ] **Caching Strategy**: Efficient contract and historical data caching
- [ ] **Symbol Discovery**: Available instruments and contract specifications

#### Success Criteria
- Historical data queries functional across all supported markets
- Contract information properly retrieved and cached
- Symbol validation working for all markets
- Data properly formatted as VT BarData objects
- Performance optimized with appropriate caching

#### Key Implementation Details
```python
class FutuHistoricalData:
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        self._cache: dict[str, list[BarData]] = {}
        self._cache_timeout = 300  # 5 minutes
        
    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """Query historical data via SDK"""
        try:
            # Check cache first
            cache_key = f"{req.vt_symbol}_{req.interval}_{req.start}_{req.end}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # Convert VT parameters to SDK format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)
            kl_type = self._convert_interval_to_ktype(req.interval)
            
            # Query from SDK
            ret, data = self.api_client.quote_ctx.get_cur_kline(
                code=code,
                num=1000,  # Max number of records
                kl_type=kl_type,
                autype=AuType.QFQ  # Forward adjusted
            )
            
            if ret != RET_OK:
                self.api_client.adapter.write_log(f"Historical data query failed: {data}")
                return []
            
            # Convert to BarData objects
            bars = []
            for kline_data in data:
                bar = BarData(
                    symbol=req.symbol,
                    exchange=req.exchange,
                    datetime=datetime.strptime(kline_data["time_key"], "%Y-%m-%d %H:%M:%S"),
                    interval=req.interval,
                    volume=float(kline_data["volume"]),
                    turnover=float(kline_data["turnover"]),
                    open_price=float(kline_data["open"]),
                    high_price=float(kline_data["high"]),
                    low_price=float(kline_data["low"]),
                    close_price=float(kline_data["close"]),
                    adapter_name=self.api_client.adapter_name,
                )
                bars.append(bar)
            
            # Cache results
            self._cache[cache_key] = bars
            
            return bars
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Historical data error: {e}")
            return []

class FutuContractManager:
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        self._contracts: dict[str, ContractData] = {}
        
    def load_all_contracts(self) -> None:
        """Load contract information for all markets"""
        markets = ["HK", "US", "CN"] if self.api_client.cn_access else ["HK", "US"]
        
        for market in markets:
            self._load_market_contracts(market)
    
    def _load_market_contracts(self, market: str) -> None:
        """Load contracts for specific market"""
        try:
            # Query stock list for market
            ret, data = self.api_client.quote_ctx.get_stock_basicinfo(
                market=Market.HK if market == "HK" else Market.US,
                stock_type=SecurityType.STOCK
            )
            
            if ret != RET_OK:
                self.api_client.adapter.write_log(f"Contract loading failed for {market}: {data}")
                return
            
            # Process contract data
            for stock_info in data:
                vt_symbol = convert_futu_to_vt_symbol(market, stock_info["code"])
                symbol, exchange_str = vt_symbol.split(".")
                
                contract = ContractData(
                    symbol=symbol,
                    exchange=Exchange(exchange_str),
                    name=stock_info["name"],
                    product=Product.EQUITY,
                    size=1.0,
                    pricetick=0.01,  # Default, may need market-specific logic
                    min_volume=1.0,
                    stop_supported=False,
                    net_position=True,
                    history_data=True,
                    adapter_name=self.api_client.adapter_name,
                )
                
                self._contracts[vt_symbol] = contract
                
                # Fire contract event
                self.api_client.adapter.on_contract(contract)
                
        except Exception as e:
            self.api_client.adapter.write_log(f"Contract loading error for {market}: {e}")
```

#### Files Created/Modified
- `foxtrot/adapter/futu/historical_data.py` - Historical data manager
- `foxtrot/adapter/futu/contract_manager.py` - Contract information manager

---

### Phase 7: Error Handling and Resilience (Week 9)
**Priority**: High - Production readiness  
**Dependencies**: Phases 1-6 partially complete

#### Deliverables
- [ ] **OpenD-Specific Error Classification**: Error categories and handling
- [ ] **Connection Recovery**: Automatic OpenD reconnection and state recovery  
- [ ] **Subscription Recovery**: Resubscribe to market data after reconnection
- [ ] **Order State Recovery**: Query and synchronize order states
- [ ] **Comprehensive Logging**: Detailed error logging and monitoring

#### Success Criteria
- Robust error handling for all OpenD and SDK error types
- Automatic recovery from connection failures with state preservation
- Clear error reporting and logging for debugging
- System remains stable under various error conditions
- Performance maintained during error recovery scenarios

#### Key Implementation Details  
```python
class FutuErrorClassifier:
    """Enhanced error classification for Futu SDK and OpenD errors"""
    
    OPEND_ERRORS = [
        "connection_refused",
        "opend_not_running", 
        "opend_version_mismatch",
        "gateway_timeout",
    ]
    
    AUTH_ERRORS = [
        "rsa_key_invalid",
        "trading_unlock_failed",
        "insufficient_permissions",
        "account_verification_required",
    ]
    
    SDK_ERRORS = [
        "protocol_version_mismatch",
        "context_initialization_failed",
        "callback_registration_failed",
        "serialization_error",
    ]
    
    TRADING_ERRORS = [
        "order_validation_failed",
        "insufficient_funds",
        "position_limit_exceeded",
        "market_closed",
    ]
    
    @classmethod
    def classify_error(cls, error: Exception) -> str:
        """Classify error for appropriate handling"""
        error_msg = str(error).lower()
        
        if any(keyword in error_msg for keyword in cls.OPEND_ERRORS):
            return "opend_error"
        elif any(keyword in error_msg for keyword in cls.AUTH_ERRORS):
            return "auth_error"
        elif any(keyword in error_msg for keyword in cls.SDK_ERRORS):
            return "sdk_error"
        elif any(keyword in error_msg for keyword in cls.TRADING_ERRORS):
            return "trading_error"
        else:
            return "unknown_error"

class FutuConnectionRecovery:
    """Handles OpenD connection recovery and state restoration"""
    
    def __init__(self, api_client: FutuApiClient):
        self.api_client = api_client
        self.recovery_in_progress = False
        
    def handle_connection_loss(self):
        """Handle OpenD connection loss with automatic recovery"""
        if self.recovery_in_progress:
            return
            
        self.recovery_in_progress = True
        self.api_client.adapter.write_log("OpenD connection lost, starting recovery...")
        
        try:
            # Step 1: Close existing contexts
            self._close_contexts()
            
            # Step 2: Wait for OpenD to stabilize
            time.sleep(5)
            
            # Step 3: Attempt reconnection
            max_attempts = 5
            for attempt in range(max_attempts):
                if self._attempt_reconnection():
                    break
                    
                delay = 2 ** attempt  # Exponential backoff
                self.api_client.adapter.write_log(f"Reconnection attempt {attempt + 1} failed, retrying in {delay}s")
                time.sleep(delay)
            else:
                raise ConnectionError("Max reconnection attempts exceeded")
            
            # Step 4: Restore state
            self._restore_state()
            
            self.api_client.adapter.write_log("OpenD connection recovery completed")
            
        except Exception as e:
            self.api_client.adapter.write_log(f"Connection recovery failed: {e}")
        finally:
            self.recovery_in_progress = False
    
    def _attempt_reconnection(self) -> bool:
        """Attempt to reconnect to OpenD"""
        try:
            # Re-initialize contexts
            settings = self.api_client.last_settings
            return self.api_client.connect(settings)
        except Exception as e:
            self.api_client.adapter.write_log(f"Reconnection attempt failed: {e}")
            return False
    
    def _restore_state(self):
        """Restore subscriptions and synchronize state after reconnection"""
        try:
            # Restore market data subscriptions
            if self.api_client.market_data:
                self.api_client.market_data.restore_subscriptions()
            
            # Query current order states
            if self.api_client.order_manager:
                self.api_client.order_manager.sync_order_states()
            
            # Refresh account and position data
            if self.api_client.account_manager:
                self.api_client.account_manager.query_account()
                self.api_client.account_manager.query_position()
                
        except Exception as e:
            self.api_client.adapter.write_log(f"State restoration failed: {e}")
```

#### Files Created/Modified
- `foxtrot/adapter/futu/error_handling.py` - Error classification and recovery
- All manager files - Enhanced with error handling and recovery

---

### Phase 8: Testing and Validation (Week 10)
**Priority**: Highest - Quality assurance  
**Dependencies**: All phases

#### Deliverables
- [ ] **Comprehensive Unit Tests**: >90% coverage for all managers
- [ ] **SDK Mock Strategy**: Mock futu SDK components for consistent testing
- [ ] **Integration Tests**: Full MainEngine and EventEngine integration
- [ ] **Performance Benchmarks**: Latency and throughput validation
- [ ] **Thread Safety Tests**: Concurrent operation validation
- [ ] **End-to-End Tests**: Real OpenD gateway testing

#### Success Criteria
- >90% test coverage across all adapter components
- All performance benchmarks met with adjusted targets
- Thread safety validated under concurrent load
- Integration with MainEngine and EventEngine verified
- End-to-end functionality confirmed with OpenD

#### Key Testing Implementation
```python  
# tests/adapter/futu/test_futu_adapter.py
class TestFutuAdapter:
    @pytest.fixture
    def mock_futu_sdk(self):
        """Mock futu SDK components"""
        with patch("futu.OpenQuoteContext") as mock_quote, \
             patch("futu.OpenSecTradeContext") as mock_trade:
            
            # Configure mock responses
            mock_quote.return_value.get_global_state.return_value = (RET_OK, {})
            mock_trade.return_value.unlock_trade.return_value = (RET_OK, {})
            
            yield mock_quote, mock_trade
    
    def test_adapter_initialization(self, event_engine):
        """Test adapter can be initialized and registered"""
        adapter = FutuAdapter(event_engine, "FUTU")
        assert adapter.adapter_name == "FUTU"
        assert adapter.default_name == "FUTU"
        assert len(adapter.exchanges) > 0
    
    def test_connection_success(self, mock_futu_sdk, event_engine):
        """Test successful OpenD connection"""
        adapter = FutuAdapter(event_engine, "FUTU")
        
        settings = {
            "Host": "127.0.0.1",
            "Port": 11111,
            "RSA Key File": "test_key.txt",
            "Trading Password": "test123"
        }
        
        # Mock successful connection
        mock_futu_sdk[0].return_value.get_global_state.return_value = (RET_OK, {})
        
        adapter.connect(settings)
        assert adapter.connected is True

# Performance test with adjusted targets
class TestFutuPerformance:
    def test_market_data_latency(self, futu_adapter):
        """Test market data processing latency < 100ms"""
        start_time = time.time()
        
        # Simulate market data callback
        quote_data = {"code": "00700", "last_price": 500.0}
        futu_adapter.api_client.quote_handler._convert_to_tick_data(quote_data)
        
        latency = (time.time() - start_time) * 1000
        assert latency < 100  # Adjusted target for gateway overhead
    
    def test_order_placement_latency(self, futu_adapter):
        """Test order placement latency < 200ms"""
        order_req = OrderRequest(
            symbol="0700",
            exchange=Exchange.SEHK,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=500.0
        )
        
        start_time = time.time()
        futu_adapter.send_order(order_req)
        latency = (time.time() - start_time) * 1000
        
        assert latency < 200  # Adjusted target for SDK + gateway overhead
```

#### Files Created/Modified
- `tests/adapter/futu/` - Complete test suite
- CI/CD configuration updates for futu SDK dependency

---

## 4. Integration Strategy - Enhanced

### 4.1 Event System Integration

**Enhanced Event Types Integration:**
Based on investigation findings, integrate with recently added event types:

```python
# Use enhanced event system discovered in investigation
from foxtrot.util.event_type import (
    EVENT_ORDER_CANCEL,
    EVENT_ORDER_CANCEL_ALL, 
    EVENT_ACCOUNT_REQUEST,
    EVENT_POSITION_REQUEST
)

class FutuAdapter(BaseAdapter):
    def cancel_order(self, req: CancelRequest) -> None:
        """Enhanced with cancel event support"""
        success = self.api_client.order_manager.cancel_order(req)
        if success:
            # Fire enhanced cancel event
            self.on_event(EVENT_ORDER_CANCEL, req)
    
    def query_account(self) -> None:
        """Enhanced with request event tracking"""
        # Fire request event for tracking
        self.on_event(EVENT_ACCOUNT_REQUEST, AccountRequest(adapter_name=self.adapter_name))
        
        # Execute query
        self.api_client.account_manager.query_account()
```

### 4.2 TUI Integration Readiness

**Based on investigation findings about TUI capabilities:**

```python
class FutuAdapter(BaseAdapter):
    """TUI-ready adapter with validation framework integration"""
    
    def validate_order(self, req: OrderRequest) -> tuple[bool, str]:
        """Order validation for TUI framework"""
        # Market-specific validation
        market, code = convert_symbol_to_futu_market(req.vt_symbol)
        
        # Validate market hours
        if not self._is_market_open(market):
            return False, f"{market} market is closed"
        
        # Validate order size
        min_size = self._get_min_order_size(market, code)
        if req.volume < min_size:
            return False, f"Minimum order size is {min_size}"
        
        return True, "Order validation passed"
    
    def get_trading_status(self) -> dict:
        """Trading status for TUI monitoring"""
        return {
            "connected": self.connected,
            "opend_status": self.api_client.get_opend_status(),
            "markets_open": self._get_market_status(),
            "active_orders": len(self.api_client.order_manager._orders),
            "subscriptions": len(self.api_client.market_data.subscriptions),
        }
```

### 4.3 Multi-Adapter Compatibility

**Ensure compatibility with existing adapters:**

```python
# MainEngine registration - no special handling needed
main_engine = MainEngine()
futu_adapter = main_engine.add_adapter(FutuAdapter, "FUTU")
binance_adapter = main_engine.add_adapter(BinanceAdapter, "BINANCE")
ib_adapter = main_engine.add_adapter(IbAdapter, "IB")

# Cross-adapter portfolio consolidation works automatically via OMS
total_positions = main_engine.get_all_positions()  # Includes Futu positions
```

---

## 5. Risk Assessment - Updated

### 5.1 Technical Risks (Refined)

#### OpenD Gateway Dependency
- **Risk**: OpenD gateway failure or instability affects all operations
- **Impact**: High - Complete adapter failure  
- **Probability**: Medium - Additional infrastructure complexity
- **Mitigation**: Robust OpenD health monitoring and automatic restart procedures
- **Contingency**: Detailed OpenD troubleshooting and recovery documentation

#### SDK Version Compatibility  
- **Risk**: Futu SDK updates breaking adapter functionality
- **Impact**: Medium - Adapter breaks on SDK updates
- **Probability**: Low - Official SDK typically maintains backward compatibility
- **Mitigation**: Pin SDK version and test updates in staging environment
- **Monitoring**: Track Futu SDK release notes and deprecation notices

#### Multi-Market Symbol Mapping
- **Risk**: Complex symbol mapping between markets and VT format
- **Impact**: Medium - Incorrect symbol routing or data corruption
- **Probability**: Medium - Multiple mapping edge cases
- **Mitigation**: Comprehensive symbol mapping tests and validation
- **Contingency**: Symbol mapping correction and data consistency checks

### 5.2 Performance Risks (Adjusted)

#### Gateway Latency Overhead
- **Risk**: OpenD gateway adds latency to all operations  
- **Impact**: Medium - Reduced trading performance
- **Expected**: 50-100ms additional latency vs direct API
- **Mitigation**: Optimize SDK usage and implement efficient caching
- **Monitoring**: Continuous latency measurement and alerting

#### Memory Usage with SDK
- **Risk**: SDK and gateway consume significant memory
- **Impact**: Medium - Increased resource requirements
- **Expected**: 50-100MB additional memory usage
- **Mitigation**: Efficient context management and proper cleanup
- **Monitoring**: Resource usage tracking and leak detection

### 5.3 Operational Risks (Updated)

#### RSA Key Management
- **Risk**: RSA key corruption or loss affecting authentication
- **Impact**: High - Unable to connect to Futu services
- **Probability**: Low - But critical when occurs
- **Mitigation**: Secure key backup and rotation procedures
- **Recovery**: Key regeneration and deployment procedures

#### Multi-Market Regulatory Compliance
- **Risk**: Different regulatory requirements across HK/US/CN markets
- **Impact**: High - Legal compliance issues
- **Probability**: Medium - Complex regulatory landscape
- **Mitigation**: Thorough research and compliance verification
- **Requirements**: 
  - Hong Kong SFC compliance for HK market access
  - US regulatory compliance for US market access
  - China CSRC compliance for A-shares access

---

## 6. Success Criteria and Validation - Enhanced

### 6.1 Performance Benchmarks (Adjusted for Architecture)

| Metric | Target | Adjusted Target | Measurement Method |
|--------|---------|-----------------|-------------------|
| Market Data Latency | <50ms | <100ms | OpenD gateway overhead |
| Order Latency | <100ms | <200ms | SDK + gateway processing |
| Connection Recovery | <30s | <60s | OpenD restart time |
| Memory Usage | <100MB | <150MB | SDK overhead included |
| Thread Count | 2-4 threads | 2-4 threads | Callback-driven model |
| Subscription Capacity | >200 symbols | >200 symbols | SDK limitation research needed |
| Order Throughput | >100 orders/min | >100 orders/min | Maintained target |

### 6.2 Integration Validation

#### BaseAdapter Compliance
- [ ] All abstract methods implemented according to contract
- [ ] Thread safety verified with concurrent operation tests
- [ ] Data immutability enforced for all VT objects passed to callbacks
- [ ] Event system integration with dual-level event firing
- [ ] Automatic reconnection with state preservation

#### OMS Integration
- [ ] Order state synchronization through events
- [ ] Position tracking across all markets
- [ ] Account balance consolidation
- [ ] Contract information properly loaded and accessible

#### EventEngine Integration  
- [ ] All events properly fired through EventEngine
- [ ] Error isolation - handler failures don't crash adapter
- [ ] General and symbol-specific event distribution
- [ ] Enhanced event types (ORDER_CANCEL, etc.) supported

### 6.3 Quality Gates (Enhanced)

#### Architecture Compliance
- [ ] Follows established adapter patterns (manager delegation, facade)
- [ ] Proper use of existing VT data objects and conventions
- [ ] Integration with existing exchanges rather than creating new ones
- [ ] Callback-driven threading model properly implemented

#### Production Readiness
- [ ] Comprehensive error handling and recovery
- [ ] Robust connection management with health monitoring
- [ ] Performance optimized for real-time trading
- [ ] Security best practices for RSA key management
- [ ] Comprehensive logging and monitoring integration

---

## 7. Implementation Timeline - Refined

### 7.1 Adjusted Timeline (10-12 weeks)

**Week 1**: Foundation + OpenD Setup  
**Week 2**: Authentication + Context Management  
**Weeks 3-4**: Market Data Subscriptions  
**Weeks 5-6**: Order Management + Execution  
**Week 7**: Account + Position Management  
**Week 8**: Historical Data + Contracts  
**Week 9**: Error Handling + Resilience  
**Week 10**: Testing + Validation  
**Weeks 11-12**: Performance Optimization + Documentation (if needed)

### 7.2 Critical Dependencies

#### Phase Dependencies
- Phase 2 (Authentication) blocks all subsequent phases
- Phase 3 (Market Data) recommended before Phase 4 (Orders) for testing
- Phase 7 (Error Handling) should start after Phase 4 completion
- Phase 8 (Testing) requires all previous phases partially complete

#### External Dependencies
- OpenD gateway installation and setup
- Futu account setup with appropriate market permissions
- RSA key generation and configuration
- Test market data and paper trading access

---

## 8. Next Steps and Immediate Actions

### 8.1 Week 1 Immediate Actions

1. **Environment Setup** (Priority: Critical)
   - [ ] Install futu-api Python SDK
   - [ ] Set up Futu paper trading account
   - [ ] Install and configure OpenD gateway
   - [ ] Generate RSA keys for authentication
   - [ ] Test basic SDK connection

2. **Development Branch Setup**
   - [ ] Create feature branch: `feature/futu-adapter-refined`
   - [ ] Set up development environment with SDK
   - [ ] Configure IDE with futu SDK documentation

3. **Architecture Validation**  
   - [ ] Validate SDK callback architecture
   - [ ] Test OpenD gateway stability
   - [ ] Verify multi-market access permissions
   - [ ] Document any architecture adjustments needed

### 8.2 Success Metrics

#### Development Metrics
- Phase completion within refined timeframes
- Code quality maintained (>90% test coverage)
- Performance benchmarks achieved (adjusted targets)
- Zero critical security vulnerabilities

#### Business Metrics
- Successful integration with existing Foxtrot platform
- Support for HK, US, and CN markets as permitted
- Production-ready stability and reliability
- Maintainable codebase with comprehensive documentation

---

## Conclusion

This refined implementation plan provides a comprehensive, accurate roadmap for developing a production-ready Futu trading adapter for the Foxtrot platform. The plan incorporates critical findings from codebase investigation, system flow analysis, and official Futu API documentation.

**Key Refinements Made:**
1. **Architecture Corrected**: OpenD gateway pattern with official SDK integration
2. **Authentication Updated**: RSA key-based instead of API key/secret  
3. **Threading Model**: Callback-driven (IB pattern) based on SDK characteristics
4. **VT Symbol Strategy**: Use existing exchanges instead of creating Futu-specific ones
5. **Performance Targets**: Adjusted for gateway overhead while maintaining trading viability
6. **Integration Strategy**: Leverages existing patterns and enhanced event system
7. **Timeline Optimized**: Reduced to 10-12 weeks with SDK advantages

**Critical Success Factors:**
1. **Thorough OpenD Gateway Management**: Understanding and managing the local gateway
2. **SDK Integration Mastery**: Leveraging official SDK effectively  
3. **Multi-Market Symbol Mapping**: Accurate conversion between VT and Futu formats
4. **Callback Processing Efficiency**: High-performance real-time data processing
5. **Error Recovery Robustness**: Maintaining stability under various failure scenarios

The refined plan provides a realistic, implementable pathway to extend the Foxtrot platform to Asian markets while maintaining the platform's architectural integrity and performance standards.

---

*Refined Implementation Plan Created: 2025-01-31*  
*Based on: Investigation Report, Flow Analysis, Official Futu API Documentation*  
*Next Review: After Phase 1 completion*