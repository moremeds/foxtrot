"""
Trading form modular package.

This package provides a modular form management system with the following components:
- Validation logic with cross-field rules
- Data binding and extraction 
- UI component state management
- Main controller orchestration

The package maintains backward compatibility by exporting the main TradingFormManager
class which provides the same interface as the original monolithic implementation.
"""

# Main controller class for backward compatibility
from .form_controller import TradingFormManager

# Core component classes
from .validation import TradingFormValidator
from .data_binding import TradingFormDataBinder
from .ui_manager import TradingFormUIManager

# Version info
__version__ = "2.0.0"
__author__ = "Foxtrot Trading Platform"

# Backward compatibility alias
FormManager = TradingFormManager

__all__ = [
    # Main classes
    "TradingFormManager",
    "FormManager",  # Backward compatibility alias
    
    # Component classes (available for advanced usage)
    "TradingFormValidator",
    "TradingFormDataBinder", 
    "TradingFormUIManager",
    
    # Package metadata
    "__version__",
    "__author__"
]