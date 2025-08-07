"""
Order command operations for EventEngineAdapter.

This module handles order-related command publishing including order placement,
cancellation, and bulk operations with proper timeout and response handling.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from foxtrot.core.event_engine import Event
from foxtrot.util.event_type import *
from foxtrot.util.object import CancelRequest, OrderData

logger = logging.getLogger(__name__)


class OrderCommands:
    """Order command publishing functionality for EventEngineAdapter."""

    def __init__(self, adapter_ref):
        """Initialize order commands with adapter reference."""
        self._adapter_ref = adapter_ref
    
    def _get_adapter(self):
        """Get adapter from weak reference with validation."""
        adapter = self._adapter_ref()
        if not adapter:
            raise RuntimeError("EventEngineAdapter reference is dead")
        if not adapter.is_started:
            raise RuntimeError("EventEngineAdapter is not started")
        return adapter

    async def publish_order(self, order_data: Dict[str, Any]) -> str:
        """Publish an order command to the MainEngine."""
        adapter = self._get_adapter()

        # Generate unique order ID
        order_id = f"TUI_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"

        # Create OrderData object
        from foxtrot.util.constants import Direction as DirectionEnum
        from foxtrot.util.constants import Exchange as ExchangeEnum
        from foxtrot.util.constants import OrderType as OrderTypeEnum

        order_obj = OrderData(
            symbol=order_data["symbol"],
            exchange=ExchangeEnum.SMART,  # Default exchange
            orderid=order_id,
            type=OrderTypeEnum.LIMIT,  # Convert string to enum
            direction=DirectionEnum.LONG if order_data["direction"] == "BUY" else DirectionEnum.SHORT,
            volume=float(order_data["volume"]),
            price=float(order_data.get("price", 0.0)),
            adapter_name="TUI"
        )

        # Create event
        event = Event(EVENT_ORDER, order_obj)

        # Create future for response tracking
        response_future = asyncio.Future()

        # Thread-safe pending command registration
        with adapter._pending_commands_lock:
            adapter.pending_commands[order_id] = response_future

        try:
            # Publish event to EventEngine
            adapter.event_engine.put(event)

            # Wait for response or timeout
            await asyncio.wait_for(response_future, timeout=adapter.command_timeout)

            logger.info(f"Order published successfully: {order_id}")
            return order_id

        except asyncio.TimeoutError:
            # Thread-safe cleanup of pending command
            with adapter._pending_commands_lock:
                adapter.pending_commands.pop(order_id, None)
            logger.error(f"Order command timed out: {order_id}")
            raise
        except Exception as e:
            # Thread-safe cleanup of pending command
            with adapter._pending_commands_lock:
                adapter.pending_commands.pop(order_id, None)
            logger.error(f"Failed to publish order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str, exchange: str = "") -> bool:
        """Cancel an existing order."""
        adapter = self._get_adapter()

        try:
            # Create cancel request
            cancel_req = CancelRequest(
                orderid=order_id,
                symbol=symbol,
                exchange=exchange
            )

            # Create event
            event = Event(EVENT_ORDER_CANCEL, cancel_req)

            # Publish event to EventEngine
            adapter.event_engine.put(event)

            logger.info(f"Cancel request published: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish cancel request: {e}")
            return False

    async def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        adapter = self._get_adapter()

        try:
            # Create cancel all event
            event = Event(EVENT_ORDER_CANCEL_ALL, {})

            # Publish event to EventEngine
            adapter.event_engine.put(event)

            logger.info("Cancel all orders request published")
            return True

        except Exception as e:
            logger.error(f"Failed to publish cancel all request: {e}")
            return False