"""
Order monitor statistics tracking.

Handles tracking and calculation of order statistics including
order counts, execution rates, and performance metrics.
"""

from typing import Any, Dict, Set
from foxtrot.util.constants import Status
from foxtrot.util.object import OrderData


class OrderStatistics:
    """Handles order statistics tracking and calculation."""
    
    def __init__(self):
        """Initialize order statistics tracker."""
        # Order tracking sets
        self.active_orders: Set[str] = set()
        self.completed_orders: Set[str] = set()
        
        # Statistics counters
        self.order_statistics: Dict[str, Any] = {
            "total_orders": 0,
            "filled_orders": 0,
            "cancelled_orders": 0,
            "rejected_orders": 0,
            "partial_filled": 0,
            "active_orders": 0,
            "submitting_orders": 0
        }
    
    def update_order_tracking(self, order_data: OrderData) -> None:
        """
        Update order tracking based on order status.
        
        Args:
            order_data: The order data to track
        """
        order_id = order_data.vt_orderid
        
        # Track active vs completed orders
        if order_data.status in [Status.NOTTRADED, Status.PARTTRADED, Status.SUBMITTING]:
            self.active_orders.add(order_id)
            self.completed_orders.discard(order_id)
        else:
            # Order is completed (filled, cancelled, or rejected)
            self.completed_orders.add(order_id)
            self.active_orders.discard(order_id)
    
    def update_order_statistics(self, order_data: OrderData) -> None:
        """
        Update order statistics based on order data.
        
        Args:
            order_data: The order data to process
        """
        # Update tracking first
        self.update_order_tracking(order_data)
        
        # Recalculate statistics from all tracked orders
        self._recalculate_statistics()
    
    def _recalculate_statistics(self) -> None:
        """Recalculate all statistics from tracking sets."""
        # Basic counts
        self.order_statistics["active_orders"] = len(self.active_orders)
        self.order_statistics["total_orders"] = (
            len(self.active_orders) + len(self.completed_orders)
        )
    
    def increment_status_counter(self, status: Status) -> None:
        """
        Increment counter for specific order status.
        
        Args:
            status: The order status to increment
        """
        if status == Status.ALLTRADED:
            self.order_statistics["filled_orders"] += 1
        elif status == Status.CANCELLED:
            self.order_statistics["cancelled_orders"] += 1
        elif status == Status.REJECTED:
            self.order_statistics["rejected_orders"] += 1
        elif status == Status.PARTTRADED:
            self.order_statistics["partial_filled"] += 1
        elif status == Status.SUBMITTING:
            self.order_statistics["submitting_orders"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current order statistics.
        
        Returns:
            Dictionary containing all order statistics
        """
        # Calculate derived statistics
        total = self.order_statistics["total_orders"]
        filled = self.order_statistics["filled_orders"]
        
        stats = self.order_statistics.copy()
        
        # Add calculated metrics
        if total > 0:
            stats["fill_rate"] = (filled / total) * 100
            stats["cancel_rate"] = (self.order_statistics["cancelled_orders"] / total) * 100
            stats["reject_rate"] = (self.order_statistics["rejected_orders"] / total) * 100
        else:
            stats["fill_rate"] = 0.0
            stats["cancel_rate"] = 0.0
            stats["reject_rate"] = 0.0
        
        return stats
    
    def get_statistics_summary(self) -> str:
        """
        Get formatted statistics summary string.
        
        Returns:
            Formatted statistics summary
        """
        stats = self.get_statistics()
        
        return (
            f"Orders: {stats['total_orders']} total, "
            f"{stats['active_orders']} active, "
            f"{stats['filled_orders']} filled "
            f"({stats['fill_rate']:.1f}% fill rate)"
        )
    
    def reset_statistics(self) -> None:
        """Reset all statistics and tracking."""
        self.active_orders.clear()
        self.completed_orders.clear()
        
        for key in self.order_statistics:
            self.order_statistics[key] = 0
    
    def get_active_order_count(self) -> int:
        """Get count of active orders."""
        return len(self.active_orders)
    
    def get_total_order_count(self) -> int:
        """Get total order count."""
        return len(self.active_orders) + len(self.completed_orders)
    
    def is_order_active(self, order_id: str) -> bool:
        """Check if order is currently active."""
        return order_id in self.active_orders