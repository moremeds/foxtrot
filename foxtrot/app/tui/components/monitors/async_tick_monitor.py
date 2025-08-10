"""
Async Tick Monitor for TUI

Enhanced real-time market data display with non-blocking updates
and efficient batch processing.
"""

from datetime import datetime
from typing import Any, List, Optional, Dict
import asyncio

from textual.coordinate import Coordinate
from textual import work
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import TickData

from foxtrot.app.tui.utils.colors import get_color_manager
from foxtrot.app.tui.utils.formatters import TUIFormatter
from ...async_bridge import AsyncDataFetcher, AsyncEventHandler
from ..async_base_monitor import AsyncTUIDataMonitor


class AsyncTUITickMonitor(AsyncTUIDataMonitor):
    """
    Async TUI Tick Monitor for high-performance market data display.
    
    Key improvements:
    - Non-blocking WebSocket data processing
    - Efficient batch updates for multiple symbols
    - Throttled updates to prevent UI overload
    - Background data fetching
    - Real-time color coding without flicker
    """
    
    # Monitor configuration
    event_type = EVENT_TICK
    data_key = "vt_symbol"
    sorting = True
    
    # Performance tuning
    BATCH_SIZE = 20  # Process up to 20 ticks per batch
    UPDATE_INTERVAL = 0.05  # 50ms between UI updates
    THROTTLE_PER_SYMBOL = 0.1  # Max 10 updates per second per symbol
    
    # Column configuration (same as original)
    headers = {
        "symbol": {
            "display": "Symbol",
            "cell": "default",
            "update": False,
            "width": 12,
            "precision": 0,
        },
        "exchange": {
            "display": "Exchange",
            "cell": "enum",
            "update": False,
            "width": 8,
            "precision": 0,
        },
        "name": {"display": "Name", "cell": "default", "update": True, "width": 20, "precision": 0},
        "last_price": {
            "display": "Last",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4,
        },
        "volume": {
            "display": "Volume",
            "cell": "volume",
            "update": True,
            "width": 10,
            "precision": 0,
        },
        "bid_price_1": {
            "display": "Bid",
            "cell": "bid",
            "update": True,
            "width": 10,
            "precision": 4,
        },
        "ask_price_1": {
            "display": "Ask",
            "cell": "ask",
            "update": True,
            "width": 10,
            "precision": 4,
        },
        "datetime": {
            "display": "Time",
            "cell": "time",
            "update": True,
            "width": 12,
            "precision": 0,
        },
    }
    
    class TickSelected(Message):
        """Message sent when a tick is selected."""
        def __init__(self, tick_data: TickData) -> None:
            self.tick_data = tick_data
            super().__init__()
    
    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs):
        """Initialize the async tick monitor."""
        super().__init__(main_engine, event_engine, "Tick Monitor", **kwargs)
        
        # Performance tracking
        self.price_history: Dict[str, List[float]] = {}
        self.last_prices: Dict[str, float] = {}
        self.update_timestamps: Dict[str, float] = {}
        
        # Data fetcher for async operations
        self.data_fetcher = AsyncDataFetcher(main_engine)
        
        # Subscribed symbols
        self.subscribed_symbols: set = set()
    
    async def on_mount(self) -> None:
        """Enhanced mount with async initialization."""
        await super().on_mount()
        
        # Start background tasks
        self.async_bridge.create_background_task(
            self._monitor_stale_data(),
            name="stale_data_monitor"
        )
        
        # Subscribe to tick events
        if self.event_adapter:
            self.event_adapter.register(EVENT_TICK, self._on_tick_event, self)
    
    @AsyncEventHandler.async_handler(timeout=1.0)
    async def _on_tick_event(self, event: Any) -> None:
        """
        Handle tick events asynchronously.
        
        Args:
            event: The tick event
        """
        if hasattr(event, 'data') and isinstance(event.data, TickData):
            await self.process_event(event)
    
    async def _apply_batch_updates(self, batch: List[Any]) -> None:
        """
        Apply batch tick updates with price change detection.
        
        Args:
            batch: List of tick events
        """
        # Group by symbol for efficient processing
        ticks_by_symbol: Dict[str, TickData] = {}
        
        for event in batch:
            if hasattr(event, 'data') and isinstance(event.data, TickData):
                tick = event.data
                symbol = tick.vt_symbol
                
                # Keep only the latest tick per symbol in this batch
                ticks_by_symbol[symbol] = tick
        
        # Process each symbol's latest tick
        for symbol, tick in ticks_by_symbol.items():
            # Check throttling
            if self._should_throttle(symbol):
                continue
            
            # Track price changes for color coding
            self._track_price_change(tick)
            
            # Update the row
            await self._process_single_update(tick)
            
            # Update timestamp
            self.update_timestamps[symbol] = asyncio.get_event_loop().time()
    
    def _track_price_change(self, tick: TickData) -> None:
        """
        Track price changes for color coding.
        
        Args:
            tick: The tick data
        """
        symbol = tick.vt_symbol
        current_price = tick.last_price
        
        # Store price history
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append(current_price)
        
        # Keep only last 10 prices
        if len(self.price_history[symbol]) > 10:
            self.price_history[symbol].pop(0)
        
        # Store last price for comparison
        self.last_prices[symbol] = current_price
    
    async def _apply_row_styling(self, row_index: int, data: TickData) -> None:
        """
        Apply styling to a row based on price changes.
        
        Args:
            row_index: The row index
            data: The tick data
        """
        if not self.data_table:
            return
        
        symbol = data.vt_symbol
        color_manager = get_color_manager()
        
        # Determine price direction
        if symbol in self.price_history and len(self.price_history[symbol]) > 1:
            prev_price = self.price_history[symbol][-2]
            curr_price = self.price_history[symbol][-1]
            
            if curr_price > prev_price:
                # Price up - green
                style = color_manager.get_style("success")
            elif curr_price < prev_price:
                # Price down - red
                style = color_manager.get_style("danger")
            else:
                # No change - default
                style = color_manager.get_style("default")
        else:
            style = color_manager.get_style("default")
        
        # Apply style to price columns
        price_columns = ["last_price", "bid_price_1", "ask_price_1"]
        for col_name in price_columns:
            if col_name in self.headers:
                col_index = list(self.headers.keys()).index(col_name)
                coord = Coordinate(row_index, col_index)
                
                # Apply style without causing flicker
                try:
                    self.data_table.update_cell_at(coord, style=style, update=False)
                except Exception:
                    pass  # Ignore styling errors
    
    async def _monitor_stale_data(self) -> None:
        """
        Monitor for stale data and mark accordingly.
        
        Runs in background to check for symbols that haven't updated recently.
        """
        stale_threshold = 5.0  # 5 seconds
        
        while True:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                now = asyncio.get_event_loop().time()
                
                for symbol, last_update in self.update_timestamps.items():
                    if now - last_update > stale_threshold:
                        # Mark as stale
                        await self._mark_symbol_stale(symbol)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Stale data monitor error: {e}")
    
    async def _mark_symbol_stale(self, symbol: str) -> None:
        """
        Mark a symbol as having stale data.
        
        Args:
            symbol: The symbol to mark as stale
        """
        # Find the row for this symbol
        if symbol in self.cells:
            row_index = self._find_row_by_key(symbol)
            if row_index is not None and self.data_table:
                # Apply stale styling (grayed out)
                color_manager = get_color_manager()
                style = color_manager.get_style("muted")
                
                # Apply to entire row
                for col_index in range(len(self.headers)):
                    coord = Coordinate(row_index, col_index)
                    try:
                        self.data_table.update_cell_at(coord, style=style, update=False)
                    except Exception:
                        pass
    
    @work(exclusive=True)
    async def subscribe_symbol(self, symbol: str) -> None:
        """
        Subscribe to a symbol's tick data.
        
        Args:
            symbol: The symbol to subscribe to
        """
        if symbol not in self.subscribed_symbols:
            # Subscribe via backend
            req = self._create_subscribe_request(symbol)
            if req:
                await self.async_bridge.run_in_thread(
                    self.main_engine.subscribe, req
                )
                self.subscribed_symbols.add(symbol)
                self._logger.info(f"Subscribed to {symbol}")
    
    def _create_subscribe_request(self, symbol: str) -> Optional[Any]:
        """
        Create a subscribe request for a symbol.
        
        Args:
            symbol: The symbol to subscribe to
            
        Returns:
            Subscribe request or None
        """
        # This should be implemented based on your backend API
        # Example:
        # from foxtrot.util.request_objects import SubscribeRequest
        # return SubscribeRequest(symbol=symbol, exchange=exchange)
        return None
    
    async def cleanup(self) -> None:
        """Clean up resources on unmount."""
        # Unsubscribe from all symbols
        for symbol in self.subscribed_symbols:
            try:
                # Unsubscribe via backend
                pass  # Implement unsubscribe logic
            except Exception as e:
                self._logger.error(f"Failed to unsubscribe {symbol}: {e}")
        
        self.subscribed_symbols.clear()
        self.price_history.clear()
        self.last_prices.clear()
        self.update_timestamps.clear()
        
        await super().cleanup()


def create_async_tick_monitor(
    main_engine: MainEngine, 
    event_engine: EventEngine
) -> AsyncTUITickMonitor:
    """
    Factory function to create an async tick monitor.
    
    Args:
        main_engine: The main engine instance
        event_engine: The event engine instance
        
    Returns:
        Configured async tick monitor instance
    """
    return AsyncTUITickMonitor(main_engine, event_engine)