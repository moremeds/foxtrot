"""
Unit tests for BinanceAdapter facade.

Tests the main adapter facade to ensure it properly delegates
to the BinanceApiClient and maintains the BaseAdapter interface.
"""

import pytest
from unittest.mock import Mock, patch

from foxtrot.adapter.binance import BinanceAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange, Direction, OrderType
from foxtrot.util.object import OrderRequest, CancelRequest, SubscribeRequest


class TestBinanceAdapter:
    """Test cases for BinanceAdapter facade."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_engine = Mock(spec=EventEngine)
        self.adapter = BinanceAdapter(self.event_engine, "TEST_BINANCE")

    def test_initialization(self):
        """Test adapter initialization."""
        assert self.adapter.adapter_name == "TEST_BINANCE"
        assert self.adapter.event_engine == self.event_engine
        assert self.adapter.default_name == "BINANCE"
        assert Exchange.BINANCE in self.adapter.exchanges
        assert hasattr(self.adapter, 'api_client')

    def test_default_settings(self):
        """Test default settings configuration."""
        expected_settings = {
            "API Key": "",
            "Secret": "",
            "Sandbox": False,
            "Proxy Host": "",
            "Proxy Port": 0,
        }
        assert self.adapter.default_setting == expected_settings

    @patch('foxtrot.adapter.binance.api_client.BinanceApiClient.connect')
    def test_connect_delegates_to_api_client(self, mock_connect):
        """Test that connect method delegates to api_client."""
        mock_connect.return_value = True
        
        settings = {
            "API Key": "test_key",
            "Secret": "test_secret",
            "Sandbox": True
        }
        
        result = self.adapter.connect(settings)
        
        assert result is True
        mock_connect.assert_called_once_with(settings)

    @patch('foxtrot.adapter.binance.api_client.BinanceApiClient.close')
    def test_close_delegates_to_api_client(self, mock_close):
        """Test that close method delegates to api_client."""
        self.adapter.close()
        mock_close.assert_called_once()

    def test_send_order_when_order_manager_none(self):
        """Test send_order returns empty string when order_manager is None."""
        self.adapter.api_client.order_manager = None
        
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.adapter.send_order(req)
        assert result == ""

    def test_send_order_delegates_to_order_manager(self):
        """Test send_order delegates to order_manager when available."""
        mock_order_manager = Mock()
        mock_order_manager.send_order.return_value = "TEST_ORDER_123"
        self.adapter.api_client.order_manager = mock_order_manager
        
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.adapter.send_order(req)
        
        assert result == "TEST_ORDER_123"
        mock_order_manager.send_order.assert_called_once_with(req)

    def test_cancel_order_when_order_manager_none(self):
        """Test cancel_order returns False when order_manager is None."""
        self.adapter.api_client.order_manager = None
        
        req = CancelRequest(orderid="TEST_ORDER_123", symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        
        result = self.adapter.cancel_order(req)
        assert result is False

    def test_cancel_order_delegates_to_order_manager(self):
        """Test cancel_order delegates to order_manager when available."""
        mock_order_manager = Mock()
        mock_order_manager.cancel_order.return_value = True
        self.adapter.api_client.order_manager = mock_order_manager
        
        req = CancelRequest(orderid="TEST_ORDER_123", symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        
        result = self.adapter.cancel_order(req)
        
        assert result is True
        mock_order_manager.cancel_order.assert_called_once_with(req)

    def test_subscribe_when_market_data_none(self):
        """Test subscribe returns False when market_data is None."""
        self.adapter.api_client.market_data = None
        
        req = SubscribeRequest(symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        
        result = self.adapter.subscribe(req)
        assert result is False

    def test_subscribe_delegates_to_market_data(self):
        """Test subscribe delegates to market_data when available."""
        mock_market_data = Mock()
        mock_market_data.subscribe.return_value = True
        self.adapter.api_client.market_data = mock_market_data
        
        req = SubscribeRequest(symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        
        result = self.adapter.subscribe(req)
        
        assert result is True
        mock_market_data.subscribe.assert_called_once_with(req)

    def test_query_account_when_account_manager_none(self):
        """Test query_account returns early when account_manager is None."""
        self.adapter.api_client.account_manager = None
        
        # Should not raise exception, just return early
        self.adapter.query_account()

    def test_query_account_delegates_to_account_manager(self):
        """Test query_account delegates to account_manager when available."""
        mock_account_manager = Mock()
        mock_account_data = Mock()
        mock_account_manager.query_account.return_value = mock_account_data
        self.adapter.api_client.account_manager = mock_account_manager
        
        # Mock the on_account callback
        self.adapter.on_account = Mock()
        
        self.adapter.query_account()
        
        mock_account_manager.query_account.assert_called_once()
        self.adapter.on_account.assert_called_once_with(mock_account_data)

    def test_connected_property(self):
        """Test connected property delegates to api_client."""
        self.adapter.api_client.connected = True
        assert self.adapter.connected is True
        
        self.adapter.api_client.connected = False
        assert self.adapter.connected is False

    def test_get_available_contracts_when_contract_manager_none(self):
        """Test get_available_contracts returns empty list when contract_manager is None."""
        self.adapter.api_client.contract_manager = None
        
        result = self.adapter.get_available_contracts()
        assert result == []

    def test_get_available_contracts_delegates_to_contract_manager(self):
        """Test get_available_contracts delegates to contract_manager when available."""
        mock_contract_manager = Mock()
        mock_contracts = [Mock(), Mock()]
        mock_contract_manager.get_available_contracts.return_value = mock_contracts
        self.adapter.api_client.contract_manager = mock_contract_manager
        
        result = self.adapter.get_available_contracts()
        
        assert result == mock_contracts
        mock_contract_manager.get_available_contracts.assert_called_once()