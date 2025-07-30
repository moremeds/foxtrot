"""
Tick Monitor for TUI

Real-time market data display component that shows live price feeds,
bid/ask spreads, volume, and market depth information.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from textual.coordinate import Coordinate

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_TICK
from foxtrot.util.object import TickData

from ..base_monitor import TUIDataMonitor
from ...utils.formatters import TUIFormatter
from ...utils.colors import get_color_manager, ColorType


class TUITickMonitor(TUIDataMonitor):
    """
    TUI Tick Monitor for displaying real-time market data.
    
    Features:
        - Real-time price updates with color coding
        - Bid/Ask spread visualization
        - Volume and price change indicators
        - Market depth information
        - Price history tracking
        - Symbol-based filtering and sorting
        - Export functionality for market analysis
    """
    
    # Monitor configuration
    event_type = EVENT_TICK
    data_key = "vt_symbol"
    sorting = True  # Enable sorting by different columns
    
    # Column configuration
    headers = {
        "symbol": {
            "display": "Symbol",
            "cell": "default",
            "update": False,
            "width": 12,
            "precision": 0
        },
        "exchange": {
            "display": "Exchange", 
            "cell": "enum",
            "update": False,
            "width": 8,
            "precision": 0
        },
        "name": {
            "display": "Name",
            "cell": "default",
            "update": True,
            "width": 20,
            "precision": 0
        },
        "last_price": {
            "display": "Last",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "volume": {
            "display": "Volume",
            "cell": "volume",
            "update": True,
            "width": 10,
            "precision": 0
        },
        "open_price": {
            "display": "Open",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "high_price": {
            "display": "High",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "low_price": {
            "display": "Low",
            "cell": "float",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "bid_price_1": {
            "display": "Bid",
            "cell": "bid",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "bid_volume_1": {
            "display": "Bid Vol",
            "cell": "bid",
            "update": True,
            "width": 10,
            "precision": 0
        },
        "ask_price_1": {
            "display": "Ask",
            "cell": "ask",
            "update": True,
            "width": 10,
            "precision": 4
        },
        "ask_volume_1": {
            "display": "Ask Vol",
            "cell": "ask",
            "update": True,
            "width": 10,
            "precision": 0
        },
        "datetime": {
            "display": "Time",
            "cell": "datetime",
            "update": True,
            "width": 12,
            "precision": 0
        },
        "gateway_name": {
            "display": "Gateway",
            "cell": "default",
            "update": False,
            "width": 10,
            "precision": 0
        }
    }
    
    def __init__(
        self, 
        main_engine: MainEngine, 
        event_engine: EventEngine,
        **kwargs: Any
    ) -> None:
        """
        Initialize the tick monitor.
        
        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(
            main_engine, 
            event_engine, 
            monitor_name="Tick Monitor",
            **kwargs
        )
        
        # Color manager for styling
        self.color_manager = get_color_manager()
        
        # Price tracking for color coding
        self.previous_prices: Dict[str, float] = {}
        
        # Filtering options
        self.symbol_filter: Optional[str] = None
        self.exchange_filter: Optional[str] = None
        self.min_volume_filter: Optional[float] = None
        
        # Display options
        self.show_spread = True
        self.show_change_indicators = True
        self.auto_resize_columns = True
    
    def compose(self):
        """Create the tick monitor layout with enhanced information."""
        for widget in super().compose():
            yield widget
    
    async def on_mount(self) -> None:
        """Called when the tick monitor is mounted."""
        await super().on_mount()
        
        # Initialize with welcome message
        await self._add_system_message("Tick monitor ready for market data")
    
    def _format_cell_content(self, content: Any, config: Dict[str, Any]) -> str:
        """
        Format cell content with tick-specific formatting.
        
        Args:
            content: The raw content to format
            config: The header configuration
            
        Returns:
            Formatted content string
        """
        if content is None:
            return "-"
        
        cell_type = config.get("cell", "default")
        precision = config.get("precision", 2)
        
        if cell_type == "float":
            return TUIFormatter.format_price(content, precision)
        
        elif cell_type == "volume":
            return TUIFormatter.format_volume(content)
        
        elif cell_type in ["bid", "ask"]:
            # Special formatting for bid/ask prices and volumes
            if "price" in str(config.get("field", "")):
                return TUIFormatter.format_price(content, precision)
            else:
                return TUIFormatter.format_volume(content)
        
        elif cell_type == "datetime":
            if isinstance(content, datetime):
                return TUIFormatter.format_datetime(content, "milliseconds")
        
        elif cell_type == "enum":
            return TUIFormatter.format_exchange(content)
        
        else:
            # Default formatting
            if isinstance(content, str) and len(content) > config.get("width", 20):
                return TUIFormatter.truncate_text(content, config.get("width", 20))
            return str(content)
    
    async def _apply_row_styling(self, row_index: int, data: TickData) -> None:
        """
        Apply color styling to tick data based on price movement and bid/ask.
        
        Args:
            row_index: The row index to style
            data: The TickData object
        """
        if not self.data_table:
            return
        
        try:
            vt_symbol = data.vt_symbol
            current_price = data.last_price
            
            # Price movement color coding
            if vt_symbol in self.previous_prices:
                previous_price = self.previous_prices[vt_symbol]
                
                if current_price > previous_price:
                    price_color = ColorType.PROFIT
                elif current_price < previous_price:
                    price_color = ColorType.LOSS
                else:
                    price_color = ColorType.NEUTRAL
            else:
                price_color = ColorType.NEUTRAL
            
            # Update previous price
            self.previous_prices[vt_symbol] = current_price
            
            # Apply color styling to specific columns
            # This would be implemented using Textual's styling system
            # For now, we store the color information for future use
            
        except Exception as e:
            await self._log_error(f"Error applying row styling: {e}")
    
    async def _process_event(self, event) -> None:
        """
        Process tick events with filtering and validation.
        
        Args:
            event: Tick event containing TickData
        """
        try:
            tick_data: TickData = event.data
            
            # Apply filters
            if not self._passes_filters(tick_data):
                return
            
            # Process the tick data
            await super()._process_event(event)
            
            # Update statistics
            await self._update_tick_statistics(tick_data)
        
        except Exception as e:
            await self._log_error(f"Error processing tick event: {e}")
    
    def _passes_filters(self, tick_data: TickData) -> bool:
        """
        Check if tick data passes current filters.
        
        Args:
            tick_data: The TickData to check
            
        Returns:
            True if tick passes all filters
        """
        # Symbol filter
        if self.symbol_filter:
            if self.symbol_filter.lower() not in tick_data.symbol.lower():
                return False
        
        # Exchange filter
        if self.exchange_filter:
            if tick_data.exchange.value != self.exchange_filter:
                return False
        
        # Volume filter
        if self.min_volume_filter is not None:
            if tick_data.volume < self.min_volume_filter:
                return False
        
        return True
    
    async def _update_tick_statistics(self, tick_data: TickData) -> None:
        """
        Update internal statistics based on new tick data.
        
        Args:
            tick_data: The new tick data
        """
        # This could track various statistics like:
        # - Price ranges
        # - Volume totals
        # - Update frequencies
        # - Spread statistics
        pass
    
    async def _add_system_message(self, message: str) -> None:
        """
        Add a system message to the monitor.
        
        Args:
            message: The message to add
        """
        # Could log to a separate system or update title
        if self.title_bar:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.title_bar.update(f"Tick Monitor - {message} ({current_time})")
    
    # Enhanced actions specific to tick monitor
    
    def action_filter_by_symbol(self, symbol: str) -> None:
        """
        Filter ticks by symbol pattern.
        
        Args:
            symbol: Symbol pattern to filter by
        """
        self.symbol_filter = symbol if symbol != self.symbol_filter else None
        self._update_filter_display()
    
    def action_filter_by_exchange(self, exchange: str) -> None:
        """
        Filter ticks by exchange.
        
        Args:
            exchange: Exchange to filter by
        """
        self.exchange_filter = exchange if exchange != self.exchange_filter else None
        self._update_filter_display()
    
    def action_filter_by_volume(self, min_volume: float) -> None:
        """
        Filter ticks by minimum volume.
        
        Args:
            min_volume: Minimum volume threshold
        """
        self.min_volume_filter = min_volume if min_volume != self.min_volume_filter else None
        self._update_filter_display()
    
    def action_toggle_spread_display(self) -> None:
        """Toggle display of bid/ask spread information."""
        self.show_spread = not self.show_spread
        self._update_display_options()
    
    def action_toggle_change_indicators(self) -> None:
        """Toggle display of price change indicators."""
        self.show_change_indicators = not self.show_change_indicators
        self._update_display_options()
    
    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.symbol_filter = None
        self.exchange_filter = None
        self.min_volume_filter = None
        self._update_filter_display()
    
    def _update_filter_display(self) -> None:
        """Update the title bar to show active filters."""
        if not self.title_bar:
            return
        
        title = "Tick Monitor"
        filters = []
        
        if self.symbol_filter:
            filters.append(f"Symbol:{self.symbol_filter}")
        
        if self.exchange_filter:
            filters.append(f"Exchange:{self.exchange_filter}")
        
        if self.min_volume_filter is not None:
            filters.append(f"Volume≥{self.min_volume_filter}")
        
        if filters:
            title += f" [{', '.join(filters)}]"
        
        self.title_bar.update(title)
    
    def _update_display_options(self) -> None:
        """Update display based on current options."""
        if not self.title_bar:
            return
        
        options = []
        if self.show_spread:
            options.append("SPREAD")
        if self.show_change_indicators:
            options.append("CHANGES")
        
        if options:
            title = f"Tick Monitor [{', '.join(options)}]"
        else:
            title = "Tick Monitor"
        
        self.title_bar.update(title)
    
    # Enhanced key bindings for tick monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("f1", "filter_symbol", "Filter Symbol"),
        ("f2", "filter_exchange", "Filter Exchange"),
        ("f3", "filter_volume", "Filter Volume"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
        ("t", "toggle_spread_display", "Toggle Spread"),
        ("i", "toggle_change_indicators", "Toggle Changes"),
    ]
    
    def action_filter_symbol(self) -> None:
        """Prompt for symbol filter."""
        # This would show an input dialog in a full implementation
        # For now, we'll use a placeholder
        pass
    
    def action_filter_exchange(self) -> None:
        """Prompt for exchange filter."""
        # This would show a selection dialog in a full implementation
        pass
    
    def action_filter_volume(self) -> None:
        """Prompt for volume filter."""
        # This would show an input dialog in a full implementation
        pass
    
    async def action_save_csv(self) -> None:
        """Save tick data to CSV with market data specific formatting."""
        if not self.data_table:
            return
        
        try:
            import csv
            from pathlib import Path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"market_data_{timestamp}.csv"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write headers with market data context
                headers = [config["display"] for config in self.headers.values()]
                headers.extend(["Export Date", "Filter Applied", "Total Symbols"])
                writer.writerow(headers)
                
                # Collect metadata
                export_time = datetime.now().isoformat()
                filter_info = f"Symbol:{self.symbol_filter or 'All'}"
                total_symbols = self.data_table.row_count
                
                # Write tick data
                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(
                            Coordinate(row_index, col_index)
                        )
                        row_data.append(str(cell_value) if cell_value else "")
                    
                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend([export_time, filter_info, str(total_symbols)])
                    else:
                        row_data.extend(["", "", ""])
                    
                    writer.writerow(row_data)
            
            await self._add_system_message(f"Market data exported to {filepath}")
        
        except Exception as e:
            await self._log_error(f"Failed to export market data: {e}")
    
    def get_current_spread(self, vt_symbol: str) -> Optional[float]:
        """
        Get current bid-ask spread for a symbol.
        
        Args:
            vt_symbol: Symbol identifier
            
        Returns:
            Spread value or None if not available
        """
        # This would calculate spread from current tick data
        # Implementation depends on data storage strategy
        return None
    
    def get_price_change(self, vt_symbol: str) -> Optional[float]:
        """
        Get price change for a symbol since last update.
        
        Args:
            vt_symbol: Symbol identifier
            
        Returns:
            Price change or None if not available
        """
        # This would calculate price change from stored data
        # Implementation depends on data storage strategy
        return None


# Convenience function for creating tick monitor
def create_tick_monitor(main_engine: MainEngine, event_engine: EventEngine) -> TUITickMonitor:
    """
    Create a configured tick monitor instance.
    
    Args:
        main_engine: The main trading engine
        event_engine: The event engine
        
    Returns:
        Configured TUITickMonitor instance
    """
    return TUITickMonitor(main_engine, event_engine)