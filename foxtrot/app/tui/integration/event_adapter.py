"""
Event Engine Adapter for TUI Integration

This module provides a thread-safe bridge between the foxtrot EventEngine
(which runs on background threads) and Textual's asyncio-based event loop.

This module now imports from the modular event_adapter package to maintain
backward compatibility while enabling better code organization.
"""

# Import all classes from the modular package to maintain backward compatibility
from .event_adapter import (
    EventEngineAdapter,
    TUIEventMixin,
    EventAdapterUtils, 
    EventCommandPublisher,
    create_event_adapter,
)

# Re-export for backward compatibility
__all__ = [
    "EventEngineAdapter",
    "TUIEventMixin",
    "EventAdapterUtils",
    "EventCommandPublisher", 
    "create_event_adapter",
]