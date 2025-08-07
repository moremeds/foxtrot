"""
Order monitor filtering functionality.

Handles filtering logic for order data display including status,
symbol, direction, and gateway filtering.
"""

from typing import Optional
from foxtrot.util.constants import Direction, Status
from foxtrot.util.object import OrderData


class OrderFilters:
    """Handles filtering logic for order monitor."""
    
    def __init__(self):
        """Initialize order filters."""
        # Filter settings
        self.status_filter: Optional[Status] = None
        self.symbol_filter: Optional[str] = None
        self.direction_filter: Optional[Direction] = None
        self.gateway_filter: Optional[str] = None
        self.show_only_active = False
    
    def passes_filters(self, order_data: OrderData) -> bool:
        """
        Check if order data passes current filter criteria.
        
        Args:
            order_data: The order data to check
            
        Returns:
            True if the order passes all active filters
        """
        # Status filter
        if self.status_filter is not None:
            if order_data.status != self.status_filter:
                return False
        
        # Active orders filter (overrides status filter)
        if self.show_only_active:
            if order_data.status not in [Status.NOTTRADED, Status.PARTTRADED, Status.SUBMITTING]:
                return False
        
        # Symbol filter
        if self.symbol_filter:
            if not order_data.symbol.lower().startswith(self.symbol_filter.lower()):
                return False
        
        # Direction filter
        if self.direction_filter is not None:
            if order_data.direction != self.direction_filter:
                return False
        
        # Gateway filter
        if self.gateway_filter:
            if order_data.gateway_name != self.gateway_filter:
                return False
        
        return True
    
    def set_status_filter(self, status: Optional[Status]) -> None:
        """Set status filter."""
        self.status_filter = status
    
    def set_symbol_filter(self, symbol: Optional[str]) -> None:
        """Set symbol filter."""
        self.symbol_filter = symbol.strip() if symbol else None
    
    def set_direction_filter(self, direction: Optional[Direction]) -> None:
        """Set direction filter."""
        self.direction_filter = direction
    
    def set_gateway_filter(self, gateway: Optional[str]) -> None:
        """Set gateway filter."""
        self.gateway_filter = gateway
    
    def set_active_only(self, active_only: bool) -> None:
        """Set active orders only filter."""
        self.show_only_active = active_only
    
    def clear_all_filters(self) -> None:
        """Clear all active filters."""
        self.status_filter = None
        self.symbol_filter = None
        self.direction_filter = None
        self.gateway_filter = None
        self.show_only_active = False
    
    def get_filter_summary(self) -> str:
        """
        Get a summary of currently active filters.
        
        Returns:
            String describing active filters
        """
        active_filters = []
        
        if self.status_filter:
            active_filters.append(f"Status: {self.status_filter.value}")
        
        if self.show_only_active:
            active_filters.append("Active Only")
        
        if self.symbol_filter:
            active_filters.append(f"Symbol: {self.symbol_filter}")
        
        if self.direction_filter:
            active_filters.append(f"Direction: {self.direction_filter.value}")
        
        if self.gateway_filter:
            active_filters.append(f"Gateway: {self.gateway_filter}")
        
        if not active_filters:
            return "No filters"
        
        return " | ".join(active_filters)
    
    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return any([
            self.status_filter is not None,
            self.symbol_filter is not None,
            self.direction_filter is not None,
            self.gateway_filter is not None,
            self.show_only_active
        ])
    
    def get_active_filter_count(self) -> int:
        """Get the number of active filters."""
        count = 0
        if self.status_filter is not None:
            count += 1
        if self.symbol_filter is not None:
            count += 1
        if self.direction_filter is not None:
            count += 1
        if self.gateway_filter is not None:
            count += 1
        if self.show_only_active:
            count += 1
        return count