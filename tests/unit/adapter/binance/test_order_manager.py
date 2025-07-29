"""
Unit tests for BinanceOrderManager.

Tests order lifecycle management including creation, tracking,
cancellation, and status updates.
"""

import pytest
from unittest.mock import Mock, patch

from foxtrot.adapter.binance.order_manager import BinanceOrderManager
from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import OrderRequest, CancelRequest


class TestBinanceOrderManager:
    """Test cases for BinanceOrderManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_api_client = Mock()
        self.mock_api_client.adapter_name = "TEST_BINANCE"
        self.order_manager = BinanceOrderManager(self.mock_api_client)

    def test_initialization(self):
        """Test order manager initialization."""
        assert self.order_manager.api_client == self.mock_api_client
        assert len(self.order_manager._orders) == 0
        assert self.order_manager._local_order_id == 0
        assert hasattr(self.order_manager, '_order_lock')

    def test_send_order_success_limit(self):
        """Test successful limit order sending."""
        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.create_limit_order.return_value = {
            'id': '12345',
            'status': 'open'
        }
        self.mock_api_client.exchange = mock_exchange
        
        # Create order request
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.order_manager.send_order(req)
        
        # Verify order was sent
        assert result == "TEST_BINANCE_1"
        mock_exchange.create_limit_order.assert_called_once_with(
            "BTC/USDT", "buy", 0.001, 30000
        )
        
        # Verify order was stored
        order = self.order_manager._orders["TEST_BINANCE_1"]
        assert order.symbol == "BTCUSDT.BINANCE"
        assert order.direction == Direction.LONG
        assert order.type == OrderType.LIMIT
        assert order.status == Status.NOTTRADED

    def test_send_order_success_market(self):
        """Test successful market order sending."""
        # Mock exchange
        mock_exchange = Mock()
        mock_exchange.create_market_order.return_value = {
            'id': '12345',
            'status': 'closed'
        }
        self.mock_api_client.exchange = mock_exchange
        
        # Create order request
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.SHORT,
            type=OrderType.MARKET,
            volume=0.001,
            price=0  # Market orders don't need price
        )
        
        result = self.order_manager.send_order(req)
        
        # Verify order was sent
        assert result == "TEST_BINANCE_1"
        mock_exchange.create_market_order.assert_called_once_with(
            "BTC/USDT", "sell", 0.001
        )

    def test_send_order_no_exchange(self):
        """Test order sending when exchange is not connected."""
        self.mock_api_client.exchange = None
        
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.order_manager.send_order(req)
        
        assert result == ""
        self.mock_api_client._log_error.assert_called_with("Exchange not connected")

    def test_send_order_invalid_symbol(self):
        """Test order sending with malformed symbol (no dot)."""
        self.mock_api_client.exchange = Mock()
        
        req = OrderRequest(
            symbol="INVALID",  # No dot - malformed VT symbol
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.order_manager.send_order(req)
        
        assert result == ""
        self.mock_api_client._log_error.assert_called_with("Invalid symbol: INVALID")

    def test_send_order_exchange_exception(self):
        """Test order sending when exchange raises exception."""
        mock_exchange = Mock()
        mock_exchange.create_limit_order.side_effect = Exception("Network error")
        self.mock_api_client.exchange = mock_exchange
        
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        
        result = self.order_manager.send_order(req)
        
        assert result == ""
        self.mock_api_client._log_error.assert_called_with("Failed to send order: Network error")

    def test_cancel_order_success(self):
        """Test successful order cancellation."""
        # First, add an order to track
        mock_exchange = Mock()
        mock_exchange.create_limit_order.return_value = {'id': '12345', 'status': 'open'}
        mock_exchange.cancel_order.return_value = {'id': '12345', 'status': 'canceled'}
        self.mock_api_client.exchange = mock_exchange
        
        # Send order first
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        order_id = self.order_manager.send_order(req)
        
        # Now cancel it
        cancel_req = CancelRequest(orderid=order_id, symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        result = self.order_manager.cancel_order(cancel_req)
        
        assert result is True
        mock_exchange.cancel_order.assert_called_once_with('12345', 'BTC/USDT')
        
        # Verify order status was updated
        order = self.order_manager._orders[order_id]
        assert order.status == Status.CANCELLED

    def test_cancel_order_not_found(self):
        """Test cancelling non-existent order."""
        self.mock_api_client.exchange = Mock()
        
        cancel_req = CancelRequest(orderid="NONEXISTENT", symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        result = self.order_manager.cancel_order(cancel_req)
        
        assert result is False
        self.mock_api_client._log_error.assert_called_with("Order not found: NONEXISTENT")

    def test_cancel_order_no_exchange(self):
        """Test cancelling order when exchange is not connected."""
        self.mock_api_client.exchange = None
        
        cancel_req = CancelRequest(orderid="TEST_ORDER", symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        result = self.order_manager.cancel_order(cancel_req)
        
        assert result is False

    def test_query_order_found(self):
        """Test querying existing order."""
        # Add an order first
        mock_exchange = Mock()
        mock_exchange.create_limit_order.return_value = {'id': '12345', 'status': 'open'}
        self.mock_api_client.exchange = mock_exchange
        
        req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=0.001,
            price=30000
        )
        order_id = self.order_manager.send_order(req)
        
        # Query the order
        result = self.order_manager.query_order(order_id)
        
        assert result is not None
        assert result.orderid == "12345"  # Exchange order ID
        assert result.symbol == "BTCUSDT.BINANCE"

    def test_query_order_not_found(self):
        """Test querying non-existent order."""
        result = self.order_manager.query_order("NONEXISTENT")
        assert result is None

    def test_convert_symbol_to_ccxt_usdt(self):
        """Test symbol conversion for USDT pairs."""
        result = self.order_manager._convert_symbol_to_ccxt("BTCUSDT.BINANCE")
        assert result == "BTC/USDT"

    def test_convert_symbol_to_ccxt_btc(self):
        """Test symbol conversion for BTC pairs."""
        result = self.order_manager._convert_symbol_to_ccxt("ETHBTC.BINANCE")
        assert result == "ETH/BTC"

    def test_convert_symbol_to_ccxt_eth(self):
        """Test symbol conversion for ETH pairs."""
        result = self.order_manager._convert_symbol_to_ccxt("ADAETH.BINANCE")
        assert result == "ADA/ETH"

    def test_convert_symbol_to_ccxt_unknown(self):
        """Test symbol conversion for unknown format."""
        result = self.order_manager._convert_symbol_to_ccxt("UNKNOWN.BINANCE")
        assert result == "UNKNOWN/USDT"  # Default to USDT

    def test_convert_symbol_to_ccxt_invalid(self):
        """Test symbol conversion for invalid format."""
        result = self.order_manager._convert_symbol_to_ccxt("INVALID")
        assert result == ""

    def test_convert_order_type_to_ccxt(self):
        """Test order type conversion."""
        assert self.order_manager._convert_order_type_to_ccxt(OrderType.MARKET) == "market"
        assert self.order_manager._convert_order_type_to_ccxt(OrderType.LIMIT) == "limit"
        assert self.order_manager._convert_order_type_to_ccxt(OrderType.STOP) == "limit"  # Default

    def test_convert_status_from_ccxt(self):
        """Test status conversion from CCXT."""
        assert self.order_manager._convert_status_from_ccxt("open") == Status.NOTTRADED
        assert self.order_manager._convert_status_from_ccxt("closed") == Status.ALLTRADED
        assert self.order_manager._convert_status_from_ccxt("canceled") == Status.CANCELLED
        assert self.order_manager._convert_status_from_ccxt("cancelled") == Status.CANCELLED
        assert self.order_manager._convert_status_from_ccxt("partial") == Status.PARTTRADED
        assert self.order_manager._convert_status_from_ccxt("unknown") == Status.SUBMITTING  # Default