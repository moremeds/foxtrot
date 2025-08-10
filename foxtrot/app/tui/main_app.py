"""
Main TUI Application for Foxtrot Trading Platform

This module implements the primary Text User Interface using Textual framework,
providing the same functionality as the Qt GUI but optimized for terminal usage.
"""

import asyncio
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Static

import foxtrot
from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.utility import TRADER_DIR
from foxtrot.util.logger import get_component_logger, create_foxtrot_logger

# Lazy initialization of logger to avoid circular imports
_foxtrot_logger = None

def _get_logger():
    """Get or create the module logger."""
    global _foxtrot_logger
    if _foxtrot_logger is None:
        _foxtrot_logger = create_foxtrot_logger()
    return _foxtrot_logger

from .components.monitors.account import create_account_monitor
from .components.monitors.log_monitor import TUILogMonitor
# Import directly from the module files to avoid directory/file confusion
from .components.monitors import order_monitor as order_monitor_module
from .components.monitors.position_monitor import create_position_monitor
from .components.monitors.tick_monitor import create_tick_monitor
from .components.monitors import trade_monitor as trade_monitor_module
from .components.trading_panel import TUITradingPanel
from .config.settings import TUISettings
from .integration.event_adapter import EventEngineAdapter
from .async_bridge import AsyncBridge, AsyncDataFetcher, AsyncEventHandler
from foxtrot.adapter.binance.binance import BinanceAdapter
from foxtrot.util.request_objects import SubscribeRequest
from foxtrot.util.constants import Exchange


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
        Binding("f5", "add_symbol", "Add Symbol"),
        Binding("f6", "remove_symbol", "Remove Symbol"),
        Binding("f2", "show_contracts", "Contracts"),
        Binding("f3", "show_settings", "Settings"),
        Binding("f4", "show_connect", "Connect"),
        Binding("tab", "cycle_focus", "Cycle Focus"),
        Binding("shift+tab", "cycle_focus_reverse", "Cycle Focus Reverse"),
    ]

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
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
        self.event_adapter: EventEngineAdapter | None = None
        self.async_bridge = AsyncBridge()
        self.data_fetcher = AsyncDataFetcher(main_engine)

        # Monitor components
        self.tick_monitor = create_tick_monitor(main_engine, event_engine)
        self.order_monitor = order_monitor_module.TUIOrderMonitor(main_engine, event_engine)
        self.trade_monitor = trade_monitor_module.TUITradeMonitor(main_engine, event_engine)
        self.position_monitor = create_position_monitor(main_engine, event_engine)
        self.account_monitor = create_account_monitor(main_engine, event_engine)
        self.log_monitor = TUILogMonitor(main_engine, event_engine)

        # Trading panel component (will be initialized in on_mount after event adapter is ready)
        self.trading_panel: TUITradingPanel | None = None

        # Widget containers
        self.monitors: dict[str, Any] = {
            "tick": self.tick_monitor,
            "order": self.order_monitor,
            "trade": self.trade_monitor,
            "position": self.position_monitor,
            "account": self.account_monitor,
            "log": self.log_monitor,
        }
        self.dialogs: dict[str, Any] = {}

        # Application state
        self.is_connected = False
        self.current_gateway = ""

        # Initialize title
        version = getattr(foxtrot, "__version__", "1.0.0")
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
            # Left panel - Trading interface (placeholder - real trading panel added in on_mount)
            with Container(classes="trading-panel", id="trading-panel-container"):
                yield Static("Loading Trading Panel...", id="trading-placeholder")

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

        # Initialize interactive trading panel
        await self._initialize_trading_panel()

        # Initialize monitor components
        await self._initialize_monitors()

        # Load settings and apply configuration
        await self._load_settings()

        # Update status
        self._update_status("TUI Initialized - Ready to Connect (F5 add symbol)")

        # Auto-connect Binance for public market data (no keys) and enable websockets if present
        # Run in background to avoid blocking UI initialization
        self.async_bridge.create_background_task(
            self._auto_connect_binance(),
            name="auto_connect_binance"
        )

    async def _auto_connect_binance(self) -> None:
        """Auto-connect to Binance for public market data (non-blocking)."""
        try:
            setting = {
                "Public Market Data Only": True,
                "websocket.enabled": True,
                "websocket.binance.enabled": True,
                "websocket.binance.symbols": [],
                "Sandbox": False,
            }
            
            # Run the blocking operations in thread pool
            def connect():
                self.main_engine.add_adapter(BinanceAdapter, "BINANCE")
                self.main_engine.connect(setting, "BINANCE")
            
            await self.async_bridge.run_in_thread(connect)
            self._log_message("INFO", "Connected to Binance (public market data)")
        except Exception as e:
            self._log_message("ERROR", f"Auto-connect Binance failed: {e}")
    
    async def _initialize_trading_panel(self) -> None:
        """Initialize the interactive trading panel."""
        try:
            # Create the trading panel with event engine integration
            self.trading_panel = TUITradingPanel(
                main_engine=self.main_engine,
                event_engine=self.event_engine
            )

            # Set up event adapter for the trading panel
            if self.event_adapter and hasattr(self.trading_panel, 'set_event_adapter'):
                self.trading_panel.set_event_adapter(self.event_adapter)

            # Replace the placeholder with the actual trading panel
            container = self.query_one("#trading-panel-container")
            placeholder = self.query_one("#trading-placeholder")

            # Remove placeholder and mount trading panel
            await placeholder.remove()
            await container.mount(self.trading_panel)

            self._log_message("INFO", "Interactive trading panel initialized successfully")

        except Exception as e:
            self._log_message("ERROR", f"Failed to initialize trading panel: {e}")
            # Keep placeholder with error message
            try:
                placeholder = self.query_one("#trading-placeholder")
                placeholder.update(f"Trading Panel Error: {e}")
            except:
                pass

    async def _initialize_monitors(self) -> None:
        """Initialize all monitor components with event handling."""
        try:
            # The monitors are already created in __init__, just ensure they're ready
            for _monitor_name, monitor in self.monitors.items():
                if hasattr(monitor, "on_mount"):
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
            if hasattr(self.settings, "theme"):
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
            from datetime import datetime

            from foxtrot.util.object import LogData

            log_data = LogData(
                msg=message,
                level=level,
                time=datetime.now(),
                gateway_name=self.current_gateway or "SYSTEM",
            )

            # Send log data to the log monitor
            if hasattr(self.log_monitor, "_process_log_data"):
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
            # Use the trading panel's cancel all functionality if available
            if self.trading_panel and hasattr(self.trading_panel, '_cancel_all_orders'):
                asyncio.create_task(self.trading_panel._cancel_all_orders())
            else:
                # Fallback to main engine
                self.main_engine.cancel_all(None)  # None means all gateways
                self._log_message("INFO", "Cancel all orders requested")
        except Exception as e:
            self._log_message("ERROR", f"Failed to cancel orders: {e}")

    def action_show_help(self) -> None:
        """Show help dialog."""
        self._log_message(
            "INFO", "Help: F1=Help, F2=Contracts, F3=Settings, F4=Connect, Ctrl+Q=Quit"
        )

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

    # Symbol management actions
    def action_add_symbol(self) -> None:
        """Prompt and subscribe a symbol (e.g., BTCUSDT)."""
        try:
            # Basic prompt via console as a temporary input (replace with dialog later)
            symbol = input("Add symbol (e.g., BTCUSDT): ").strip().upper()
            if not symbol:
                return
            req = SubscribeRequest(symbol=symbol, exchange=Exchange.BINANCE)
            self.main_engine.subscribe(req, "BINANCE")
            self._log_message("INFO", f"Subscribed {symbol}")
        except Exception as e:
            self._log_message("ERROR", f"Add symbol failed: {e}")

    def action_remove_symbol(self) -> None:
        """Prompt and unsubscribe a symbol."""
        try:
            symbol = input("Remove symbol (e.g., BTCUSDT): ").strip().upper()
            if not symbol:
                return
            vt_symbol = f"{symbol}.BINANCE"
            if hasattr(self.main_engine, "unsubscribe"):
                self.main_engine.unsubscribe(vt_symbol, "BINANCE")
            self._log_message("INFO", f"Unsubscribed {symbol}")
        except Exception as e:
            self._log_message("ERROR", f"Remove symbol failed: {e}")

    # Trading panel integration handlers

    async def on_trading_panel_order_submitted(self, message) -> None:
        """Handle order submitted message from trading panel."""
        if hasattr(message, 'order_data') and hasattr(message, 'order_id'):
            self._log_message("INFO", f"Order submitted: {message.order_id}")

    async def on_trading_panel_cancel_all_requested(self, message) -> None:
        """Handle cancel all requested message from trading panel."""
        self._log_message("INFO", "Cancel all orders requested from trading panel")

    # Monitor message handlers

    async def on_tick_selected(self, message) -> None:
        """Handle tick selection from tick monitor."""
        if hasattr(message, "tick_data"):
            tick_data = message.tick_data
            await self._update_trading_from_tick(tick_data)

    async def on_position_selected(self, message) -> None:
        """Handle position selection from position monitor."""
        if hasattr(message, "position_data"):
            position_data = message.position_data
            await self._update_trading_from_position(position_data)

    async def _update_trading_from_tick(self, tick_data) -> None:
        """Update trading panel from selected tick data."""
        try:
            if self.trading_panel and hasattr(self.trading_panel, 'symbol_input'):
                # Update the interactive trading panel with tick information
                if self.trading_panel.symbol_input:
                    self.trading_panel.symbol_input.value = tick_data.symbol

                # Update market data if available
                if hasattr(self.trading_panel, 'market_data') and self.trading_panel.market_data:
                    await self.trading_panel.market_data.update_symbol(tick_data.symbol)

                self._log_message("INFO", f"Updated trading panel with {tick_data.symbol}")
            else:
                self._log_message("INFO", f"Trading panel not ready for tick update: {tick_data.symbol}")
        except Exception as e:
            self._log_message("ERROR", f"Failed to update trading panel from tick: {e}")

    async def _update_trading_from_position(self, position_data) -> None:
        """Update trading panel from selected position data."""
        try:
            if self.trading_panel and hasattr(self.trading_panel, 'symbol_input'):
                # Update the interactive trading panel with position information
                if self.trading_panel.symbol_input:
                    self.trading_panel.symbol_input.value = position_data.symbol

                if self.trading_panel.volume_input:
                    self.trading_panel.volume_input.value = str(abs(position_data.volume))

                # Set direction based on position volume
                if self.trading_panel.direction_radio:
                    pass
                    # Set radio button selection (this might need adjustment based on actual RadioSet API)

                self._log_message("INFO", f"Updated trading panel with {position_data.symbol} position")
            else:
                self._log_message("INFO", f"Trading panel not ready for position update: {position_data.symbol}")
        except Exception as e:
            self._log_message("ERROR", f"Failed to update trading panel from position: {e}")


def main() -> None:
    """
    Entry point for the TUI application.

    This function should be called when running the TUI version of Foxtrot.
    """
    import sys
    import traceback
    
    # Get logger with lazy initialization
    logger = get_component_logger("TUIMain", _get_logger())

    try:
        # Import foxtrot components
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine

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
        # MIGRATION: Replace print with ERROR logging for import failures
        logger.error(
            "TUI startup failed due to missing dependencies",
            extra={
                "error_type": type(e).__name__,
                "error_msg": str(e)
            }
        )
        print(f"Import Error: {e}")
        print("Make sure all dependencies are installed: uv sync")
        sys.exit(1)

    except Exception as e:
        # MIGRATION: Replace print with ERROR logging for startup failures
        logger.error(
            "TUI application startup failed",
            extra={
                "error_type": type(e).__name__,
                "error_msg": str(e)
            }
        )
        print(f"Failed to start TUI: {e}")
        print("Falling back to GUI mode...")
        try:
            # Try to start GUI as fallback
            logger.warning("GUI fallback requested but not implemented")
            print("GUI fallback not implemented yet")
        except ImportError:
            logger.error("GUI fallback unavailable")
            print("GUI fallback also unavailable")
        sys.exit(1)


if __name__ == "__main__":
    main()
