"""
Information request operations for EventEngineAdapter.

This module handles information request publishing including account and
position data requests through the EventEngine system.
"""

import logging

from foxtrot.core.event_engine import Event
from foxtrot.util.event_type import *

logger = logging.getLogger(__name__)


class InfoRequests:
    """Information request functionality for EventEngineAdapter."""

    def __init__(self, adapter_ref):
        """Initialize info requests with adapter reference."""
        self._adapter_ref = adapter_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference with validation."""
        adapter = self._adapter_ref()
        if not adapter:
            raise RuntimeError("EventEngineAdapter reference is dead")
        if not adapter.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        return adapter

    async def request_account_info(self) -> bool:
        """Request account information update."""
        adapter = self._get_adapter()

        try:
            # Create account info request event
            event = Event(EVENT_ACCOUNT_REQUEST, {})

            # Publish event to EventEngine
            adapter.event_engine.put(event)

            logger.info("Account info request published")
            return True

        except Exception as e:
            logger.error(f"Failed to request account info: {e}")
            return False

    async def request_position_info(self) -> bool:
        """Request position information update."""
        adapter = self._get_adapter()

        try:
            # Create position info request event
            event = Event(EVENT_POSITION_REQUEST, {})

            # Publish event to EventEngine
            adapter.event_engine.put(event)

            logger.info("Position info request published")
            return True

        except Exception as e:
            logger.error(f"Failed to request position info: {e}")
            return False