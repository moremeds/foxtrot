"""
Unit tests for Binance Market Data WebSocket functionality.

Tests the WebSocket implementation in BinanceMarketData.
"""

import asyncio
import pytest
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

from foxtrot.adapter.binance.market_data import BinanceMarketData
from foxtrot.core.event import Event
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import SubscribeRequest, TickData


class TestBinanceMarketDataWebSocket:
    """Test cases for BinanceMarketData WebSocket functionality."""

    @pytest.fixture
    def event_engine(self):
        """Create EventEngine for testing."""
        engine = EventEngine()
        engine.start()
        yield engine
        engine.stop()

    @pytest.fixture
    def mock_api_client(self, event_engine):
        """Create a mock API client."""
        client = MagicMock()
        client.event_engine = event_engine
        client.adapter_name = "TestAdapter"
        client._log_info = MagicMock()
        client._log_error = MagicMock()
        client._log_warning = MagicMock()
        
        # Mock exchange
        client.exchange = MagicMock()
        client.exchange.fetch_ticker = MagicMock(return_value={
            "symbol": "BTC/USDT",
            "last": 45000.0,
            "bid": 44999.0,
            "ask": 45001.0,
            "high": 46000.0,
            "low": 44000.0,
            "open": 44500.0,
            "baseVolume": 1234.56,
            "quoteVolume": 55555555.0
        })
        
        # Mock exchange_pro for WebSocket
        client.exchange_pro = AsyncMock()
        async def mock_watch_ticker(symbol):
            # Return mock ticker data
            return {
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "last": 45000.0,
                "bid": 44999.0,
                "ask": 45001.0,
                "bidVolume": 10.0,
                "askVolume": 10.0,
                "high": 46000.0,
                "low": 44000.0,
                "open": 44500.0,
                "previousClose": 44500.0,
                "baseVolume": 1234.56,
                "quoteVolume": 55555555.0
            }
        client.exchange_pro.watchTicker = mock_watch_ticker
        
        # WebSocket configuration
        client.use_websocket = True
        client.websocket_enabled_symbols = set()
        
        def is_websocket_enabled(symbol=None):
            if symbol is None:
                return client.use_websocket
            return client.use_websocket and (
                not client.websocket_enabled_symbols or 
                symbol in client.websocket_enabled_symbols
            )
        
        client.is_websocket_enabled = is_websocket_enabled
        
        return client

    @pytest.fixture
    def market_data(self, mock_api_client):
        """Create BinanceMarketData instance."""
        return BinanceMarketData(mock_api_client)

    def test_initialization(self, market_data, mock_api_client):
        """Test market data initialization."""
        assert market_data.api_client == mock_api_client
        assert len(market_data._subscribed_symbols) == 0
        assert market_data._ws_thread is None
        assert not market_data._active
        assert market_data.async_bridge is None
        assert market_data.websocket_manager is None

    def test_subscribe_success(self, market_data):
        """Test successful subscription."""
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        result = market_data.subscribe(req)
        
        assert result is True
        assert "BTCUSDT.BINANCE" in market_data._subscribed_symbols
        assert market_data._active
        assert market_data._ws_thread is not None

    def test_subscribe_duplicate(self, market_data):
        """Test subscribing to same symbol twice."""
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        # First subscription
        market_data.subscribe(req)
        
        # Second subscription
        with patch.object(market_data.api_client, '_log_info') as mock_log:
            result = market_data.subscribe(req)
            assert result is True
            mock_log.assert_called_with("Already subscribed to BTCUSDT.BINANCE")

    def test_unsubscribe(self, market_data):
        """Test unsubscribing from symbol."""
        # Subscribe first
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        market_data.subscribe(req)
        
        # Unsubscribe
        result = market_data.unsubscribe("BTCUSDT.BINANCE")
        
        assert result is True
        assert "BTCUSDT.BINANCE" not in market_data._subscribed_symbols

    def test_symbol_conversion(self, market_data):
        """Test symbol format conversion."""
        test_cases = [
            ("BTCUSDT.BINANCE", "BTC/USDT"),
            ("ETHUSDT.BINANCE", "ETH/USDT"),
            ("BNBBTC.BINANCE", "BNB/BTC"),
            ("SOLETH.BINANCE", "SOL/ETH"),
            ("ABC.BINANCE", ""),  # Too short
            ("XYZ.BINANCE", ""),  # Unknown format
        ]
        
        for vt_symbol, expected in test_cases:
            result = market_data._convert_symbol_to_ccxt(vt_symbol)
            assert result == expected

    def test_websocket_components_initialization(self, market_data, mock_api_client):
        """Test WebSocket components are initialized when enabled."""
        # Enable WebSocket
        mock_api_client.use_websocket = True
        
        # Subscribe to trigger WebSocket start
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        market_data.subscribe(req)
        
        # Give thread time to initialize
        time.sleep(0.1)
        
        # Components should be initialized
        assert market_data.async_bridge is not None
        assert market_data._ws_thread.is_alive()

    def test_http_fallback_mode(self, market_data, mock_api_client):
        """Test fallback to HTTP polling when WebSocket disabled."""
        # Disable WebSocket
        mock_api_client.use_websocket = False
        
        # Subscribe
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        result = market_data.subscribe(req)
        
        assert result is True
        assert market_data._active
        assert market_data._ws_thread is not None
        # Should use HTTP polling thread
        assert market_data.async_bridge is None  # Not initialized for HTTP mode

    def test_close_market_data(self, market_data):
        """Test closing market data connections."""
        # Subscribe to start thread
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        market_data.subscribe(req)
        
        # Close
        market_data.close()
        
        # Verify cleanup
        assert len(market_data._subscribed_symbols) == 0
        assert not market_data._active
        # Thread should stop
        time.sleep(0.1)
        assert not market_data._ws_thread.is_alive()

    def test_tick_data_conversion(self, market_data):
        """Test converting ticker to tick data."""
        ticker = {
            "symbol": "BTC/USDT",
            "timestamp": 1234567890000,
            "last": 45000.0,
            "bid": 44999.0,
            "ask": 45001.0,
            "bidVolume": 10.0,
            "askVolume": 12.0,
            "high": 46000.0,
            "low": 44000.0,
            "open": 44500.0,
            "previousClose": 44400.0,
            "baseVolume": 1234.56,
            "quoteVolume": 55555555.0
        }
        
        tick = market_data._convert_ticker_to_tick(ticker, "BTCUSDT.BINANCE")
        
        assert isinstance(tick, TickData)
        assert tick.symbol == "BTCUSDT.BINANCE"
        assert tick.exchange == Exchange.BINANCE
        assert tick.last_price == 45000.0
        assert tick.bid_price_1 == 44999.0
        assert tick.ask_price_1 == 45001.0
        assert tick.volume == 1234.56

    @pytest.mark.asyncio
    async def test_watch_symbol_async(self, market_data, mock_api_client, event_engine):
        """Test async watch symbol functionality."""
        # Initialize WebSocket components
        from foxtrot.util.websocket_utils import AsyncThreadBridge
        market_data.async_bridge = AsyncThreadBridge(event_engine)
        market_data.api_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE"}
        
        # Add subscription
        market_data._subscribed_symbols.add("BTCUSDT.BINANCE")
        market_data._active = True
        
        # Track emitted events
        emitted_events = []
        original_emit = market_data.async_bridge.emit_event_threadsafe
        
        def track_emit(event):
            emitted_events.append(event)
            # Stop watching after first event to prevent infinite loop
            market_data._active = False
            original_emit(event)
        
        market_data.async_bridge.emit_event_threadsafe = track_emit
        
        # Start watching (will complete after one tick)
        await market_data._watch_symbol("BTCUSDT.BINANCE")
        
        # Should have emitted a tick event
        assert len(emitted_events) > 0
        assert emitted_events[0].type == EVENT_TICK
        assert isinstance(emitted_events[0].data, TickData)

    def test_multiple_subscriptions(self, market_data):
        """Test managing multiple subscriptions."""
        symbols = ["BTCUSDT.BINANCE", "ETHUSDT.BINANCE", "BNBUSDT.BINANCE"]
        
        # Subscribe to all
        for symbol in symbols:
            req = SubscribeRequest(symbol=symbol, exchange=Exchange.BINANCE)
            assert market_data.subscribe(req)
        
        assert len(market_data._subscribed_symbols) == 3
        assert market_data._active
        
        # Unsubscribe from one
        market_data.unsubscribe("ETHUSDT.BINANCE")
        assert len(market_data._subscribed_symbols) == 2
        assert market_data._active  # Still active with remaining subscriptions
        
        # Unsubscribe from all
        for symbol in ["BTCUSDT.BINANCE", "BNBUSDT.BINANCE"]:
            market_data.unsubscribe(symbol)
        
        assert len(market_data._subscribed_symbols) == 0
        # Thread should stop when no subscriptions
        time.sleep(0.1)
        assert not market_data._active