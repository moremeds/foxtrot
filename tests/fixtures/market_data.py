"""Realistic market data fixtures for testing.

Current market conditions (as of 2025):
- BTC: $112,000
- ETH: $3,800  
- BNB: $750
- EUR/USD: 1.0850
- SPY: $520
"""

from datetime import datetime, timedelta
from decimal import Decimal

from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import (
    AccountData,
    BarData,
    OrderData,
    PositionData,
    TickData,
    TradeData,
)


class MarketDataFixtures:
    """Provides realistic market data for testing."""

    # Current realistic prices (2025 market conditions)
    PRICES = {
        "BTC": 112000.0,
        "ETH": 3800.0,
        "BNB": 750.0,
        "SOL": 180.0,
        "ADA": 1.15,
        "DOT": 8.50,
        "LINK": 25.50,
        "EUR": 1.0850,  # EUR/USD
        "GBP": 1.2750,  # GBP/USD
        "JPY": 148.50,  # USD/JPY
        "SPY": 520.0,   # S&P 500 ETF
        "QQQ": 450.0,   # Nasdaq ETF
        "AAPL": 195.0,
        "GOOGL": 150.0,
        "MSFT": 425.0,
        "TSLA": 380.0,
    }

    # Realistic spreads (in basis points)
    SPREADS_BPS = {
        "BTC": 5,    # 0.05%
        "ETH": 5,
        "EUR": 2,    # 0.02% for major forex
        "SPY": 1,    # 0.01% for liquid ETFs
        "AAPL": 2,
    }

    # Realistic volumes (24h volume in units)
    VOLUMES_24H = {
        "BTC": 25000,
        "ETH": 150000,
        "EUR": 5000000,
        "SPY": 85000000,
    }

    @classmethod
    def get_tick_data(cls, symbol: str, exchange: Exchange = Exchange.BINANCE, 
                      timestamp: datetime = None) -> TickData:
        """Generate realistic tick data for a symbol."""
        if timestamp is None:
            timestamp = datetime.now()

        base_price = cls.PRICES.get(symbol, 100.0)
        spread_bps = cls.SPREADS_BPS.get(symbol, 10)
        spread = base_price * spread_bps / 10000

        # Add some realistic market noise (±0.1%)
        import random
        noise = base_price * random.uniform(-0.001, 0.001)
        last_price = base_price + noise

        return TickData(
            adapter_name="TEST",
            symbol=symbol,
            exchange=exchange,
            datetime=timestamp,
            name=symbol,
            volume=float(cls.VOLUMES_24H.get(symbol, 10000)),
            open_price=base_price * 0.995,  # -0.5% from base
            high_price=base_price * 1.002,  # +0.2% from base
            low_price=base_price * 0.994,   # -0.6% from base
            last_price=last_price,
            last_volume=random.uniform(0.01, 2.0) if symbol == "BTC" else random.uniform(1, 100),
            bid_price_1=last_price - spread/2,
            bid_volume_1=random.uniform(0.1, 5.0) if symbol == "BTC" else random.uniform(10, 500),
            ask_price_1=last_price + spread/2,
            ask_volume_1=random.uniform(0.1, 5.0) if symbol == "BTC" else random.uniform(10, 500),
            # Level 2 data
            bid_price_2=last_price - spread,
            bid_volume_2=random.uniform(0.2, 10.0) if symbol == "BTC" else random.uniform(20, 1000),
            ask_price_2=last_price + spread,
            ask_volume_2=random.uniform(0.2, 10.0) if symbol == "BTC" else random.uniform(20, 1000),
            # Level 3 data
            bid_price_3=last_price - spread * 1.5,
            bid_volume_3=random.uniform(0.5, 20.0) if symbol == "BTC" else random.uniform(50, 2000),
            ask_price_3=last_price + spread * 1.5,
            ask_volume_3=random.uniform(0.5, 20.0) if symbol == "BTC" else random.uniform(50, 2000),
        )

    @classmethod
    def get_bar_data(cls, symbol: str, exchange: Exchange = Exchange.BINANCE,
                     interval: int = 60, count: int = 100, 
                     end_time: datetime = None) -> list[BarData]:
        """Generate realistic OHLCV bar data."""
        if end_time is None:
            end_time = datetime.now()

        bars = []
        base_price = cls.PRICES.get(symbol, 100.0)
        
        # Generate bars backwards from end_time
        for i in range(count - 1, -1, -1):
            timestamp = end_time - timedelta(minutes=interval * i)
            
            # Add trending and volatility
            trend = 0.0001 * (count - i)  # Slight upward trend
            volatility = 0.002 if symbol in ["BTC", "ETH"] else 0.001
            
            # Random walk for realistic price movement
            import random
            change = random.normalvariate(trend, volatility)
            
            open_price = base_price * (1 + change)
            high_price = open_price * (1 + abs(random.normalvariate(0, volatility/2)))
            low_price = open_price * (1 - abs(random.normalvariate(0, volatility/2)))
            close_price = random.uniform(low_price, high_price)
            
            # Realistic volume patterns (higher during active hours)
            hour = timestamp.hour
            volume_multiplier = 1.5 if 9 <= hour <= 16 else 0.7  # Market hours
            base_volume = cls.VOLUMES_24H.get(symbol, 10000) / (24 * 60 / interval)
            volume = base_volume * volume_multiplier * random.uniform(0.5, 1.5)
            
            bars.append(BarData(
                adapter_name="TEST",
                symbol=symbol,
                exchange=exchange,
                datetime=timestamp,
                interval=interval,
                volume=volume,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
            ))
            
            # Update base price for next bar
            base_price = close_price

        return bars

    @classmethod
    def get_order_data(cls, symbol: str, order_type: OrderType = OrderType.LIMIT,
                       direction: Direction = Direction.LONG, volume: float = None,
                       price: float = None, status: Status = Status.NOTTRADED,
                       exchange: Exchange = Exchange.BINANCE) -> OrderData:
        """Generate realistic order data."""
        base_price = cls.PRICES.get(symbol, 100.0)
        
        if price is None:
            if order_type == OrderType.LIMIT:
                # Limit orders slightly off market
                if direction == Direction.LONG:
                    price = base_price * 0.998  # Buy 0.2% below market
                else:
                    price = base_price * 1.002  # Sell 0.2% above market
            else:
                price = base_price  # Market orders at current price

        if volume is None:
            # Realistic order sizes
            if symbol == "BTC":
                volume = random.uniform(0.01, 0.5)
            elif symbol in ["ETH", "BNB"]:
                volume = random.uniform(0.1, 5.0)
            elif symbol in ["EUR", "GBP"]:
                volume = random.uniform(1000, 100000)
            else:
                volume = random.uniform(1, 100)

        import time
        # Use time + random to ensure unique order IDs
        orderid = str(int(time.time() * 1000000 + random.randint(0, 9999)) % 1000000)

        return OrderData(
            adapter_name="TEST",
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            type=order_type,
            direction=direction,
            volume=volume,
            price=price,
            traded=0.0 if status == Status.NOTTRADED else volume * random.uniform(0.1, 1.0),
            status=status,
            datetime=datetime.now(),
        )

    @classmethod
    def get_trade_data(cls, order: OrderData, trade_price: float = None,
                       trade_volume: float = None) -> TradeData:
        """Generate realistic trade data from an order."""
        if trade_price is None:
            # Realistic slippage
            slippage = 0.0001 if order.symbol in ["EUR", "SPY"] else 0.0005
            if order.direction == Direction.LONG:
                trade_price = order.price * (1 + slippage)
            else:
                trade_price = order.price * (1 - slippage)

        if trade_volume is None:
            trade_volume = order.volume

        import time
        tradeid = str(int(time.time() * 1000) % 1000000)

        return TradeData(
            adapter_name=order.adapter_name,
            symbol=order.symbol,
            exchange=order.exchange,
            orderid=order.orderid,
            tradeid=tradeid,
            direction=order.direction,
            volume=trade_volume,
            price=trade_price,
            datetime=datetime.now(),
        )

    @classmethod
    def get_position_data(cls, symbol: str, volume: float = None,
                          exchange: Exchange = Exchange.BINANCE) -> PositionData:
        """Generate realistic position data."""
        base_price = cls.PRICES.get(symbol, 100.0)
        
        if volume is None:
            # Realistic position sizes
            if symbol == "BTC":
                volume = random.uniform(0.1, 2.0)
            elif symbol in ["ETH", "BNB"]:
                volume = random.uniform(1, 20)
            else:
                volume = random.uniform(10, 1000)

        # Simulate some P&L
        entry_price = base_price * random.uniform(0.98, 1.02)
        pnl = (base_price - entry_price) * volume

        return PositionData(
            adapter_name="TEST",
            symbol=symbol,
            exchange=exchange,
            direction=Direction.LONG if volume > 0 else Direction.SHORT,
            volume=abs(volume),
            price=entry_price,
            pnl=pnl,
        )

    @classmethod
    def get_account_data(cls, currency: str = "USD", 
                         balance: float = 100000.0) -> AccountData:
        """Generate realistic account data."""
        # Simulate some positions taking up margin
        frozen = balance * random.uniform(0.1, 0.3)
        
        return AccountData(
            adapter_name="TEST",
            accountid=f"TEST-{currency}",
            balance=balance,
            frozen=frozen,
        )


# Import commonly used fixtures at module level
import random