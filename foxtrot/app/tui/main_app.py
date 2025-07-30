"""
Main TUI Application for Foxtrot Trading Platform

This module implements the primary Text User Interface using Textual framework,
providing the same functionality as the Qt GUI but optimized for terminal usage.
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Button
from textual.binding import Binding
from textual.screen import Screen

import foxtrot
from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.utility import TRADER_DIR

from .config.settings import TUISettings
from .integration.event_adapter import EventEngineAdapter
from .components.monitors.tick_monitor import create_tick_monitor
from .components.monitors.order_monitor import create_order_monitor
from .components.monitors.trade_monitor import create_trade_monitor
from .components.monitors.position_monitor import create_position_monitor
from .components.monitors.account_monitor import create_account_monitor
from .components.monitors.log_monitor import TUILogMonitor


class FoxtrotTUIApp(App[None]):
    """
    Main TUI Application for Foxtrot Trading Platform.
    
    Replicates the functionality of the Qt MainWindow but optimized for terminal usage.
    Maintains the same event-driven architecture while providing a keyboard-friendly interface.
    """
    
    # Textual CSS for styling
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-gutter: 1;
    }
    
    .trading-panel {
        column-span: 1;
        row-span: 3;
        border: solid $primary;
        padding: 1;
    }
    
    .monitor-panel {
        border: solid $accent;
        padding: 1;
    }
    
    .top-monitors {
        column-span: 2;
        row-span: 2;
    }
    
    .bottom-monitors {
        column-span: 2;
        row-span: 1;
    }
    
    .status-bar {
        background: $primary;
        color: $text;
        height: 1;
    }
    
    .title-bar {
        background: $accent;
        color: $text;
        height: 1;
    }
    """
    
    # Global key bindings
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+c", "cancel_all_orders", "Cancel All", priority=True),
        Binding("f1", "show_help", "Help"),
        Binding("f2", "show_contracts", "Contracts"),
        Binding("f3", "show_settings", "Settings"),
        Binding("f4", "show_connect", "Connect"),
        Binding("tab", "cycle_focus", "Cycle Focus"),
        Binding("shift+tab", "cycle_focus_reverse", "Cycle Focus Reverse"),
    ]

    def __init__(
        self, 
        main_engine: MainEngine, 
        event_engine: EventEngine,
        **kwargs: Any
    ) -> None:
        """
        Initialize the TUI application.
        
        Args:
            main_engine: The main trading engine
            event_engine: The event engine for handling events
            **kwargs: Additional arguments passed to App
        """
        super().__init__(**kwargs)
        
        self.main_engine = main_engine
        self.event_engine = event_engine
        
        # Initialize TUI-specific components
        self.settings = TUISettings()
        self.event_adapter: Optional[EventEngineAdapter] = None
        
        # Monitor components
        self.tick_monitor = create_tick_monitor(main_engine, event_engine)
        self.order_monitor = create_order_monitor(main_engine, event_engine)
        self.trade_monitor = create_trade_monitor(main_engine, event_engine)
        self.position_monitor = create_position_monitor(main_engine, event_engine)
        self.account_monitor = create_account_monitor(main_engine, event_engine)
        self.log_monitor = TUILogMonitor(main_engine, event_engine)
        
        # Widget containers
        self.monitors: Dict[str, Any] = {
            "tick": self.tick_monitor,
            "order": self.order_monitor,
            "trade": self.trade_monitor,
            "position": self.position_monitor,
            "account": self.account_monitor,
            "log": self.log_monitor,
        }
        self.dialogs: Dict[str, Any] = {}
        
        # Application state
        self.is_connected = False
        self.current_gateway = ""
        
        # Initialize title
        version = getattr(foxtrot, '__version__', '1.0.0')
        self.title = f"Foxtrot TUI v{version} - {TRADER_DIR}"
        self.sub_title = "Event-Driven Trading Platform"

    def compose(self) -> ComposeResult:
        """
        Create the initial layout of the TUI application.
        
        Yields:
            The widgets that make up the application layout
        """
        # Header with title and status
        yield Header(show_clock=True)
        
        # Main content area with grid layout
        with Container(id="main-content"):
            # Left panel - Trading interface
            with Container(classes="trading-panel", id="trading-panel"):
                yield Static("Trading Panel", classes="title-bar")
                yield Static("Symbol: [Not Selected]", id="trading-symbol")
                yield Static("Price: ---", id="trading-price")
                yield Static("Volume: ---", id="trading-volume")
                yield Button("Send Order", id="send-order", variant="primary")
                yield Button("Cancel All", id="cancel-all", variant="error")
            
            # Right side - Monitors (using actual monitor components)
            with Vertical(classes="top-monitors"):
                # Top right - Tick/Order monitors
                with Horizontal():
                    yield self.tick_monitor
                    yield self.order_monitor
                
                # Middle right - Trade/Position monitors
                with Horizontal():
                    yield self.trade_monitor
                    yield self.position_monitor
            
            # Bottom - Account and Log monitors
            with Horizontal(classes="bottom-monitors"):
                yield self.account_monitor
                yield self.log_monitor
        
        # Footer with status and hotkeys
        yield Footer()
    
    async def on_mount(self) -> None:
        """
        Called when the app is mounted. Initialize the event system integration.
        """
        # Initialize event adapter for thread-safe communication
        self.event_adapter = EventEngineAdapter(self.event_engine)
        
        # Start the event adapter with the current asyncio loop
        await self.event_adapter.start(asyncio.get_event_loop())
        
        # Initialize monitor components
        await self._initialize_monitors()
        
        # Load settings and apply configuration
        await self._load_settings()
        
        # Update status
        self._update_status("TUI Initialized - Ready to Connect")
    
    async def _initialize_monitors(self) -> None:
        """Initialize all monitor components with event handling."""
        try:
            # The monitors are already created in __init__, just ensure they're ready
            for monitor_name, monitor in self.monitors.items():
                if hasattr(monitor, 'on_mount'):
                    # The monitors will be mounted automatically by Textual
                    pass
            
            self._log_message("INFO", "All monitors initialized successfully")
        except Exception as e:
            self._log_message("ERROR", f"Failed to initialize monitors: {e}")
    
    async def _load_settings(self) -> None:
        """Load TUI-specific settings."""
        try:
            await self.settings.load()
            # Apply theme and layout settings
            if hasattr(self.settings, 'theme'):
                # Apply theme settings if available
                pass
        except Exception as e:
            self._update_status(f"Settings load warning: {e}")
    
    def _update_status(self, message: str) -> None:
        """Update the status message."""
        # This would typically update a status bar widget
        # For now, we'll use the log monitor
        self._log_message("INFO", message)
    
    def _log_message(self, level: str, message: str) -> None:
        """Add a message to the log monitor."""
        try:
            # Create a log data object to send to the log monitor
            from foxtrot.util.object import LogData
            from datetime import datetime
            
            log_data = LogData(
                msg=message,
                level=level,
                time=datetime.now(),
                gateway_name=self.current_gateway or "SYSTEM"
            )
            
            # Send log data to the log monitor
            if hasattr(self.log_monitor, '_process_log_data'):
                asyncio.create_task(self.log_monitor._process_log_data(log_data))
        except Exception:
            # If logging fails, print to console as fallback
            print(f"[{level}] {message}")
    
    # Action handlers for key bindings
    
    def action_quit(self) -> None:
        """Handle quit action."""
        self.exit()
    
    def action_cancel_all_orders(self) -> None:
        """Handle cancel all orders action."""
        try:
            # Cancel all orders through the main engine
            self.main_engine.cancel_all(None)  # None means all gateways
            self._log_message("INFO", "Cancel all orders requested")
        except Exception as e:
            self._log_message("ERROR", f"Failed to cancel orders: {e}")
    
    def action_show_help(self) -> None:
        """Show help dialog."""
        self._log_message("INFO", "Help: F1=Help, F2=Contracts, F3=Settings, F4=Connect, Ctrl+Q=Quit")
    
    def action_show_contracts(self) -> None:
        """Show contract manager dialog."""
        self._log_message("INFO", "Contract manager - Feature coming soon")
    
    def action_show_settings(self) -> None:
        """Show settings dialog."""
        self._log_message("INFO", "Settings dialog - Feature coming soon")
    
    def action_show_connect(self) -> None:
        """Show connection dialog."""
        self._log_message("INFO", "Connection dialog - Feature coming soon")
    
    def action_cycle_focus(self) -> None:
        """Cycle focus to next widget."""
        self.screen.focus_next()
    
    def action_cycle_focus_reverse(self) -> None:
        """Cycle focus to previous widget."""
        self.screen.focus_previous()
    
    # Button event handlers
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "send-order":
            await self._handle_send_order()
        elif button_id == "cancel-all":
            self.action_cancel_all_orders()
    
    async def _handle_send_order(self) -> None:
        """Handle send order button press."""
        self._log_message("INFO", "Send order - Feature implementation in progress")
        # TODO: Implement order sending logic
    
    # Monitor message handlers
    
    async def on_tick_selected(self, message) -> None:
        """Handle tick selection from tick monitor."""
        if hasattr(message, 'tick_data'):
            tick_data = message.tick_data
            await self._update_trading_from_tick(tick_data)
    
    async def on_position_selected(self, message) -> None:
        """Handle position selection from position monitor."""
        if hasattr(message, 'position_data'):
            position_data = message.position_data
            await self._update_trading_from_position(position_data)
    
    async def _update_trading_from_tick(self, tick_data) -> None:
        """Update trading panel from selected tick data."""
        try:
            # Update trading panel with tick information
            symbol_widget = self.query_one("#trading-symbol", Static)
            price_widget = self.query_one("#trading-price", Static)
            
            symbol_widget.update(f"Symbol: {tick_data.symbol}")
            price_widget.update(f"Price: {tick_data.last_price}")
            
            self._log_message("INFO", f"Updated trading panel with {tick_data.symbol}")
        except Exception as e:
            self._log_message("ERROR", f"Failed to update trading panel from tick: {e}")
    
    async def _update_trading_from_position(self, position_data) -> None:
        """Update trading panel from selected position data."""
        try:
            # Update trading panel with position information
            symbol_widget = self.query_one("#trading-symbol", Static)
            price_widget = self.query_one("#trading-price", Static)
            volume_widget = self.query_one("#trading-volume", Static)
            
            symbol_widget.update(f"Symbol: {position_data.symbol}")
            price_widget.update(f"Price: {position_data.price}")
            volume_widget.update(f"Volume: {position_data.volume}")
            
            self._log_message("INFO", f"Updated trading panel with {position_data.symbol} position")
        except Exception as e:
            self._log_message("ERROR", f"Failed to update trading panel from position: {e}")


def main() -> None:
    """
    Entry point for the TUI application.
    
    This function should be called when running the TUI version of Foxtrot.
    """
    import sys
    import asyncio
    from pathlib import Path
    
    try:
        # Import foxtrot components
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine
        from foxtrot.util.settings import SETTINGS
        
        print("Starting Foxtrot TUI...")
        print("=" * 50)
        
        # Create event and main engines
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        
        # Create and run the TUI application
        app = FoxtrotTUIApp(main_engine, event_engine)
        
        print("TUI Application initialized successfully!")
        print("Press Ctrl+Q to quit")
        print("Press F1 for help")
        print("=" * 50)
        
        # Run the application
        app.run()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure all dependencies are installed: uv sync")
        sys.exit(1)
    
    except Exception as e:
        print(f"Failed to start TUI: {e}")
        print("Falling back to GUI mode...")
        try:
            # Try to start GUI as fallback
            from foxtrot.app.ui.mainwindow import MainWindow
            print("GUI fallback not implemented yet")
        except ImportError:
            print("GUI fallback also unavailable")
        sys.exit(1)


if __name__ == "__main__":
    main()