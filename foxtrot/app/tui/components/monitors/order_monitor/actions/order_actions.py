"""
Order monitor action handlers.

Handles user actions for order management including filtering,
cancellation, and display configuration.
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from foxtrot.util.constants import Direction, Status
from foxtrot.util.object import OrderData

if TYPE_CHECKING:
    from ...order_monitor import TUIOrderMonitor


class OrderActions:
    """Handles action logic for order monitor."""
    
    def __init__(self, monitor: 'TUIOrderMonitor'):
        """Initialize order actions handler."""
        self.monitor = monitor
        self.main_engine = monitor.main_engine
    
    # Filter Actions
    def filter_by_status(self, status: Status) -> None:
        """Filter orders by status."""
        self.monitor.order_filters.set_status_filter(status)
        self._refresh_display()
    
    def filter_by_symbol(self, symbol: str) -> None:
        """Filter orders by symbol."""
        self.monitor.order_filters.set_symbol_filter(symbol)
        self._refresh_display()
    
    def filter_by_direction(self, direction: Direction) -> None:
        """Filter orders by direction."""
        self.monitor.order_filters.set_direction_filter(direction)
        self._refresh_display()
    
    def filter_by_gateway(self, gateway: str) -> None:
        """Filter orders by gateway."""
        self.monitor.order_filters.set_gateway_filter(gateway)
        self._refresh_display()
    
    def toggle_active_only(self) -> None:
        """Toggle show active orders only."""
        current_state = self.monitor.order_filters.show_only_active
        self.monitor.order_filters.set_active_only(not current_state)
        self._refresh_display()
    
    def clear_filters(self) -> None:
        """Clear all filters."""
        self.monitor.order_filters.clear_all_filters()
        self._refresh_display()
    
    # Quick Filter Actions
    def filter_active(self) -> None:
        """Show only active orders (NOTTRADED, PARTTRADED)."""
        self.monitor.order_filters.set_active_only(True)
        self._refresh_display()
    
    def filter_filled(self) -> None:
        """Filter by filled orders."""
        self.filter_by_status(Status.ALLTRADED)
    
    def filter_cancelled(self) -> None:
        """Filter by cancelled orders."""
        self.filter_by_status(Status.CANCELLED)
    
    def filter_long(self) -> None:
        """Filter by long direction."""
        self.filter_by_direction(Direction.LONG)
    
    def filter_short(self) -> None:
        """Filter by short direction."""
        self.filter_by_direction(Direction.SHORT)
    
    # Order Management Actions
    async def cancel_selected_order(self) -> None:
        """Cancel the currently selected order."""
        try:
            selected_data = self.monitor.get_selected_row_data()
            if not selected_data:
                await self.monitor._add_system_message("No order selected for cancellation")
                return
            
            order_data = selected_data
            if not isinstance(order_data, OrderData):
                await self.monitor._add_system_message("Invalid order data selected")
                return
            
            # Check if order can be cancelled
            if order_data.status in [Status.ALLTRADED, Status.CANCELLED, Status.REJECTED]:
                await self.monitor._add_system_message(
                    f"Cannot cancel order {order_data.orderid} - status: {order_data.status.value}"
                )
                return
            
            # Send cancel request
            self.main_engine.cancel_order(order_data.vt_orderid)
            
            await self.monitor._add_system_message(
                f"Cancel request sent for order {order_data.orderid}"
            )
            
            # Post message for external listeners
            await self.monitor.post_message(
                self.monitor.OrderCancelRequested(order_data)
            )
            
        except Exception as e:
            await self.monitor._add_system_message(f"Error cancelling order: {e}")
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> None:
        """
        Cancel all orders, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter cancellations
        """
        try:
            cancelled_count = 0
            
            # Get all active orders from the data
            for order_data in self.monitor.table_data.values():
                if not isinstance(order_data, OrderData):
                    continue
                
                # Check if order is cancellable
                if order_data.status not in [Status.NOTTRADED, Status.PARTTRADED, Status.SUBMITTING]:
                    continue
                
                # Apply symbol filter if specified
                if symbol and order_data.symbol != symbol:
                    continue
                
                # Send cancel request
                self.main_engine.cancel_order(order_data.vt_orderid)
                cancelled_count += 1
            
            if cancelled_count > 0:
                symbol_text = f" for {symbol}" if symbol else ""
                await self.monitor._add_system_message(
                    f"Cancel requests sent for {cancelled_count} orders{symbol_text}"
                )
                
                # Post message for external listeners
                await self.monitor.post_message(
                    self.monitor.AllOrdersCancelRequested(symbol)
                )
            else:
                await self.monitor._add_system_message("No cancellable orders found")
                
        except Exception as e:
            await self.monitor._add_system_message(f"Error cancelling orders: {e}")
    
    # Display Actions
    def toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to order updates."""
        self.monitor.auto_scroll_to_updates = not self.monitor.auto_scroll_to_updates
        status = "ON" if self.monitor.auto_scroll_to_updates else "OFF"
        asyncio.create_task(
            self.monitor._add_system_message(f"Auto-scroll {status}")
        )
    
    def toggle_highlight_recent(self) -> None:
        """Toggle highlighting of recent updates."""
        self.monitor.highlight_recent_updates = not self.monitor.highlight_recent_updates
        status = "ON" if self.monitor.highlight_recent_updates else "OFF"
        asyncio.create_task(
            self.monitor._add_system_message(f"Recent highlights {status}")
        )
    
    # Helper Methods
    def _refresh_display(self) -> None:
        """Refresh the monitor display after filter changes."""
        # Update filter display
        asyncio.create_task(self._update_filter_display())
        
        # Refresh table data
        self.monitor.refresh()
    
    async def _update_filter_display(self) -> None:
        """Update the filter display in the UI."""
        filter_summary = self.monitor.order_filters.get_filter_summary()
        await self.monitor._add_system_message(f"Filters: {filter_summary}")
    
    def get_available_symbols(self) -> list[str]:
        """Get list of symbols from current orders."""
        symbols = set()
        for order_data in self.monitor.table_data.values():
            if isinstance(order_data, OrderData):
                symbols.add(order_data.symbol)
        return sorted(list(symbols))
    
    def get_available_gateways(self) -> list[str]:
        """Get list of gateways from current orders."""
        gateways = set()
        for order_data in self.monitor.table_data.values():
            if isinstance(order_data, OrderData):
                gateways.add(order_data.gateway_name)
        return sorted(list(gateways))