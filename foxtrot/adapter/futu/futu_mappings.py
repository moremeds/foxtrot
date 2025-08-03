"""
Data mapping functions between Futu SDK and VT formats.

This module provides conversion functions between Futu OpenAPI data structures
and the standardized VT (Virtual Trading) data objects used in Foxtrot.
"""


from foxtrot.util.constants import Direction, Exchange, OrderType, Status
import futu as ft


def convert_symbol_to_futu_market(vt_symbol: str) -> tuple[str, str]:
    """
    Convert VT symbol to Futu SDK market and code format.

    Args:
        vt_symbol: VT format symbol (e.g., "0700.SEHK", "AAPL.NASDAQ")

    Returns:
        Tuple of (market, code) for Futu SDK (e.g., ("HK", "00700"), ("US", "AAPL"))

    Raises:
        ValueError: If exchange is not supported
    """
    symbol, exchange = vt_symbol.split(".")

    if exchange == "SEHK":
        # Hong Kong stocks - pad with zeros and use HK prefix
        return ("HK", f"HK.{symbol.zfill(5)}")
    if exchange in ["NASDAQ", "NYSE"]:
        # US stocks - use US prefix
        return ("US", f"US.{symbol}")
    if exchange in ["SZSE", "SSE"]:
        # China A-shares - use CN prefix
        return ("CN", f"CN.{symbol}")
    raise ValueError(f"Unsupported exchange: {exchange}")


def convert_futu_to_vt_symbol(market: str, code: str) -> str:
    """
    Convert Futu SDK format to VT symbol.

    Args:
        market: Futu market code (HK, US, CN)
        code: Futu stock code (e.g., "HK.00700", "US.AAPL")

    Returns:
        VT format symbol (e.g., "0700.SEHK", "AAPL.NASDAQ")

    Raises:
        ValueError: If market is not supported
    """
    # Remove market prefix from code
    clean_code = code.split(".", 1)[1] if "." in code else code

    if market == "HK":
        # For HK stocks, convert from padded format back to VT format
        # Input like "00700" should become "0700", "00005" should become "5"
        if clean_code.isdigit() and len(clean_code) >= 5:
            # For 5-digit padded format, intelligently restore original format
            num = int(clean_code)
            if num >= 100:  # 3+ digit numbers typically keep leading zero (like 0700)
                return f"{num:04d}.SEHK"
            # shorter numbers don't need padding (like 5)
            return f"{num}.SEHK"
        # Clean the leading zeros normally for non-standard formats
        stripped = clean_code.lstrip('0') or '0'
        return f"{stripped}.SEHK"
    if market == "US":
        # For US stocks, determine specific exchange (simplified - use NASDAQ as default)
        # In a production system, you'd query the actual exchange
        return f"{clean_code}.NASDAQ"
    if market == "CN":
        # For China stocks, determine specific exchange based on stock code
        # 6xxxxx codes go to SSE (Shanghai), others to SZSE (Shenzhen)
        if clean_code.startswith("6"):
            return f"{clean_code}.SSE"
        return f"{clean_code}.SZSE"
    raise ValueError(f"Unsupported market: {market}")


def convert_order_type_to_futu(order_type: OrderType) -> ft.OrderType:
    """
    Convert VT OrderType to Futu SDK OrderType.

    Args:
        order_type: VT order type

    Returns:
        Corresponding Futu SDK order type
    """
    mapping = {
        OrderType.LIMIT: ft.OrderType.NORMAL,      # Regular limit order
        OrderType.MARKET: ft.OrderType.MARKET,     # Market order
        OrderType.STOP: ft.OrderType.STOP,         # Stop order
    }
    return mapping.get(order_type, ft.OrderType.NORMAL)


def convert_futu_to_vt_order_type(futu_order_type: ft.OrderType) -> OrderType:
    """
    Convert Futu SDK OrderType to VT OrderType.

    Args:
        futu_order_type: Futu SDK order type

    Returns:
        Corresponding VT order type
    """
    mapping = {
        ft.OrderType.NORMAL: OrderType.LIMIT,
        ft.OrderType.MARKET: OrderType.MARKET,
        ft.OrderType.STOP: OrderType.STOP,
    }
    return mapping.get(futu_order_type, OrderType.LIMIT)


def convert_direction_to_futu(direction: Direction) -> ft.TrdSide:
    """
    Convert VT Direction to Futu SDK TrdSide.

    Args:
        direction: VT direction

    Returns:
        Corresponding Futu SDK trade side
    """
    mapping = {
        Direction.LONG: ft.TrdSide.BUY,
        Direction.SHORT: ft.TrdSide.SELL,
    }
    return mapping.get(direction, ft.TrdSide.BUY)


def convert_futu_to_vt_direction(futu_trd_side: ft.TrdSide) -> Direction:
    """
    Convert Futu SDK TrdSide to VT Direction.

    Args:
        futu_trd_side: Futu SDK trade side

    Returns:
        Corresponding VT direction
    """
    mapping = {
        ft.TrdSide.BUY: Direction.LONG,
        ft.TrdSide.SELL: Direction.SHORT,
    }
    return mapping.get(futu_trd_side, Direction.LONG)


def convert_futu_order_status(futu_status: ft.OrderStatus) -> Status:
    """
    Convert Futu SDK order status to VT Status.

    Args:
        futu_status: Futu SDK order status

    Returns:
        Corresponding VT status
    """
    mapping = {
        ft.OrderStatus.NONE: Status.SUBMITTING,
        ft.OrderStatus.UNSUBMITTED: Status.NOTTRADED,
        ft.OrderStatus.WAITING_SUBMIT: Status.SUBMITTING,
        ft.OrderStatus.SUBMITTING: Status.SUBMITTING,
        ft.OrderStatus.SUBMITTED: Status.NOTTRADED,
        ft.OrderStatus.FILLED_PART: Status.PARTTRADED,
        ft.OrderStatus.FILLED_ALL: Status.ALLTRADED,
        ft.OrderStatus.CANCELLED_PART: Status.PARTTRADED,
        ft.OrderStatus.CANCELLED_ALL: Status.CANCELLED,
        ft.OrderStatus.FAILED: Status.REJECTED,
        ft.OrderStatus.DISABLED: Status.REJECTED,
        ft.OrderStatus.DELETED: Status.CANCELLED,
    }
    return mapping.get(futu_status, Status.SUBMITTING)


def convert_futu_market_to_exchange(market: str) -> Exchange:
    """
    Convert Futu market string to VT Exchange.

    Args:
        market: Futu market code (HK, US, CN)

    Returns:
        Corresponding VT exchange

    Raises:
        ValueError: If market is not supported
    """
    mapping = {
        "HK": Exchange.SEHK,
        "US": Exchange.NASDAQ,  # Default for US stocks
        "CN": Exchange.SZSE,    # Default for CN stocks
    }

    return mapping.get(market, Exchange.SEHK)  # Default to SEHK


def get_futu_trd_market(market: str) -> ft.TrdMarket:
    """
    Convert market string to Futu SDK TrdMarket enum.

    Args:
        market: Market identifier (HK, US, CN)

    Returns:
        Corresponding Futu SDK TrdMarket
    """
    mapping = {
        "HK": ft.TrdMarket.HK,
        "US": ft.TrdMarket.US,
        "CN": ft.TrdMarket.CN,  # Using CN instead of CN_SH for consistency
    }
    return mapping.get(market, ft.TrdMarket.HK)


def get_futu_market_enum(market: str) -> ft.Market:
    """
    Convert market string to Futu SDK Market enum.

    Args:
        market: Market identifier (HK, US, CN)

    Returns:
        Corresponding Futu SDK Market enum
    """
    if market == "HK":
        return ft.Market.HK
    if market == "US":
        return ft.Market.US
    if market == "CN":
        # Try CN_SH first, fallback to HK if not available
        if hasattr(ft.Market, 'CN_SH'):
            return ft.Market.CN_SH
        return ft.Market.HK  # Fallback
    return ft.Market.HK  # Default


def validate_symbol_format(vt_symbol: str) -> bool:
    """
    Validate VT symbol format for Futu compatibility.

    Args:
        vt_symbol: VT format symbol

    Returns:
        True if valid, False otherwise
    """
    try:
        symbol, exchange = vt_symbol.split(".")

        # Check if exchange is supported
        supported_exchanges = ["SEHK", "NASDAQ", "NYSE", "SZSE", "SSE"]
        if exchange not in supported_exchanges:
            return False

        # Basic symbol validation
        if not symbol or len(symbol) > 20:
            return False

        # Exchange-specific validation
        if exchange == "SEHK":
            # Hong Kong stocks are typically numeric (e.g., "0700", "00700")
            # Also allow some special symbols like ETFs
            if not (symbol.isdigit() or 
                   (len(symbol) >= 4 and symbol[:2].isdigit() and symbol[2:].isdigit())):
                return False
        elif exchange in ["NASDAQ", "NYSE"]:
            # US stocks are typically alphabetic symbols (e.g., "AAPL", "TSLA")
            if not symbol.replace(".", "").isalpha():
                return False
        elif exchange in ["SZSE", "SSE"]:
            # China A-shares are typically numeric (e.g., "000001", "600000")
            if not symbol.isdigit():
                return False

        return True

    except ValueError:
        return False


def get_market_from_vt_symbol(vt_symbol: str) -> str:
    """
    Extract market identifier from VT symbol.

    Args:
        vt_symbol: VT format symbol

    Returns:
        Market identifier (HK, US, or CN)

    Raises:
        ValueError: If symbol format is invalid
    """
    try:
        symbol, exchange = vt_symbol.split(".")

        if exchange == "SEHK":
            return "HK"
        if exchange in ["NASDAQ", "NYSE"]:
            return "US"
        if exchange in ["SZSE", "SSE"]:
            return "CN"
        raise ValueError(f"Unsupported exchange: {exchange}")

    except ValueError as e:
        raise ValueError(f"Invalid VT symbol format: {vt_symbol}") from e
