"""
Color Management System for TUI

This module provides color schemes, styling utilities, and theme management
for consistent visual presentation across all TUI components.
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from foxtrot.util.constants import Direction, Status


class ColorType(Enum):
    """Types of colors used in the TUI."""
    BID = "bid"
    ASK = "ask"
    PROFIT = "profit"
    LOSS = "loss"
    NEUTRAL = "neutral"
    LONG = "long"
    SHORT = "short"
    FILLED = "filled"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ColorConfig:
    """Configuration for a specific color."""
    foreground: str
    background: Optional[str] = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False


class TUIColorManager:
    """
    Centralized color management for TUI components.
    
    Provides consistent color schemes, theme switching, and
    context-aware color selection for trading data visualization.
    """
    
    # Default color schemes for different themes
    COLOR_SCHEMES = {
        "dark": {
            ColorType.BID: ColorConfig("bright_green", bold=True),
            ColorType.ASK: ColorConfig("bright_red", bold=True),
            ColorType.PROFIT: ColorConfig("bright_green", bold=True),
            ColorType.LOSS: ColorConfig("bright_red", bold=True),
            ColorType.NEUTRAL: ColorConfig("white"),
            ColorType.LONG: ColorConfig("green", bold=True),
            ColorType.SHORT: ColorConfig("red", bold=True),
            ColorType.FILLED: ColorConfig("green"),
            ColorType.PENDING: ColorConfig("yellow"),
            ColorType.CANCELLED: ColorConfig("red"),
            ColorType.REJECTED: ColorConfig("bright_red", bold=True),
            ColorType.WARNING: ColorConfig("yellow", bold=True),
            ColorType.ERROR: ColorConfig("bright_red", bold=True),
            ColorType.INFO: ColorConfig("cyan"),
            ColorType.SUCCESS: ColorConfig("green"),
        },
        
        "light": {
            ColorType.BID: ColorConfig("dark_green", bold=True),
            ColorType.ASK: ColorConfig("dark_red", bold=True),
            ColorType.PROFIT: ColorConfig("dark_green", bold=True),
            ColorType.LOSS: ColorConfig("dark_red", bold=True),
            ColorType.NEUTRAL: ColorConfig("black"),
            ColorType.LONG: ColorConfig("dark_green", bold=True),
            ColorType.SHORT: ColorConfig("dark_red", bold=True),
            ColorType.FILLED: ColorConfig("dark_green"),
            ColorType.PENDING: ColorConfig("orange3"),
            ColorType.CANCELLED: ColorConfig("dark_red"),
            ColorType.REJECTED: ColorConfig("red", bold=True),
            ColorType.WARNING: ColorConfig("orange3", bold=True),
            ColorType.ERROR: ColorConfig("red", bold=True),
            ColorType.INFO: ColorConfig("blue"),
            ColorType.SUCCESS: ColorConfig("dark_green"),
        },
        
        "high_contrast": {
            ColorType.BID: ColorConfig("white", "green", bold=True),
            ColorType.ASK: ColorConfig("white", "red", bold=True),
            ColorType.PROFIT: ColorConfig("black", "bright_green", bold=True),
            ColorType.LOSS: ColorConfig("white", "bright_red", bold=True),
            ColorType.NEUTRAL: ColorConfig("white", bold=True),
            ColorType.LONG: ColorConfig("white", "green", bold=True),
            ColorType.SHORT: ColorConfig("white", "red", bold=True),
            ColorType.FILLED: ColorConfig("black", "green"),
            ColorType.PENDING: ColorConfig("black", "yellow"),
            ColorType.CANCELLED: ColorConfig("white", "red"),
            ColorType.REJECTED: ColorConfig("white", "bright_red", bold=True),
            ColorType.WARNING: ColorConfig("black", "yellow", bold=True),
            ColorType.ERROR: ColorConfig("white", "red", bold=True),
            ColorType.INFO: ColorConfig("white", "blue"),
            ColorType.SUCCESS: ColorConfig("black", "green"),
        },
        
        "trading_green": {
            ColorType.BID: ColorConfig("bright_green", bold=True),
            ColorType.ASK: ColorConfig("red", bold=True),
            ColorType.PROFIT: ColorConfig("bright_green", bold=True),
            ColorType.LOSS: ColorConfig("red", bold=True),
            ColorType.NEUTRAL: ColorConfig("green"),
            ColorType.LONG: ColorConfig("bright_green", bold=True),
            ColorType.SHORT: ColorConfig("red", bold=True),
            ColorType.FILLED: ColorConfig("bright_green"),
            ColorType.PENDING: ColorConfig("yellow"),
            ColorType.CANCELLED: ColorConfig("red"),
            ColorType.REJECTED: ColorConfig("bright_red", bold=True),
            ColorType.WARNING: ColorConfig("yellow", bold=True),
            ColorType.ERROR: ColorConfig("bright_red", bold=True),
            ColorType.INFO: ColorConfig("green"),
            ColorType.SUCCESS: ColorConfig("bright_green"),
        }
    }
    
    def __init__(self, theme: str = "dark"):
        """
        Initialize color manager with specified theme.
        
        Args:
            theme: Theme name (dark, light, high_contrast, trading_green)
        """
        self.current_theme = theme
        self._load_theme(theme)
    
    def _load_theme(self, theme: str) -> None:
        """Load color scheme for specified theme."""
        if theme not in self.COLOR_SCHEMES:
            theme = "dark"  # Fallback to dark theme
        
        self.colors = self.COLOR_SCHEMES[theme].copy()
        self.current_theme = theme
    
    def get_color(self, color_type: ColorType) -> ColorConfig:
        """
        Get color configuration for specified type.
        
        Args:
            color_type: Type of color to retrieve
            
        Returns:
            Color configuration object
        """
        return self.colors.get(color_type, ColorConfig("white"))
    
    def get_color_string(self, color_type: ColorType) -> str:
        """
        Get color as string for Textual styling.
        
        Args:
            color_type: Type of color to retrieve
            
        Returns:
            Color string compatible with Textual
        """
        config = self.get_color(color_type)
        
        # Build color string for Textual
        parts = []
        
        if config.bold:
            parts.append("bold")
        if config.dim:
            parts.append("dim")
        if config.italic:
            parts.append("italic")
        if config.underline:
            parts.append("underline")
        
        # Add foreground color
        parts.append(config.foreground)
        
        # Add background color if specified
        if config.background:
            parts.append(f"on {config.background}")
        
        return " ".join(parts)
    
    def get_price_color(self, current_price: float, previous_price: float) -> ColorType:
        """
        Get appropriate color for price based on price movement.
        
        Args:
            current_price: Current price value
            previous_price: Previous price value
            
        Returns:
            Appropriate color type
        """
        if current_price > previous_price:
            return ColorType.PROFIT
        elif current_price < previous_price:
            return ColorType.LOSS
        else:
            return ColorType.NEUTRAL
    
    def get_pnl_color(self, pnl_value: float) -> ColorType:
        """
        Get appropriate color for P&L value.
        
        Args:
            pnl_value: P&L value
            
        Returns:
            Appropriate color type
        """
        if pnl_value > 0:
            return ColorType.PROFIT
        elif pnl_value < 0:
            return ColorType.LOSS
        else:
            return ColorType.NEUTRAL
    
    def get_direction_color(self, direction: Direction) -> ColorType:
        """
        Get appropriate color for trading direction.
        
        Args:
            direction: Trading direction
            
        Returns:
            Appropriate color type
        """
        if direction == Direction.LONG:
            return ColorType.LONG
        elif direction == Direction.SHORT:
            return ColorType.SHORT
        else:
            return ColorType.NEUTRAL
    
    def get_status_color(self, status: Status) -> ColorType:
        """
        Get appropriate color for order/trade status.
        
        Args:
            status: Order or trade status
            
        Returns:
            Appropriate color type
        """
        status_color_map = {
            Status.SUBMITTING: ColorType.PENDING,
            Status.NOTTRADED: ColorType.PENDING,
            Status.PARTTRADED: ColorType.PENDING,
            Status.ALLTRADED: ColorType.FILLED,
            Status.CANCELLED: ColorType.CANCELLED,
            Status.REJECTED: ColorType.REJECTED,
        }
        
        return status_color_map.get(status, ColorType.NEUTRAL)
    
    def switch_theme(self, theme: str) -> None:
        """
        Switch to a different theme.
        
        Args:
            theme: New theme name
        """
        self._load_theme(theme)
    
    def get_available_themes(self) -> list[str]:
        """Get list of available themes."""
        return list(self.COLOR_SCHEMES.keys())
    
    def create_rich_text(
        self, 
        text: str, 
        color_type: ColorType,
        additional_styles: Optional[list[str]] = None
    ) -> str:
        """
        Create rich text markup for Textual display.
        
        Args:
            text: Text content
            color_type: Color type to apply
            additional_styles: Additional style attributes
            
        Returns:
            Rich text markup string
        """
        color_string = self.get_color_string(color_type)
        
        if additional_styles:
            color_string += " " + " ".join(additional_styles)
        
        return f"[{color_string}]{text}[/]"
    
    def get_bid_ask_colors(self) -> Tuple[str, str]:
        """
        Get bid and ask colors as strings.
        
        Returns:
            Tuple of (bid_color, ask_color) strings
        """
        bid_color = self.get_color_string(ColorType.BID)
        ask_color = self.get_color_string(ColorType.ASK)
        return bid_color, ask_color
    
    def customize_color(
        self, 
        color_type: ColorType, 
        foreground: str,
        background: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """
        Customize a specific color in the current theme.
        
        Args:
            color_type: Color type to customize
            foreground: Foreground color
            background: Background color (optional)
            **kwargs: Additional color attributes
        """
        self.colors[color_type] = ColorConfig(
            foreground=foreground,
            background=background,
            **kwargs
        )
    
    def reset_theme(self) -> None:
        """Reset current theme to default colors."""
        self._load_theme(self.current_theme)


# Global color manager instance
_color_manager: Optional[TUIColorManager] = None


def get_color_manager() -> TUIColorManager:
    """Get the global color manager instance."""
    global _color_manager
    if _color_manager is None:
        _color_manager = TUIColorManager()
    return _color_manager


def reset_color_manager() -> None:
    """Reset the global color manager instance."""
    global _color_manager
    _color_manager = None


def get_themed_color(color_type: ColorType) -> str:
    """
    Convenience function to get themed color string.
    
    Args:
        color_type: Color type to retrieve
        
    Returns:
        Color string for current theme
    """
    return get_color_manager().get_color_string(color_type)