"""
Event adapter modular package.

This package provides a thread-safe bridge between foxtrot's EventEngine
(threading-based) and Textual's asyncio-based UI system, split into focused
modular components for better maintainability.

Public API:
    - EventEngineAdapter: Main adapter class for threading/asyncio bridge
    - TUIEventMixin: Mixin for TUI components needing event handling
    - EventAdapterUtils: Utilities for statistics and maintenance
    - EventCommandPublisher: Command publishing functionality
    - create_event_adapter: Convenience factory function
"""

from .event_adapter_core import EventEngineAdapter
from .event_adapter_utils import EventAdapterUtils
from .event_command_publisher import EventCommandPublisher
from .event_batch_processor import EventBatchProcessor
from .event_mixin import TUIEventMixin

# Import necessary dependencies for factory function
from foxtrot.core.event_engine import EventEngine


def create_event_adapter(event_engine: EventEngine) -> EventEngineAdapter:
    """
    Create a configured EventEngineAdapter instance.

    Args:
        event_engine: The foxtrot EventEngine instance

    Returns:
        Configured EventEngineAdapter instance
    """
    return EventEngineAdapter(event_engine)


# Public API exports for backward compatibility
__all__ = [
    "EventEngineAdapter",
    "TUIEventMixin", 
    "EventAdapterUtils",
    "EventCommandPublisher",
    "EventBatchProcessor",
    "create_event_adapter",
]

# Version and module metadata
__version__ = "1.0.0"
__author__ = "Foxtrot Trading Platform"
__description__ = "Modular event adapter components for threading/asyncio bridge"