"""
Core IB API client that coordinates all manager components.
"""

from datetime import datetime
from threading import Thread

from ibapi.client import EClient
from ibapi.common import BarData as IbBarData
from ibapi.common import OrderId, TickAttrib, TickerId
from ibapi.contract import Contract, ContractDetails
from ibapi.execution import Execution
from ibapi.order import Order
from ibapi.order_state import OrderState
from ibapi.ticktype import TickType
from ibapi.wrapper import EWrapper

from foxtrot.util.utility import ZoneInfo

from .account_manager import AccountManager
from .contract_manager import ContractManager
from .historical_data import HistoricalDataManager
from .market_data import MarketDataManager
from .order_manager import OrderManager

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


class IbApi(EWrapper):
    """
    IB API client that coordinates all trading operations.

    This class acts as the central coordinator, delegating specific
    responsibilities to specialized managers while maintaining the
    EWrapper interface for IB callbacks.
    """

    def __init__(self, adapter):
        """Initialize IB API with manager components."""
        super().__init__()

        self.adapter = adapter
        self.adapter_name: str = adapter.adapter_name

        # Connection state
        self.status: bool = False
        self.data_ready: bool = False

        # Request ID management
        self.reqid: int = 0

        # Connection parameters
        self.host: str = ""
        self.port: int = 0
        self.clientid: int = 0

        # Initialize specialized managers
        self.contract_manager = ContractManager(self.adapter_name)
        self.market_data_manager = MarketDataManager(self.adapter_name)
        self.order_manager = OrderManager(self.adapter_name)
        self.account_manager = AccountManager(self.adapter_name)
        self.historical_data_manager = HistoricalDataManager(self.adapter_name)

        # IB client
        self.client: EClient = EClient(self)

    def get_next_reqid(self) -> int:
        """Get next request ID."""
        self.reqid += 1
        return self.reqid

    # ===== Connection Management =====

    def connect(self, host: str, port: int, clientid: int, account: str) -> None:
        """Connect to TWS."""
        if self.status:
            return

        self.host = host
        self.port = port
        self.clientid = clientid
        self.account_manager.account = account
        self.order_manager.clientid = clientid

        self.client.connect(host, port, clientid)
        self.thread = Thread(target=self.client.run)
        self.thread.start()

    def close(self) -> None:
        """Disconnect from TWS."""
        if not self.status:
            return

        self.contract_manager.save_contract_data()

        self.status = False
        self.client.disconnect()

    def check_connection(self) -> None:
        """Check and maintain connection."""
        if self.client.isConnected():
            return

        if self.status:
            self.close()

        self.client.connect(self.host, self.port, self.clientid)
        self.thread = Thread(target=self.client.run)
        self.thread.start()

    # ===== IB Wrapper Callbacks =====

    def connectAck(self) -> None:
        """Callback for successful connection."""
        self.status = True
        self.adapter.write_log("IB TWS connected successfully")

        self.contract_manager.load_contract_data(self.adapter.on_contract, self.adapter.write_log)

        self.data_ready = False

    def connectionClosed(self) -> None:
        """Callback for connection loss."""
        self.status = False
        self.adapter.write_log("IB TWS connection lost")

    def nextValidId(self, orderId: int) -> None:
        """Callback for next valid order ID."""
        super().nextValidId(orderId)
        self.order_manager.set_next_order_id(orderId)

    def currentTime(self, time: int) -> None:
        """Callback for current server time."""
        super().currentTime(time)

        dt: datetime = datetime.fromtimestamp(time)
        time_string: str = dt.strftime("%Y-%m-%d %H:%M:%S.%f")

        msg: str = f"Server time: {time_string}"
        self.adapter.write_log(msg)

    def error(
        self, reqId: TickerId, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""
    ) -> None:
        """Callback for error messages."""
        super().error(reqId, errorCode, errorString)

        # Handle historical data errors
        if reqId == self.historical_data_manager.history_reqid and errorCode not in range(
            2000, 3000
        ):
            self.historical_data_manager.history_condition.acquire()
            self.historical_data_manager.history_condition.notify()
            self.historical_data_manager.history_condition.release()

        msg: str = f"Information message, code: {errorCode}, content: {errorString}"
        self.adapter.write_log(msg)

        # Market data server connected
        if errorCode == 2104 and not self.data_ready:
            self.data_ready = True
            self.client.reqCurrentTime()
            self.market_data_manager.resubscribe_on_ready(self.client)

    # ===== Market Data Callbacks =====

    def tickPrice(
        self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib
    ) -> None:
        """Callback for tick price updates."""
        super().tickPrice(reqId, tickType, price, attrib)
        self.market_data_manager.process_tick_price(
            reqId,
            tickType,
            price,
            attrib,
            self.contract_manager,
            self.adapter.on_tick,
            self.adapter.write_log,
        )

    def tickSize(self, reqId: TickerId, tickType: TickType, size) -> None:
        """Callback for tick size updates."""
        super().tickSize(reqId, tickType, size)
        self.market_data_manager.process_tick_size(
            reqId, tickType, size, self.adapter.on_tick, self.adapter.write_log
        )

    def tickString(self, reqId: TickerId, tickType: TickType, value: str) -> None:
        """Callback for tick string updates."""
        super().tickString(reqId, tickType, value)
        self.market_data_manager.process_tick_string(
            reqId, tickType, value, self.adapter.on_tick, self.adapter.write_log
        )

    def tickOptionComputation(
        self,
        reqId: TickerId,
        tickType: TickType,
        tickAttrib: int,
        impliedVol: float,
        delta: float,
        optPrice: float,
        pvDividend: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float,
    ) -> None:
        """Callback for option computation data."""
        super().tickOptionComputation(
            reqId,
            tickType,
            tickAttrib,
            impliedVol,
            delta,
            optPrice,
            pvDividend,
            gamma,
            vega,
            theta,
            undPrice,
        )
        self.market_data_manager.process_tick_option_computation(
            reqId,
            tickType,
            impliedVol,
            delta,
            optPrice,
            gamma,
            vega,
            theta,
            undPrice,
            self.adapter.write_log,
        )

    def tickSnapshotEnd(self, reqId: int) -> None:
        """Callback for end of market data snapshot."""
        super().tickSnapshotEnd(reqId)
        self.market_data_manager.process_tick_snapshot_end(reqId, self.adapter.write_log)

    # ===== Order Management Callbacks =====

    def orderStatus(
        self,
        orderId: OrderId,
        status: str,
        filled,
        remaining,
        avgFillPrice: float,
        permId: int,
        parentId: int,
        lastFillPrice: float,
        clientId: int,
        whyHeld: str,
        mktCapPrice: float,
    ) -> None:
        """Callback for order status updates."""
        super().orderStatus(
            orderId,
            status,
            filled,
            remaining,
            avgFillPrice,
            permId,
            parentId,
            lastFillPrice,
            clientId,
            whyHeld,
            mktCapPrice,
        )
        self.order_manager.process_order_status(
            orderId, status, filled, remaining, avgFillPrice, self.adapter.on_order
        )

    def openOrder(
        self, orderId: OrderId, ib_contract: Contract, ib_order: Order, orderState: OrderState
    ) -> None:
        """Callback for open orders."""
        super().openOrder(orderId, ib_contract, ib_order, orderState)
        self.order_manager.process_open_order(
            orderId, ib_contract, ib_order, orderState, self.contract_manager, self.adapter.on_order
        )

    def execDetails(self, reqId: int, contract: Contract, execution: Execution) -> None:
        """Callback for execution details."""
        super().execDetails(reqId, contract, execution)
        self.order_manager.process_execution(
            reqId,
            contract,
            execution,
            self.contract_manager,
            self.adapter.on_trade,
            self.adapter.write_log,
        )

    # ===== Account Management Callbacks =====

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str) -> None:
        """Callback for account value updates."""
        super().updateAccountValue(key, val, currency, accountName)
        self.account_manager.process_account_value(key, val, currency, accountName)

    def updatePortfolio(
        self,
        contract: Contract,
        position,
        marketPrice: float,
        marketValue: float,
        averageCost: float,
        unrealizedPNL: float,
        realizedPNL: float,
        accountName: str,
    ) -> None:
        """Callback for portfolio updates."""
        super().updatePortfolio(
            contract,
            position,
            marketPrice,
            marketValue,
            averageCost,
            unrealizedPNL,
            realizedPNL,
            accountName,
        )
        self.account_manager.process_portfolio_update(
            contract,
            position,
            marketPrice,
            marketValue,
            averageCost,
            unrealizedPNL,
            realizedPNL,
            accountName,
            self.contract_manager,
            self.adapter.on_position,
            self.adapter.write_log,
        )

    def updateAccountTime(self, timeStamp: str) -> None:
        """Callback for account update time."""
        super().updateAccountTime(timeStamp)
        self.account_manager.process_account_time(timeStamp, self.adapter.on_account)

    def managedAccounts(self, accountsList: str) -> None:
        """Callback for managed accounts list."""
        super().managedAccounts(accountsList)
        self.account_manager.set_account(accountsList, self.client, self.adapter.write_log)

    # ===== Contract Management Callbacks =====

    def contractDetails(self, reqId: int, contractDetails: ContractDetails) -> None:
        """Callback for contract details."""
        super().contractDetails(reqId, contractDetails)
        self.contract_manager.process_contract_details(
            reqId, contractDetails, self.adapter.on_contract, self.adapter.write_log
        )

    def contractDetailsEnd(self, reqId: int) -> None:
        """Callback for end of contract details."""
        super().contractDetailsEnd(reqId)
        self.contract_manager.process_contract_details_end(reqId, self.adapter.write_log)

    # ===== Historical Data Callbacks =====

    def historicalData(self, reqId: int, ib_bar: IbBarData) -> None:
        """Callback for historical data."""
        self.historical_data_manager.process_historical_data(reqId, ib_bar, self.adapter.write_log)

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        """Callback for end of historical data."""
        self.historical_data_manager.process_historical_data_end(reqId, start, end)

    # ===== Public Interface Methods =====

    def subscribe(self, req) -> None:
        """Subscribe to market data."""
        if not self.status:
            return

        # Update request ID generator for market data manager
        def get_reqid():
            return self.get_next_reqid()

        # Temporarily set the request ID generator
        original_method = self.market_data_manager._get_next_reqid
        self.market_data_manager._get_next_reqid = get_reqid

        try:
            self.market_data_manager.subscribe(
                req, self.client, self.contract_manager, self.adapter.write_log, self.data_ready
            )
        finally:
            self.market_data_manager._get_next_reqid = original_method

    def send_order(self, req) -> str:
        """Send an order."""
        if not self.status:
            return ""

        return self.order_manager.send_order(
            req,
            self.client,
            self.account_manager.get_account(),
            self.adapter.write_log,
            self.adapter.on_order,
        )

    def cancel_order(self, req) -> None:
        """Cancel an order."""
        if not self.status:
            return

        self.order_manager.cancel_order(req, self.client)

    def query_history(self, req):
        """Query historical data."""

        # Update request ID generator for historical data manager
        def get_reqid():
            return self.get_next_reqid()

        # Temporarily set the request ID generator
        original_method = self.historical_data_manager._get_next_reqid
        self.historical_data_manager._get_next_reqid = get_reqid

        try:
            return self.historical_data_manager.query_history(
                req, self.client, self.contract_manager, self.adapter.write_log
            )
        finally:
            self.historical_data_manager._get_next_reqid = original_method

    def query_tick(self, vt_symbol: str) -> None:
        """Query snapshot tick data."""
        if not self.status:
            return

        # Update request ID generator for market data manager
        def get_reqid():
            return self.get_next_reqid()

        # Temporarily set the request ID generator
        original_method = self.market_data_manager._get_next_reqid
        self.market_data_manager._get_next_reqid = get_reqid

        try:
            self.market_data_manager.query_tick(
                vt_symbol, self.client, self.contract_manager, self.adapter.write_log
            )
        finally:
            self.market_data_manager._get_next_reqid = original_method

    def unsubscribe(self, req) -> None:
        """Unsubscribe from market data."""
        self.market_data_manager.unsubscribe(req, self.client)

    def query_option_portfolio(self, underlying: Contract) -> None:
        """Query option chain contract data."""
        if not self.status:
            return

        # Parse IB option contract
        ib_contract: Contract = Contract()
        ib_contract.symbol = underlying.symbol
        ib_contract.currency = underlying.currency

        # Futures options must use the specified exchange
        if underlying.secType == "FUT":
            ib_contract.secType = "FOP"
            ib_contract.exchange = underlying.exchange
        # Spot options support smart routing
        else:
            ib_contract.secType = "OPT"
            ib_contract.exchange = "SMART"

        # Query contract information through TWS
        reqid = self.get_next_reqid()
        self.client.reqContractDetails(reqid, ib_contract)

        # Cache the query record
        self.contract_manager.reqid_underlying_map[reqid] = underlying
