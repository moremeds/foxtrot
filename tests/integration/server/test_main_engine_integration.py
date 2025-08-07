"""
Integration tests for MainEngine with all refactored components.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.app.app import BaseApp
from foxtrot.util.constants import Exchange, Direction, OrderType, Offset, Product, Status
from foxtrot.util.object import (
    OrderRequest,
    SubscribeRequest,
    CancelRequest,
    ContractData,
    OrderData,
    TickData,
)


class MockAdapter(BaseAdapter):
    """Mock adapter for integration testing."""

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
        return f"{self.adapter_name}_ORDER_ID"

    def cancel_order(self, req):
        pass

    def send_quote(self, req):
        return f"{self.adapter_name}_QUOTE_ID"

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


class MockApp(BaseApp):
    """Mock app for integration testing."""

    app_name = "mock_app"
    app_module = "mock_module"
    app_path = "mock_path"
    display_name = "Mock App"
    engine_class = None
    
    def close(self):
        """Mock close method."""
        pass


class TestMainEngineIntegration:
    """Test MainEngine integration with all components."""

    @pytest.fixture
    def main_engine(self):
        """Create MainEngine instance."""
        engine = MainEngine()
        yield engine
        engine.close()

    def test_main_engine_initialization(self, main_engine):
        """Test that MainEngine initializes all components correctly."""
        # Verify event engine is running
        assert main_engine.event_engine is not None
        assert main_engine.event_engine._active is True
        
        # Verify managers are initialized
        assert main_engine.adapter_manager is not None
        assert main_engine.engine_manager is not None
        assert main_engine.app_manager is not None
        
        # Verify backward compatibility attributes
        assert main_engine.adapters == {}
        assert main_engine.engines != {}  # Should have LogEngine and OmsEngine
        assert main_engine.apps == {}
        assert main_engine.exchanges == []
        
        # Verify OMS methods are bound
        assert callable(main_engine.get_tick)
        assert callable(main_engine.get_order)
        assert callable(main_engine.get_all_orders)
        assert callable(main_engine.send_email)

    def test_adapter_integration(self, main_engine):
        """Test adapter integration through MainEngine."""
        # Add adapter
        adapter = main_engine.add_adapter(MockAdapter, "TEST")
        assert adapter is not None
        assert "TEST" in main_engine.adapters
        
        # Connect adapter
        settings = {"host": "testhost", "port": 9090}
        main_engine.connect(settings, "TEST")
        assert adapter.connected is True
        
        # Send order
        req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        order_id = main_engine.send_order(req, "TEST")
        assert order_id == "TEST_ORDER_ID"
        
        # Get adapter
        retrieved = main_engine.get_adapter("TEST")
        assert retrieved == adapter

    def test_engine_integration(self, main_engine):
        """Test engine integration through MainEngine."""
        # Verify default engines are loaded
        assert "log" in main_engine.engines
        assert "oms" in main_engine.engines
        assert "email" in main_engine.engines
        
        # Get engine
        oms_engine = main_engine.get_engine("oms")
        assert oms_engine is not None
        
        # Test OMS functionality
        tick = TickData(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            name="Test Symbol",
            datetime=datetime.now(),
            adapter_name="TEST"
        )
        oms_engine.data_store.ticks[tick.vt_symbol] = tick
        
        # Verify MainEngine can access OMS data
        retrieved_tick = main_engine.get_tick(tick.vt_symbol)
        assert retrieved_tick == tick

    def test_app_integration(self, main_engine):
        """Test app integration through MainEngine."""
        # Add app
        engine = main_engine.add_app(MockApp)
        assert engine is None  # MockApp has no engine_class
        assert "mock_app" in main_engine.apps
        
        # Get all apps
        apps = main_engine.get_all_apps()
        assert len(apps) == 1
        assert isinstance(apps[0], MockApp)

    def test_oms_engine_integration(self, main_engine):
        """Test OMS engine integration with event processing."""
        # Create contract to initialize offset converter
        contract = ContractData(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            name="Test Contract",
            product=Product.EQUITY,
            size=1,
            pricetick=0.01,
            adapter_name="TEST_ADAPTER"
        )
        
        # Process contract through OMS
        oms_engine = main_engine.get_engine("oms")
        oms_engine.data_store.contracts[contract.vt_symbol] = contract
        
        # Verify contract is accessible
        retrieved = main_engine.get_contract(contract.vt_symbol)
        assert retrieved == contract
        
        # Test order processing
        order = OrderData(
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
        
        oms_engine.data_store.orders[order.vt_orderid] = order
        retrieved = main_engine.get_order(order.vt_orderid)
        assert retrieved == order

    def test_multiple_adapters(self, main_engine):
        """Test managing multiple adapters."""
        # Add multiple adapters
        adapter1 = main_engine.add_adapter(MockAdapter, "TEST1")
        adapter2 = main_engine.add_adapter(MockAdapter, "TEST2")
        
        assert "TEST1" in main_engine.adapters
        assert "TEST2" in main_engine.adapters
        
        # Get all gateway names
        names = main_engine.get_all_gateway_names()
        assert "TEST1" in names
        assert "TEST2" in names
        
        # Connect both
        main_engine.connect({}, "TEST1")
        main_engine.connect({}, "TEST2")
        
        assert adapter1.connected is True
        assert adapter2.connected is True

    def test_event_flow_integration(self, main_engine):
        """Test event flow through the system."""
        # Add adapter
        adapter = main_engine.add_adapter(MockAdapter, "TEST")
        
        # Write log through MainEngine
        main_engine.write_log("Test log message", "TEST_SOURCE")
        
        # Give event engine time to process
        import time
        time.sleep(0.1)
        
        # Note: In a real test, we'd verify the log was processed
        # but without mocking the logger, we can't easily verify

    def test_close_integration(self, main_engine):
        """Test proper shutdown of all components."""
        # Add adapter and app
        adapter = main_engine.add_adapter(MockAdapter, "TEST")
        adapter.connected = True
        main_engine.add_app(MockApp)
        
        # Close main engine
        main_engine.close()
        
        # Verify event engine stopped
        assert main_engine.event_engine._active is False
        
        # Verify adapter closed
        assert adapter.connected is False

    def test_backward_compatibility(self, main_engine):
        """Test that backward compatibility is maintained."""
        # Test direct access to manager collections
        assert main_engine.adapters == main_engine.adapter_manager.adapters
        assert main_engine.engines == main_engine.engine_manager.engines
        assert main_engine.apps == main_engine.app_manager.apps
        assert main_engine.exchanges == main_engine.adapter_manager.exchanges
        
        # Test delegated methods work
        adapter = main_engine.add_adapter(MockAdapter, "TEST")
        assert main_engine.get_adapter("TEST") == adapter
        
        # Test OMS methods are callable
        assert callable(main_engine.get_tick)
        assert callable(main_engine.get_all_contracts)
        assert callable(main_engine.update_order_request)

    def test_engine_initialization_order(self, main_engine):
        """Test that engines are initialized in correct order."""
        # LogEngine should be first
        engines_list = list(main_engine.engines.keys())
        assert engines_list[0] == "log"
        
        # OMS and Email engines should be present
        assert "oms" in engines_list
        assert "email" in engines_list

    @patch('foxtrot.util.settings.SETTINGS')
    def test_email_engine_integration(self, mock_settings, main_engine):
        """Test email engine integration."""
        # Mock email settings
        mock_settings.__getitem__.side_effect = lambda key: {
            "email.receiver": "test@example.com",
            "email.sender": "sender@example.com",
            "email.server": "smtp.example.com",
            "email.port": 587,
            "email.username": "user",
            "email.password": "pass",
        }.get(key, "")
        
        # Send email should be callable
        assert callable(main_engine.send_email)
        
        # Note: Actual email sending would require more mocking

    def test_offset_converter_integration(self, main_engine):
        """Test offset converter integration through OMS."""
        # Add adapter first
        main_engine.add_adapter(MockAdapter, "TEST")
        
        # Create contract to initialize converter
        contract = ContractData(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            name="Test Contract",
            product=Product.EQUITY,
            size=1,
            pricetick=0.01,
            adapter_name="TEST"
        )
        
        oms_engine = main_engine.get_engine("oms")
        
        # Simulate contract event processing
        from foxtrot.core.event_engine import Event
        from foxtrot.util.event_type import EVENT_CONTRACT
        event = Event(EVENT_CONTRACT, contract)
        oms_engine.process_contract_event(event)
        
        # Verify converter was created
        converter = main_engine.get_converter("TEST")
        assert converter is not None

    def test_full_workflow_integration(self, main_engine):
        """Test a complete workflow through the system."""
        # 1. Add and connect adapter
        adapter = main_engine.add_adapter(MockAdapter, "TEST")
        main_engine.connect({}, "TEST")
        
        # 2. Subscribe to market data
        sub_req = SubscribeRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL
        )
        main_engine.subscribe(sub_req, "TEST")
        
        # 3. Send order
        order_req = OrderRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=10.0,
            offset=Offset.NONE,
        )
        order_id = main_engine.send_order(order_req, "TEST")
        assert order_id == "TEST_ORDER_ID"
        
        # 4. Cancel order
        cancel_req = CancelRequest(
            orderid=order_id,
            symbol="TEST",
            exchange=Exchange.LOCAL
        )
        main_engine.cancel_order(cancel_req, "TEST")
        
        # 5. Query history
        from foxtrot.util.object import HistoryRequest
        hist_req = HistoryRequest(
            symbol="TEST",
            exchange=Exchange.LOCAL,
            start=None,
            end=None,
            interval=None
        )
        history = main_engine.query_history(hist_req, "TEST")
        assert history == []