"""
Order preview modular package.

This package provides a modular order preview system with the following components:
- Calculation engine for pure business logic
- UI components for presentation and display
- Main controller for orchestration and public interface

The package maintains backward compatibility by exporting the main OrderPreviewPanel
class which provides the same interface as the original monolithic implementation.
"""

# Main controller class for backward compatibility
from .preview_controller import OrderPreviewPanel

# Core component classes
from .calculation_engine import OrderCalculationEngine
from .ui_components import OrderPreviewUIManager

# Version info
__version__ = "2.0.0"
__author__ = "Foxtrot Trading Platform"

__all__ = [
    # Main classes
    "OrderPreviewPanel",
    
    # Component classes (available for advanced usage)
    "OrderCalculationEngine",
    "OrderPreviewUIManager",
    
    # Package metadata
    "__version__",
    "__author__"
]