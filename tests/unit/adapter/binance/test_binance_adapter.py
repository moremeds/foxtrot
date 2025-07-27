"""
Unit tests for BinanceAdapter.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from foxtrot.adapter.binance import BinanceAdapter
from foxtrot.core.engine import EventEngine
from foxtrot.util.constants import Exchange, Status, Direction, OrderType
from foxtrot.util.object import (
    SubscribeRequest, OrderRequest, CancelRequest, HistoryRequest,
    OrderData, AccountData, BarData, TickData, TradeData
)


class TestBinanceAdapter:
    """Test cases for BinanceAdapter class."""

    def test_adapter_instantiation(self):
        """Test that BinanceAdapter can be instantiated correctly."""
        # Create mock EventEngine
        mock_event_engine = Mock(spec=EventEngine)
        adapter_name = "test_binance"
        
        # Instantiate adapter
        adapter = BinanceAdapter(
            event_engine=mock_event_engine,
            adapter_name=adapter_name
        )
        
        # Verify basic properties
        assert adapter.event_engine is mock_event_engine
        assert adapter.adapter_name == adapter_name
        assert adapter.default_name == "BINANCE"
        assert Exchange.BINANCE in adapter.exchanges
        assert adapter.ccxt_exchange is None
        assert adapter.connected is False

    def test_default_setting_structure(self):
        """Test that default_setting has required fields."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        required_fields = ["API Key", "Secret", "Sandbox", "Proxy Host", "Proxy Port"]
        for field in required_fields:
            assert field in adapter.default_setting

    def test_status_mappings(self):
        """Test status conversion mappings."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Test CCXT to VT status mapping
        assert adapter.STATUS_CCXT2VT["open"] == Status.NOTTRADED
        assert adapter.STATUS_CCXT2VT["closed"] == Status.ALLTRADED
        assert adapter.STATUS_CCXT2VT["canceled"] == Status.CANCELLED
        
        # Test VT to CCXT status mapping
        assert adapter.STATUS_VT2CCXT[Status.NOTTRADED] == "open"
        assert adapter.STATUS_VT2CCXT[Status.ALLTRADED] == "closed"

    def test_order_type_mappings(self):
        """Test order type conversion mappings."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        assert adapter.ORDERTYPE_VT2CCXT[OrderType.LIMIT] == "limit"
        assert adapter.ORDERTYPE_VT2CCXT[OrderType.MARKET] == "market"
        
        assert adapter.ORDERTYPE_CCXT2VT["limit"] == OrderType.LIMIT
        assert adapter.ORDERTYPE_CCXT2VT["market"] == OrderType.MARKET

    def test_direction_mappings(self):
        """Test direction conversion mappings."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        assert adapter.DIRECTION_VT2CCXT[Direction.LONG] == "buy"
        assert adapter.DIRECTION_VT2CCXT[Direction.SHORT] == "sell"
        
        assert adapter.DIRECTION_CCXT2VT["buy"] == Direction.LONG
        assert adapter.DIRECTION_CCXT2VT["sell"] == Direction.SHORT

    def test_symbol_conversion(self):
        """Test symbol format conversion."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Test VT symbol to CCXT
        vt_symbol = "BTC.BINANCE"
        ccxt_symbol = adapter._convert_symbol_to_ccxt(vt_symbol)
        assert ccxt_symbol == "BTC/USDT"
        
        # Test CCXT symbol to VT
        ccxt_symbol = "ETH/USDT"
        vt_symbol = adapter._convert_symbol_from_ccxt(ccxt_symbol)
        assert vt_symbol == "ETH.BINANCE"

    def test_interval_conversion(self):
        """Test interval to timeframe conversion."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Test common intervals
        assert adapter._convert_interval_to_ccxt_timeframe(1) == "1m"
        assert adapter._convert_interval_to_ccxt_timeframe(5) == "5m"
        assert adapter._convert_interval_to_ccxt_timeframe(60) == "1h"
        assert adapter._convert_interval_to_ccxt_timeframe(1440) == "1d"
        
        # Test default fallback
        assert adapter._convert_interval_to_ccxt_timeframe(999) == "1h"

    @patch('ccxt.binance')
    def test_init_ccxt_success(self, mock_ccxt_binance):
        """Test successful CCXT initialization."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        mock_exchange = Mock()
        mock_ccxt_binance.return_value = mock_exchange
        
        adapter._init_ccxt("test_key", "test_secret", False)
        
        # Verify CCXT exchange was created
        mock_ccxt_binance.assert_called_once()
        assert adapter.ccxt_exchange == mock_exchange

    def test_connect_not_connected(self):
        """Test operations when not connected."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Test query_account when not connected
        adapter.query_account()
        # Should not raise exception, just log warning
        
        # Test send_order when not connected
        mock_order_req = Mock(spec=OrderRequest)
        result = adapter.send_order(mock_order_req)
        assert result == ""

    def test_convert_ccxt_order_to_order_data(self):
        """Test conversion of CCXT order to OrderData."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        ccxt_order = {
            'id': '12345',
            'symbol': 'BTC/USDT',
            'type': 'limit',
            'side': 'buy',
            'amount': 1.0,
            'price': 50000.0,
            'filled': 0.5,
            'status': 'open',
            'timestamp': 1640995200000  # 2022-01-01 00:00:00 UTC
        }
        
        order_data = adapter._convert_ccxt_order_to_order_data(ccxt_order)
        
        assert order_data.orderid == '12345'
        assert order_data.symbol == 'BTC'
        assert order_data.exchange == Exchange.BINANCE
        assert order_data.type == OrderType.LIMIT
        assert order_data.direction == Direction.LONG
        assert order_data.volume == 1.0
        assert order_data.price == 50000.0
        assert order_data.traded == 0.5
        assert order_data.status == Status.NOTTRADED

    def test_convert_ccxt_trade_to_trade_data(self):
        """Test conversion of CCXT trade to TradeData."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        ccxt_trade = {
            'id': '67890',
            'order': '12345',
            'symbol': 'ETH/USDT',
            'side': 'sell',
            'amount': 2.0,
            'price': 3000.0,
            'timestamp': 1640995200000
        }
        
        trade_data = adapter._convert_ccxt_trade_to_trade_data(ccxt_trade)
        
        assert trade_data.tradeid == '67890'
        assert trade_data.orderid == '12345'
        assert trade_data.symbol == 'ETH'
        assert trade_data.exchange == Exchange.BINANCE
        assert trade_data.direction == Direction.SHORT
        assert trade_data.volume == 2.0
        assert trade_data.price == 3000.0

    def test_convert_ccxt_ticker_to_tick_data(self):
        """Test conversion of CCXT ticker to TickData."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        ticker = {
            'symbol': 'BTC/USDT',
            'timestamp': 1640995200000,
            'baseVolume': 100.0,
            'open': 49000.0,
            'high': 51000.0,
            'low': 48000.0,
            'last': 50000.0,
            'ask': 50010.0,
            'bid': 49990.0
        }
        
        mock_req = Mock()
        mock_req.symbol = 'BTC'
        
        tick_data = adapter._convert_ccxt_ticker_to_tick_data(ticker, mock_req)
        
        assert tick_data.symbol == 'BTC'
        assert tick_data.exchange == Exchange.BINANCE
        assert tick_data.volume == 100.0
        assert tick_data.open_price == 49000.0
        assert tick_data.high_price == 51000.0
        assert tick_data.low_price == 48000.0
        assert tick_data.last_price == 50000.0
        assert tick_data.ask_price_1 == 50010.0
        assert tick_data.bid_price_1 == 49990.0

    def test_query_position_not_implemented(self):
        """Test that query_position raises NotImplementedError."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        with pytest.raises(NotImplementedError):
            adapter.query_position()

    @patch.object(BinanceAdapter, 'write_log')
    def test_error_logging(self, mock_write_log):
        """Test that errors are properly logged."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Test connection error logging
        adapter.query_account()
        mock_write_log.assert_called_with("Not connected to Binance")

    def test_close_connection(self):
        """Test connection closing."""
        mock_event_engine = Mock(spec=EventEngine)
        adapter = BinanceAdapter(mock_event_engine, "test")
        
        # Setup a mock exchange
        mock_exchange = Mock()
        adapter.ccxt_exchange = mock_exchange
        adapter.connected = True
        
        adapter.close()
        
        assert adapter.connected is False
        assert adapter.ccxt_exchange is None