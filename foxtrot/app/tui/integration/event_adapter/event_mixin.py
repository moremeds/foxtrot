"""
Event mixin for TUI components needing event handling capabilities.

This module provides convenient methods for TUI components to register
and handle events from the EventEngine through the EventEngineAdapter.
"""

import logging
from typing import Any, Callable

from foxtrot.core.event_engine import Event

logger = logging.getLogger(__name__)


class TUIEventMixin:
    """
    Mixin class for TUI components that need event handling.

    This mixin provides convenient methods for TUI components to register
    and handle events from the EventEngine.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event_handlers: list[tuple[str, Callable]] = []
        self._event_adapter = None

    def set_event_adapter(self, adapter) -> None:
        """Set the event adapter for this component."""
        self._event_adapter = adapter

    def register_event_handler(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """
        Register an event handler for this component.

        Args:
            event_type: Type of event to handle
            handler: Handler function (can be sync or async)
        """
        if not self._event_adapter:
            raise RuntimeError("Event adapter not set. Call set_event_adapter first.")

        self._event_adapter.register(event_type, handler, self)
        self._event_handlers.append((event_type, handler))

    def unregister_all_handlers(self) -> None:
        """Unregister all event handlers for this component."""
        if not self._event_adapter:
            return

        for event_type, handler in self._event_handlers:
            self._event_adapter.unregister(event_type, handler)

        self._event_handlers.clear()

    def cleanup_events(self) -> None:
        """Clean up event handlers (call when component is destroyed)."""
        self.unregister_all_handlers()

    # Command Publishing Convenience Methods

    async def publish_order(self, order_data: dict[str, Any]) -> str | None:
        """
        Publish an order through the event adapter.

        Args:
            order_data: Order information dictionary

        Returns:
            Order ID if successful, None if failed
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot publish order.")
            return None

        try:
            return await self._event_adapter.publish_order(order_data)
        except Exception as e:
            logger.error(f"Failed to publish order from component: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """
        Cancel an order through the event adapter.

        Args:
            order_id: Order ID to cancel
            symbol: Symbol of the order
            exchange: Exchange where order was placed

        Returns:
            True if cancel request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot cancel order.")
            return False

        try:
            return await self._event_adapter.cancel_order(order_id, symbol, exchange)
        except Exception as e:
            logger.error(f"Failed to cancel order from component: {e}")
            return False

    async def cancel_all_orders(self) -> bool:
        """
        Cancel all orders through the event adapter.

        Returns:
            True if cancel all request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot cancel all orders.")
            return False

        try:
            return await self._event_adapter.cancel_all_orders()
        except Exception as e:
            logger.error(f"Failed to cancel all orders from component: {e}")
            return False

    async def request_account_info(self) -> bool:
        """
        Request account information update.

        Returns:
            True if request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot request account info.")
            return False

        try:
            return await self._event_adapter.request_account_info()
        except Exception as e:
            logger.error(f"Failed to request account info from component: {e}")
            return False

    async def request_position_info(self) -> bool:
        """
        Request position information update.

        Returns:
            True if request was successful
        """
        if not self._event_adapter:
            logger.error("Event adapter not set. Cannot request position info.")
            return False

        try:
            return await self._event_adapter.request_position_info()
        except Exception as e:
            logger.error(f"Failed to request position info from component: {e}")
            return False