"""
Common utilities and factory functions for data object conversion.

This module breaks circular dependencies between util modules by providing
a centralized location for object creation and conversion functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..util.request_objects import OrderRequest, CancelRequest, QuoteRequest
    from ..util.trading_objects import OrderData
    from ..util.market_objects import QuoteData


def create_order_data_from_request(
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
    from ..util.trading_objects import OrderData
    from ..util.constants import Status
    
    order = OrderData(
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
    return order


def create_cancel_request_from_order(order: "OrderData") -> "CancelRequest":
    """
    Create CancelRequest from OrderData.
    
    Args:
        order: The order data object
        
    Returns:
        CancelRequest object for canceling the order
    """
    from ..util.request_objects import CancelRequest
    
    req = CancelRequest(
        orderid=order.orderid, 
        symbol=order.symbol, 
        exchange=order.exchange
    )
    return req


def create_cancel_request_from_quote(quote: "QuoteData") -> "CancelRequest":
    """
    Create CancelRequest from QuoteData.
    
    Args:
        quote: The quote data object
        
    Returns:
        CancelRequest object for canceling the quote
    """
    from ..util.request_objects import CancelRequest
    
    req = CancelRequest(
        orderid=quote.quoteid, 
        symbol=quote.symbol, 
        exchange=quote.exchange
    )
    return req


def create_quote_data_from_request(
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
    
    quote = QuoteData(
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
    return quote