"""
Interactive Trading Panel for Foxtrot TUI

This module provides a comprehensive trading interface that allows users
to place orders through a terminal-based interface with real-time validation,
market data integration, and order confirmation.
"""

from datetime import datetime
from decimal import Decimal
import logging
from typing import Any

from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Label, RadioSet, Select, Static

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import *
from foxtrot.util.object import Direction, OrderData, OrderType

from ..config.settings import get_settings
from ..integration.event_adapter import TUIEventMixin
from ..security import SecureInputValidator
from ..utils.formatters import format_currency, format_number
from ..validation import (
    DirectionValidator,
    FormValidator,
    OrderTypeValidator,
    PriceValidator,
    SymbolValidator,
    ValidationErrorCollector,
    ValidationResult,
    VolumeValidator,
)
from .dialogs.modal import get_modal_manager

# Set up logging
logger = logging.getLogger(__name__)


class SymbolInput(Input):
    """
    Enhanced input widget for symbol entry with auto-completion.

    Features:
    - Real-time symbol validation
    - Auto-completion based on available contracts
    - Contract information display
    """

    def __init__(
        self,
        contract_manager = None,
        placeholder: str = "Enter symbol (e.g., AAPL, BTCUSDT)",
        **kwargs
    ):
        super().__init__(placeholder=placeholder, **kwargs)
        self.contract_manager = contract_manager
        self.validator = SymbolValidator(contract_manager=contract_manager)
        self.suggestions: list[str] = []

    async def validate_symbol(self, value: str) -> ValidationResult:
        """Validate symbol and return result."""
        return self.validator.validate(value)

    async def get_suggestions(self, partial: str) -> list[str]:
        """Get symbol suggestions for auto-completion."""
        if not self.contract_manager or len(partial) < 2:
            return []

        # This would integrate with actual contract manager
        # For now, return some mock suggestions
        mock_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "SPY", "QQQ"
        ]

        return [
            symbol for symbol in mock_symbols
            if symbol.startswith(partial.upper())
        ][:5]


class OrderPreviewPanel(Container):
    """
    Panel that displays order preview with calculations and risk metrics.

    Shows:
    - Total order value
    - Available funds
    - Estimated commission
    - Position impact
    - Risk metrics
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order_data: dict[str, Any] = {}
        self.market_data: dict[str, Any] = {}

        # UI components
        self.order_value_label: Static | None = None
        self.funds_check_label: Static | None = None
        self.commission_label: Static | None = None
        self.risk_label: Static | None = None

        # Settings
        self.settings = get_settings()

    def compose(self):
        """Create the preview panel layout."""
        with Vertical(classes="order-preview"):
            yield Static("Order Preview", classes="preview-title")

            with Vertical(classes="preview-content"):
                self.order_value_label = Static("Order Value: -", classes="preview-item")
                yield self.order_value_label

                self.funds_check_label = Static("Available Funds: -", classes="preview-item")
                yield self.funds_check_label

                self.commission_label = Static("Est. Commission: -", classes="preview-item")
                yield self.commission_label

                self.risk_label = Static("Position Impact: -", classes="preview-item")
                yield self.risk_label

    async def update_preview(
        self,
        symbol: str = "",
        price: Decimal | None = None,
        volume: Decimal | None = None,
        order_type: str = "MARKET",
        direction: str = "BUY"
    ):
        """Update the order preview with current form data."""
        self.order_data = {
            "symbol": symbol,
            "price": price,
            "volume": volume,
            "order_type": order_type,
            "direction": direction
        }

        await self._calculate_preview()

    async def _calculate_preview(self):
        """Calculate and display order preview values."""
        if not self.order_data.get("symbol") or not self.order_data.get("volume"):
            self._clear_preview()
            return

        try:
            volume = self.order_data["volume"]
            price = self.order_data.get("price")
            order_type = self.order_data.get("order_type", "MARKET")

            # Use market price if no price specified or market order
            if not price or order_type == "MARKET":
                price = await self._get_market_price()

            if not price:
                self._clear_preview()
                return

            # Calculate order value
            order_value = volume * price

            # Calculate estimated commission
            commission = await self._calculate_commission(volume, price)

            # Get available funds
            available_funds = await self._get_available_funds()

            # Calculate position impact
            position_impact = await self._calculate_position_impact(volume, self.order_data["direction"])

            # Update UI
            await self._update_preview_display(
                order_value, commission, available_funds, position_impact
            )

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "order_preview_calculation"
            )
            self._show_error(secure_error.user_message)

    async def _get_market_price(self) -> Decimal | None:
        """Get current market price for the symbol."""
        # This would integrate with market data
        # For now, return a mock price
        return Decimal("150.00")

    async def _calculate_commission(self, volume: Decimal, price: Decimal) -> Decimal:
        """Calculate estimated commission."""
        # Simple commission calculation - $1 per trade
        return Decimal("1.00")

    async def _get_available_funds(self) -> Decimal | None:
        """Get available funds from account."""
        # This would integrate with account manager
        # For now, return mock funds
        return Decimal("10000.00")

    async def _calculate_position_impact(self, volume: Decimal, direction: str) -> str:
        """Calculate position impact description."""
        action = "increase" if direction == "BUY" else "decrease"
        return f"Will {action} position by {volume} shares"

    async def _update_preview_display(
        self,
        order_value: Decimal,
        commission: Decimal,
        available_funds: Decimal | None,
        position_impact: str
    ):
        """Update the preview display with calculated values."""
        if self.order_value_label:
            self.order_value_label.update(f"Order Value: {format_currency(order_value)}")

        if self.commission_label:
            self.commission_label.update(f"Est. Commission: {format_currency(commission)}")

        if self.funds_check_label and available_funds is not None:
            total_cost = order_value + commission
            sufficient = available_funds >= total_cost
            status = "✓" if sufficient else "✗"

            self.funds_check_label.update(
                f"Available: {format_currency(available_funds)} {status}"
            )
            # Apply color styling if available

        if self.risk_label:
            self.risk_label.update(f"Impact: {position_impact}")

    def _clear_preview(self):
        """Clear all preview values."""
        if self.order_value_label:
            self.order_value_label.update("Order Value: -")
        if self.funds_check_label:
            self.funds_check_label.update("Available Funds: -")
        if self.commission_label:
            self.commission_label.update("Est. Commission: -")
        if self.risk_label:
            self.risk_label.update("Position Impact: -")

    def _show_error(self, message: str):
        """Show error message in preview."""
        if self.order_value_label:
            self.order_value_label.update(f"Error: {message}")


class MarketDataPanel(Container):
    """
    Panel displaying real-time market data for the selected symbol.

    Shows:
    - Current bid/ask prices
    - Last traded price
    - Volume and change
    - Market depth (5-level)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_symbol: str | None = None
        self.market_data: dict[str, Any] = {}

        # UI components
        self.bid_ask_label: Static | None = None
        self.last_price_label: Static | None = None
        self.volume_label: Static | None = None
        self.depth_container: Container | None = None

    def compose(self):
        """Create market data panel layout."""
        with Vertical(classes="market-data"):
            yield Static("Market Data", classes="market-title")

            with Vertical(classes="market-content"):
                self.bid_ask_label = Static("Bid/Ask: -", classes="market-item")
                yield self.bid_ask_label

                self.last_price_label = Static("Last: -", classes="market-item")
                yield self.last_price_label

                self.volume_label = Static("Volume: -", classes="market-item")
                yield self.volume_label

                yield Static("Market Depth:", classes="depth-title")

                with Vertical(classes="depth-container") as depth_container:
                    self.depth_container = depth_container
                    for i in range(5):
                        yield Static(f"Level {i+1}: -", classes="depth-level")

    async def update_symbol(self, symbol: str):
        """Update market data for new symbol."""
        self.current_symbol = symbol
        await self._fetch_market_data()

    async def _fetch_market_data(self):
        """Fetch and display market data for current symbol."""
        if not self.current_symbol:
            self._clear_market_data()
            return

        try:
            # Mock market data - in practice this would come from market data feed
            self.market_data = {
                "bid": Decimal("149.95"),
                "ask": Decimal("150.05"),
                "last": Decimal("150.00"),
                "volume": 1250000,
                "change": Decimal("1.25"),
                "change_percent": Decimal("0.84")
            }

            await self._update_market_display()

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "market_data_fetch"
            )
            self._show_error(secure_error.user_message)

    async def _update_market_display(self):
        """Update market data display."""
        if not self.market_data:
            return

        # Update bid/ask
        if self.bid_ask_label:
            bid = self.market_data.get("bid")
            ask = self.market_data.get("ask")
            if bid and ask:
                self.bid_ask_label.update(f"Bid/Ask: {bid} / {ask}")

        # Update last price with change
        if self.last_price_label:
            last = self.market_data.get("last")
            change = self.market_data.get("change")
            change_percent = self.market_data.get("change_percent")

            if last and change and change_percent:
                change_sign = "+" if change > 0 else ""
                self.last_price_label.update(
                    f"Last: {last} ({change_sign}{change} / {change_sign}{change_percent}%)"
                )

        # Update volume
        if self.volume_label:
            volume = self.market_data.get("volume")
            if volume:
                self.volume_label.update(f"Volume: {format_number(volume)}")

    def _clear_market_data(self):
        """Clear all market data displays."""
        if self.bid_ask_label:
            self.bid_ask_label.update("Bid/Ask: -")
        if self.last_price_label:
            self.last_price_label.update("Last: -")
        if self.volume_label:
            self.volume_label.update("Volume: -")

    def _show_error(self, message: str):
        """Show error message."""
        if self.bid_ask_label:
            self.bid_ask_label.update(f"Error: {message}")


class TUITradingPanel(Container, TUIEventMixin):
    """
    Complete interactive trading panel for the Foxtrot TUI.

    This panel provides full trading functionality including:
    - Symbol selection with validation
    - Order entry with real-time validation
    - Order preview with calculations
    - Market data display
    - Order submission with confirmation
    - Integration with MainEngine
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
        super().__init__(**kwargs)
        TUIEventMixin.__init__(self)

        self.main_engine = main_engine
        self.event_engine = event_engine

        # Validators
        self.form_validator = FormValidator()
        self.symbol_validator = SymbolValidator()
        self.price_validator = PriceValidator()
        self.volume_validator = VolumeValidator()
        self.order_type_validator = OrderTypeValidator()
        self.direction_validator = DirectionValidator()

        # Form validators dictionary for easy access by tests
        self._form_validators = {
            'symbol': self.symbol_validator,
            'price': self.price_validator,
            'volume': self.volume_validator,
            'order_type': self.order_type_validator,
            'direction': self.direction_validator
        }

        # Form state
        self.current_contract_info = None
        self.validation_errors = ValidationErrorCollector()

        # UI Components
        self.symbol_input: SymbolInput | None = None
        self.exchange_select: Select | None = None
        self.direction_radio: RadioSet | None = None
        self.order_type_select: Select | None = None
        self.price_input: Input | None = None
        self.volume_input: Input | None = None
        self.submit_button: Button | None = None
        self.reset_button: Button | None = None
        self.cancel_all_button: Button | None = None

        self.order_preview: OrderPreviewPanel | None = None
        self.market_data: MarketDataPanel | None = None
        self.error_display: Static | None = None

        # Settings
        self.settings = get_settings()

        # Modal manager for dialogs (initialized in on_mount)
        self.modal_manager = None
        self.event_adapter = None

    def set_event_adapter(self, event_adapter):
        # Set the internal adapter first
        self._event_adapter = event_adapter
        self.event_adapter = event_adapter

        # Now we can register handlers
        self.register_event_handler(EVENT_TICK, self._on_tick_event)
        self.register_event_handler(EVENT_ORDER, self._on_order_event)
        self.register_event_handler(EVENT_ACCOUNT, self._on_account_event)

    def compose(self):
        """Create the trading panel layout."""
        with Vertical(classes="trading-panel"):
            yield Static("Trading Panel", classes="panel-title")

            with Horizontal(classes="trading-content"):
                # Left side - Order Entry Form
                with Vertical(classes="order-form", id="order-form"):
                    yield Static("Order Entry", classes="form-title")

                    # Symbol and Exchange
                    with Horizontal(classes="form-row"):
                        yield Label("Symbol:", classes="form-label")
                        self.symbol_input = SymbolInput(
                            placeholder="AAPL, BTCUSDT, etc.",
                            classes="form-input"
                        )
                        yield self.symbol_input

                    with Horizontal(classes="form-row"):
                        yield Label("Exchange:", classes="form-label")
                        self.exchange_select = Select(
                            options=[
                                ("Auto-detect", ""),
                                ("SMART", "SMART"),
                                ("NASDAQ", "NASDAQ"),
                                ("NYSE", "NYSE"),
                                ("BINANCE", "BINANCE"),
                            ],
                            value="",
                            classes="form-select"
                        )
                        yield self.exchange_select

                    # Direction and Order Type
                    with Horizontal(classes="form-row"):
                        yield Label("Direction:", classes="form-label")
                        self.direction_radio = RadioSet(
                            "BUY", "SELL",
                            classes="form-radio"
                        )
                        yield self.direction_radio

                    with Horizontal(classes="form-row"):
                        yield Label("Order Type:", classes="form-label")
                        self.order_type_select = Select(
                            options=[
                                ("Market", "MARKET"),
                                ("Limit", "LIMIT"),
                                ("Stop", "STOP"),
                                ("Stop Limit", "STOP_LIMIT"),
                            ],
                            value="MARKET",
                            classes="form-select"
                        )
                        yield self.order_type_select

                    # Price and Volume
                    with Horizontal(classes="form-row"):
                        yield Label("Price:", classes="form-label")
                        self.price_input = Input(
                            placeholder="Leave empty for market orders",
                            classes="form-input"
                        )
                        yield self.price_input

                    with Horizontal(classes="form-row"):
                        yield Label("Volume:", classes="form-label")
                        self.volume_input = Input(
                            placeholder="Number of shares/units",
                            classes="form-input"
                        )
                        yield self.volume_input

                    # Error display
                    self.error_display = Static("", classes="error-display")
                    yield self.error_display

                    # Action buttons
                    with Horizontal(classes="button-row"):
                        self.submit_button = Button("Submit Order", variant="primary", classes="submit-btn")
                        yield self.submit_button

                        self.reset_button = Button("Reset", variant="default", classes="reset-btn")
                        yield self.reset_button

                        self.cancel_all_button = Button("Cancel All", variant="error", classes="cancel-btn")
                        yield self.cancel_all_button

                # Right side - Preview and Market Data
                with Vertical(classes="info-panels"):
                    # Order Preview
                    self.order_preview = OrderPreviewPanel(classes="preview-panel")
                    yield self.order_preview

                    # Market Data
                    self.market_data = MarketDataPanel(classes="market-panel")
                    yield self.market_data

    async def on_mount(self):
        """Initialize the trading panel."""
        # Initialize modal manager
        self.modal_manager = get_modal_manager(self.app)

        # Set up form validation
        await self._setup_form_validation()

        # Set up event handlers
        await self._setup_event_handlers()

        # Initialize UI state
        await self._update_ui_state()

    async def _setup_form_validation(self):
        """Set up form validators."""
        self.form_validator.add_field_validator("symbol", self.symbol_validator)
        self.form_validator.add_field_validator("price", self.price_validator)
        self.form_validator.add_field_validator("volume", self.volume_validator)
        self.form_validator.add_field_validator("order_type", self.order_type_validator)
        self.form_validator.add_field_validator("direction", self.direction_validator)

        # Add cross-field validation rules
        self.form_validator.add_cross_field_rule(self._validate_price_required)
        self.form_validator.add_cross_field_rule(self._validate_sufficient_funds)

    async def _setup_event_handlers(self):
        """Set up event handlers for real-time updates."""
        # Register for market data events
        if self._event_adapter:
            self.register_event_handler(EVENT_TICK, self._on_tick_event)
            self.register_event_handler(EVENT_ORDER, self._on_order_event)
            self.register_event_handler(EVENT_ACCOUNT, self._on_account_event)

    # Event Handlers

    async def on_input_changed(self, event: Input.Changed):
        """Handle input field changes for real-time validation."""
        await self._validate_form()
        await self._update_preview()

    async def on_select_changed(self, event: Select.Changed):
        """Handle select field changes."""
        await self._validate_form()
        await self._update_preview()

        # Update price input state based on order type
        if event.select == self.order_type_select:
            await self._update_price_input_state()

    async def on_radio_set_changed(self, event: RadioSet.Changed):
        """Handle radio button changes."""
        await self._validate_form()
        await self._update_preview()

    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button presses."""
        if event.button == self.submit_button:
            await self._submit_order()
        elif event.button == self.reset_button:
            await self._reset_form()
        elif event.button == self.cancel_all_button:
            await self._cancel_all_orders()

    # Validation Methods

    async def _validate_form(self) -> bool:
        """Validate the entire form and display errors."""
        self.validation_errors.clear()

        # Get form data
        form_data = await self._get_form_data()

        # Validate with form validator
        validation_results = self.form_validator.validate(form_data)

        # Collect errors
        has_errors = False
        for field_name, result in validation_results.items():
            if not result.is_valid:
                has_errors = True
                for error in result.errors:
                    self.validation_errors.add_error(error, field_name)

        # Update error display
        await self._update_error_display()

        # Update submit button state
        if self.submit_button:
            self.submit_button.disabled = has_errors

        return not has_errors

    def _validate_price_required(self, data: dict[str, Any]) -> ValidationResult:
        """Cross-field validation: price required for non-market orders."""
        order_type = data.get("order_type", "MARKET")
        price = data.get("price")

        if order_type != "MARKET" and not price:
            return ValidationResult(
                is_valid=False,
                errors=[f"Price is required for {order_type} orders"]
            )

        return ValidationResult(is_valid=True)

    def _validate_sufficient_funds(self, data: dict[str, Any]) -> ValidationResult:
        """Cross-field validation: sufficient funds check."""
        # This would integrate with account manager for real fund checking
        # For now, return success
        return ValidationResult(is_valid=True)

    # UI Update Methods

    async def _update_ui_state(self):
        """Update UI state based on current form values."""
        await self._update_price_input_state()
        await self._validate_form()
        await self._update_preview()

    async def _update_price_input_state(self):
        """Update price input enabled/disabled state based on order type."""
        if not self.price_input or not self.order_type_select:
            return

        order_type = self.order_type_select.value
        if order_type == "MARKET":
            self.price_input.disabled = True
            self.price_input.placeholder = "Market orders use market price"
        else:
            self.price_input.disabled = False
            self.price_input.placeholder = "Enter price"

    async def _update_preview(self):
        """Update order preview panel."""
        if not self.order_preview:
            return

        form_data = await self._get_form_data()

        await self.order_preview.update_preview(
            symbol=form_data.get("symbol", ""),
            price=form_data.get("price"),
            volume=form_data.get("volume"),
            order_type=form_data.get("order_type", "MARKET"),
            direction=form_data.get("direction", "BUY")
        )

    async def _update_error_display(self):
        """Update error display with validation errors."""
        if not self.error_display:
            return

        if self.validation_errors.has_errors():
            errors = self.validation_errors.get_error_messages()
            error_text = "\n".join(errors[:3])  # Show first 3 errors
            self.error_display.update(error_text)
            self.error_display.add_class("error-active")
        else:
            self.error_display.update("")
            self.error_display.remove_class("error-active")

    # Form Data Methods

    async def _get_form_data(self) -> dict[str, Any]:
        """Get current form data as dictionary."""
        data = {}

        if self.symbol_input:
            data["symbol"] = self.symbol_input.value

        if self.exchange_select:
            data["exchange"] = self.exchange_select.value

        if self.direction_radio:
            data["direction"] = self.direction_radio.pressed_button.label if self.direction_radio.pressed_button else "BUY"

        if self.order_type_select:
            data["order_type"] = self.order_type_select.value

        if self.price_input and self.price_input.value:
            # Use secure validation instead of bare except clause
            is_valid, decimal_value, error = SecureInputValidator.validate_decimal_input(
                self.price_input.value,
                "price",
                min_value=0.0,
                max_value=1000000.0,
                max_precision=8
            )
            if is_valid:
                data["price"] = Decimal(str(decimal_value))
            else:
                # Log security event and use None (validation will catch this later)
                if error:
                    logger.warning(f"Price validation failed: {error.user_message}")
                data["price"] = None

        if self.volume_input and self.volume_input.value:
            # Use secure validation instead of bare except clause
            is_valid, decimal_value, error = SecureInputValidator.validate_decimal_input(
                self.volume_input.value,
                "volume",
                min_value=0.0,
                max_value=1000000.0,
                max_precision=8
            )
            if is_valid:
                data["volume"] = Decimal(str(decimal_value))
            else:
                # Log security event and use None (validation will catch this later)
                if error:
                    logger.warning(f"Volume validation failed: {error.user_message}")
                data["volume"] = None

        return data

    # Order Management Methods

    async def _submit_order(self):
        """Submit the order to MainEngine."""
        # Final validation
        if not await self._validate_form():
            return

        try:
            form_data = await self._get_form_data()

            # Create order data object
            order_data = await self._create_order_data(form_data)

            # Show confirmation if enabled
            if self.settings.confirm_orders:
                if not await self._confirm_order(order_data):
                    return

            # Submit order through MainEngine
            await self._send_order_to_engine(order_data)

            # Clear form if successful - default behavior
            # TODO: Add clear_form_after_submit setting to TUISettings
            clear_form_after_submit = True  # Default behavior
            if clear_form_after_submit:
                await self._reset_form()

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "order_submission", {"order_action": "submit"}
            )
            await self._show_error(secure_error.user_message)

    async def _create_order_data(self, form_data: dict[str, Any]) -> OrderData:
        """Create OrderData object from form data."""
        # This would create a proper OrderData object
        # For now, return a mock object
        return {
            "symbol": form_data["symbol"],
            "exchange": form_data.get("exchange", ""),
            "direction": Direction.LONG if form_data["direction"] == "BUY" else Direction.SHORT,
            "type": OrderType.MARKET if form_data["order_type"] == "MARKET" else OrderType.LIMIT,
            "volume": form_data["volume"],
            "price": form_data.get("price", 0),
            "orderid": f"TUI_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

    async def _confirm_order(self, order_data: dict[str, Any]) -> bool:
        """Show order confirmation dialog."""
        if not self.modal_manager:
            # Fallback if modal manager not available
            return True

        try:
            # Get account balance for confirmation dialog
            account_balance = await self._get_available_funds()

            # Get market price for confirmation dialog
            market_price = None
            if order_data.get('order_type') == 'MARKET':
                market_price = await self._get_market_price()

            # Show confirmation dialog
            result = await self.modal_manager.show_order_confirmation(
                order_data=order_data,
                account_balance=float(account_balance) if account_balance else None,
                market_price=float(market_price) if market_price else None
            )

            return result.success

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "order_confirmation_dialog"
            )
            await self._show_error(secure_error.user_message)
            return False

    async def _send_order_to_engine(self, order_data: dict[str, Any]):
        """Send order to MainEngine via EventEngine."""
        try:
            # Use the TUIEventMixin method to publish order
            order_id = await self.publish_order(order_data)

            if order_id:
                await self._show_success(f"Order submitted successfully: {order_id}")
                self.post_message(self.OrderSubmitted(order_data, order_id))
            else:
                await self._show_error("Failed to submit order: No order ID returned")

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "order_engine_submission"
            )
            await self._show_error(secure_error.user_message)

    async def _reset_form(self):
        """Reset all form fields to defaults."""
        if self.symbol_input:
            self.symbol_input.value = ""

        if self.price_input:
            self.price_input.value = ""

        if self.volume_input:
            self.volume_input.value = ""

        if self.order_type_select:
            self.order_type_select.value = "MARKET"

        if self.direction_radio:
            # Reset to first button (BUY)
            pass

        if self.exchange_select:
            self.exchange_select.value = ""

        # Clear errors and preview
        self.validation_errors.clear()
        await self._update_error_display()
        await self._update_preview()

    async def _cancel_all_orders(self):
        """Cancel all open orders."""
        if not self.modal_manager:
            # Fallback without confirmation
            await self._execute_cancel_all()
            return

        try:
            # Show confirmation dialog
            # TODO: Get actual open orders count from order manager
            open_orders_count = 0  # Placeholder

            result = await self.modal_manager.show_cancel_all_confirmation(
                open_orders_count=open_orders_count
            )

            if result.success:
                await self._execute_cancel_all()

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "cancel_confirmation_dialog"
            )
            await self._show_error(secure_error.user_message)

    async def _execute_cancel_all(self):
        """Execute the cancel all orders action."""
        try:
            # Use the TUIEventMixin method to cancel all orders
            success = await self.cancel_all_orders()

            if success:
                await self._show_success("Cancel all orders request submitted")
                self.post_message(self.CancelAllRequested())
            else:
                await self._show_error("Failed to submit cancel all orders request")

        except Exception as e:
            from ..security import SecurityAwareErrorHandler
            secure_error = SecurityAwareErrorHandler.handle_exception(
                e, "cancel_all_orders_execution"
            )
            await self._show_error(secure_error.user_message)

    # Event Handlers

    async def _update_market_data(self, tick_data):
        """Update market data display with tick data."""
        if self.market_data and self.symbol_input:
            current_symbol = self.symbol_input.value
            if tick_data.symbol == current_symbol:
                await self.market_data.update_symbol(current_symbol)

    async def _on_tick_event(self, event: Event):
        """Handle tick data events for market data updates."""
        tick_data = event.data
        if self.market_data and self.symbol_input:
            current_symbol = self.symbol_input.value
            if tick_data.symbol == current_symbol:
                await self.market_data.update_symbol(current_symbol)

    async def _on_order_event(self, event: Event):
        """Handle order status events."""
        # Update UI based on order status changes

    async def _on_account_event(self, event: Event):
        """Handle account update events."""
        # Update available funds display

    async def _handle_order_error(self, error_msg: str):
        """Handle order submission errors."""
        await self._show_error(f"Order Error: {error_msg}")

    async def _get_account_balance(self, account_id: str) -> Decimal | None:
        """Get account balance from the main engine."""
        account = self.main_engine.get_account(account_id)
        return account.balance if account else None

    # Utility Methods

    async def _get_available_funds(self) -> Decimal | None:
        """Get available funds from account."""
        # This would integrate with account manager
        # For now, return mock funds
        return Decimal("10000.00")

    async def _get_market_price(self) -> Decimal | None:
        """Get current market price for the symbol."""
        # This would integrate with market data
        # For now, return a mock price
        return Decimal("150.00")

    async def _show_error(self, message: str):
        """Show error message to user."""
        if self.error_display:
            self.error_display.update(f"❌ {message}")
            self.error_display.add_class("error-active")

    async def _show_success(self, message: str):
        """Show success message to user."""
        if self.error_display:
            self.error_display.update(f"✅ {message}")
            self.error_display.remove_class("error-active")
            self.error_display.add_class("success-active")

    # Action Methods (Keyboard Shortcuts)

    async def action_submit_order(self):
        """Submit order via keyboard shortcut."""
        await self._submit_order()

    async def action_reset_form(self):
        """Reset form via keyboard shortcut."""
        await self._reset_form()

    async def action_cancel_all_orders(self):
        """Cancel all orders via keyboard shortcut."""
        await self._cancel_all_orders()

    def action_show_help(self):
        """Show help dialog."""
        # This would show a help dialog

    # Custom Messages

    class OrderSubmitted(Message):
        """Message sent when an order is submitted."""

        def __init__(self, order_data: dict[str, Any], order_id: str | None = None):
            self.order_data = order_data
            self.order_id = order_id
            super().__init__()

    class CancelAllRequested(Message):
        """Message sent when cancel all is requested."""

    class ValidationFailed(Message):
        """Message sent when form validation fails."""

        def __init__(self, errors: list[str]):
            self.errors = errors
            super().__init__()
