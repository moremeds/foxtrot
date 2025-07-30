"""
Market data handling for Interactive Brokers.
"""

from copy import copy
from datetime import datetime

from ibapi.common import TickAttrib, TickerId
from ibapi.contract import Contract
from ibapi.ticktype import TickType, TickTypeEnum

from foxtrot.util.constants import Exchange
from foxtrot.util.object import SubscribeRequest, TickData
from foxtrot.util.utility import ZoneInfo

from .contract_manager import generate_ib_contract
from .ib_mappings import EXCHANGE_VT2IB, TICKFIELD_IB2VT

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


class MarketDataManager:
    """Manages market data subscriptions and tick processing."""

    def __init__(self, adapter_name: str):
        """Initialize market data manager."""
        self.adapter_name = adapter_name

        # Tick data storage
        self.ticks: dict[int, TickData] = {}
        self.subscribed: dict[str, SubscribeRequest] = {}

    def subscribe(
        self, req: SubscribeRequest, client, contract_manager, write_log_callback, data_ready: bool
    ) -> bool:
        """Subscribe to tick data updates."""
        if req.exchange not in EXCHANGE_VT2IB:
            write_log_callback(f"Unsupported exchange {req.exchange}")
            return False

        if " " in req.symbol:
            write_log_callback("Subscription failed, symbol contains spaces")
            return False

        # Filter out duplicate subscriptions
        if req.vt_symbol in self.subscribed:
            return True
        self.subscribed[req.vt_symbol] = req

        # Parse IB contract details
        ib_contract: Contract = generate_ib_contract(req.symbol, req.exchange)
        if not ib_contract:
            write_log_callback("Symbol parsing failed, please check the format")
            return False

        # Query contract information through TWS
        reqid = self._get_next_reqid()
        client.reqContractDetails(reqid, ib_contract)

        # If a string-style symbol is used, it needs to be cached
        if "-" in req.symbol:
            contract_manager.reqid_symbol_map[reqid] = req.symbol

        # Subscribe to tick data and create a tick object buffer
        tick_reqid = self._get_next_reqid()
        client.reqMktData(tick_reqid, ib_contract, "", False, False, [])

        tick: TickData = TickData(
            symbol=req.symbol,
            exchange=req.exchange,
            datetime=datetime.now(LOCAL_TZ),
            adapter_name=self.adapter_name,
        )
        tick.extra = {}

        self.ticks[tick_reqid] = tick
        return True

    def unsubscribe(self, req: SubscribeRequest, client) -> None:
        """Unsubscribe from tick data updates."""
        # Remove subscription record
        if req.vt_symbol not in self.subscribed:
            return
        self.subscribed.pop(req.vt_symbol)

        # Get subscription ID
        cancel_id: int = 0
        for reqid, tick in self.ticks.items():
            if tick.vt_symbol == req.vt_symbol:
                cancel_id = reqid
                break

        # Send unsubscribe request
        client.cancelMktData(cancel_id)

    def query_tick(self, vt_symbol: str, client, contract_manager, write_log_callback) -> None:
        """Query tick data."""
        contract = contract_manager.get_contract(vt_symbol)
        if not contract:
            write_log_callback(
                f"Failed to query tick data, could not find contract data for {vt_symbol}"
            )
            return

        ib_contract = contract_manager.get_ib_contract(vt_symbol)
        if not ib_contract:
            write_log_callback(
                f"Failed to query tick data, could not find IB contract data for {vt_symbol}"
            )
            return

        reqid = self._get_next_reqid()
        client.reqMktData(reqid, ib_contract, "", True, False, [])

        tick: TickData = TickData(
            symbol=contract.symbol,
            exchange=contract.exchange,
            datetime=datetime.now(LOCAL_TZ),
            adapter_name=self.adapter_name,
        )
        tick.extra = {}

        self.ticks[reqid] = tick

    def process_tick_price(
        self,
        reqId: TickerId,
        tickType: TickType,
        price: float,
        attrib: TickAttrib,
        contract_manager,
        on_tick_callback,
        write_log_callback,
    ) -> None:
        """Process tick price updates."""
        if tickType not in TICKFIELD_IB2VT:
            return

        tick: TickData | None = self.ticks.get(reqId, None)
        if not tick:
            write_log_callback(f"tickPrice function received an unsolicited push, reqId: {reqId}")
            return

        name: str = TICKFIELD_IB2VT[tickType]
        setattr(tick, name, price)

        # Update the name field of the tick data
        contract = contract_manager.get_contract(tick.vt_symbol)
        if contract:
            tick.name = contract.name

        # Locally calculate the tick time and latest price for Forex of IDEALPRO and Spot Commodity
        if tick.exchange == Exchange.IDEALPRO or "CMDTY" in tick.symbol:
            if not tick.bid_price_1 or not tick.ask_price_1 or tick.low_price == -1:
                return
            tick.last_price = (tick.bid_price_1 + tick.ask_price_1) / 2
            tick.datetime = datetime.now(LOCAL_TZ)

        on_tick_callback(copy(tick))

    def process_tick_size(
        self, reqId: TickerId, tickType: TickType, size, on_tick_callback, write_log_callback
    ) -> None:
        """Process tick size updates."""
        if tickType not in TICKFIELD_IB2VT:
            return

        tick: TickData | None = self.ticks.get(reqId, None)
        if not tick:
            write_log_callback(f"tickSize function received an unsolicited push, reqId: {reqId}")
            return

        name: str = TICKFIELD_IB2VT[tickType]
        setattr(tick, name, float(size))

        on_tick_callback(copy(tick))

    def process_tick_string(
        self, reqId: TickerId, tickType: TickType, value: str, on_tick_callback, write_log_callback
    ) -> None:
        """Process tick string updates."""
        if tickType != TickTypeEnum.LAST_TIMESTAMP:
            return

        tick: TickData | None = self.ticks.get(reqId, None)
        if not tick:
            write_log_callback(f"tickString function received an unsolicited push, reqId: {reqId}")
            return

        dt: datetime = datetime.fromtimestamp(int(value))
        tick.datetime = dt.replace(tzinfo=LOCAL_TZ)

        on_tick_callback(copy(tick))

    def process_tick_option_computation(
        self,
        reqId: TickerId,
        tickType: TickType,
        impliedVol: float,
        delta: float,
        optPrice: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float,
        write_log_callback,
    ) -> None:
        """Process tick option data."""
        tick: TickData | None = self.ticks.get(reqId, None)
        if not tick:
            write_log_callback(
                f"tickOptionComputation function received an unsolicited push, reqId: {reqId}"
            )
            return

        prefix: str = TICKFIELD_IB2VT[tickType]

        if tick.extra is None:
            tick.extra = {}
        tick.extra["underlying_price"] = undPrice

        if optPrice:
            tick.extra[f"{prefix}_price"] = optPrice
            tick.extra[f"{prefix}_impv"] = impliedVol
            tick.extra[f"{prefix}_delta"] = delta
            tick.extra[f"{prefix}_gamma"] = gamma
            tick.extra[f"{prefix}_theta"] = theta
            tick.extra[f"{prefix}_vega"] = vega
        else:
            tick.extra[f"{prefix}_price"] = 0
            tick.extra[f"{prefix}_impv"] = 0
            tick.extra[f"{prefix}_delta"] = 0
            tick.extra[f"{prefix}_gamma"] = 0
            tick.extra[f"{prefix}_theta"] = 0
            tick.extra[f"{prefix}_vega"] = 0

    def process_tick_snapshot_end(self, reqId: int, write_log_callback) -> None:
        """Process end of market data snapshot."""
        tick: TickData | None = self.ticks.get(reqId, None)
        if not tick:
            write_log_callback(
                f"tickSnapshotEnd function received an unsolicited push, reqId: {reqId}"
            )
            return

        write_log_callback(f"{tick.vt_symbol} market data snapshot query successful")

    def resubscribe_on_ready(self, client) -> None:
        """Resubscribe to all symbols when data connection is ready."""
        reqs: list[SubscribeRequest] = list(self.subscribed.values())
        self.subscribed.clear()
        for req in reqs:
            # Note: This would need the full subscribe method called externally
            pass

    def _get_next_reqid(self) -> int:
        """Get next request ID - this should be managed by the main API client."""
        # This is a placeholder - actual implementation should be in the main API client
        return 0
