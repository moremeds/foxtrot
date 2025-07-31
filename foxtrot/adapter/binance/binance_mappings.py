"""
Binance Mappings - Data transformation utilities for Binance adapter.

This module provides centralized data transformations between CCXT library
formats and the foxtrot internal data structures.
"""


from foxtrot.util.constants import Direction, Exchange, OrderType, Status


def convert_symbol_to_ccxt(vt_symbol: str) -> str:
    """
    Convert VT symbol format to CCXT format.

    Args:
        vt_symbol: Symbol in VT format (e.g., "BTCUSDT.BINANCE")

    Returns:
        Symbol in CCXT format (e.g., "BTC/USDT")
    """
    try:
        # Must contain a dot for valid VT symbol format
        if "." not in vt_symbol:
            return ""

        symbol = vt_symbol.split(".")[0]

        # Validate symbol format
        if len(symbol) < 3:
            return ""

        # Enhanced symbol conversion with common trading pairs
        if symbol.endswith("USDT") and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/USDT"
        if symbol.endswith("BUSD") and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/BUSD"
        if symbol.endswith("USDC") and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/USDC"
        if symbol.endswith("BTC") and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/BTC"
        if symbol.endswith("ETH") and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/ETH"
        if symbol.endswith("BNB") and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/BNB"
        # Unknown format - default to USDT pair
        return f"{symbol}/USDT"

    except Exception:
        return ""


def convert_symbol_from_ccxt(ccxt_symbol: str, exchange: Exchange = Exchange.BINANCE) -> str:
    """
    Convert CCXT symbol format to VT format.

    Args:
        ccxt_symbol: Symbol in CCXT format (e.g., "BTC/USDT")
        exchange: Exchange enum value

    Returns:
        Symbol in VT format (e.g., "BTCUSDT.BINANCE")
    """
    try:
        base, quote = ccxt_symbol.split("/")
        return f"{base}{quote}.{exchange.value}"
    except Exception:
        return f"{ccxt_symbol}.{exchange.value}"


def convert_direction_to_ccxt(direction: Direction) -> str:
    """
    Convert VT direction to CCXT side format.

    Args:
        direction: VT Direction enum

    Returns:
        CCXT side string ("buy" or "sell")
    """
    if direction == Direction.LONG:
        return "buy"
    if direction == Direction.SHORT:
        return "sell"
    return "buy"  # Default to buy


def convert_direction_from_ccxt(ccxt_side: str) -> Direction:
    """
    Convert CCXT side to VT direction format.

    Args:
        ccxt_side: CCXT side string

    Returns:
        VT Direction enum
    """
    if ccxt_side.lower() == "buy":
        return Direction.LONG
    if ccxt_side.lower() == "sell":
        return Direction.SHORT
    return Direction.LONG  # Default to long


def convert_order_type_to_ccxt(order_type: OrderType) -> str:
    """
    Convert VT order type to CCXT type format.

    Args:
        order_type: VT OrderType enum

    Returns:
        CCXT order type string
    """
    type_map = {
        OrderType.MARKET: "market",
        OrderType.LIMIT: "limit",
        OrderType.STOP: "stop_market",
        OrderType.FAK: "immediate_or_cancel",
        OrderType.FOK: "fill_or_kill",
    }
    return type_map.get(order_type, "limit")


def convert_order_type_from_ccxt(ccxt_type: str) -> OrderType:
    """
    Convert CCXT order type to VT format.

    Args:
        ccxt_type: CCXT order type string

    Returns:
        VT OrderType enum
    """
    type_map = {
        "market": OrderType.MARKET,
        "limit": OrderType.LIMIT,
        "stop_market": OrderType.STOP,
        "stop_limit": OrderType.STOP,
        "immediate_or_cancel": OrderType.FAK,
        "fill_or_kill": OrderType.FOK,
    }
    return type_map.get(ccxt_type.lower(), OrderType.LIMIT)


def convert_status_from_ccxt(ccxt_status: str) -> Status:
    """
    Convert CCXT order status to VT format.

    Args:
        ccxt_status: CCXT order status string

    Returns:
        VT Status enum
    """
    status_map = {
        "open": Status.NOTTRADED,
        "closed": Status.ALLTRADED,
        "canceled": Status.CANCELLED,
        "cancelled": Status.CANCELLED,
        "partial": Status.PARTTRADED,
        "partially_filled": Status.PARTTRADED,
        "filled": Status.ALLTRADED,
        "expired": Status.CANCELLED,
        "rejected": Status.REJECTED,
        "pending": Status.SUBMITTING,
    }
    return status_map.get(ccxt_status.lower(), Status.SUBMITTING)


def convert_status_to_ccxt(status: Status) -> str:
    """
    Convert VT status to CCXT format.

    Args:
        status: VT Status enum

    Returns:
        CCXT status string
    """
    status_map = {
        Status.SUBMITTING: "pending",
        Status.NOTTRADED: "open",
        Status.PARTTRADED: "partial",
        Status.ALLTRADED: "closed",
        Status.CANCELLED: "canceled",
        Status.REJECTED: "rejected",
    }
    return status_map.get(status, "open")


def classify_error(error: Exception) -> str:
    """
    Classify CCXT errors into categories for appropriate handling.

    Args:
        error: Exception object from CCXT

    Returns:
        Error category string
    """
    error_str = str(error).lower()

    # Network and connectivity errors (retriable)
    if any(term in error_str for term in ["network", "timeout", "connection", "unavailable"]):
        return "network_error"

    # Authentication errors (not retriable)
    if any(
        term in error_str
        for term in ["authentication", "invalid api key", "signature", "timestamp"]
    ):
        return "auth_error"

    # Rate limiting (retriable with backoff)
    if any(term in error_str for term in ["rate limit", "too many requests", "429"]):
        return "rate_limit"

    # Invalid order parameters (not retriable)
    if any(term in error_str for term in ["invalid", "bad request", "insufficient", "minimum"]):
        return "invalid_request"

    # Market closed or symbol issues
    if any(term in error_str for term in ["market", "symbol", "not found", "trading pair"]):
        return "market_error"

    # Default to unknown error
    return "unknown_error"


def get_retry_delay(error_category: str, attempt: int) -> float:
    """
    Get appropriate retry delay based on error category and attempt number.

    Args:
        error_category: Error category from classify_error()
        attempt: Current retry attempt number (starting from 1)

    Returns:
        Delay in seconds, or 0 if should not retry
    """
    if error_category == "network_error":
        # Exponential backoff for network errors
        return min(2**attempt, 30)  # Max 30 seconds

    if error_category == "rate_limit":
        # Longer backoff for rate limiting
        return min(5 * (2**attempt), 60)  # Max 60 seconds

    if error_category in ["auth_error", "invalid_request", "market_error"]:
        # Don't retry these errors
        return 0

    # Default backoff for unknown errors
    return min(2**attempt, 10)  # Max 10 seconds


def should_retry_error(error_category: str, attempt: int, max_attempts: int = 3) -> bool:
    """
    Determine if an error should be retried.

    Args:
        error_category: Error category from classify_error()
        attempt: Current attempt number
        max_attempts: Maximum number of attempts allowed

    Returns:
        True if should retry, False otherwise
    """
    if attempt >= max_attempts:
        return False

    # Retry network and rate limit errors
    return error_category in ["network_error", "rate_limit", "unknown_error"]
