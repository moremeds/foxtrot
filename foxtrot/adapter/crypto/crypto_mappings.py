"""
Crypto Mappings - Data transformation utilities for Crypto adapter.
"""

from typing import Dict, Optional

from foxtrot.util.constants import Direction, OrderType, Status, Exchange


def convert_symbol_to_ccxt(vt_symbol: str) -> str:
    """
    Convert VT symbol format to CCXT format.
    """
    try:
        if '.' not in vt_symbol:
            return ""

        symbol = vt_symbol.split('.')[0]

        if len(symbol) < 3:
            return ""

        if symbol.endswith('USDT') and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/USDT"
        elif symbol.endswith('BUSD') and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/BUSD"
        elif symbol.endswith('USDC') and len(symbol) > 4:
            base = symbol[:-4]
            return f"{base}/USDC"
        elif symbol.endswith('BTC') and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/BTC"
        elif symbol.endswith('ETH') and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/ETH"
        elif symbol.endswith('BNB') and len(symbol) > 3:
            base = symbol[:-3]
            return f"{base}/BNB"
        else:
            return f"{symbol}/USDT"

    except Exception:
        return ""


def convert_symbol_from_ccxt(ccxt_symbol: str, exchange: Exchange) -> str:
    """
    Convert CCXT symbol format to VT format.
    """
    try:
        base, quote = ccxt_symbol.split('/')
        return f"{base}{quote}.{exchange.value}"
    except Exception:
        return f"{ccxt_symbol}.{exchange.value}"


def convert_direction_to_ccxt(direction: Direction) -> str:
    """
    Convert VT direction to CCXT side format.
    """
    if direction == Direction.LONG:
        return "buy"
    elif direction == Direction.SHORT:
        return "sell"
    else:
        return "buy"


def convert_direction_from_ccxt(ccxt_side: str) -> Direction:
    """
    Convert CCXT side to VT direction format.
    """
    if ccxt_side.lower() == "buy":
        return Direction.LONG
    elif ccxt_side.lower() == "sell":
        return Direction.SHORT
    else:
        return Direction.LONG


def convert_order_type_to_ccxt(order_type: OrderType) -> str:
    """
    Convert VT order type to CCXT type format.
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
    """
    error_str = str(error).lower()

    if any(term in error_str for term in ["network", "timeout", "connection", "unavailable"]):
        return "network_error"

    if any(term in error_str for term in ["authentication", "invalid api key", "signature", "timestamp"]):
        return "auth_error"

    if any(term in error_str for term in ["rate limit", "too many requests", "429"]):
        return "rate_limit"

    if any(term in error_str for term in ["invalid", "bad request", "insufficient", "minimum"]):
        return "invalid_request"

    if any(term in error_str for term in ["market", "symbol", "not found", "trading pair"]):
        return "market_error"

    return "unknown_error"


def get_retry_delay(error_category: str, attempt: int) -> float:
    """
    Get appropriate retry delay based on error category and attempt number.
    """
    if error_category == "network_error":
        return min(2 ** attempt, 30)

    elif error_category == "rate_limit":
        return min(5 * (2 ** attempt), 60)

    elif error_category in ["auth_error", "invalid_request", "market_error"]:
        return 0

    else:
        return min(2 ** attempt, 10)


def should_retry_error(error_category: str, attempt: int, max_attempts: int = 3) -> bool:
    """
    Determine if an error should be retried.
    """
    if attempt >= max_attempts:
        return False

    if error_category in ["network_error", "rate_limit", "unknown_error"]:
        return True

    return False
