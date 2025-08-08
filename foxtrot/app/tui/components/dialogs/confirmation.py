"""
Confirmation Dialogs for Trading Operations

This module provides specialized confirmation dialogs for trading operations
including order submission, cancellation, and other critical actions.
"""

import asyncio
from decimal import Decimal
from typing import Any

from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Label, Static

from foxtrot.util.constants import OrderType

from foxtrot.app.tui.utils.colors import get_color_manager
from foxtrot.app.tui.utils.formatters import TUIFormatter
from .base import BaseDialog, DialogResult, DialogType


class OrderConfirmationDialog(BaseDialog):
    """
    Order confirmation dialog for reviewing and confirming trading orders.

    Features:
    - Order details display with formatting
    - Risk calculations and warnings
    - Account balance verification
    - Customizable confirmation requirements
    """

    DEFAULT_CSS = BaseDialog.DEFAULT_CSS + """
    OrderConfirmationDialog .dialog-container {
        width: 70%;
        max-width: 90;
        min-height: 20;
    }

    .order-details {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    .order-detail-row {
        height: 1;
        margin-bottom: 1;
    }

    .detail-label {
        width: 15;
        text-style: bold;
        color: $text-muted;
    }

    .detail-value {
        width: 25;
        color: $text;
    }

    .order-summary {
        background: $surface-lighten-1;
        border: solid $accent;
        padding: 1;
        margin-bottom: 1;
    }

    .summary-title {
        text-style: bold;
        text-align: center;
        color: $accent;
        margin-bottom: 1;
    }

    .risk-warning {
        background: $warning;
        color: $warning-text;
        text-style: bold;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }

    .insufficient-funds {
        background: $error;
        color: $error-text;
        text-style: bold;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        order_data: dict[str, Any],
        account_balance: Decimal | None = None,
        market_price: Decimal | None = None,
        **kwargs
    ):
        super().__init__(
            title="Confirm Order",
            dialog_type=DialogType.CONFIRMATION,
            confirm_text="Submit Order",
            cancel_text="Cancel",
            **kwargs
        )

        self.order_data = order_data
        self.account_balance = account_balance
        self.market_price = market_price

        # UI components
        self.order_details_container: Container | None = None
        self.risk_warning_widget: Static | None = None
        self.funds_warning_widget: Static | None = None

        # Calculated values
        self.order_value = self._calculate_order_value()
        self.estimated_commission = self._calculate_commission()
        self.total_cost = self.order_value + self.estimated_commission
        self.has_sufficient_funds = self._check_sufficient_funds()

        # Color manager
        self.color_manager = get_color_manager()

    def compose_content(self) -> list[Widget]:
        """Compose order confirmation dialog content."""
        widgets = []

        # Order details section
        with Container(classes="order-details") as details_container:
            self.order_details_container = details_container

            yield Static("Order Details", classes="summary-title")

            # Symbol and exchange
            with Horizontal(classes="order-detail-row"):
                yield Label("Symbol:", classes="detail-label")
                symbol_display = f"{self.order_data['symbol']}"
                if self.order_data.get('exchange'):
                    symbol_display += f".{self.order_data['exchange']}"
                yield Static(symbol_display, classes="detail-value")

            # Direction and order type
            with Horizontal(classes="order-detail-row"):
                yield Label("Direction:", classes="detail-label")
                direction_text = TUIFormatter.format_direction(self.order_data['direction'])
                self.color_manager.get_direction_color(self.order_data['direction'])
                yield Static(direction_text, classes="detail-value")

            with Horizontal(classes="order-detail-row"):
                yield Label("Order Type:", classes="detail-label")
                order_type_text = TUIFormatter.format_order_type(self.order_data['order_type'])
                yield Static(order_type_text, classes="detail-value")

            # Volume and price
            with Horizontal(classes="order-detail-row"):
                yield Label("Volume:", classes="detail-label")
                volume_text = TUIFormatter.format_volume(self.order_data['volume'])
                yield Static(volume_text, classes="detail-value")

            with Horizontal(classes="order-detail-row"):
                yield Label("Price:", classes="detail-label")
                if self.order_data.get('price') and self.order_data['order_type'] != OrderType.MARKET:
                    price_text = TUIFormatter.format_price(self.order_data['price'])
                else:
                    price_text = "Market Price"
                    if self.market_price:
                        price_text += f" (~{TUIFormatter.format_price(self.market_price)})"
                yield Static(price_text, classes="detail-value")

        widgets.append(details_container)

        # Order summary section
        with Container(classes="order-summary") as summary_container:
            yield Static("Order Summary", classes="summary-title")

            with Horizontal(classes="order-detail-row"):
                yield Label("Order Value:", classes="detail-label")
                order_value_text = TUIFormatter.format_currency(self.order_value)
                yield Static(order_value_text, classes="detail-value")

            with Horizontal(classes="order-detail-row"):
                yield Label("Est. Commission:", classes="detail-label")
                commission_text = TUIFormatter.format_currency(self.estimated_commission)
                yield Static(commission_text, classes="detail-value")

            with Horizontal(classes="order-detail-row"):
                yield Label("Total Cost:", classes="detail-label")
                total_cost_text = TUIFormatter.format_currency(self.total_cost)
                yield Static(total_cost_text, classes="detail-value")

            if self.account_balance:
                with Horizontal(classes="order-detail-row"):
                    yield Label("Available Funds:", classes="detail-label")
                    balance_text = TUIFormatter.format_currency(self.account_balance)
                    yield Static(balance_text, classes="detail-value")

        widgets.append(summary_container)

        # Risk warnings
        risk_warnings = self._get_risk_warnings()
        for warning in risk_warnings:
            self.risk_warning_widget = Static(warning, classes="risk-warning")
            widgets.append(self.risk_warning_widget)

        # Insufficient funds warning
        if not self.has_sufficient_funds:
            self.funds_warning_widget = Static(
                "⚠️ INSUFFICIENT FUNDS - Order cannot be executed",
                classes="insufficient-funds"
            )
            widgets.append(self.funds_warning_widget)

        return widgets

    async def setup_dialog(self):
        """Setup order confirmation dialog."""
        await super().setup_dialog()

        # Disable confirm button if insufficient funds
        if self.confirm_button and not self.has_sufficient_funds:
            self.confirm_button.disabled = True

    async def validate_input(self) -> DialogResult:
        """Validate order before confirmation."""
        if not self.has_sufficient_funds:
            return DialogResult(
                confirmed=False,
                error="Insufficient funds to execute order"
            )

        return DialogResult(confirmed=True)

    async def collect_data(self) -> dict[str, Any]:
        """Collect order confirmation data."""
        return {
            "order_data": self.order_data,
            "order_value": float(self.order_value),
            "estimated_commission": float(self.estimated_commission),
            "total_cost": float(self.total_cost),
            "confirmed_at": asyncio.get_event_loop().time()
        }

    def _calculate_order_value(self) -> Decimal:
        """Calculate the total value of the order."""
        try:
            volume = Decimal(str(self.order_data['volume']))

            # Use specified price or market price
            if self.order_data.get('price') and self.order_data['order_type'] != OrderType.MARKET:
                price = Decimal(str(self.order_data['price']))
            elif self.market_price:
                price = Decimal(str(self.market_price))
            else:
                # Default fallback price
                price = Decimal('100.00')

            return volume * price

        except (ValueError, TypeError, KeyError):
            return Decimal('0.00')

    def _calculate_commission(self) -> Decimal:
        """Calculate estimated commission for the order."""
        # Simple flat commission model - could be enhanced
        return Decimal('1.00')

    def _check_sufficient_funds(self) -> bool:
        """Check if account has sufficient funds for the order."""
        if not self.account_balance:
            return True  # Can't verify, assume sufficient

        return self.account_balance >= self.total_cost

    def _get_risk_warnings(self) -> list[str]:
        """Get list of risk warnings for the order."""
        warnings = []

        # Large order warning
        if self.order_value > Decimal('10000.00'):
            warnings.append("⚠️ Large order value - please review carefully")

        # Market order warning
        if self.order_data.get('order_type') == OrderType.MARKET:
            warnings.append("⚠️ Market order - execution price may vary")

        # High percentage of account warning
        if self.account_balance and self.total_cost > (self.account_balance * Decimal('0.5')):
            warnings.append("⚠️ Order exceeds 50% of available funds")

        return warnings


class CancelConfirmationDialog(BaseDialog):
    """
    Confirmation dialog for cancelling orders or positions.
    """

    DEFAULT_CSS = BaseDialog.DEFAULT_CSS + """
    CancelConfirmationDialog .dialog-container {
        width: 50%;
        max-width: 70;
    }

    .cancel-warning {
        background: $warning;
        color: $warning-text;
        text-style: bold;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        title: str = "Cancel Order",
        message: str = "Are you sure you want to cancel this order?",
        order_id: str | None = None,
        show_warning: bool = True,
        **kwargs
    ):
        super().__init__(
            title=title,
            dialog_type=DialogType.WARNING,
            confirm_text="Cancel Order",
            cancel_text="Keep Order",
            **kwargs
        )

        self.message = message
        self.order_id = order_id
        self.show_warning = show_warning

        self.message_widget: Static | None = None
        self.warning_widget: Static | None = None
        self.order_info_widget: Static | None = None

    def compose_content(self) -> list[Widget]:
        """Compose cancel confirmation dialog content."""
        widgets = []

        # Warning message
        if self.show_warning:
            self.warning_widget = Static(
                "⚠️ This action cannot be undone",
                classes="cancel-warning"
            )
            widgets.append(self.warning_widget)

        # Main message
        self.message_widget = Static(self.message, classes="dialog-message")
        widgets.append(self.message_widget)

        # Order information if provided
        if self.order_id:
            self.order_info_widget = Static(
                f"Order ID: {self.order_id}",
                classes="dialog-message"
            )
            widgets.append(self.order_info_widget)

        return widgets

    async def collect_data(self) -> dict[str, Any]:
        """Collect cancellation confirmation data."""
        return {
            "order_id": self.order_id,
            "confirmed_at": asyncio.get_event_loop().time()
        }


class CancelAllConfirmationDialog(BaseDialog):
    """
    Confirmation dialog for cancelling all orders.
    """

    DEFAULT_CSS = BaseDialog.DEFAULT_CSS + """
    CancelAllConfirmationDialog .dialog-container {
        width: 60%;
        max-width: 80;
    }

    .danger-warning {
        background: $error;
        color: $error-text;
        text-style: bold;
        text-align: center;
        padding: 1;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        open_orders_count: int = 0,
        **kwargs
    ):
        super().__init__(
            title="Cancel All Orders",
            dialog_type=DialogType.WARNING,
            confirm_text="Cancel All",
            cancel_text="Keep Orders",
            **kwargs
        )

        self.open_orders_count = open_orders_count

        self.warning_widget: Static | None = None
        self.message_widget: Static | None = None
        self.count_widget: Static | None = None

    def compose_content(self) -> list[Widget]:
        """Compose cancel all confirmation dialog content."""
        widgets = []

        # Danger warning
        self.warning_widget = Static(
            "🚨 DANGER: This will cancel ALL open orders",
            classes="danger-warning"
        )
        widgets.append(self.warning_widget)

        # Order count information
        if self.open_orders_count > 0:
            self.count_widget = Static(
                f"This will cancel {self.open_orders_count} open order(s)",
                classes="dialog-message"
            )
            widgets.append(self.count_widget)

        # Confirmation message
        self.message_widget = Static(
            "Are you sure you want to cancel all open orders?\\nThis action cannot be undone.",
            classes="dialog-message"
        )
        widgets.append(self.message_widget)

        return widgets

    async def collect_data(self) -> dict[str, Any]:
        """Collect cancel all confirmation data."""
        return {
            "orders_count": self.open_orders_count,
            "confirmed_at": asyncio.get_event_loop().time()
        }
