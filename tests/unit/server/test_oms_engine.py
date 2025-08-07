"""
Unit tests for OmsEngine.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.oms_engine import OmsEngine
from foxtrot.util.converter import OffsetConverter
from foxtrot.util.event_type import (
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_QUOTE,
    EVENT_TICK,
    EVENT_TRADE,
)
from foxtrot.util.constants import Exchange, Direction, OrderType, Status, Offset
from foxtrot.util.object import (
    AccountData,
    ContractData,
    OrderData,
    OrderRequest,
    PositionData,
    QuoteData,
    TickData,
    TradeData,
)


@pytest.fixture
def event_engine():
    """Create mock event engine."""
    return MagicMock(spec=EventEngine)


@pytest.fixture
def main_engine():
    """Create mock main engine."""
    return MagicMock()


@pytest.fixture
def oms_engine(main_engine, event_engine):
    """Create OmsEngine instance."""
    return OmsEngine(main_engine, event_engine)


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


class TestOmsEngine:
    """Test OmsEngine functionality."""

    def test_init(self, oms_engine, event_engine):
        """Test OmsEngine initialization."""
        assert oms_engine.engine_name == "oms"
        assert oms_engine.data_store is not None
        assert oms_engine.offset_converters == {}
        
        # Verify event registration
        event_engine.register.assert_any_call(EVENT_TICK, oms_engine.process_tick_event)
        event_engine.register.assert_any_call(EVENT_ORDER, oms_engine.process_order_event)
        event_engine.register.assert_any_call(EVENT_TRADE, oms_engine.process_trade_event)
        event_engine.register.assert_any_call(EVENT_POSITION, oms_engine.process_position_event)
        event_engine.register.assert_any_call(EVENT_ACCOUNT, oms_engine.process_account_event)
        event_engine.register.assert_any_call(EVENT_CONTRACT, oms_engine.process_contract_event)
        event_engine.register.assert_any_call(EVENT_QUOTE, oms_engine.process_quote_event)

    def test_backward_compatibility_attributes(self, oms_engine):
        """Test that backward compatibility attributes are exposed."""
        assert hasattr(oms_engine, 'ticks')
        assert hasattr(oms_engine, 'orders')
        assert hasattr(oms_engine, 'trades')
        assert hasattr(oms_engine, 'positions')
        assert hasattr(oms_engine, 'accounts')
        assert hasattr(oms_engine, 'contracts')
        assert hasattr(oms_engine, 'quotes')
        assert hasattr(oms_engine, 'active_orders')
        assert hasattr(oms_engine, 'active_quotes')

    def test_process_tick_event(self, oms_engine, sample_tick):
        """Test processing tick event."""
        event = Event(EVENT_TICK, sample_tick)
        oms_engine.process_tick_event(event)
        
        assert oms_engine.data_store.ticks[sample_tick.vt_symbol] == sample_tick
        assert oms_engine.get_tick(sample_tick.vt_symbol) == sample_tick

    def test_process_order_event_active(self, oms_engine, sample_order):
        """Test processing active order event."""
        sample_order.status = Status.NOTTRADED  # Active status
        event = Event(EVENT_ORDER, sample_order)
        
        # Mock offset converter
        mock_converter = MagicMock(spec=OffsetConverter)
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        oms_engine.process_order_event(event)
        
        # Verify order stored
        assert oms_engine.data_store.orders[sample_order.vt_orderid] == sample_order
        assert oms_engine.data_store.active_orders[sample_order.vt_orderid] == sample_order
        
        # Verify converter updated
        mock_converter.update_order.assert_called_once_with(sample_order)

    def test_process_order_event_inactive(self, oms_engine, sample_order):
        """Test processing inactive order event."""
        # First add to active orders
        sample_order.status = Status.NOTTRADED
        oms_engine.data_store.active_orders[sample_order.vt_orderid] = sample_order
        
        # Now process as filled
        sample_order.status = Status.ALLTRADED
        event = Event(EVENT_ORDER, sample_order)
        oms_engine.process_order_event(event)
        
        # Verify order stored but removed from active
        assert oms_engine.data_store.orders[sample_order.vt_orderid] == sample_order
        assert sample_order.vt_orderid not in oms_engine.data_store.active_orders

    def test_process_trade_event(self, oms_engine, sample_trade):
        """Test processing trade event."""
        event = Event(EVENT_TRADE, sample_trade)
        
        # Mock offset converter
        mock_converter = MagicMock(spec=OffsetConverter)
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        oms_engine.process_trade_event(event)
        
        # Verify trade stored
        assert oms_engine.data_store.trades[sample_trade.vt_tradeid] == sample_trade
        
        # Verify converter updated
        mock_converter.update_trade.assert_called_once_with(sample_trade)

    def test_process_position_event(self, oms_engine, sample_position):
        """Test processing position event."""
        event = Event(EVENT_POSITION, sample_position)
        
        # Mock offset converter
        mock_converter = MagicMock(spec=OffsetConverter)
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        oms_engine.process_position_event(event)
        
        # Verify position stored
        assert oms_engine.data_store.positions[sample_position.vt_positionid] == sample_position
        
        # Verify converter updated
        mock_converter.update_position.assert_called_once_with(sample_position)

    def test_process_account_event(self, oms_engine, sample_account):
        """Test processing account event."""
        event = Event(EVENT_ACCOUNT, sample_account)
        oms_engine.process_account_event(event)
        
        assert oms_engine.data_store.accounts[sample_account.vt_accountid] == sample_account

    def test_process_contract_event(self, oms_engine, sample_contract):
        """Test processing contract event."""
        event = Event(EVENT_CONTRACT, sample_contract)
        
        with patch('foxtrot.server.oms_engine.OffsetConverter') as MockConverter:
            mock_converter_instance = MagicMock()
            MockConverter.return_value = mock_converter_instance
            
            oms_engine.process_contract_event(event)
            
            # Verify contract stored
            assert oms_engine.data_store.contracts[sample_contract.vt_symbol] == sample_contract
            
            # Verify converter created for new adapter
            assert "TEST_ADAPTER" in oms_engine.offset_converters
            MockConverter.assert_called_once_with(oms_engine)

    def test_process_quote_event_active(self, oms_engine, sample_quote):
        """Test processing active quote event."""
        sample_quote.status = Status.NOTTRADED  # Active status
        event = Event(EVENT_QUOTE, sample_quote)
        
        oms_engine.process_quote_event(event)
        
        # Verify quote stored
        assert oms_engine.data_store.quotes[sample_quote.vt_quoteid] == sample_quote
        assert oms_engine.data_store.active_quotes[sample_quote.vt_quoteid] == sample_quote

    def test_process_quote_event_inactive(self, oms_engine, sample_quote):
        """Test processing inactive quote event."""
        # First add to active quotes
        sample_quote.status = Status.NOTTRADED
        oms_engine.data_store.active_quotes[sample_quote.vt_quoteid] = sample_quote
        
        # Now process as cancelled
        sample_quote.status = Status.CANCELLED
        event = Event(EVENT_QUOTE, sample_quote)
        oms_engine.process_quote_event(event)
        
        # Verify quote stored but removed from active
        assert oms_engine.data_store.quotes[sample_quote.vt_quoteid] == sample_quote
        assert sample_quote.vt_quoteid not in oms_engine.data_store.active_quotes

    def test_delegated_get_methods(self, oms_engine, sample_tick, sample_order):
        """Test that get methods delegate to data store."""
        # Store some data
        oms_engine.data_store.ticks[sample_tick.vt_symbol] = sample_tick
        oms_engine.data_store.orders[sample_order.vt_orderid] = sample_order
        
        # Test delegation
        assert oms_engine.get_tick(sample_tick.vt_symbol) == sample_tick
        assert oms_engine.get_order(sample_order.vt_orderid) == sample_order
        assert oms_engine.get_all_ticks() == [sample_tick]
        assert oms_engine.get_all_orders() == [sample_order]

    def test_update_order_request(self, oms_engine):
        """Test updating order request to converter."""
        req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        
        mock_converter = MagicMock(spec=OffsetConverter)
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        oms_engine.update_order_request(req, "ORDER_001", "TEST_ADAPTER")
        
        mock_converter.update_order_request.assert_called_once_with(req, "ORDER_001")

    def test_convert_order_request_with_converter(self, oms_engine):
        """Test converting order request with converter."""
        req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        
        mock_converter = MagicMock(spec=OffsetConverter)
        mock_converter.convert_order_request.return_value = [req]
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        result = oms_engine.convert_order_request(req, "TEST_ADAPTER", lock=True, net=False)
        
        mock_converter.convert_order_request.assert_called_once_with(req, True, False)
        assert result == [req]

    def test_convert_order_request_without_converter(self, oms_engine):
        """Test converting order request without converter."""
        req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        
        result = oms_engine.convert_order_request(req, "NONEXISTENT", lock=True)
        assert result == [req]

    def test_get_converter(self, oms_engine):
        """Test getting offset converter."""
        mock_converter = MagicMock(spec=OffsetConverter)
        oms_engine.offset_converters["TEST_ADAPTER"] = mock_converter
        
        result = oms_engine.get_converter("TEST_ADAPTER")
        assert result == mock_converter
        
        result = oms_engine.get_converter("NONEXISTENT")
        assert result is None