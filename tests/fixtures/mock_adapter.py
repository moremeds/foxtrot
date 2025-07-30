"""Mock adapter for testing with realistic broker behavior."""

from datetime import datetime
import random
import threading
import time

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import (
    AccountData,
    BarData,
    CancelRequest,
    ContractData,
    HistoryRequest,
    OrderData,
    OrderRequest,
    PositionData,
    SubscribeRequest,
    TradeData,
)

from .market_data import MarketDataFixtures


class MockAdapter(BaseAdapter):
    """Mock adapter that simulates realistic broker behavior."""

    default_name: str = "MOCK"

    default_setting: dict[str, str | int | bool] = {
        "Account ID": "TEST123",
        "Initial Balance": 100000,
        "Latency MS": 50,  # Simulate network latency
        "Fill Rate": 0.95,  # 95% of orders get filled
        "Partial Fill Rate": 0.2,  # 20% of fills are partial
    }

    exchanges: list[Exchange] = [Exchange.BINANCE, Exchange.SMART, Exchange.IDEALPRO]

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize mock adapter."""
        super().__init__(event_engine, adapter_name)

        self.connected = False
        self.account_id = ""
        self.balance = 100000.0
        self.latency_ms = 50
        self.fill_rate = 0.95
        self.partial_fill_rate = 0.2

        # Track orders and positions
        self.orders: dict[str, OrderData] = {}
        self.positions: dict[str, PositionData] = {}
        self.order_counter = 0

        # Market simulation
        self.subscribed_symbols: set[str] = set()
        self.market_thread: threading.Thread | None = None
        self.stop_market = threading.Event()

    def connect(self, setting: dict) -> None:
        """Simulate broker connection."""
        self.account_id = str(setting.get("Account ID", "TEST123"))
        self.balance = float(setting.get("Initial Balance", 100000))
        self.latency_ms = int(setting.get("Latency MS", 50))
        self.fill_rate = float(setting.get("Fill Rate", 0.95))
        self.partial_fill_rate = float(setting.get("Partial Fill Rate", 0.2))

        # Simulate connection delay
        self.write_log(f"Connecting to {self.default_name}...")
        time.sleep(self.latency_ms / 1000)

        self.connected = True
        self.write_log(f"Connected to {self.default_name}")

        # Send initial account data
        account = AccountData(
            adapter_name=self.adapter_name,
            accountid=self.account_id,
            balance=self.balance,
            frozen=0.0,
        )
        self.on_account(account)

        # Send some test contracts
        self._send_test_contracts()

        # Start market simulation
        self.stop_market.clear()
        self.market_thread = threading.Thread(target=self._market_simulation, daemon=True)
        self.market_thread.start()

    def close(self) -> None:
        """Close mock connection."""
        if self.connected:
            self.connected = False
            self.stop_market.set()
            if self.market_thread:
                self.market_thread.join(timeout=1)
            self.write_log(f"Disconnected from {self.default_name}")

    def subscribe(self, req: SubscribeRequest) -> None:
        """Subscribe to market data."""
        if not self.connected:
            self.write_log("Not connected")
            return

        symbol = req.symbol
        self.subscribed_symbols.add(symbol)
        self.write_log(f"Subscribed to {symbol}")

        # Send initial tick
        tick = MarketDataFixtures.get_tick_data(symbol, req.exchange)
        tick.adapter_name = self.adapter_name
        self.on_tick(tick)

    def send_order(self, req: OrderRequest) -> str:
        """Simulate order sending."""
        if not self.connected:
            self.write_log("Not connected")
            return ""

        # Generate order ID
        self.order_counter += 1
        orderid = f"MOCK{self.order_counter:06d}"

        # Create order
        order = req.create_order_data(orderid, self.adapter_name)
        order.datetime = datetime.now()
        order.status = Status.SUBMITTING

        # Store order
        self.orders[order.vt_orderid] = order

        # Send order event
        self.on_order(order)

        # Simulate async order processing
        threading.Thread(target=self._process_order, args=(order,), daemon=True).start()

        return order.vt_orderid

    def cancel_order(self, req: CancelRequest) -> None:
        """Simulate order cancellation."""
        if not self.connected:
            self.write_log("Not connected")
            return

        # Construct vt_orderid from request
        vt_orderid = f"{self.adapter_name}.{req.orderid}"

        order = self.orders.get(vt_orderid)
        if not order:
            self.write_log(f"Order {vt_orderid} not found")
            return

        if order.status in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
            self.write_log(f"Order {vt_orderid} already finished")
            return

        # Simulate cancellation
        threading.Thread(target=self._process_cancel, args=(order,), daemon=True).start()

    def query_account(self) -> None:
        """Query account data."""
        if not self.connected:
            return

        # Calculate frozen amount from open orders
        frozen = 0.0
        for order in self.orders.values():
            if order.status in [Status.SUBMITTING, Status.NOTTRADED, Status.PARTTRADED]:
                if order.direction == Direction.LONG:
                    frozen += order.price * (order.volume - order.traded)

        account = AccountData(
            adapter_name=self.adapter_name,
            accountid=self.account_id,
            balance=self.balance,
            frozen=frozen,
        )
        self.on_account(account)

    def query_position(self) -> None:
        """Query positions."""
        if not self.connected:
            return

        for position in self.positions.values():
            self.on_position(position)

    def query_history(self, req: HistoryRequest) -> list[BarData]:
        """Query historical data."""
        if not self.connected:
            return []

        # Simulate latency
        time.sleep(self.latency_ms / 1000)

        # Generate realistic bar data
        bars = MarketDataFixtures.get_bar_data(
            symbol=req.symbol,
            exchange=req.exchange,
            interval=req.interval,
            count=100,
            end_time=req.end,
        )

        # Update adapter name
        for bar in bars:
            bar.adapter_name = self.adapter_name

        return bars

    def _send_test_contracts(self) -> None:
        """Send test contract data."""
        test_contracts = [
            ("BTC", Exchange.BINANCE, "Bitcoin/USDT"),
            ("ETH", Exchange.BINANCE, "Ethereum/USDT"),
            ("EUR", Exchange.IDEALPRO, "EUR.USD"),
            ("SPY", Exchange.SMART, "SPDR S&P 500 ETF"),
        ]

        for symbol, exchange, name in test_contracts:
            contract = ContractData(
                adapter_name=self.adapter_name,
                symbol=symbol,
                exchange=exchange,
                name=name,
                product="SPOT",
                size=1,
                pricetick=0.01 if symbol in ["BTC", "ETH"] else 0.0001,
                min_volume=0.001 if symbol == "BTC" else 0.01,
            )
            self.on_contract(contract)

    def _market_simulation(self) -> None:
        """Simulate market data updates."""
        while not self.stop_market.is_set():
            try:
                # Update subscribed symbols
                for symbol in self.subscribed_symbols:
                    if self.stop_market.is_set():
                        break

                    # Generate tick with some randomness
                    tick = MarketDataFixtures.get_tick_data(symbol)
                    tick.adapter_name = self.adapter_name
                    self.on_tick(tick)

                # Market updates every 100-500ms
                sleep_time = random.uniform(0.1, 0.5)
                self.stop_market.wait(sleep_time)

            except Exception as e:
                self.write_log(f"Market simulation error: {e}")

    def _process_order(self, order: OrderData) -> None:
        """Simulate order processing with realistic behavior."""
        # Initial latency
        time.sleep(self.latency_ms / 1000)

        # Update to NOTTRADED
        order.status = Status.NOTTRADED
        self.on_order(order)

        # Simulate rejection for some orders
        if random.random() > 0.98:  # 2% rejection rate
            time.sleep(self.latency_ms / 1000)
            order.status = Status.REJECTED
            self.on_order(order)
            return

        # Simulate order fills based on fill rate
        if random.random() > self.fill_rate:
            # Order doesn't fill
            return

        # Determine fill behavior
        is_partial = random.random() < self.partial_fill_rate

        if order.type == OrderType.MARKET:
            # Market orders fill immediately
            self._fill_order(order, partial=is_partial)
        else:
            # Limit orders fill with some delay
            fill_delay = random.uniform(0.5, 5.0)
            time.sleep(fill_delay)

            # Check if order was cancelled
            if order.status == Status.CANCELLED:
                return

            self._fill_order(order, partial=is_partial)

    def _fill_order(self, order: OrderData, partial: bool = False) -> None:
        """Simulate order fill."""
        base_price = MarketDataFixtures.PRICES.get(order.symbol, 100.0)

        # Calculate fill price with slippage
        if order.type == OrderType.MARKET:
            slippage = random.uniform(0.0001, 0.0005)
            if order.direction == Direction.LONG:
                fill_price = base_price * (1 + slippage)
            else:
                fill_price = base_price * (1 - slippage)
        else:
            # Limit orders fill at order price
            fill_price = order.price

        # Determine fill volume
        if partial:
            fill_volume = order.volume * random.uniform(0.2, 0.8)
            order.traded = fill_volume
            order.status = Status.PARTTRADED
        else:
            fill_volume = order.volume
            order.traded = order.volume
            order.status = Status.ALLTRADED

        # Send order update
        self.on_order(order)

        # Create trade
        trade = TradeData(
            adapter_name=self.adapter_name,
            symbol=order.symbol,
            exchange=order.exchange,
            orderid=order.orderid,
            tradeid=f"T{order.orderid}",
            direction=order.direction,
            volume=fill_volume,
            price=fill_price,
            datetime=datetime.now(),
        )
        self.on_trade(trade)

        # Update position
        self._update_position(trade)

    def _process_cancel(self, order: OrderData) -> None:
        """Process order cancellation."""
        # Simulate latency
        time.sleep(self.latency_ms / 1000)

        # Check if order can be cancelled
        if order.status in [Status.NOTTRADED, Status.PARTTRADED]:
            order.status = Status.CANCELLED
            self.on_order(order)
            self.write_log(f"Order {order.vt_orderid} cancelled")
        else:
            self.write_log(f"Order {order.vt_orderid} cannot be cancelled")

    def _update_position(self, trade: TradeData) -> None:
        """Update position based on trade."""
        position = self.positions.get(trade.vt_symbol)

        if not position:
            position = PositionData(
                adapter_name=self.adapter_name,
                symbol=trade.symbol,
                exchange=trade.exchange,
                direction=trade.direction,
                volume=0.0,
                price=0.0,
                pnl=0.0,
            )
            self.positions[trade.vt_symbol] = position

        # Update position
        if trade.direction == position.direction:
            # Adding to position
            total_cost = position.price * position.volume + trade.price * trade.volume
            position.volume += trade.volume
            position.price = total_cost / position.volume if position.volume > 0 else 0
        else:
            # Reducing position
            position.volume -= trade.volume
            if position.volume < 0:
                # Position flipped
                position.direction = trade.direction
                position.volume = abs(position.volume)
                position.price = trade.price
            elif position.volume == 0:
                # Position closed
                del self.positions[trade.vt_symbol]
                return

        # Calculate PnL
        current_price = MarketDataFixtures.PRICES.get(trade.symbol, 100.0)
        if position.direction == Direction.LONG:
            position.pnl = (current_price - position.price) * position.volume
        else:
            position.pnl = (position.price - current_price) * position.volume

        self.on_position(position)
