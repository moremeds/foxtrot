"""
Dependency Injection Container for managing object creation and dependencies.

This module provides a centralized dependency injection container that:
- Eliminates circular import issues
- Provides explicit dependency management
- Enables easy testing through mock injection
- Follows the Dependency Inversion Principle
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Type, TypeVar

if TYPE_CHECKING:
    from ..util.request_objects import OrderRequest, CancelRequest, QuoteRequest
    from ..util.trading_objects import OrderData
    from ..util.market_objects import QuoteData

T = TypeVar('T')


class DIContainer:
    """
    Dependency Injection Container for managing object creation and dependencies.
    
    This container provides:
    - Registration of factories for different types
    - Lazy initialization to avoid circular imports
    - Override capability for testing
    - Type-safe object creation
    """
    
    def __init__(self):
        """Initialize the DI container with empty registrations."""
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._overrides: Dict[Type, Any] = {}
    
    def register_factory(self, cls: Type[T], factory: Callable[..., T]) -> None:
        """
        Register a factory function for a given class.
        
        Args:
            cls: The class type to register
            factory: The factory function that creates instances
        """
        self._factories[cls] = factory
    
    def register_singleton(self, cls: Type[T], instance: T) -> None:
        """
        Register a singleton instance for a given class.
        
        Args:
            cls: The class type to register
            instance: The singleton instance
        """
        self._singletons[cls] = instance
    
    def override(self, cls: Type[T], instance: T) -> None:
        """
        Override a registration for testing purposes.
        
        Args:
            cls: The class type to override
            instance: The override instance (typically a mock)
        """
        self._overrides[cls] = instance
    
    def clear_overrides(self) -> None:
        """Clear all overrides (useful for test cleanup)."""
        self._overrides.clear()
    
    def get(self, cls: Type[T], **kwargs) -> T:
        """
        Get an instance of the specified class.
        
        Args:
            cls: The class type to instantiate
            **kwargs: Additional arguments for the factory
            
        Returns:
            An instance of the requested class
            
        Raises:
            ValueError: If no factory is registered for the class
        """
        # Check for test overrides first
        if cls in self._overrides:
            return self._overrides[cls]
        
        # Check for singletons
        if cls in self._singletons:
            return self._singletons[cls]
        
        # Use factory
        if cls in self._factories:
            return self._factories[cls](**kwargs)
        
        raise ValueError(f"No registration found for {cls.__name__}")
    
    def create_order_data(
        self,
        request: "OrderRequest",
        orderid: str,
        adapter_name: str
    ) -> "OrderData":
        """
        Create OrderData from OrderRequest.
        
        Args:
            request: The order request object
            orderid: Unique order identifier
            adapter_name: Name of the adapter
            
        Returns:
            OrderData object created from the request
        """
        # Import here to avoid circular dependencies at module level
        from ..util.trading_objects import OrderData
        from ..util.constants import Status
        
        return OrderData(
            symbol=request.symbol,
            exchange=request.exchange,
            orderid=orderid,
            type=request.type,
            direction=request.direction,
            offset=request.offset,
            price=request.price,
            volume=request.volume,
            reference=request.reference,
            adapter_name=adapter_name,
            status=Status.SUBMITTING,
        )
    
    def create_cancel_request_from_order(self, order: "OrderData") -> "CancelRequest":
        """
        Create CancelRequest from OrderData.
        
        Args:
            order: The order data object
            
        Returns:
            CancelRequest object for canceling the order
        """
        from ..util.request_objects import CancelRequest
        
        return CancelRequest(
            orderid=order.orderid,
            symbol=order.symbol,
            exchange=order.exchange
        )
    
    def create_cancel_request_from_quote(self, quote: "QuoteData") -> "CancelRequest":
        """
        Create CancelRequest from QuoteData.
        
        Args:
            quote: The quote data object
            
        Returns:
            CancelRequest object for canceling the quote
        """
        from ..util.request_objects import CancelRequest
        
        return CancelRequest(
            orderid=quote.quoteid,
            symbol=quote.symbol,
            exchange=quote.exchange
        )
    
    def create_quote_data(
        self,
        request: "QuoteRequest",
        quoteid: str,
        adapter_name: str
    ) -> "QuoteData":
        """
        Create QuoteData from QuoteRequest.
        
        Args:
            request: The quote request object
            quoteid: Unique quote identifier
            adapter_name: Name of the adapter
            
        Returns:
            QuoteData object created from the request
        """
        from ..util.market_objects import QuoteData
        from ..util.constants import Status
        
        return QuoteData(
            symbol=request.symbol,
            exchange=request.exchange,
            quoteid=quoteid,
            bid_price=request.bid_price,
            bid_volume=request.bid_volume,
            ask_price=request.ask_price,
            ask_volume=request.ask_volume,
            bid_offset=request.bid_offset,
            ask_offset=request.ask_offset,
            status=Status.SUBMITTING,
            adapter_name=adapter_name,
        )


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """
    Get the global DI container instance.
    
    Returns:
        The global DIContainer instance
    """
    return _container


def create_order_data_from_request(
    request: "OrderRequest",
    orderid: str,
    adapter_name: str
) -> "OrderData":
    """
    Create OrderData from OrderRequest using DI container.
    
    This function maintains backward compatibility while using
    the DI container internally.
    
    Args:
        request: The order request object
        orderid: Unique order identifier
        adapter_name: Name of the adapter
        
    Returns:
        OrderData object created from the request
    """
    return _container.create_order_data(request, orderid, adapter_name)


def create_cancel_request_from_order(order: "OrderData") -> "CancelRequest":
    """
    Create CancelRequest from OrderData using DI container.
    
    This function maintains backward compatibility while using
    the DI container internally.
    
    Args:
        order: The order data object
        
    Returns:
        CancelRequest object for canceling the order
    """
    return _container.create_cancel_request_from_order(order)


def create_cancel_request_from_quote(quote: "QuoteData") -> "CancelRequest":
    """
    Create CancelRequest from QuoteData using DI container.
    
    This function maintains backward compatibility while using
    the DI container internally.
    
    Args:
        quote: The quote data object
        
    Returns:
        CancelRequest object for canceling the quote
    """
    return _container.create_cancel_request_from_quote(quote)


def create_quote_data_from_request(
    request: "QuoteRequest",
    quoteid: str,
    adapter_name: str
) -> "QuoteData":
    """
    Create QuoteData from QuoteRequest using DI container.
    
    This function maintains backward compatibility while using
    the DI container internally.
    
    Args:
        request: The quote request object
        quoteid: Unique quote identifier
        adapter_name: Name of the adapter
        
    Returns:
        QuoteData object created from the request
    """
    return _container.create_quote_data(request, quoteid, adapter_name)