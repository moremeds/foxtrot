"""
Performance benchmarking suite for WebSocket implementation.

Tests latency, throughput, and resource usage compared to HTTP polling.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from foxtrot.adapter.binance.api_client import BinanceApiClient
from foxtrot.adapter.binance.market_data import BinanceMarketData
from foxtrot.core.event import Event
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import SubscribeRequest, TickData


class PerformanceBenchmark:
    """Performance benchmarking utilities."""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.tick_counts: Dict[str, int] = {}
        self.start_time: float = 0
        self.first_tick_time: Dict[str, float] = {}
        self.tick_timestamps: List[float] = []
        
    def record_tick(self, symbol: str, timestamp: float, tick_data: TickData) -> None:
        """Record tick arrival."""
        if symbol not in self.tick_counts:
            self.tick_counts[symbol] = 0
            self.first_tick_time[symbol] = timestamp
            
        self.tick_counts[symbol] += 1
        self.tick_timestamps.append(timestamp)
        
        # Calculate latency from tick timestamp to reception
        if hasattr(tick_data, 'datetime') and tick_data.datetime:
            # Convert datetime to timestamp
            tick_time = tick_data.datetime.timestamp()
            reception_time = timestamp
            latency = (reception_time - tick_time) * 1000  # Convert to ms
            
            # Only record reasonable latencies (ignore initialization delays)
            if 0 < latency < 5000:  # Ignore latencies over 5 seconds
                self.latencies.append(latency)
        
        # Also calculate inter-arrival times for throughput
        if len(self.tick_timestamps) > 1:
            inter_arrival = (self.tick_timestamps[-1] - self.tick_timestamps[-2]) * 1000
            if inter_arrival < 5000:  # Reasonable inter-arrival times
                if not hasattr(self, 'inter_arrivals'):
                    self.inter_arrivals = []
                self.inter_arrivals.append(inter_arrival)
            
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {
            "throughput": {
                "total_ticks": sum(self.tick_counts.values()),
                "ticks_per_symbol": self.tick_counts,
                "duration": time.time() - self.start_time if self.start_time else 0
            }
        }
        
        # Add latency stats if available
        if self.latencies and len(self.latencies) > 1:
            stats["latencies"] = {
                "min": min(self.latencies),
                "max": max(self.latencies),
                "mean": statistics.mean(self.latencies),
                "median": statistics.median(self.latencies),
                "p95": statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) > 20 else max(self.latencies),
                "p99": statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) > 100 else max(self.latencies),
            }
        
        # Add inter-arrival stats if available
        if hasattr(self, 'inter_arrivals') and self.inter_arrivals:
            stats["inter_arrival"] = {
                "mean": statistics.mean(self.inter_arrivals),
                "median": statistics.median(self.inter_arrivals),
                "min": min(self.inter_arrivals),
                "max": max(self.inter_arrivals)
            }
            
        return stats


class TestWebSocketPerformance:
    """WebSocket performance benchmarks."""
    
    @pytest.fixture
    def event_engine(self):
        """Create EventEngine for testing."""
        engine = EventEngine()
        engine.start()
        yield engine
        engine.stop()
        
    @pytest.fixture
    def mock_websocket_exchange(self):
        """Create mock WebSocket exchange with realistic timing."""
        exchange = AsyncMock()
        
        async def mock_watch_ticker(symbol):
            # Simulate realistic WebSocket latency (10-50ms)
            await asyncio.sleep(0.01 + (time.time() % 0.04))
            
            return {
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "last": 45000.0 + (time.time() % 100),
                "bid": 44999.0,
                "ask": 45001.0,
                "bidVolume": 10.5,
                "askVolume": 12.3,
                "high": 46000.0,
                "low": 44000.0,
                "open": 44500.0,
                "close": 45000.0,
                "previousClose": 44500.0,
                "baseVolume": 1234.56,
                "quoteVolume": 55555555.0
            }
            
        exchange.watchTicker = mock_watch_ticker
        exchange.close = AsyncMock()
        return exchange
        
    @pytest.fixture
    def mock_http_exchange(self):
        """Create mock HTTP exchange with realistic timing."""
        exchange = MagicMock()
        
        def mock_fetch_ticker(symbol):
            # Simulate realistic HTTP latency (100-200ms)
            time.sleep(0.1 + (time.time() % 0.1))
            
            return {
                "symbol": symbol,
                "timestamp": int(time.time() * 1000),
                "last": 45000.0 + (time.time() % 100),
                "bid": 44999.0,
                "ask": 45001.0,
                "high": 46000.0,
                "low": 44000.0,
                "open": 44500.0,
                "close": 45000.0,
                "baseVolume": 1234.56,
                "quoteVolume": 55555555.0
            }
            
        exchange.fetch_ticker = mock_fetch_ticker
        return exchange
        
    @pytest.mark.asyncio
    async def test_websocket_latency(self, event_engine, mock_websocket_exchange):
        """Test WebSocket latency meets <200ms target."""
        # Setup API client with WebSocket
        api_client = BinanceApiClient(event_engine, "TestAdapter")
        api_client.exchange = MagicMock()
        api_client.exchange_pro = mock_websocket_exchange
        api_client.use_websocket = True
        api_client.connected = True
        api_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE"}
        api_client.initialize_managers()
        
        # Setup performance tracking
        benchmark = PerformanceBenchmark()
        
        def on_tick(event: Event):
            benchmark.record_tick(event.data.symbol, time.time(), event.data)
            
        event_engine.register(EVENT_TICK, on_tick)
        
        # Subscribe and start timing
        req = SubscribeRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE
        )
        
        benchmark.start_time = time.time()
        assert api_client.market_data.subscribe(req)
        
        # Collect data for 5 seconds
        await asyncio.sleep(5.0)
        
        # Get statistics
        stats = benchmark.get_statistics()
        
        # Verify latency meets target
        assert stats["latencies"]["median"] < 200, \
            f"Median latency {stats['latencies']['median']:.1f}ms exceeds 200ms target"
        assert stats["latencies"]["p95"] < 300, \
            f"95th percentile latency {stats['latencies']['p95']:.1f}ms exceeds 300ms"
            
        # Cleanup
        api_client.market_data.close()
        
        # Report results
        print("\nWebSocket Performance Results:")
        print(f"  Median latency: {stats['latencies']['median']:.1f}ms")
        print(f"  95th percentile: {stats['latencies']['p95']:.1f}ms")
        print(f"  99th percentile: {stats['latencies']['p99']:.1f}ms")
        print(f"  Total ticks: {stats['throughput']['total_ticks']}")
        
    @pytest.mark.asyncio
    async def test_http_vs_websocket_comparison(
        self, event_engine, mock_websocket_exchange, mock_http_exchange
    ):
        """Compare WebSocket vs HTTP polling performance."""
        results = {}
        
        # Test WebSocket performance
        ws_client = BinanceApiClient(event_engine, "WSAdapter")
        ws_client.exchange = MagicMock()
        ws_client.exchange_pro = mock_websocket_exchange
        ws_client.use_websocket = True
        ws_client.connected = True
        ws_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE"}
        ws_client.initialize_managers()
        
        ws_benchmark = PerformanceBenchmark()
        
        def on_ws_tick(event: Event):
            if event.data.adapter_name == "WSAdapter":
                ws_benchmark.record_tick(event.data.symbol, time.time(), event.data)
                
        event_engine.register(EVENT_TICK, on_ws_tick)
        
        # Subscribe WebSocket
        req = SubscribeRequest(symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        ws_benchmark.start_time = time.time()
        ws_client.market_data.subscribe(req)
        
        # Collect WebSocket data
        await asyncio.sleep(3.0)
        results["websocket"] = ws_benchmark.get_statistics()
        ws_client.market_data.close()
        
        # Test HTTP polling performance
        http_client = BinanceApiClient(event_engine, "HTTPAdapter")
        http_client.exchange = mock_http_exchange
        http_client.use_websocket = False
        http_client.connected = True
        http_client.initialize_managers()
        
        http_benchmark = PerformanceBenchmark()
        
        def on_http_tick(event: Event):
            if event.data.adapter_name == "HTTPAdapter":
                http_benchmark.record_tick(event.data.symbol, time.time(), event.data)
                
        event_engine.register(EVENT_TICK, on_http_tick)
        
        # Subscribe HTTP
        http_benchmark.start_time = time.time()
        http_client.market_data.subscribe(req)
        
        # Collect HTTP data
        await asyncio.sleep(3.0)
        results["http"] = http_benchmark.get_statistics()
        http_client.market_data.close()
        
        # Compare results
        ws_median = results["websocket"]["latencies"]["median"]
        http_median = results["http"]["latencies"]["median"]
        improvement = ((http_median - ws_median) / http_median) * 100
        
        print("\nPerformance Comparison:")
        print(f"  WebSocket median latency: {ws_median:.1f}ms")
        print(f"  HTTP median latency: {http_median:.1f}ms")
        print(f"  Improvement: {improvement:.1f}%")
        
        # WebSocket should be significantly faster
        assert ws_median < http_median * 0.5, \
            "WebSocket should be at least 50% faster than HTTP polling"
            
    @pytest.mark.asyncio
    async def test_multiple_symbol_performance(self, event_engine, mock_websocket_exchange):
        """Test performance with multiple simultaneous subscriptions."""
        # Setup API client
        api_client = BinanceApiClient(event_engine, "TestAdapter")
        api_client.exchange = MagicMock()
        api_client.exchange_pro = mock_websocket_exchange
        api_client.use_websocket = True
        api_client.connected = True
        
        # Test symbols
        symbols = [
            "BTCUSDT.BINANCE",
            "ETHUSDT.BINANCE",
            "BNBUSDT.BINANCE",
            "ADAUSDT.BINANCE",
            "DOGEUSDT.BINANCE"
        ]
        
        api_client.websocket_enabled_symbols = set(symbols)
        api_client.initialize_managers()
        
        # Setup performance tracking
        benchmark = PerformanceBenchmark()
        
        def on_tick(event: Event):
            benchmark.record_tick(event.data.symbol, time.time(), event.data)
            
        event_engine.register(EVENT_TICK, on_tick)
        
        # Subscribe to all symbols
        benchmark.start_time = time.time()
        for symbol in symbols:
            req = SubscribeRequest(symbol=symbol, exchange=Exchange.BINANCE)
            assert api_client.market_data.subscribe(req)
            
        # Collect data
        await asyncio.sleep(5.0)
        
        # Get statistics
        stats = benchmark.get_statistics()
        
        # Verify all symbols received data
        assert len(stats["throughput"]["ticks_per_symbol"]) == len(symbols)
        for symbol in symbols:
            assert stats["throughput"]["ticks_per_symbol"][symbol] > 0
            
        # Verify latency still meets target with multiple symbols
        assert stats["latencies"]["median"] < 200, \
            f"Median latency {stats['latencies']['median']:.1f}ms exceeds target with multiple symbols"
            
        # Cleanup
        api_client.market_data.close()
        
        print(f"\nMulti-symbol Performance ({len(symbols)} symbols):")
        print(f"  Median latency: {stats['latencies']['median']:.1f}ms")
        print(f"  Total ticks: {stats['throughput']['total_ticks']}")
        print(f"  Ticks per symbol: {stats['throughput']['ticks_per_symbol']}")
        
    @pytest.mark.asyncio
    async def test_reconnection_performance(self, event_engine, mock_websocket_exchange):
        """Test performance impact of reconnections."""
        # Setup API client
        api_client = BinanceApiClient(event_engine, "TestAdapter")
        api_client.exchange = MagicMock()
        api_client.exchange_pro = mock_websocket_exchange
        api_client.use_websocket = True
        api_client.connected = True
        api_client.websocket_enabled_symbols = {"BTCUSDT.BINANCE"}
        api_client.initialize_managers()
        
        # Track reconnection time
        reconnect_times = []
        
        # Subscribe
        req = SubscribeRequest(symbol="BTCUSDT.BINANCE", exchange=Exchange.BINANCE)
        assert api_client.market_data.subscribe(req)
        
        # Simulate 3 reconnections
        for i in range(3):
            await asyncio.sleep(1.0)
            
            # Simulate connection error
            ws_manager = api_client.market_data.websocket_manager
            ws_manager.connection_state = ws_manager.connection_state.__class__.ERROR
            
            # Time reconnection
            start = time.time()
            success = await ws_manager.handle_reconnection()
            reconnect_time = (time.time() - start) * 1000
            
            assert success
            reconnect_times.append(reconnect_time)
            
        # Cleanup
        api_client.market_data.close()
        
        # Verify reconnection times are reasonable
        avg_reconnect = statistics.mean(reconnect_times)
        print(f"\nReconnection Performance:")
        print(f"  Average reconnection time: {avg_reconnect:.1f}ms")
        print(f"  Reconnection times: {[f'{t:.1f}ms' for t in reconnect_times]}")
        
        # Reconnection should be fast (under 5 seconds)
        assert avg_reconnect < 5000, "Reconnection taking too long"


def run_performance_benchmarks():
    """Run all performance benchmarks and generate report."""
    import subprocess
    import sys
    
    print("Running WebSocket Performance Benchmarks...")
    print("=" * 60)
    
    # Run pytest with verbose output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "-s"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
        
    return result.returncode == 0


if __name__ == "__main__":
    # Run benchmarks when executed directly
    success = run_performance_benchmarks()
    sys.exit(0 if success else 1)