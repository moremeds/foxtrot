"""
Trading actions modular package.

This package provides a modular trading actions system with the following components:
- Event handlers for user interactions and messaging
- Action executor for core business logic operations
- Main controller for orchestration and public interface

The package maintains backward compatibility by exporting the main TradingActionHandler
class which provides the same interface as the original monolithic implementation.
"""

# Main controller class for backward compatibility
from .actions_controller import TradingActionHandler

# Core component classes
from .event_handlers import TradingEventHandler, OrderSubmissionMessage, OrderValidationMessage
from .action_executor import TradingActionExecutor

# Version info
__version__ = "2.0.0"
__author__ = "Foxtrot Trading Platform"

__all__ = [
    # Main classes
    "TradingActionHandler",
    
    # Component classes (available for advanced usage)
    "TradingEventHandler",
    "TradingActionExecutor",
    
    # Message classes
    "OrderSubmissionMessage",
    "OrderValidationMessage",
    
    # Package metadata
    "__version__",
    "__author__"
]