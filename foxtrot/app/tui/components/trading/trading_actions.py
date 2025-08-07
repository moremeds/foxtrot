"""
Trading action handlers for order submission and management.

This module provides backward compatibility by importing from the modular
trading_actions package. The original monolithic implementation has been
split into separate event handlers and action executor components.
"""

# Import from the modular package for backward compatibility
from .trading_actions import TradingActionHandler, OrderSubmissionMessage, OrderValidationMessage

__all__ = [
    "TradingActionHandler",
    "OrderSubmissionMessage", 
    "OrderValidationMessage"
]