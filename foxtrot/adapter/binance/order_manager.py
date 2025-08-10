"""
Binance Order Manager - Handles order lifecycle management.

This module manages order operations including creation, tracking, cancellation,
and trade event generation.
"""

from datetime import datetime
import math
import threading
from typing import TYPE_CHECKING, Any, Optional

from foxtrot.util.constants import Direction, Exchange, OrderType, Status
from foxtrot.util.object import CancelRequest, OrderData, OrderRequest

# datetime import removed - using datetime.now() directly

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


class BinanceOrderManager:
    """
    Manager for Binance order operations.

    Handles order creation, tracking, cancellation, and status updates.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the order manager."""
        self.api_client = api_client
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.Lock()
        self._local_order_id = 0

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order to Binance.

        Args:
            req: Order request object

        Returns:
            Local order ID string
        """
        try:
            if not self.api_client.exchange:
                self.api_client._log_error("Exchange not connected")
                return ""

            # Generate local order ID
            with self._order_lock:
                self._local_order_id += 1
                local_orderid = f"{self.api_client.adapter_name}_{self._local_order_id}"

            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.symbol)
            if not ccxt_symbol:
                self.api_client._log_error(f"Invalid symbol: {req.symbol}")
                return ""

            # Convert order parameters
            side = "buy" if req.direction == Direction.LONG else "sell"
            order_type = self._convert_order_type_to_ccxt(req.type)

            # Create order data
            order = OrderData(
                adapter_name=self.api_client.adapter_name,
                # Store base symbol (no suffix); VT fields are computed in OrderData
                symbol=(req.symbol.split(".")[0] if "." in req.symbol else req.symbol),
                exchange=Exchange.BINANCE,
                orderid=local_orderid,
                type=req.type,
                direction=req.direction,
                volume=req.volume,
                price=req.price,
                status=Status.SUBMITTING,
                datetime=datetime.now(),
            )

            # Store order locally
            with self._order_lock:
                self._orders[local_orderid] = order
            # Emit submitting event
            if hasattr(self.api_client, "adapter") and self.api_client.adapter:
                try:
                    self.api_client.adapter.on_order(order)
                except Exception:
                    pass

            # Prepare price/amount respecting CCXT/Binance filters
            amount_to_send = float(req.volume)
            price_to_send: Optional[float] = None
            if order_type == "limit":
                price_to_send = float(req.price)

            amount_to_send, price_to_send = self._apply_symbol_filters(
                ccxt_symbol=ccxt_symbol,
                side=side,
                order_type=order_type,
                amount=amount_to_send,
                price=price_to_send,
            )

            # Send order to exchange
            if order_type == "market":
                result = self.api_client.exchange.create_market_order(
                    ccxt_symbol, side, amount_to_send
                )
            else:
                result = self.api_client.exchange.create_limit_order(
                    ccxt_symbol, side, amount_to_send, price_to_send
                )

            if result:
                # Update order with exchange information
                order.orderid = str(result.get("id", local_orderid))
                order.status = self._convert_status_from_ccxt(result.get("status", "open"))
                # Reflect possibly adjusted price/amount
                order.price = float(price_to_send) if price_to_send is not None else order.price
                order.volume = float(amount_to_send)

                with self._order_lock:
                    self._orders[local_orderid] = order
                # Fire order event update
                if hasattr(self.api_client, "adapter") and self.api_client.adapter:
                    try:
                        self.api_client.adapter.on_order(order)
                    except Exception:
                        pass

                self.api_client._log_info(f"Order sent successfully: {local_orderid}")
                return order.vt_orderid
            self.api_client._log_error("Failed to send order - no response")
            return ""

        except Exception as e:
            # Fire rejected event
            try:
                order.status = Status.REJECTED
                if hasattr(self.api_client, "adapter") and self.api_client.adapter:
                    self.api_client.adapter.on_order(order)
            except Exception:
                pass
            self.api_client._log_error(f"Failed to send order: {str(e)}")
            return ""

    def cancel_order(self, req: CancelRequest) -> bool:
        """
        Cancel an order.

        Args:
            req: Cancel request object

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            if not self.api_client.exchange:
                return False

            with self._order_lock:
                order = self._orders.get(req.orderid)

            if not order:
                self.api_client._log_error(f"Order not found: {req.orderid}")
                return False

            # Convert symbol format
            # order.vt_symbol has proper VT suffix; use that for conversion
            ccxt_symbol = self._convert_symbol_to_ccxt(order.vt_symbol)
            if not ccxt_symbol:
                return False

            # Cancel order on exchange
            result = self.api_client.exchange.cancel_order(order.orderid, ccxt_symbol)

            if result:
                # Update order status
                order.status = Status.CANCELLED
                with self._order_lock:
                    self._orders[req.orderid] = order
                # Emit cancel event
                if hasattr(self.api_client, "adapter") and self.api_client.adapter:
                    try:
                        self.api_client.adapter.on_order(order)
                    except Exception:
                        pass

                self.api_client._log_info(f"Order cancelled: {req.orderid}")
                return True
            return False

        except Exception as e:
            self.api_client._log_error(f"Failed to cancel order: {str(e)}")
            return False

    def query_order(self, orderid: str) -> OrderData | None:
        """
        Query order status.

        Args:
            orderid: Order ID to query

        Returns:
            OrderData if found, None otherwise
        """
        with self._order_lock:
            return self._orders.get(orderid)

    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
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

            # Validate minimum symbol length
            if len(symbol) < 3:
                return ""

            # Convert BTCUSDT to BTC/USDT format
            if symbol.endswith("USDT") and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            if symbol.endswith("BTC") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            if symbol.endswith("ETH") and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            # Unknown format - default to USDT pair
            return f"{symbol}/USDT"
        except Exception:
            return ""

    def _convert_order_type_to_ccxt(self, order_type: OrderType) -> str:
        """Convert VT order type to CCXT format."""
        if order_type == OrderType.MARKET:
            return "market"
        if order_type == OrderType.LIMIT:
            return "limit"
        return "limit"  # Default to limit

    def _convert_status_from_ccxt(self, ccxt_status: str) -> Status:
        """Convert CCXT order status to VT format."""
        status_map = {
            "open": Status.NOTTRADED,
            "closed": Status.ALLTRADED,
            "canceled": Status.CANCELLED,
            "cancelled": Status.CANCELLED,
            "partial": Status.PARTTRADED,
            "expired": Status.CANCELLED,
        }
        return status_map.get(ccxt_status.lower(), Status.SUBMITTING)

    # ---------------------------------
    # CCXT / Binance filters integration
    # ---------------------------------
    def _apply_symbol_filters(
        self,
        ccxt_symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: Optional[float],
    ) -> tuple[float, Optional[float]]:
        """
        Apply Binance/CCXT filters to amount and price.

        Ensures LOT_SIZE, PRICE_FILTER, MIN_NOTIONAL, and PERCENT_PRICE_BY_SIDE
        are satisfied. For limit orders with out-of-band price, clamps into the
        valid range and nudges to avoid immediate execution while staying valid.
        """
        exchange = self.api_client.exchange
        if not exchange:
            return amount, price

        # Ensure market metadata is loaded
        try:
            market: dict[str, Any] = exchange.market(ccxt_symbol)
        except Exception:
            exchange.load_markets()
            market = exchange.market(ccxt_symbol)

        precision = market.get("precision", {}) or {}
        amount_precision = int(precision.get("amount", 8) or 8)
        price_precision = int(precision.get("price", 8) or 8)

        info_filters = {}
        for f in market.get("info", {}).get("filters", []):
            ftype = f.get("filterType")
            if ftype:
                info_filters[ftype] = f

        # LOT_SIZE
        step_size = None
        min_qty = None
        lot = info_filters.get("LOT_SIZE")
        if lot:
            step_size = float(lot.get("stepSize", 0) or 0)
            min_qty = float(lot.get("minQty", 0) or 0)

        # PRICE_FILTER
        tick_size = None
        price_filter = info_filters.get("PRICE_FILTER")
        if price_filter:
            tick_size = float(price_filter.get("tickSize", 0) or 0)
            min_price = float(price_filter.get("minPrice", 0) or 0)
            max_price = float(price_filter.get("maxPrice", 0) or 0)
        else:
            min_price = 0.0
            max_price = float("inf")

        # PERCENT_PRICE_BY_SIDE
        percent_by_side = info_filters.get("PERCENT_PRICE_BY_SIDE")

        # Fetch current market to choose a safe non-executing price
        # and to compute percent-price bounds
        last_price = None
        best_bid = None
        best_ask = None
        try:
            ticker = exchange.fetch_ticker(ccxt_symbol)
            last_price = float(
                ticker.get("last")
                or ticker.get("close")
                or ticker.get("bid")
                or ticker.get("ask")
                or 0
            ) or None
            best_bid = float(ticker.get("bid") or 0) or None
            best_ask = float(ticker.get("ask") or 0) or None
        except Exception:
            pass

        # Adjust price for limit orders
        adjusted_price = price
        if order_type == "limit":
            reference_price = last_price or best_bid or best_ask
            if reference_price is None:
                reference_price = 0.0

            # Compute percent-price-by-side bounds if available
            lower_bound = min_price if min_price > 0 else 0.0
            upper_bound = max_price if math.isfinite(max_price) else float("inf")
            if percent_by_side and reference_price > 0:
                try:
                    if side == "buy":
                        down = float(percent_by_side.get("bidMultiplierDown", 1))
                        up = float(percent_by_side.get("bidMultiplierUp", 1))
                    else:
                        down = float(percent_by_side.get("askMultiplierDown", 1))
                        up = float(percent_by_side.get("askMultiplierUp", 1))
                    lower_bound = max(lower_bound, reference_price * down)
                    upper_bound = min(upper_bound, reference_price * up)
                except Exception:
                    pass

            # Choose a target that avoids immediate execution but stays valid
            if side == "buy":
                target = (best_bid * 0.999) if best_bid else (reference_price * 0.995)
                adjusted_price = max(min(target, upper_bound), lower_bound)
            else:
                target = (best_ask * 1.001) if best_ask else (reference_price * 1.005)
                adjusted_price = max(min(target, upper_bound), lower_bound)

            # Apply tickSize and exchange precision
            if tick_size and tick_size > 0:
                # Snap to tick grid properly depending on side
                steps = adjusted_price / tick_size
                steps = math.floor(steps) if side == "buy" else math.ceil(steps)
                adjusted_price = steps * tick_size

            try:
                adjusted_price = float(exchange.price_to_precision(ccxt_symbol, adjusted_price))
            except Exception:
                # Fallback rounding
                adjusted_price = round(adjusted_price, price_precision)

        # Adjust amount to LOT_SIZE and MIN_NOTIONAL
        adjusted_amount = amount
        if step_size and step_size > 0:
            steps = adjusted_amount / step_size
            steps = math.floor(steps)
            adjusted_amount = steps * step_size
        try:
            adjusted_amount = float(exchange.amount_to_precision(ccxt_symbol, adjusted_amount))
        except Exception:
            adjusted_amount = round(adjusted_amount, amount_precision)
        if min_qty and adjusted_amount < min_qty:
            # Bump to minimum quantity
            multiplier = math.ceil((min_qty + 1e-12) / max(adjusted_amount, 1e-12))
            adjusted_amount = max(min_qty, adjusted_amount * multiplier)
            if step_size and step_size > 0:
                steps = math.ceil(adjusted_amount / step_size)
                adjusted_amount = steps * step_size
            try:
                adjusted_amount = float(exchange.amount_to_precision(ccxt_symbol, adjusted_amount))
            except Exception:
                adjusted_amount = round(adjusted_amount, amount_precision)

        # MIN_NOTIONAL constraint
        min_notional = None
        min_notional_filter = info_filters.get("MIN_NOTIONAL")
        if min_notional_filter:
            min_notional = float(min_notional_filter.get("minNotional", 0) or 0)
        notional_price = adjusted_price if (order_type == "limit" and adjusted_price) else (best_ask if side == "buy" else best_bid) or last_price or 0.0
        if min_notional and notional_price:
            notional = adjusted_amount * notional_price
            if notional < min_notional:
                required_amount = (min_notional + 1e-12) / max(notional_price, 1e-12)
                if step_size and step_size > 0:
                    steps = math.ceil(required_amount / step_size)
                    required_amount = steps * step_size
                try:
                    adjusted_amount = float(exchange.amount_to_precision(ccxt_symbol, required_amount))
                except Exception:
                    adjusted_amount = round(required_amount, amount_precision)

        return adjusted_amount, adjusted_price
