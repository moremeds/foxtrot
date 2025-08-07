"""
Refactored Trading Panel for TUI

This module provides the main trading panel UI that coordinates
all the modular components for trading functionality.
"""

from typing import Any, Optional

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Label, RadioSet, Select, Static

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_ORDER, EVENT_TICK
from foxtrot.app.tui.config.settings import get_settings
from foxtrot.app.tui.integration.event_adapter import TUIEventMixin

from .trading.form import TradingFormManager
from .trading.market_data import MarketDataPanel
from .trading.order_preview import OrderPreviewPanel
from .trading.symbol_input import SymbolInput
from .trading.trading_controller import TradingController
from .trading.trading_actions import TradingActionHandler


class OrderSubmittedMessage(Message):
    """Message sent when an order is submitted."""
    def __init__(self, order_data: Any, order_id: str):
        super().__init__()
        self.order_data = order_data
        self.order_id = order_id


class CancelAllRequestedMessage(Message):
    """Message sent when cancel all is requested."""
    pass


class TUITradingPanel(Container, TUIEventMixin):
    """
    Refactored interactive trading panel for the Foxtrot TUI.

    This panel coordinates modular components to provide:
    - Symbol selection with validation
    - Order entry with real-time validation
    - Order preview with calculations
    - Market data display
    - Order submission with confirmation
    """

    BINDINGS = [
        Binding("ctrl+enter", "submit_order", "Submit Order"),
        Binding("ctrl+r", "reset_form", "Reset Form"),
        Binding("ctrl+c", "cancel_all_orders", "Cancel All"),
        Binding("f1", "show_help", "Help"),
    ]

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        **kwargs
    ):
        """
        Initialize the trading panel.

        Args:
            main_engine: Main trading engine
            event_engine: Event engine for handling events
            **kwargs: Additional container arguments
        """
        super().__init__(**kwargs)
        TUIEventMixin.__init__(self)

        self.main_engine = main_engine
        self.event_engine = event_engine

        # Initialize components
        self.controller = TradingController(main_engine, event_engine)
        self.form_manager = TradingFormManager()
        self.action_handler = TradingActionHandler(main_engine, event_engine, self.form_manager)
        
        # UI Components (initialized in compose)
        self.order_preview: Optional[OrderPreviewPanel] = None
        self.market_data: Optional[MarketDataPanel] = None
        self.error_display: Optional[Static] = None

        # Settings
        self.settings = get_settings()

        # Modal manager for dialogs
        self.modal_manager = None
        self.event_adapter = None

    def set_event_adapter(self, event_adapter):
        """Set the event adapter for thread-safe communication."""
        self._event_adapter = event_adapter
        self.event_adapter = event_adapter

    def compose(self):
        """Create the trading panel layout."""
        with Vertical(classes="trading-panel"):
            yield Label("Trading Panel", classes="panel-title")

            # Error display
            self.error_display = Static("", classes="error-display")
            yield self.error_display

            with Horizontal(classes="trading-main"):
                # Left side - Order entry form
                with Vertical(classes="order-form"):
                    yield Label("Order Entry", classes="form-title")

                    # Symbol input
                    yield Label("Symbol:")
                    symbol_input = SymbolInput(
                        contract_manager=self.main_engine.get_contract_manager() if hasattr(self.main_engine, 'get_contract_manager') else None,
                        id="symbol-input"
                    )
                    yield symbol_input

                    # Exchange selection
                    yield Label("Exchange:")
                    exchange_select = Select(
                        options=[
                            ("SMART", "SMART"),
                            ("NYSE", "NYSE"),
                            ("NASDAQ", "NASDAQ"),
                            ("BINANCE", "BINANCE"),
                        ],
                        value="SMART",
                        id="exchange-select"
                    )
                    yield exchange_select

                    # Direction radio buttons
                    yield Label("Direction:")
                    direction_radio = RadioSet(
                        "BUY",
                        "SELL",
                        id="direction-radio"
                    )
                    yield direction_radio

                    # Order type selection
                    yield Label("Order Type:")
                    order_type_select = Select(
                        options=[
                            ("MARKET", "Market"),
                            ("LIMIT", "Limit"),
                            ("STOP", "Stop"),
                            ("STOP_LIMIT", "Stop Limit"),
                        ],
                        value="MARKET",
                        id="order-type-select"
                    )
                    yield order_type_select

                    # Price input
                    yield Label("Price:")
                    price_input = Input(
                        placeholder="Enter price",
                        disabled=True,
                        id="price-input"
                    )
                    yield price_input

                    # Volume input
                    yield Label("Volume:")
                    volume_input = Input(
                        placeholder="Enter volume",
                        id="volume-input"
                    )
                    yield volume_input

                    # Action buttons
                    with Horizontal(classes="form-buttons"):
                        submit_button = Button("Submit Order", variant="primary", id="submit-button")
                        yield submit_button
                        
                        reset_button = Button("Reset", variant="default", id="reset-button")
                        yield reset_button
                        
                        cancel_all_button = Button("Cancel All", variant="error", id="cancel-all-button")
                        yield cancel_all_button

                # Right side - Market data and preview
                with Vertical(classes="data-panels"):
                    # Market data panel
                    self.market_data = MarketDataPanel(classes="market-panel")
                    yield self.market_data

                    # Order preview panel
                    self.order_preview = OrderPreviewPanel(classes="preview-panel")
                    yield self.order_preview

            # Store form input references
            self.form_manager.set_inputs(
                symbol_input=symbol_input,
                exchange_select=exchange_select,
                direction_radio=direction_radio,
                order_type_select=order_type_select,
                price_input=price_input,
                volume_input=volume_input,
                submit_button=submit_button,
                reset_button=reset_button,
                cancel_all_button=cancel_all_button
            )

    async def on_mount(self):
        """Initialize components when panel is mounted."""
        await self._setup_event_handlers()

    async def _setup_event_handlers(self):
        """Set up event handlers for form inputs."""
        # Register for trading events if event adapter available
        if self.event_adapter:
            await self.event_adapter.subscribe_async(EVENT_TICK, self._on_tick_event)
            await self.event_adapter.subscribe_async(EVENT_ORDER, self._on_order_event)

    # Additional event handlers are provided by TradingActionsMixin