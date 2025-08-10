"""
Common utilities and factory functions for data object conversion.

This module provides backward compatibility for factory functions while
using the DI container internally to avoid circular dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Import the actual implementations from the DI container
from .di_container import (
    create_order_data_from_request,
    create_cancel_request_from_order,
    create_cancel_request_from_quote,
    create_quote_data_from_request,
)

if TYPE_CHECKING:
    from ..util.request_objects import OrderRequest, CancelRequest, QuoteRequest
    from ..util.trading_objects import OrderData
    from ..util.market_objects import QuoteData

# Re-export the functions for backward compatibility
__all__ = [
    'create_order_data_from_request',
    'create_cancel_request_from_order',
    'create_cancel_request_from_quote',
    'create_quote_data_from_request',
]