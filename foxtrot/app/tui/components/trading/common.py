"""
Common constants, types, and utilities for trading components.

This module provides shared functionality used across trading components
to maintain consistency and reduce duplication.
"""

from typing import Any, Dict, List, Optional
from decimal import Decimal
from enum import Enum


class OrderAction(Enum):
    """Order actions for clarity and type safety."""
    SUBMIT = "submit"
    CANCEL = "cancel"
    MODIFY = "modify"


class TradingConstants:
    """Constants used throughout trading components."""
    
    # Default form values
    DEFAULT_ORDER_TYPE = "MARKET"
    DEFAULT_DIRECTION = "BUY"
    DEFAULT_EXCHANGE = ""
    
    # Validation limits
    MAX_PRICE = 1000000.0
    MIN_PRICE = 0.0
    MAX_VOLUME = 1000000.0
    MIN_VOLUME = 0.0
    PRICE_PRECISION = 8
    VOLUME_PRECISION = 8
    
    # UI constants
    MAX_ERROR_DISPLAY = 3
    MOCK_ACCOUNT_BALANCE = Decimal("10000.00")
    MOCK_MARKET_PRICE = Decimal("150.00")
    MOCK_COMMISSION = Decimal("1.00")
    
    # Symbol suggestions for auto-completion
    MOCK_SYMBOLS = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "BTCUSDT", "ETHUSDT", "ADAUSDT", "SPY", "QQQ"
    ]


class TradingFormData:
    """Type-safe container for trading form data."""
    
    def __init__(
        self,
        symbol: str = "",
        exchange: str = "",
        direction: str = TradingConstants.DEFAULT_DIRECTION,
        order_type: str = TradingConstants.DEFAULT_ORDER_TYPE,
        price: Optional[Decimal] = None,
        volume: Optional[Decimal] = None
    ):
        self.symbol = symbol
        self.exchange = exchange
        self.direction = direction
        self.order_type = order_type
        self.price = price
        self.volume = volume
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for compatibility with existing code."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "direction": self.direction,
            "order_type": self.order_type,
            "price": self.price,
            "volume": self.volume
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingFormData':
        """Create from dictionary for compatibility with existing code."""
        return cls(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            direction=data.get("direction", TradingConstants.DEFAULT_DIRECTION),
            order_type=data.get("order_type", TradingConstants.DEFAULT_ORDER_TYPE),
            price=data.get("price"),
            volume=data.get("volume")
        )


def format_order_impact(volume: Decimal, direction: str) -> str:
    """Format position impact description consistently."""
    action = "increase" if direction == "BUY" else "decrease"
    return f"Will {action} position by {volume} shares"


def get_symbol_suggestions(partial: str, max_results: int = 5) -> List[str]:
    """Get symbol suggestions for auto-completion."""
    if len(partial) < 2:
        return []
    
    return [
        symbol for symbol in TradingConstants.MOCK_SYMBOLS
        if symbol.startswith(partial.upper())
    ][:max_results]