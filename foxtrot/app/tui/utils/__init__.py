"""
TUI Utilities Package

This package provides utility functions and classes for the Foxtrot TUI,
including formatting, color management, and other common functionality.
"""

from .colors import (
    ColorType,
    TUIColorManager,
    get_color_for_value,
    get_color_manager,
    get_themed_color,
)
from .formatters import (
    TUIFormatter,
    format_currency,
    format_datetime,
    format_number,
    format_percentage,
    format_pnl,
    format_price,
    format_volume,
)

__all__ = [
    "TUIColorManager",
    "ColorType",
    "get_color_manager",
    "get_themed_color",
    "get_color_for_value",
    "TUIFormatter",
    "format_currency",
    "format_price",
    "format_volume",
    "format_number",
    "format_percentage",
    "format_datetime",
    "format_pnl"
]
