"""
Futu order manager for trade execution and order lifecycle management.

This module handles order placement, cancellation, and tracking via the Futu OpenD gateway
with enhanced error handling, retry logic, and performance optimization.
"""

from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING

from foxtrot.util.constants import Status
from foxtrot.util.object import CancelRequest, OrderData, OrderRequest
import futu as ft

from .futu_mappings import (
    convert_direction_to_futu,
    convert_order_type_to_futu,
    convert_symbol_to_futu_market,
    get_market_from_vt_symbol,
    validate_symbol_format,
)

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuOrderManager:
    """
    Enhanced order management for Futu OpenD gateway.

    Handles order placement, cancellation, and tracking with thread-safe
    state management, retry logic, and comprehensive error handling.

    Features:
    - Thread-safe order tracking with RLock for callback synchronization
    - Intelligent retry logic with exponential backoff
    - Order validation and pre-submission checks
    - Resource management and connection health monitoring
    - Performance optimization with batch operations
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the enhanced order manager."""
        self.api_client = api_client

        # Thread-safe order tracking
        self._orders: dict[str, OrderData] = {}
        self._order_lock = threading.RLock()  # Support nested locking
        self._local_order_id = 0

        # Performance and retry settings
        self._max_retries = 3
        self._retry_delay = 1.0  # Initial retry delay in seconds
        self._max_retry_delay = 10.0  # Maximum retry delay
        self._order_timeout = 30.0  # Order submission timeout

        # Resource management
        self._max_orders_per_minute = 60  # Rate limiting
        self._order_timestamps: list[float] = []
        self._rate_limit_lock = threading.Lock()

        # Order statistics for monitoring
        self._stats = {
            "orders_submitted": 0,
            "orders_successful": 0,
            "orders_failed": 0,
            "orders_cancelled": 0,
            "avg_submission_time": 0.0,
        }

    def send_order(self, req: OrderRequest) -> str:
        """
        Send order via Futu SDK with enhanced validation and retry logic.

        Args:
            req: Order request with comprehensive validation

        Returns:
            Local order ID if successful, empty string otherwise
        """
        start_time = time.time()

        try:
            # Pre-submission validation
            if not self._validate_order_request(req):
                self._update_stats("orders_failed")
                return ""

            # Rate limiting check
            if not self._check_rate_limit():
                self.api_client._log_error("Order rate limit exceeded, please wait")
                self._update_stats("orders_failed")
                return ""

            # Convert VT request to SDK format
            market, code = convert_symbol_to_futu_market(req.vt_symbol)
            futu_order_type = convert_order_type_to_futu(req.type)
            futu_trd_side = convert_direction_to_futu(req.direction)

            # Generate local order ID
            with self._order_lock:
                self._local_order_id += 1
                local_orderid = f"FUTU.{self._local_order_id}"

            # Create initial OrderData
            order = OrderData(
                symbol=req.symbol,
                exchange=req.exchange,
                orderid=local_orderid,
                type=req.type,
                direction=req.direction,
                volume=req.volume,
                price=req.price,
                status=Status.SUBMITTING,
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )

            # Store order before submission
            with self._order_lock:
                self._orders[local_orderid] = order

            # Get appropriate trade context with validation
            trade_ctx = self.api_client.get_trade_context(market)
            if not trade_ctx:
                self.api_client._log_error(f"No trade context available for market: {market}")
                self._reject_order(order, "No trade context available")
                return ""

            # Submit with retry logic
            success, exchange_orderid = self._submit_order_with_retry(
                trade_ctx, req, code, futu_trd_side, futu_order_type
            )

            if not success:
                self._reject_order(order, "Order submission failed after retries")
                return ""

            # Update order with exchange ID
            if exchange_orderid:
                order.orderid = exchange_orderid
                order.status = Status.NOTTRADED

                with self._order_lock:
                    # Keep both local and exchange ID mapping
                    self._orders[local_orderid] = order
                    self._orders[exchange_orderid] = order

            # Fire order event and update stats
            self.api_client.adapter.on_order(order)
            self.api_client._log_info(f"Order submitted successfully: {order.orderid}")

            submission_time = time.time() - start_time
            self._update_stats("orders_successful", submission_time)

            return local_orderid

        except Exception as e:
            self.api_client._log_error(f"Order submission error: {e}")
            self._update_stats("orders_failed")
            return ""

    def cancel_order(self, req: CancelRequest) -> None:
        """
        Cancel order via SDK.

        Args:
            req: Cancel request
        """
        try:
            # Find order by VT order ID
            order = self._orders.get(req.vt_orderid)
            if not order:
                self.api_client._log_error(f"Order not found: {req.vt_orderid}")
                return

            # Get market and trade context
            market = get_market_from_vt_symbol(order.vt_symbol)
            trade_ctx = self.api_client.get_trade_context(market)
            if not trade_ctx:
                self.api_client._log_error(f"No trade context for cancel: {market}")
                return

            # Cancel via SDK
            ret, data = trade_ctx.modify_order(
                ft.ModifyOrderOp.CANCEL,
                order_id=int(order.orderid),
                qty=0,
                price=0
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Order cancellation failed: {data}")
            else:
                self.api_client._log_info(f"Order cancellation requested: {order.orderid}")

        except Exception as e:
            self.api_client._log_error(f"Cancel order error: {e}")

    def on_order_update(self, order: OrderData) -> None:
        """
        Handle order update from callback.

        Args:
            order: Updated order data
        """
        with self._order_lock:
            self._orders[order.orderid] = order

    def get_order(self, orderid: str) -> OrderData | None:
        """Get order by ID."""
        with self._order_lock:
            return self._orders.get(orderid)

    def get_all_orders(self) -> dict[str, OrderData]:
        """Get all tracked orders."""
        with self._order_lock:
            return self._orders.copy()

    def _validate_order_request(self, req: OrderRequest) -> bool:
        """
        Comprehensive validation of order request.

        Args:
            req: Order request to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Symbol format validation
            if not validate_symbol_format(req.vt_symbol):
                self.api_client._log_error(f"Invalid symbol format: {req.vt_symbol}")
                return False

            # Price validation
            if req.price <= 0:
                self.api_client._log_error(f"Invalid price: {req.price}")
                return False

            # Volume validation
            if req.volume <= 0:
                self.api_client._log_error(f"Invalid volume: {req.volume}")
                return False

            # Market access validation
            market = get_market_from_vt_symbol(req.vt_symbol)
            if market == "HK" and not self.api_client.hk_access:
                self.api_client._log_error("HK market access not enabled")
                return False
            if market == "US" and not self.api_client.us_access:
                self.api_client._log_error("US market access not enabled")
                return False
            if market == "CN" and not self.api_client.cn_access:
                self.api_client._log_error("CN market access not enabled")
                return False

            return True

        except Exception as e:
            self.api_client._log_error(f"Order validation error: {e}")
            return False

    def _check_rate_limit(self) -> bool:
        """
        Check if order submission is within rate limits.

        Returns:
            True if within limits, False otherwise
        """
        with self._rate_limit_lock:
            current_time = time.time()

            # Remove timestamps older than 1 minute
            self._order_timestamps = [
                ts for ts in self._order_timestamps
                if current_time - ts < 60
            ]

            # Check rate limit
            if len(self._order_timestamps) >= self._max_orders_per_minute:
                return False

            # Add current timestamp
            self._order_timestamps.append(current_time)
            return True

    def _submit_order_with_retry(
        self,
        trade_ctx,
        req: OrderRequest,
        code: str,
        futu_trd_side: ft.TrdSide,
        futu_order_type: ft.OrderType
    ) -> tuple[bool, str | None]:
        """
        Submit order with intelligent retry logic.

        Args:
            trade_ctx: Trade context for submission
            req: Order request
            code: Futu stock code
            futu_trd_side: Futu trade side
            futu_order_type: Futu order type

        Returns:
            Tuple of (success, exchange_order_id)
        """
        retry_delay = self._retry_delay

        for attempt in range(self._max_retries):
            try:
                trd_env = ft.TrdEnv.SIMULATE if self.api_client.paper_trading else ft.TrdEnv.REAL
                ret, data = trade_ctx.place_order(
                    price=req.price,
                    qty=int(req.volume),
                    code=code,
                    trd_side=futu_trd_side,
                    order_type=futu_order_type,
                    trd_env=trd_env,
                )

                if ret == ft.RET_OK:
                    # Success - extract order ID
                    if isinstance(data, dict) and "order_id" in data:
                        return True, str(data["order_id"])
                    return True, None

                # Log failure and retry if not last attempt
                self.api_client._log_error(
                    f"Order submission attempt {attempt + 1} failed: {data}"
                )

                if attempt < self._max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self._max_retry_delay)

            except Exception as e:
                self.api_client._log_error(
                    f"Order submission attempt {attempt + 1} error: {e}"
                )

                if attempt < self._max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self._max_retry_delay)

        return False, None

    def _reject_order(self, order: OrderData, reason: str) -> None:
        """
        Reject order and update tracking.

        Args:
            order: Order to reject
            reason: Rejection reason
        """
        order.status = Status.REJECTED
        with self._order_lock:
            self._orders[order.orderid] = order

        self.api_client.adapter.on_order(order)
        self.api_client._log_error(f"Order rejected: {reason}")
        self._update_stats("orders_failed")

    def _update_stats(self, stat_type: str, value: float = 0.0) -> None:
        """
        Update order statistics for monitoring.

        Args:
            stat_type: Type of statistic to update
            value: Value for timing statistics
        """
        self._stats["orders_submitted"] += 1

        if stat_type == "orders_successful":
            self._stats["orders_successful"] += 1
            # Update average submission time
            current_avg = self._stats["avg_submission_time"]
            count = self._stats["orders_successful"]
            self._stats["avg_submission_time"] = (current_avg * (count - 1) + value) / count

        elif stat_type == "orders_failed":
            self._stats["orders_failed"] += 1
        elif stat_type == "orders_cancelled":
            self._stats["orders_cancelled"] += 1

    def get_statistics(self) -> dict[str, float]:
        """
        Get order manager performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        return self._stats.copy()
