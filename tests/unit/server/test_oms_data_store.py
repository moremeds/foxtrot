"""
Unit tests for OmsDataStore.
"""

from datetime import datetime
import pytest

from foxtrot.server.oms_data_store import OmsDataStore
from foxtrot.util.constants import Exchange, Product, Direction, OrderType, Status, Offset
from foxtrot.util.object import (
    AccountData,
    ContractData,
    OrderData,
    PositionData,
    QuoteData,
    TickData,
    TradeData,
)


@pytest.fixture
def data_store():
    """Create OmsDataStore instance."""
    return OmsDataStore()


@pytest.fixture
def sample_tick():
    """Create sample tick data."""
    return TickData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        name="Test Symbol",
        datetime=datetime.now(),
        last_price=100.0,
        volume=1000,
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_order():
    """Create sample order data."""
    return OrderData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        orderid="ORDER_001",
        type=OrderType.LIMIT,
        direction=Direction.LONG,
        offset=Offset.NONE,
        price=100.0,
        volume=10,
        traded=0,
        status=Status.NOTTRADED,
        datetime=datetime.now(),
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_trade():
    """Create sample trade data."""
    return TradeData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        orderid="ORDER_001",
        tradeid="TRADE_001",
        direction=Direction.LONG,
        offset=Offset.NONE,
        price=100.0,
        volume=10,
        datetime=datetime.now(),
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_position():
    """Create sample position data."""
    return PositionData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        direction=Direction.LONG,
        volume=100,
        frozen=0,
        price=100.0,
        pnl=0.0,
        yd_volume=0,
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_account():
    """Create sample account data."""
    return AccountData(
        accountid="ACC_001",
        balance=10000.0,
        frozen=0.0,
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_contract():
    """Create sample contract data."""
    return ContractData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        name="Test Contract",
        product=Product.EQUITY,
        size=1,
        pricetick=0.01,
        adapter_name="TEST_ADAPTER"
    )


@pytest.fixture
def sample_quote():
    """Create sample quote data."""
    return QuoteData(
        symbol="TEST",
        exchange=Exchange.LOCAL,
        quoteid="QUOTE_001",
        bid_price=99.5,
        bid_volume=100,
        ask_price=100.5,
        ask_volume=100,
        bid_offset=Offset.NONE,
        ask_offset=Offset.NONE,
        status=Status.NOTTRADED,
        datetime=datetime.now(),
        adapter_name="TEST_ADAPTER"
    )


class TestOmsDataStore:
    """Test OmsDataStore functionality."""

    def test_init(self, data_store):
        """Test OmsDataStore initialization."""
        assert data_store.ticks == {}
        assert data_store.orders == {}
        assert data_store.trades == {}
        assert data_store.positions == {}
        assert data_store.accounts == {}
        assert data_store.contracts == {}
        assert data_store.quotes == {}
        assert data_store.active_orders == {}
        assert data_store.active_quotes == {}

    def test_tick_operations(self, data_store, sample_tick):
        """Test tick data operations."""
        # Store tick
        data_store.ticks[sample_tick.vt_symbol] = sample_tick
        
        # Get tick
        tick = data_store.get_tick(sample_tick.vt_symbol)
        assert tick == sample_tick
        
        # Get nonexistent tick
        tick = data_store.get_tick("NONEXISTENT")
        assert tick is None
        
        # Get all ticks
        ticks = data_store.get_all_ticks()
        assert len(ticks) == 1
        assert ticks[0] == sample_tick

    def test_order_operations(self, data_store, sample_order):
        """Test order data operations."""
        # Store order
        data_store.orders[sample_order.vt_orderid] = sample_order
        
        # Get order
        order = data_store.get_order(sample_order.vt_orderid)
        assert order == sample_order
        
        # Get nonexistent order
        order = data_store.get_order("NONEXISTENT")
        assert order is None
        
        # Get all orders
        orders = data_store.get_all_orders()
        assert len(orders) == 1
        assert orders[0] == sample_order

    def test_trade_operations(self, data_store, sample_trade):
        """Test trade data operations."""
        # Store trade
        data_store.trades[sample_trade.vt_tradeid] = sample_trade
        
        # Get trade
        trade = data_store.get_trade(sample_trade.vt_tradeid)
        assert trade == sample_trade
        
        # Get nonexistent trade
        trade = data_store.get_trade("NONEXISTENT")
        assert trade is None
        
        # Get all trades
        trades = data_store.get_all_trades()
        assert len(trades) == 1
        assert trades[0] == sample_trade

    def test_position_operations(self, data_store, sample_position):
        """Test position data operations."""
        # Store position
        data_store.positions[sample_position.vt_positionid] = sample_position
        
        # Get position
        position = data_store.get_position(sample_position.vt_positionid)
        assert position == sample_position
        
        # Get nonexistent position
        position = data_store.get_position("NONEXISTENT")
        assert position is None
        
        # Get all positions
        positions = data_store.get_all_positions()
        assert len(positions) == 1
        assert positions[0] == sample_position

    def test_account_operations(self, data_store, sample_account):
        """Test account data operations."""
        # Store account
        data_store.accounts[sample_account.vt_accountid] = sample_account
        
        # Get account
        account = data_store.get_account(sample_account.vt_accountid)
        assert account == sample_account
        
        # Get nonexistent account
        account = data_store.get_account("NONEXISTENT")
        assert account is None
        
        # Get all accounts
        accounts = data_store.get_all_accounts()
        assert len(accounts) == 1
        assert accounts[0] == sample_account

    def test_contract_operations(self, data_store, sample_contract):
        """Test contract data operations."""
        # Store contract
        data_store.contracts[sample_contract.vt_symbol] = sample_contract
        
        # Get contract
        contract = data_store.get_contract(sample_contract.vt_symbol)
        assert contract == sample_contract
        
        # Get nonexistent contract
        contract = data_store.get_contract("NONEXISTENT")
        assert contract is None
        
        # Get all contracts
        contracts = data_store.get_all_contracts()
        assert len(contracts) == 1
        assert contracts[0] == sample_contract

    def test_quote_operations(self, data_store, sample_quote):
        """Test quote data operations."""
        # Store quote
        data_store.quotes[sample_quote.vt_quoteid] = sample_quote
        
        # Get quote
        quote = data_store.get_quote(sample_quote.vt_quoteid)
        assert quote == sample_quote
        
        # Get nonexistent quote
        quote = data_store.get_quote("NONEXISTENT")
        assert quote is None
        
        # Get all quotes
        quotes = data_store.get_all_quotes()
        assert len(quotes) == 1
        assert quotes[0] == sample_quote

    def test_active_orders(self, data_store, sample_order):
        """Test active orders tracking."""
        # Add active order
        data_store.active_orders[sample_order.vt_orderid] = sample_order
        
        # Get all active orders
        active_orders = data_store.get_all_active_orders()
        assert len(active_orders) == 1
        assert active_orders[0] == sample_order
        
        # Remove from active orders
        del data_store.active_orders[sample_order.vt_orderid]
        active_orders = data_store.get_all_active_orders()
        assert len(active_orders) == 0

    def test_active_quotes(self, data_store, sample_quote):
        """Test active quotes tracking."""
        # Add active quote
        data_store.active_quotes[sample_quote.vt_quoteid] = sample_quote
        
        # Get all active quotes
        active_quotes = data_store.get_all_active_quotes()
        assert len(active_quotes) == 1
        assert active_quotes[0] == sample_quote
        
        # Remove from active quotes
        del data_store.active_quotes[sample_quote.vt_quoteid]
        active_quotes = data_store.get_all_active_quotes()
        assert len(active_quotes) == 0

    def test_multiple_items(self, data_store):
        """Test storing multiple items of different types."""
        # Create multiple items
        tick1 = TickData(symbol="TEST1", exchange=Exchange.LOCAL, name="Test1", 
                        datetime=datetime.now(), adapter_name="TEST")
        tick2 = TickData(symbol="TEST2", exchange=Exchange.LOCAL, name="Test2",
                        datetime=datetime.now(), adapter_name="TEST")
        
        order1 = OrderData(symbol="TEST1", exchange=Exchange.LOCAL, orderid="ORD1",
                          type=OrderType.LIMIT, direction=Direction.LONG,
                          offset=Offset.NONE, price=100, volume=10,
                          status=Status.NOTTRADED, datetime=datetime.now(),
                          adapter_name="TEST")
        order2 = OrderData(symbol="TEST2", exchange=Exchange.LOCAL, orderid="ORD2",
                          type=OrderType.LIMIT, direction=Direction.SHORT,
                          offset=Offset.NONE, price=100, volume=10,
                          status=Status.NOTTRADED, datetime=datetime.now(),
                          adapter_name="TEST")
        
        # Store items
        data_store.ticks[tick1.vt_symbol] = tick1
        data_store.ticks[tick2.vt_symbol] = tick2
        data_store.orders[order1.vt_orderid] = order1
        data_store.orders[order2.vt_orderid] = order2
        
        # Verify storage
        assert len(data_store.get_all_ticks()) == 2
        assert len(data_store.get_all_orders()) == 2