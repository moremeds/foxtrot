"""
Order preview panel with calculations and risk metrics.

This module provides order preview functionality with real-time calculations,
risk assessment, and fund availability checking for trading operations.

REFACTORED: This file now imports from the modular order_preview package
while maintaining complete backward compatibility.
"""

# Import from the modular package for backward compatibility
from .order_preview import OrderPreviewPanel

# Also export for advanced usage
from .order_preview import OrderCalculationEngine, OrderPreviewUIManager

# Backward compatibility - ensure all original imports continue to work
__all__ = ["OrderPreviewPanel", "OrderCalculationEngine", "OrderPreviewUIManager"]