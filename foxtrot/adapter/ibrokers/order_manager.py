"""
Order management for Interactive Brokers.
"""

from copy import copy
from datetime import datetime
from decimal import Decimal

from ibapi.common import OrderId
from ibapi.contract import Contract
from ibapi.execution import Execution
from ibapi.order import Order
from ibapi.order_cancel import OrderCancel
from ibapi.order_state import OrderState

from foxtrot.util.constants import Exchange, OrderType
from foxtrot.util.object import CancelRequest, OrderData, OrderRequest, TradeData
from foxtrot.util.utility import ZoneInfo

from .contract_manager import generate_ib_contract
from .ib_mappings import (
    DIRECTION_IB2VT,
    DIRECTION_VT2IB,
    EXCHANGE_IB2VT,
    EXCHANGE_VT2IB,
    ORDERTYPE_IB2VT,
    ORDERTYPE_VT2IB,
    STATUS_IB2VT,
)

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


class OrderManager:
    """Manages order placement, tracking, and execution."""

    def __init__(self, adapter_name: str):
        """Initialize order manager."""
        self.adapter_name = adapter_name

        # Order storage
        self.orders: dict[str, OrderData] = {}

        # Order ID tracking
        self.orderid: int = 0
        self.clientid: int = 0

    def set_next_order_id(self, orderId: int) -> None:
        """Set the next valid order ID from IB."""
        if not self.orderid:
            self.orderid = orderId

    def send_order(
        self, req: OrderRequest, client, account: str, write_log_callback, on_order_callback
    ) -> str:
        """Send an order to IB."""
        if req.exchange not in EXCHANGE_VT2IB:
            write_log_callback(f"Unsupported exchange: {req.exchange}")
            return ""

        if req.type not in ORDERTYPE_VT2IB:
            write_log_callback(f"Unsupported price type: {req.type}")
            return ""

        if " " in req.symbol:
            write_log_callback("Order failed, symbol contains spaces")
            return ""

        self.orderid += 1

        ib_contract: Contract = generate_ib_contract(req.symbol, req.exchange)
        if not ib_contract:
            return ""

        ib_order: Order = Order()
        ib_order.orderId = self.orderid
        ib_order.clientId = self.clientid
        ib_order.action = DIRECTION_VT2IB[req.direction]
        ib_order.orderType = ORDERTYPE_VT2IB[req.type]
        ib_order.totalQuantity = Decimal(req.volume)
        ib_order.account = account
        ib_order.orderRef = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if req.type == OrderType.LIMIT:
            ib_order.lmtPrice = req.price
        elif req.type == OrderType.STOP:
            ib_order.auxPrice = req.price

        client.placeOrder(self.orderid, ib_contract, ib_order)
        client.reqIds(1)

        order: OrderData = req.create_order_data(str(self.orderid), self.adapter_name)
        self.orders[order.orderid] = order
        on_order_callback(order)
        return order.vt_orderid

    def cancel_order(self, req: CancelRequest, client) -> None:
        """Cancel an order."""
        cancel: OrderCancel = OrderCancel()
        client.cancelOrder(int(req.orderid), cancel)

    def process_order_status(
        self,
        orderId: OrderId,
        status: str,
        filled: Decimal,
        remaining: Decimal,
        avgFillPrice: float,
        on_order_callback,
    ) -> None:
        """Process order status updates."""
        orderid: str = str(orderId)
        order: OrderData = self.orders.get(orderid, None)
        if not order:
            return

        order.traded = float(filled)

        # Filter out "canceling" status
        order_status = STATUS_IB2VT.get(status, None)
        if order_status:
            order.status = order_status

        on_order_callback(copy(order))

    def process_open_order(
        self,
        orderId: OrderId,
        ib_contract: Contract,
        ib_order: Order,
        orderState: OrderState,
        contract_manager,
        on_order_callback,
    ) -> None:
        """Process new/updated order information."""
        orderid: str = str(orderId)

        if ib_order.orderRef:
            dt: datetime = datetime.strptime(ib_order.orderRef, "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.now()

        # Prioritize using locally cached order records to resolve issues with exchange information changing when SMART is used
        order: OrderData = self.orders.get(orderid, None)
        if not order:
            order = OrderData(
                symbol=contract_manager.generate_symbol(ib_contract),
                exchange=EXCHANGE_IB2VT.get(ib_contract.exchange, Exchange.SMART),
                type=ORDERTYPE_IB2VT[ib_order.orderType],
                orderid=orderid,
                direction=DIRECTION_IB2VT[ib_order.action],
                volume=ib_order.totalQuantity,
                datetime=dt,
                adapter_name=self.adapter_name,
            )

        if order.type == OrderType.LIMIT:
            order.price = ib_order.lmtPrice
        elif order.type == OrderType.STOP:
            order.price = ib_order.auxPrice

        self.orders[orderid] = order
        on_order_callback(copy(order))

    def process_execution(
        self,
        reqId: int,
        contract: Contract,
        execution: Execution,
        contract_manager,
        on_trade_callback,
        write_log_callback,
    ) -> None:
        """Process trade execution data."""
        # Parse execution time
        time_str: str = execution.time
        time_split: list = time_str.split(" ")
        words_count: int = 3

        if len(time_split) == words_count:
            timezone = time_split[-1]
            time_str = time_str.replace(f" {timezone}", "")
            tz = ZoneInfo(timezone)
        elif len(time_split) == (words_count - 1):
            tz = LOCAL_TZ
        else:
            write_log_callback(f"Received unsupported time format: {time_str}")
            return

        dt: datetime = datetime.strptime(time_str, "%Y%m%d %H:%M:%S")
        dt = dt.replace(tzinfo=tz)

        if tz != LOCAL_TZ:
            dt = dt.astimezone(LOCAL_TZ)

        # Prioritize using locally cached order records to resolve issues with exchange information changing when SMART is used
        orderid: str = str(execution.orderId)
        order: OrderData = self.orders.get(orderid, None)

        if order:
            symbol: str = order.symbol
            exchange: Exchange = order.exchange
        else:
            symbol = contract_manager.generate_symbol(contract)
            exchange = EXCHANGE_IB2VT.get(contract.exchange, Exchange.SMART)

        # Push trade data
        trade: TradeData = TradeData(
            symbol=symbol,
            exchange=exchange,
            orderid=orderid,
            tradeid=str(execution.execId),
            direction=DIRECTION_IB2VT[execution.side],
            price=execution.price,
            volume=float(execution.shares),
            datetime=dt,
            adapter_name=self.adapter_name,
        )

        on_trade_callback(trade)

    def get_order(self, orderid: str) -> OrderData | None:
        """Get order by order ID."""
        return self.orders.get(orderid)
