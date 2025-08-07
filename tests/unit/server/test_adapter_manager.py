"""
Unit tests for AdapterManager.
"""

from unittest.mock import MagicMock, patch
import pytest

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.adapter_manager import AdapterManager
from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.util.constants import Exchange, Product, OrderType, Direction, Offset
from foxtrot.util.object import (
    SubscribeRequest,
    OrderRequest,
    CancelRequest,
    QuoteRequest,
    HistoryRequest,
)


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""

    def __init__(self, event_engine, adapter_name):
        super().__init__(event_engine, adapter_name)
        self.connected = False
        self.default_setting = {"host": "localhost", "port": 8080}
        self.exchanges = [Exchange.LOCAL]

    def connect(self, setting):
        self.connected = True

    def close(self):
        self.connected = False

    def subscribe(self, req):
        pass

    def send_order(self, req):
        return "TEST_ORDER_ID"

    def cancel_order(self, req):
        pass

    def send_quote(self, req):
        return "TEST_QUOTE_ID"

    def cancel_quote(self, req):
        pass

    def query_account(self):
        pass

    def query_position(self):
        pass

    def query_history(self, req):
        return []

    def process_timer_event(self, event):
        pass


@pytest.fixture
def event_engine():
    """Create mock event engine."""
    return MagicMock(spec=EventEngine)


@pytest.fixture
def write_log():
    """Create mock write_log function."""
    return MagicMock()


@pytest.fixture
def adapter_manager(event_engine, write_log):
    """Create AdapterManager instance."""
    return AdapterManager(event_engine, write_log)


class TestAdapterManager:
    """Test AdapterManager functionality."""

    def test_init(self, adapter_manager):
        """Test AdapterManager initialization."""
        assert adapter_manager.adapters == {}
        assert adapter_manager.exchanges == []

    def test_add_adapter(self, adapter_manager):
        """Test adding an adapter."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        
        assert "TEST" in adapter_manager.adapters
        assert adapter_manager.adapters["TEST"] == adapter
        assert adapter.adapter_name == "TEST"
        assert Exchange.LOCAL in adapter_manager.exchanges

    def test_add_duplicate_adapter(self, adapter_manager, write_log):
        """Test adding duplicate adapter."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        
        # Should log error and return existing adapter
        write_log.assert_called_with("Adapter TEST already exists.", source="MAIN")
        assert adapter == adapter_manager.adapters["TEST"]

    def test_get_adapter(self, adapter_manager):
        """Test getting adapter by name."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        
        result = adapter_manager.get_adapter("TEST")
        assert result == adapter
        
        result = adapter_manager.get_adapter("NONEXISTENT")
        assert result is None

    def test_get_default_setting(self, adapter_manager):
        """Test getting default settings."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        
        settings = adapter_manager.get_default_setting("TEST")
        assert settings == {"host": "localhost", "port": 8080}
        
        settings = adapter_manager.get_default_setting("NONEXISTENT")
        assert settings is None

    def test_get_all_gateway_names(self, adapter_manager):
        """Test getting all gateway names."""
        adapter_manager.add_adapter(MockAdapter, "TEST1")
        adapter_manager.add_adapter(MockAdapter, "TEST2")
        
        names = adapter_manager.get_all_gateway_names()
        assert set(names) == {"TEST1", "TEST2"}

    def test_get_all_exchanges(self, adapter_manager):
        """Test getting all exchanges."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        
        exchanges = adapter_manager.get_all_exchanges()
        assert Exchange.LOCAL in exchanges

    def test_connect(self, adapter_manager):
        """Test connecting to an adapter."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        settings = {"host": "testhost", "port": 9090}
        
        adapter_manager.connect(settings, "TEST")
        assert adapter.connected is True

    def test_connect_nonexistent(self, adapter_manager, write_log):
        """Test connecting to nonexistent adapter."""
        adapter_manager.connect({}, "NONEXISTENT")
        write_log.assert_called_with("Adapter NONEXISTENT not found.", source="MAIN")

    def test_subscribe(self, adapter_manager):
        """Test subscribing to market data."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        req = SubscribeRequest(symbol="TEST", exchange=Exchange.LOCAL)
        
        with patch.object(adapter, 'subscribe') as mock_subscribe:
            adapter_manager.subscribe(req, "TEST")
            mock_subscribe.assert_called_once_with(req)

    def test_send_order(self, adapter_manager):
        """Test sending an order."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        
        order_id = adapter_manager.send_order(req, "TEST")
        assert order_id == "TEST_ORDER_ID"

    def test_cancel_order(self, adapter_manager):
        """Test canceling an order."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        req = CancelRequest(orderid="TEST_ORDER", symbol="TEST", exchange=Exchange.LOCAL)
        
        with patch.object(adapter, 'cancel_order') as mock_cancel:
            adapter_manager.cancel_order(req, "TEST")
            mock_cancel.assert_called_once_with(req)

    def test_send_quote(self, adapter_manager):
        """Test sending a quote."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        req = QuoteRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            bid_price=9.9,
            bid_volume=100,
            ask_price=10.1,
            ask_volume=100,
            bid_offset=Offset.NONE,
            ask_offset=Offset.NONE,
        )
        
        quote_id = adapter_manager.send_quote(req, "TEST")
        assert quote_id == "TEST_QUOTE_ID"

    def test_cancel_quote(self, adapter_manager):
        """Test canceling a quote."""
        adapter = adapter_manager.add_adapter(MockAdapter, "TEST")
        req = CancelRequest(orderid="TEST_QUOTE", symbol="TEST", exchange=Exchange.LOCAL)
        
        with patch.object(adapter, 'cancel_quote') as mock_cancel:
            adapter_manager.cancel_quote(req, "TEST")
            mock_cancel.assert_called_once_with(req)

    def test_query_history(self, adapter_manager):
        """Test querying history."""
        adapter_manager.add_adapter(MockAdapter, "TEST")
        req = HistoryRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            start=None,
            end=None,
            interval=None,
        )
        
        history = adapter_manager.query_history(req, "TEST")
        assert history == []

    def test_close(self, adapter_manager):
        """Test closing all adapters."""
        adapter1 = adapter_manager.add_adapter(MockAdapter, "TEST1")
        adapter2 = adapter_manager.add_adapter(MockAdapter, "TEST2")
        
        adapter1.connected = True
        adapter2.connected = True
        
        adapter_manager.close()
        
        assert adapter1.connected is False
        assert adapter2.connected is False