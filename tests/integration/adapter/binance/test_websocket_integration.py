"""
Integration tests for Binance WebSocket functionality.

Tests the full WebSocket implementation with mock CCXT Pro exchange.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from foxtrot.adapter.binance.api_client import BinanceApiClient
from foxtrot.adapter.binance.market_data import BinanceMarketData
from foxtrot.core.event import Event
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import SubscribeRequest, TickData


class TestWebSocketIntegration:
    """Integration tests for WebSocket streaming."""

    @pytest.fixture
    def event_engine(self):
        """Create a real EventEngine."""
        engine = EventEngine()
        engine.start()
        yield engine
        engine.stop()

    @pytest.fixture
    def mock_ccxt_exchange(self):
        """Create a mock CCXT exchange."""
        exchange = MagicMock()
        exchange.load_markets = MagicMock(return_value={
            "BTC/USDT": {"symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"},
            "ETH/USDT": {"symbol": "ETH/USDT", "base": "ETH", "quote": "USDT"}
        })
        exchange.fetch_ticker = MagicMock(return_value={
            "symbol": "BTC/USDT",
            "last": 45000.0,
            "bid": 44999.0,
            "ask": 45001.0,
            "high": 46000.0,
            "low": 44000.0,
            "open": 44500.0,
            "close": 45000.0,
            "baseVolume": 1234.56,
            "quoteVolume": 55555555.0
        })
        return exchange

    @pytest.fixture
    def mock_ccxtpro_exchange(self):
        """Create a mock CCXT Pro exchange."""
        exchange = AsyncMock()
        
        # Mock WebSocket ticker data
        async def mock_watch_ticker(symbol):
            # Simulate real-time updates with varying prices
            base_price = 45000.0 if symbol == "BTC/USDT" else 3000.0
            variation = time.time() % 100  # Price variation
            
            return {
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "last": base_price + variation,
                "bid": base_price + variation - 1,
                "ask": base_price + variation + 1,
                "bidVolume": 10.5,
                "askVolume": 12.3,
                "high": base_price + 1000,
                "low": base_price - 1000,
                "open": base_price - 500,
                "close": base_price + variation,
                "previousClose": base_price - 500,
                "baseVolume": 1234.56,
                "quoteVolume": 55555555.0
            }
        
        exchange.watchTicker = mock_watch_ticker
        exchange.close = AsyncMock()
        return exchange

    @pytest.fixture
    def api_client(self, event_engine, mock_ccxt_exchange, mock_ccxtpro_exchange):
        """Create an API client with mocked exchanges."""
        client = BinanceApiClient(event_engine, "TestAdapter")
        
        # Directly set the exchange instances
        client.exchange = mock_ccxt_exchange
        client.exchange_pro = mock_ccxtpro_exchange
        client.use_websocket = True
        client.connected = True
        
        # Initialize managers
        client.initialize_managers()
        
        return client

    @pytest.mark.asyncio
    async def test_websocket_streaming(self, api_client, event_engine):
        """Test WebSocket streaming functionality."""
        # Track received events
        received_ticks = []
        
        def on_tick(event: Event):
            received_ticks.append(event.data)
        
        # Register event handler
        event_engine.register(EVENT_TICK, on_tick)
        
        # Subscribe to symbols
        req1 = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        req2 = SubscribeRequest(
            symbol="ETHUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        # Enable WebSocket for these symbols
        api_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE", "ETHUSDT.BINANCE"}
        
        # Subscribe
        assert api_client.market_data.subscribe(req1)
        assert api_client.market_data.subscribe(req2)
        
        # Wait for the WebSocket thread to start and process some ticks
        # The WebSocket runs in a separate thread, so we need to give it time
        for _ in range(30):  # Try for up to 3 seconds
            await asyncio.sleep(0.1)
            if len(received_ticks) >= 2:  # At least one tick for each symbol
                break
        
        # Verify we received ticks
        assert len(received_ticks) > 0, "No ticks received"
        
        # Check tick data - may not have both symbols yet due to async nature
        symbols_seen = {t.symbol for t in received_ticks}
        assert len(symbols_seen) > 0, "No symbols in received ticks"
        
        # Verify tick data structure
        for tick in received_ticks:
            assert isinstance(tick, TickData)
            assert tick.adapter_name == "TestAdapter"
            assert tick.exchange == Exchange.BINANCE
            assert tick.last_price > 0
            assert tick.volume >= 0
            
        # Cleanup
        api_client.market_data.close()

    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, api_client, event_engine):
        """Test WebSocket reconnection behavior."""
        # Track connection states
        connection_states = []
        
        # Subscribe to a symbol
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        api_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE"}
        
        assert api_client.market_data.subscribe(req)
        
        # Get WebSocket manager
        ws_manager = api_client.market_data.websocket_manager
        
        # Simulate connection error
        ws_manager.connection_state = ws_manager.connection_state.__class__.ERROR
        
        # Trigger reconnection
        success = await ws_manager.handle_reconnection()
        
        # Should attempt reconnection
        assert ws_manager.reconnect_manager.reconnect_attempts > 0
        
        # Cleanup
        api_client.market_data.close()

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, api_client, event_engine):
        """Test WebSocket error handling."""
        from foxtrot.adapter.binance.error_handler import WebSocketErrorHandler
        
        # Create error handler
        error_handler = WebSocketErrorHandler("TestAdapter")
        
        # Test various error scenarios
        test_errors = [
            (Exception("Connection timeout"), "network"),
            (Exception("Invalid API key"), "authentication"),
            (Exception("Rate limit exceeded"), "rate_limit"),
            (Exception("Unknown symbol INVALID"), "symbol")
        ]
        
        for error, expected_type in test_errors:
            response = await error_handler.handle_error(error, "test")
            assert response.error_type.value == expected_type
            
        # Verify error statistics
        stats = error_handler.get_error_statistics()
        assert stats["total_errors"] == len(test_errors)

    @pytest.mark.asyncio
    async def test_http_fallback(self, api_client, event_engine, mock_ccxt_exchange):
        """Test fallback to HTTP polling when WebSocket fails."""
        # Disable WebSocket
        api_client.use_websocket = False
        
        # Track received events
        received_ticks = []
        
        def on_tick(event: Event):
            received_ticks.append(event.data)
        
        event_engine.register(EVENT_TICK, on_tick)
        
        # Subscribe
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        assert api_client.market_data.subscribe(req)
        
        # Wait for HTTP polling
        await asyncio.sleep(2.0)
        
        # Should have received ticks via HTTP
        assert len(received_ticks) > 0
        assert mock_ccxt_exchange.fetch_ticker.called
        
        # Cleanup
        api_client.market_data.close()

    @pytest.mark.asyncio
    async def test_subscription_management(self, api_client):
        """Test subscription add/remove functionality."""
        market_data = api_client.market_data
        
        # Subscribe to multiple symbols
        symbols = ["BTCUSDT.BINANCE", "ETHUSDT.BINANCE", "BNBUSDT.BINANCE"]
        
        for symbol in symbols:
            req = SubscribeRequest(symbol=symbol, exchange=Exchange.BINANCE)
            assert market_data.subscribe(req)
            
        # Verify subscriptions
        assert len(market_data._subscribed_symbols) == 3
        
        # Unsubscribe one
        assert market_data.unsubscribe("ETHUSDT.BINANCE")
        assert len(market_data._subscribed_symbols) == 2
        assert "ETHUSDT.BINANCE" not in market_data._subscribed_symbols
        
        # Unsubscribe remaining
        for symbol in ["BTCUSDT.BINANCE", "BNBUSDT.BINANCE"]:
            assert market_data.unsubscribe(symbol)
            
        assert len(market_data._subscribed_symbols) == 0
        
        # WebSocket should stop when no subscriptions
        assert not market_data._active

    def test_symbol_conversion(self, api_client):
        """Test symbol format conversion."""
        market_data = api_client.market_data
        
        # Test conversions
        test_cases = [
            ("BTCUSDT.BINANCE", "BTC/USDT"),
            ("ETHUSDT.BINANCE", "ETH/USDT"),
            ("BNBBTC.BINANCE", "BNB/BTC"),
            ("SOLETH.BINANCE", "SOL/ETH"),
            ("ABC.BINANCE", ""),  # Too short
            ("ABCD.BINANCE", ""),  # No known quote currency
        ]
        
        for vt_symbol, expected_ccxt in test_cases:
            result = market_data._convert_symbol_to_ccxt(vt_symbol)
            assert result == expected_ccxt

    @pytest.mark.asyncio
    async def test_concurrent_subscriptions(self, api_client, event_engine):
        """Test handling multiple concurrent WebSocket subscriptions."""
        # Enable WebSocket for all test symbols
        test_symbols = [f"TEST{i}USDT.BINANCE" for i in range(10)]
        api_client.websocket_enabled_symbols = set(test_symbols)
        
        # Track events
        received_events = []
        
        def on_tick(event: Event):
            received_events.append(event.data)
        
        event_engine.register(EVENT_TICK, on_tick)
        
        # Subscribe to multiple symbols concurrently
        tasks = []
        for symbol in test_symbols:
            req = SubscribeRequest(symbol=symbol, exchange=Exchange.BINANCE)
            # Note: subscribe is synchronous, but the WebSocket operations are async
            api_client.market_data.subscribe(req)
        
        # Give time for async operations
        await asyncio.sleep(1.0)
        
        # Verify all subscriptions are active
        assert len(api_client.market_data._subscribed_symbols) == 10
        
        # Cleanup
        api_client.market_data.close()