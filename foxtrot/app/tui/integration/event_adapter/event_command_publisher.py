"""
Event command publisher facade for EventEngineAdapter.

This module provides a unified interface to command publishing operations
by delegating to specialized modules for order commands, info requests, 
and response handling.
"""

from typing import Any, Dict

from foxtrot.core.event_engine import Event
from .command_responses import CommandResponses
from .info_requests import InfoRequests
from .order_commands import OrderCommands


class EventCommandPublisher:
    """Command publishing facade that delegates to specialized modules."""

    def __init__(self, adapter_ref):
        """Initialize command publisher with adapter reference."""
        self._adapter_ref = adapter_ref
        self._order_commands = OrderCommands(adapter_ref)
        self._info_requests = InfoRequests(adapter_ref)
        self._command_responses = CommandResponses(adapter_ref)

    # Order operations delegation
    async def publish_order(self, order_data: Dict[str, Any]) -> str:
        """Publish an order command to the MainEngine."""
        return await self._order_commands.publish_order(order_data)

    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """Cancel an existing order."""
        return await self._order_commands.cancel_order(order_id, symbol, exchange)

    async def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        return await self._order_commands.cancel_all_orders()

    # Information request operations delegation
    async def request_account_info(self) -> bool:
        """Request account information update."""
        return await self._info_requests.request_account_info()

    async def request_position_info(self) -> bool:
        """Request position information update."""
        return await self._info_requests.request_position_info()

    # Response handling delegation
    def handle_command_response(self, event: Event) -> None:
        """Handle command response events."""
        return self._command_responses.handle_command_response(event)

    def get_pending_commands_info(self) -> Dict[str, Any]:
        """Get information about pending commands."""
        return self._command_responses.get_pending_commands_info()