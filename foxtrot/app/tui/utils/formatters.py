"""
Data Formatters for TUI Components

This module provides formatting utilities for displaying trading data
in the TUI with proper formatting, precision, and visual styling.
"""

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from foxtrot.util.constants import Direction, Exchange, OrderType, Status


class TUIFormatter:
    """
    Comprehensive formatter for TUI data display.

    Provides consistent formatting across all TUI components with
    proper precision, alignment, and visual styling.
    """

    @staticmethod
    def format_price(
        price: float | int | Decimal | None, precision: int = 4, show_sign: bool = False
    ) -> str:
        """
        Format price values with appropriate precision.

        Args:
            price: Price value to format
            precision: Number of decimal places
            show_sign: Whether to show + for positive values

        Returns:
            Formatted price string
        """
        if price is None or price == 0:
            return "-"

        try:
            # Convert to Decimal for precise formatting
            if isinstance(price, int | float):
                decimal_price = Decimal(str(price))
            else:
                decimal_price = Decimal(price)

            # Round to specified precision
            rounded_price = decimal_price.quantize(
                Decimal("0." + "0" * precision), rounding=ROUND_HALF_UP
            )

            # Format with sign if requested
            if show_sign and rounded_price > 0:
                return f"+{rounded_price:.{precision}f}"
            return f"{rounded_price:.{precision}f}"

        except (ValueError, TypeError, ArithmeticError):
            return str(price) or "-"

    @staticmethod
    def format_volume(volume: float | int | None) -> str:
        """
        Format volume with appropriate scaling and units.

        Args:
            volume: Volume value to format

        Returns:
            Formatted volume string
        """
        if volume is None or volume == 0:
            return "-"

        try:
            vol = float(volume)

            if vol >= 1_000_000_000:
                return f"{vol / 1_000_000_000:.2f}B"
            if vol >= 1_000_000:
                return f"{vol / 1_000_000:.2f}M"
            if vol >= 1_000:
                return f"{vol / 1_000:.2f}K"
            # Show as integer for small volumes
            return f"{int(vol)}" if vol == int(vol) else f"{vol:.2f}"

        except (ValueError, TypeError):
            return str(volume) or "-"

    @staticmethod
    def format_percentage(
        value: float | int | None, precision: int = 2, show_sign: bool = True
    ) -> str:
        """
        Format percentage values with sign and precision.

        Args:
            value: Percentage value (as decimal, e.g., 0.05 for 5%)
            precision: Number of decimal places
            show_sign: Whether to show + for positive values

        Returns:
            Formatted percentage string
        """
        if value is None:
            return "-"

        try:
            percent = float(value) * 100

            if show_sign and percent > 0:
                return f"+{percent:.{precision}f}%"
            return f"{percent:.{precision}f}%"

        except (ValueError, TypeError):
            return str(value) or "-"

    @staticmethod
    def format_currency(
        amount: float | int | Decimal | None,
        currency: str = "USD",
        show_currency: bool = True,
        precision: int = 2,
    ) -> str:
        """
        Format currency values with appropriate symbols and precision.

        Args:
            amount: Currency amount
            currency: Currency code (USD, EUR, etc.)
            show_currency: Whether to show currency symbol
            precision: Number of decimal places

        Returns:
            Formatted currency string
        """
        if amount is None:
            return "-"

        try:
            # Currency symbols mapping
            currency_symbols = {
                "USD": "$",
                "EUR": "€",
                "GBP": "£",
                "JPY": "¥",
                "CNY": "¥",
                "CHF": "CHF",
                "CAD": "C$",
                "AUD": "A$",
            }

            formatted_amount = TUIFormatter.format_price(amount, precision)

            if show_currency:
                symbol = currency_symbols.get(currency.upper(), currency)
                return f"{symbol}{formatted_amount}"
            return formatted_amount

        except (ValueError, TypeError):
            return str(amount) or "-"

    @staticmethod
    def format_datetime(dt: datetime | None, format_type: str = "time") -> str:
        """
        Format datetime objects for display.

        Args:
            dt: Datetime object to format
            format_type: Type of formatting ("time", "date", "datetime", "compact")

        Returns:
            Formatted datetime string
        """
        if dt is None:
            return "-"

        try:
            if format_type == "time":
                return dt.strftime("%H:%M:%S")
            if format_type == "date":
                return dt.strftime("%Y-%m-%d")
            if format_type == "datetime":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            if format_type == "compact":
                return dt.strftime("%m/%d %H:%M")
            if format_type == "milliseconds":
                return dt.strftime("%H:%M:%S.%f")[:-3]  # Show milliseconds
            return dt.strftime("%H:%M:%S")

        except (ValueError, AttributeError):
            return str(dt) or "-"

    @staticmethod
    def format_enum(enum_value: Enum | None) -> str:
        """
        Format enum values for display.

        Args:
            enum_value: Enum value to format

        Returns:
            Formatted enum string
        """
        if enum_value is None:
            return "-"

        try:
            if hasattr(enum_value, "value"):
                return str(enum_value.value)
            return str(enum_value)
        except (ValueError, AttributeError):
            return str(enum_value) or "-"

    @staticmethod
    def format_direction(direction: Direction | None) -> str:
        """
        Format trading direction with visual indicators.

        Args:
            direction: Direction enum value

        Returns:
            Formatted direction string
        """
        if direction is None:
            return "-"

        direction_symbols = {
            Direction.LONG: "↗ LONG",
            Direction.SHORT: "↘ SHORT",
        }

        return direction_symbols.get(direction, str(direction))

    @staticmethod
    def format_order_type(order_type: OrderType | None) -> str:
        """
        Format order type for display.

        Args:
            order_type: OrderType enum value

        Returns:
            Formatted order type string
        """
        if order_type is None:
            return "-"

        # Use shorter abbreviations for TUI display
        type_abbreviations = {
            OrderType.LIMIT: "LMT",
            OrderType.MARKET: "MKT",
            OrderType.STOP: "STP",
            OrderType.FAK: "FAK",
            OrderType.FOK: "FOK",
        }

        return type_abbreviations.get(order_type, str(order_type))

    @staticmethod
    def format_status(status: Status | None) -> str:
        """
        Format order/trade status for display.

        Args:
            status: Status enum value

        Returns:
            Formatted status string
        """
        if status is None:
            return "-"

        # Use shorter status names for TUI
        status_names = {
            Status.SUBMITTING: "SUBMIT",
            Status.NOTTRADED: "PENDING",
            Status.PARTTRADED: "PARTIAL",
            Status.ALLTRADED: "FILLED",
            Status.CANCELLED: "CANCEL",
            Status.REJECTED: "REJECT",
        }

        return status_names.get(status, str(status))

    @staticmethod
    def format_exchange(exchange: Exchange | None) -> str:
        """
        Format exchange name for display.

        Args:
            exchange: Exchange enum value

        Returns:
            Formatted exchange string
        """
        if exchange is None:
            return "-"

        return str(exchange.value) if hasattr(exchange, "value") else str(exchange)

    @staticmethod
    def format_pnl(
        pnl: float | int | None,
        currency: str = "USD",
        show_percentage: bool = False,
        percentage_value: float | None = None,
    ) -> str:
        """
        Format P&L values with appropriate styling.

        Args:
            pnl: P&L amount
            currency: Currency code
            show_percentage: Whether to show percentage alongside amount
            percentage_value: Percentage value if show_percentage is True

        Returns:
            Formatted P&L string
        """
        if pnl is None:
            return "-"

        try:
            formatted_amount = TUIFormatter.format_currency(pnl, currency)

            if show_percentage and percentage_value is not None:
                formatted_percent = TUIFormatter.format_percentage(percentage_value)
                return f"{formatted_amount} ({formatted_percent})"
            return formatted_amount

        except (ValueError, TypeError):
            return str(pnl) or "-"

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to fit within specified length.

        Args:
            text: Text to truncate
            max_length: Maximum allowed length
            suffix: Suffix to add when truncating

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def align_text(text: str, width: int, alignment: str = "left") -> str:
        """
        Align text within specified width.

        Args:
            text: Text to align
            width: Target width
            alignment: Alignment type ("left", "right", "center")

        Returns:
            Aligned text
        """
        if alignment == "right":
            return text.rjust(width)
        if alignment == "center":
            return text.center(width)
        # left alignment
        return text.ljust(width)


# Convenience functions for easy access
def format_currency(
    amount: float | int | Decimal | None,
    currency: str = "USD",
    show_currency: bool = True,
    precision: int = 2,
) -> str:
    """Convenience function for formatting currency."""
    return TUIFormatter.format_currency(amount, currency, show_currency, precision)


def format_price(
    price: float | int | Decimal | None,
    precision: int = 4,
    show_sign: bool = False
) -> str:
    """Convenience function for formatting prices."""
    return TUIFormatter.format_price(price, precision, show_sign)


def format_volume(volume: float | int | None) -> str:
    """Convenience function for formatting volume."""
    return TUIFormatter.format_volume(volume)


def format_percentage(
    value: float | int | None,
    precision: int = 2,
    show_sign: bool = True
) -> str:
    """Convenience function for formatting percentages."""
    return TUIFormatter.format_percentage(value, precision, show_sign)


def format_number(value: float | int | None) -> str:
    """Convenience function for formatting numbers with scaling."""
    return TUIFormatter.format_volume(value)  # Same logic as volume formatting


def format_datetime(dt: datetime | None, format_type: str = "time") -> str:
    """Convenience function for formatting datetime."""
    return TUIFormatter.format_datetime(dt, format_type)


def format_pnl(
    pnl: float | int | None,
    currency: str = "USD",
    show_percentage: bool = False,
    percentage_value: float | None = None,
) -> str:
    """Convenience function for formatting P&L."""
    return TUIFormatter.format_pnl(pnl, currency, show_percentage, percentage_value)
