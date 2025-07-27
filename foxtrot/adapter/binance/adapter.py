"""
Binance adapter implementation using CCXT library.
"""

from decimal import Decimal
from datetime import datetime
from typing import Any, Dict

import ccxt

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.engine import EventEngine
from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import (
    AccountData,
    BarData,
    CancelRequest,
    HistoryRequest,
    OrderData,
    OrderRequest,
    PositionData,
    SubscribeRequest,
    TradeData,
)


class BinanceAdapter(BaseAdapter):
    """
    Binance trading adapter using CCXT library.
    
    This adapter provides a drop-in replacement interface for Binance
    while maintaining compatibility with the existing foxtrot framework.
    """

    default_name: str = "BINANCE"

    default_setting: dict[str, str | int | bool] = {
        "API Key": "",
        "Secret": "",
        "Sandbox": False,
        "Proxy Host": "",
        "Proxy Port": 0,
    }

    exchanges: list[Exchange] = [Exchange.BINANCE]

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize the Binance adapter."""
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)

        self.ccxt_exchange: ccxt.binance | None = None
        self.api_key: str = ""
        self.secret: str = ""
        self.sandbox: bool = False
        self.connected: bool = False
        
        # Order tracking
        self.order_count: int = 0

    # Data transformation mappings
    STATUS_CCXT2VT: Dict[str, Status] = {
        "open": Status.NOTTRADED,
        "closed": Status.ALLTRADED,
        "canceled": Status.CANCELLED,
        "cancelled": Status.CANCELLED,
        "rejected": Status.REJECTED,
        "expired": Status.CANCELLED,
    }

    STATUS_VT2CCXT: Dict[Status, str] = {
        Status.SUBMITTING: "open",
        Status.NOTTRADED: "open", 
        Status.PARTTRADED: "open",
        Status.ALLTRADED: "closed",
        Status.CANCELLED: "canceled",
        Status.REJECTED: "rejected",
    }

    ORDERTYPE_VT2CCXT: Dict[OrderType, str] = {
        OrderType.LIMIT: "limit",
        OrderType.MARKET: "market",
    }

    ORDERTYPE_CCXT2VT: Dict[str, OrderType] = {
        "limit": OrderType.LIMIT,
        "market": OrderType.MARKET,
    }

    DIRECTION_VT2CCXT: Dict[Direction, str] = {
        Direction.LONG: "buy",
        Direction.SHORT: "sell",
    }

    DIRECTION_CCXT2VT: Dict[str, Direction] = {
        "buy": Direction.LONG,
        "sell": Direction.SHORT,
    }

    def connect(self, setting: dict[str, str | int | float | bool]) -> None:
        """
        Connect to Binance API.
        
        Implementation requirements from BaseAdapter:
        - Connect to server if necessary
        - Log connected if all necessary connection is established
        - Query and respond with on_xxxx callbacks:
          * contracts: on_contract
          * account asset: on_account
          * account holding: on_position
          * orders of account: on_order
          * trades of account: on_trade
        - If any query fails, write log
        """
        try:
            # Extract settings
            self.api_key = str(setting["API Key"])
            self.secret = str(setting["Secret"])
            self.sandbox = bool(setting["Sandbox"])
            proxy_host = str(setting.get("Proxy Host", ""))
            proxy_port = int(setting.get("Proxy Port", 0))

            # Initialize CCXT exchange
            self._init_ccxt(self.api_key, self.secret, self.sandbox, proxy_host, proxy_port)
            
            if not self.ccxt_exchange:
                self.write_log("Failed to initialize CCXT exchange")
                return

            # Test connection with authenticated call
            self.write_log("Connecting to Binance...")
            balance = self.ccxt_exchange.fetch_balance()
            
            if balance:
                self.connected = True
                self.write_log("Binance connection established")
                
                # Query initial state and emit events
                self._query_initial_state()
            else:
                self.write_log("Failed to authenticate with Binance")
                
        except ccxt.AuthenticationError as e:
            self.write_log(f"Binance authentication failed: {e}")
        except ccxt.NetworkError as e:
            self.write_log(f"Binance network error: {e}")
        except Exception as e:
            self.write_log(f"Binance connection error: {e}")

    def close(self) -> None:
        """Close adapter connection."""
        if self.ccxt_exchange:
            try:
                # Set connected to False to stop WebSocket loops
                self.connected = False
                
                # Close WebSocket connections if they exist
                if hasattr(self.ccxt_exchange, 'close'):
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is running, schedule the close
                            asyncio.ensure_future(self.ccxt_exchange.close())
                        else:
                            # If no loop is running, run synchronously
                            asyncio.run(self.ccxt_exchange.close())
                    except Exception as ws_error:
                        self.write_log(f"Error closing WebSocket: {ws_error}")
                
                self.ccxt_exchange = None
                self.write_log("Binance connection closed")
            except Exception as e:
                self.write_log(f"Error closing Binance connection: {e}")

    def subscribe(self, req: SubscribeRequest) -> None:
        """Subscribe tick data update."""
        if not self.ccxt_exchange or not self.connected:
            self.write_log("Not connected to Binance")
            return

        try:
            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.vt_symbol)
            
            # Check if CCXT exchange supports WebSocket streaming
            if not hasattr(self.ccxt_exchange, 'watch_ticker'):
                self.write_log("WebSocket streaming not supported by CCXT exchange")
                return
            
            # Start WebSocket subscription in a separate thread
            import threading
            
            def websocket_worker():
                import asyncio
                asyncio.run(self._websocket_loop(ccxt_symbol, req))
            
            thread = threading.Thread(target=websocket_worker, daemon=True)
            thread.start()
            
            self.write_log(f"Subscribed to {req.vt_symbol} tick data")
            
        except Exception as e:
            self.write_log(f"Failed to subscribe to {req.vt_symbol}: {e}")

    async def _websocket_loop(self, ccxt_symbol: str, req: SubscribeRequest) -> None:
        """WebSocket event loop for real-time data."""
        try:
            while self.connected:
                try:
                    # Watch ticker data
                    ticker = await self.ccxt_exchange.watch_ticker(ccxt_symbol)
                    
                    if ticker:
                        # Convert ticker to TickData
                        tick = self._convert_ccxt_ticker_to_tick_data(ticker, req)
                        self.on_tick(tick)
                        
                except Exception as e:
                    self.write_log(f"WebSocket ticker error: {e}")
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            self.write_log(f"WebSocket loop error: {e}")

    def _convert_ccxt_ticker_to_tick_data(self, ticker: dict, req: SubscribeRequest) -> 'TickData':
        """Convert CCXT ticker data to TickData object."""
        from foxtrot.util.object import TickData
        
        return TickData(
            adapter_name=self.adapter_name,
            symbol=req.symbol,
            exchange=Exchange.BINANCE,
            datetime=datetime.fromtimestamp(ticker['timestamp'] / 1000) if ticker.get('timestamp') else datetime.now(),
            name=req.symbol,
            volume=float(ticker.get('baseVolume', 0)) if ticker.get('baseVolume') else 0.0,
            open_price=float(ticker.get('open', 0)) if ticker.get('open') else 0.0,
            high_price=float(ticker.get('high', 0)) if ticker.get('high') else 0.0,
            low_price=float(ticker.get('low', 0)) if ticker.get('low') else 0.0,
            last_price=float(ticker.get('last', 0)) if ticker.get('last') else 0.0,
            last_volume=float(ticker.get('baseVolume', 0)) if ticker.get('baseVolume') else 0.0,
            ask_price_1=float(ticker.get('ask', 0)) if ticker.get('ask') else 0.0,
            ask_volume_1=0.0,  # Not available in ticker
            bid_price_1=float(ticker.get('bid', 0)) if ticker.get('bid') else 0.0,
            bid_volume_1=0.0,  # Not available in ticker
        )

    def send_order(self, req: OrderRequest) -> str:
        """
        Send a new order to server.
        
        Implementation requirements from BaseAdapter:
        - Create OrderData from req using OrderRequest.create_order_data
        - Assign unique adapter-scoped id to OrderData.orderid
        - Send request to server
          * If sent: OrderData.status = Status.SUBMITTING
          * If failed: OrderData.status = Status.REJECTED
        - Response on_order
        - Return vt_orderid
        
        Returns:
            str: vt_orderid for created OrderData
        """
        if not self.ccxt_exchange or not self.connected:
            self.write_log("Not connected to Binance")
            return ""

        # Generate unique order ID
        self.order_count += 1
        orderid = str(self.order_count)
        
        # Create OrderData from request
        order = req.create_order_data(orderid, self.adapter_name)
        order.datetime = datetime.now()
        
        try:
            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.vt_symbol)
            
            # Convert order parameters
            ccxt_side = self.DIRECTION_VT2CCXT[req.direction]
            ccxt_type = self.ORDERTYPE_VT2CCXT[req.type]
            
            # Prepare order parameters
            params = {}
            if req.type == OrderType.LIMIT:
                # Limit order requires price
                result = self.ccxt_exchange.create_order(
                    symbol=ccxt_symbol,
                    type=ccxt_type,
                    side=ccxt_side,
                    amount=req.volume,
                    price=req.price,
                    params=params
                )
            else:
                # Market order
                result = self.ccxt_exchange.create_order(
                    symbol=ccxt_symbol,
                    type=ccxt_type,
                    side=ccxt_side,
                    amount=req.volume,
                    params=params
                )
            
            # Update order with exchange order ID and status
            if result and result.get("id"):
                order.orderid = str(result["id"])
                order.status = Status.SUBMITTING
                self.write_log(f"Order sent successfully: {order.vt_orderid}")
            else:
                order.status = Status.REJECTED
                self.write_log(f"Order failed: No order ID returned")
            
        except ccxt.InsufficientFunds as e:
            order.status = Status.REJECTED
            self.write_log(f"Order rejected - insufficient funds: {e}")
        except ccxt.InvalidOrder as e:
            order.status = Status.REJECTED
            self.write_log(f"Order rejected - invalid order: {e}")
        except Exception as e:
            order.status = Status.REJECTED
            self.write_log(f"Order failed: {e}")
        
        # Emit order event
        self.on_order(order)
        return order.vt_orderid

    def cancel_order(self, req: CancelRequest) -> None:
        """
        Cancel an existing order.
        
        Implementation requirements from BaseAdapter:
        - Send cancel request to server
        """
        if not self.ccxt_exchange or not self.connected:
            self.write_log("Not connected to Binance")
            return

        try:
            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.vt_symbol)
            
            # Cancel the order using CCXT
            result = self.ccxt_exchange.cancel_order(
                id=req.orderid,
                symbol=ccxt_symbol
            )
            
            if result:
                self.write_log(f"Order cancelled successfully: {req.vt_orderid}")
                
                # Create updated OrderData with cancelled status
                order = OrderData(
                    adapter_name=self.adapter_name,
                    symbol=req.symbol,
                    exchange=Exchange.BINANCE,
                    orderid=req.orderid,
                    type=OrderType.LIMIT,  # Will be updated when we query order details
                    direction=Direction.LONG,  # Will be updated when we query order details  
                    volume=0.0,  # Will be updated when we query order details
                    price=0.0,  # Will be updated when we query order details
                    traded=0.0,
                    status=Status.CANCELLED,
                    datetime=datetime.now(),
                )
                
                # Emit order event
                self.on_order(order)
            else:
                self.write_log(f"Failed to cancel order: {req.vt_orderid}")
                
        except ccxt.OrderNotFound as e:
            self.write_log(f"Order not found for cancellation: {req.vt_orderid} - {e}")
        except ccxt.InvalidOrder as e:
            self.write_log(f"Invalid order for cancellation: {req.vt_orderid} - {e}")
        except Exception as e:
            self.write_log(f"Failed to cancel order {req.vt_orderid}: {e}")

    def query_account(self) -> None:
        """Query account balance."""
        if not self.ccxt_exchange or not self.connected:
            self.write_log("Not connected to Binance")
            return
            
        try:
            balance_data = self.ccxt_exchange.fetch_balance()
            
            # Convert CCXT balance data to foxtrot AccountData objects
            for currency, balance_info in balance_data.items():
                if currency in ["free", "used", "total"]:
                    continue  # Skip summary fields
                    
                if isinstance(balance_info, dict) and balance_info.get("total", 0) > 0:
                    account = AccountData(
                        adapter_name=self.adapter_name,
                        accountid=currency,
                        balance=float(balance_info["total"]),
                        frozen=float(balance_info["used"]),
                    )
                    self.on_account(account)
                    
        except Exception as e:
            self.write_log(f"Failed to query account: {e}")

    def query_position(self) -> None:
        """Query holding positions."""
        raise NotImplementedError("query_position method not implemented")

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """Query bar history data."""
        if not self.ccxt_exchange or not self.connected:
            self.write_log("Not connected to Binance")
            return []

        try:
            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.vt_symbol)
            
            # Convert interval to CCXT timeframe
            timeframe = self._convert_interval_to_ccxt_timeframe(req.interval)
            
            # Calculate limit - CCXT fetchOHLCV uses limit parameter
            # Default to 500 if not specified, max 1000 for Binance
            limit = getattr(req, 'limit', 500)
            limit = min(limit, 1000)  # Binance API limit
            
            # Fetch OHLCV data
            ohlcv_data = self.ccxt_exchange.fetch_ohlcv(
                symbol=ccxt_symbol,
                timeframe=timeframe,
                since=int(req.start.timestamp() * 1000) if req.start else None,
                limit=limit
            )
            
            # Convert to BarData objects
            bars = []
            for ohlcv in ohlcv_data:
                # OHLCV format: [timestamp, open, high, low, close, volume]
                if len(ohlcv) >= 6:
                    bar = BarData(
                        adapter_name=self.adapter_name,
                        symbol=req.symbol,
                        exchange=Exchange.BINANCE,
                        datetime=datetime.fromtimestamp(ohlcv[0] / 1000),
                        interval=req.interval,
                        volume=float(ohlcv[5]),
                        open_price=float(ohlcv[1]),
                        high_price=float(ohlcv[2]),
                        low_price=float(ohlcv[3]),
                        close_price=float(ohlcv[4]),
                    )
                    bars.append(bar)
            
            self.write_log(f"Retrieved {len(bars)} bars for {req.vt_symbol}")
            return bars
            
        except Exception as e:
            self.write_log(f"Failed to query history for {req.vt_symbol}: {e}")
            return []

    def _convert_interval_to_ccxt_timeframe(self, interval: int) -> str:
        """Convert foxtrot interval (minutes) to CCXT timeframe string."""
        # Map common intervals to CCXT timeframe strings
        interval_map = {
            1: '1m',
            3: '3m', 
            5: '5m',
            15: '15m',
            30: '30m',
            60: '1h',
            120: '2h',
            240: '4h',
            360: '6h',
            480: '8h',
            720: '12h',
            1440: '1d',
            4320: '3d',
            10080: '1w',
            43200: '1M',  # 1 month (30 days)
        }
        
        return interval_map.get(interval, '1h')  # Default to 1 hour

    def _init_ccxt(self, api_key: str, secret: str, sandbox: bool = False, proxy_host: str = "", proxy_port: int = 0) -> None:
        """Initialize CCXT Binance exchange instance."""
        try:
            # Create exchange configuration
            config = {
                'apiKey': api_key,
                'secret': secret,
                'timeout': 30000,
                'enableRateLimit': True,
                'verbose': False,
            }
            
            # Add proxy configuration if provided
            if proxy_host and proxy_port:
                config['proxies'] = {
                    'http': f'http://{proxy_host}:{proxy_port}',
                    'https': f'https://{proxy_host}:{proxy_port}',
                }
            
            # Initialize CCXT exchange
            self.ccxt_exchange = ccxt.binance(config)
            
            # Set sandbox mode if requested
            if sandbox:
                self.ccxt_exchange.sandbox = True
                self.write_log("Binance adapter initialized in sandbox mode")
            else:
                self.write_log("Binance adapter initialized in live mode")
                
        except Exception as e:
            self.write_log(f"Failed to initialize CCXT exchange: {e}")
            self.ccxt_exchange = None

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """Convert foxtrot vt_symbol to CCXT symbol format."""
        # vt_symbol format: "BTC.BINANCE" -> CCXT format: "BTC/USDT"
        # For now, assume USDT as default quote currency
        # In a full implementation, this would need proper symbol mapping
        symbol = vt_symbol.split('.')[0]
        
        # Handle common cryptocurrency pairs
        if symbol in ['BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'LINK']:
            return f"{symbol}/USDT"
        else:
            # Default fallback - this should be configurable in production
            return f"{symbol}/USDT"

    def _convert_symbol_from_ccxt(self, ccxt_symbol: str) -> str:
        """Convert CCXT symbol to foxtrot vt_symbol format."""
        # CCXT format: "BTC/USDT" -> vt_symbol format: "BTC.BINANCE"
        symbol = ccxt_symbol.split('/')[0]
        return f"{symbol}.{Exchange.BINANCE.value}"

    def _query_initial_state(self) -> None:
        """Query initial state after connection and emit events."""
        try:
            # Query account balance
            self.query_account()
            
            # Query open orders
            self._query_open_orders()
            
            # Query recent trades
            self._query_recent_trades()
            
            # Start order update WebSocket if supported
            self._start_order_updates()
            
            self.write_log("Initial state queried successfully")
            
        except Exception as e:
            self.write_log(f"Failed to query initial state: {e}")

    def _start_order_updates(self) -> None:
        """Start WebSocket subscription for order updates."""
        try:
            # Check if CCXT exchange supports order watching
            if not hasattr(self.ccxt_exchange, 'watch_orders'):
                self.write_log("Order watching not supported by CCXT exchange")
                return
            
            # Start order watching in a separate thread
            import threading
            
            def order_watcher():
                import asyncio
                asyncio.run(self._order_update_loop())
            
            thread = threading.Thread(target=order_watcher, daemon=True)
            thread.start()
            
            self.write_log("Started order update WebSocket")
            
        except Exception as e:
            self.write_log(f"Failed to start order updates: {e}")

    async def _order_update_loop(self) -> None:
        """WebSocket event loop for order updates."""
        try:
            while self.connected:
                try:
                    # Watch order updates
                    orders = await self.ccxt_exchange.watch_orders()
                    
                    if orders:
                        for ccxt_order in orders:
                            order = self._convert_ccxt_order_to_order_data(ccxt_order)
                            self.on_order(order)
                        
                except Exception as e:
                    self.write_log(f"WebSocket order error: {e}")
                    await asyncio.sleep(1)  # Wait before retry
                    
        except Exception as e:
            self.write_log(f"Order update loop error: {e}")

    def _query_open_orders(self) -> None:
        """Query and emit open orders."""
        if not self.ccxt_exchange or not self.connected:
            return
            
        try:
            open_orders = self.ccxt_exchange.fetch_open_orders()
            
            for ccxt_order in open_orders:
                order = self._convert_ccxt_order_to_order_data(ccxt_order)
                self.on_order(order)
                
        except Exception as e:
            self.write_log(f"Failed to query open orders: {e}")

    def _query_recent_trades(self) -> None:
        """Query and emit recent trades."""
        if not self.ccxt_exchange or not self.connected:
            return
            
        try:
            my_trades = self.ccxt_exchange.fetch_my_trades()
            
            for ccxt_trade in my_trades[-10:]:  # Last 10 trades
                trade = self._convert_ccxt_trade_to_trade_data(ccxt_trade)
                self.on_trade(trade)
                
        except Exception as e:
            self.write_log(f"Failed to query recent trades: {e}")

    def _convert_ccxt_order_to_order_data(self, ccxt_order: dict) -> OrderData:
        """Convert CCXT order data to OrderData object."""
        return OrderData(
            adapter_name=self.adapter_name,
            symbol=ccxt_order['symbol'].split('/')[0],
            exchange=Exchange.BINANCE,
            orderid=str(ccxt_order['id']),
            type=self.ORDERTYPE_CCXT2VT.get(ccxt_order['type'], OrderType.LIMIT),
            direction=self.DIRECTION_CCXT2VT.get(ccxt_order['side'], Direction.LONG),
            volume=float(ccxt_order['amount']),
            price=float(ccxt_order['price']) if ccxt_order['price'] else 0.0,
            traded=float(ccxt_order['filled']),
            status=self.STATUS_CCXT2VT.get(ccxt_order['status'], Status.NOTTRADED),
            datetime=datetime.fromtimestamp(ccxt_order['timestamp'] / 1000) if ccxt_order['timestamp'] else datetime.now(),
        )

    def _convert_ccxt_trade_to_trade_data(self, ccxt_trade: dict) -> TradeData:
        """Convert CCXT trade data to TradeData object."""
        return TradeData(
            adapter_name=self.adapter_name,
            symbol=ccxt_trade['symbol'].split('/')[0],
            exchange=Exchange.BINANCE,
            orderid=str(ccxt_trade['order']),
            tradeid=str(ccxt_trade['id']),
            direction=self.DIRECTION_CCXT2VT.get(ccxt_trade['side'], Direction.LONG),
            volume=float(ccxt_trade['amount']),
            price=float(ccxt_trade['price']),
            datetime=datetime.fromtimestamp(ccxt_trade['timestamp'] / 1000) if ccxt_trade['timestamp'] else datetime.now(),
        )