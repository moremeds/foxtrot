"""
Historical data management for Interactive Brokers.
"""
from datetime import datetime, timedelta
from threading import Condition

from ibapi.common import BarData as IbBarData

from foxtrot.util.constants import Product
from foxtrot.util.object import BarData, HistoryRequest
from foxtrot.util.utility import ZoneInfo

from .contract_manager import generate_ib_contract
from .ib_mappings import INTERVAL_VT2IB

LOCAL_TZ = ZoneInfo("Asia/Shanghai")


class HistoricalDataManager:
    """Manages historical data queries and processing."""

    def __init__(self, adapter_name: str):
        """Initialize historical data manager."""
        self.adapter_name = adapter_name

        # Historical data state
        self.history_req: HistoryRequest | None = None
        self.history_condition: Condition = Condition()
        self.history_buf: list[BarData] = []
        self.history_reqid: int = 0

    def query_history(self, req: HistoryRequest, client, contract_manager,
                     write_log_callback) -> list[BarData]:
        """Query historical data from IB."""
        contract = contract_manager.get_contract(req.vt_symbol)
        if not contract:
            write_log_callback(f"Contract not found: {req.vt_symbol}, please subscribe first")
            return []

        self.history_req = req

        # Get next request ID
        reqid = self._get_next_reqid()

        ib_contract = generate_ib_contract(req.symbol, req.exchange)

        if req.end:
            end: datetime = req.end
        else:
            end = datetime.now(LOCAL_TZ)

        # Use UTC end time
        utc_tz: ZoneInfo = ZoneInfo("UTC")
        utc_end: datetime = end.astimezone(utc_tz)
        end_str: str = utc_end.strftime("%Y%m%d-%H:%M:%S")

        delta: timedelta = end - req.start
        days: int = delta.days
        if days < 365:
            duration: str = f"{days} D"
        else:
            duration = f"{delta.days/365:.0f} Y"

        bar_size: str = INTERVAL_VT2IB[req.interval]

        if contract.product in [Product.SPOT, Product.FOREX]:
            bar_type: str = "MIDPOINT"
        else:
            bar_type = "TRADES"

        self.history_reqid = reqid
        client.reqHistoricalData(
            reqid,
            ib_contract,
            end_str,
            duration,
            bar_size,
            bar_type,
            0,
            1,
            False,
            []
        )

        self.history_condition.acquire()    # Wait for asynchronous data to be returned
        self.history_condition.wait(600)
        self.history_condition.release()

        history: list[BarData] = self.history_buf
        self.history_buf = []       # Create a new buffer list
        self.history_req = None

        return history

    def process_historical_data(self, reqId: int, ib_bar: IbBarData,
                              write_log_callback) -> None:
        """Process historical bar data."""
        # Daily and weekly data format is %Y%m%d
        time_str: str = ib_bar.date
        time_split: list = time_str.split(" ")
        words_count: int = 3

        if ":" not in time_str:
            words_count -= 1

        if len(time_split) == words_count:
            timezone = time_split[-1]
            time_str = time_str.replace(f" {timezone}", "")
            tz = ZoneInfo(timezone)
        elif len(time_split) == (words_count - 1):
            tz = LOCAL_TZ
        else:
            write_log_callback(f"Received unsupported time format: {time_str}")
            return

        if ":" in time_str:
            dt: datetime = datetime.strptime(time_str, "%Y%m%d %H:%M:%S")
        else:
            dt = datetime.strptime(time_str, "%Y%m%d")
        dt = dt.replace(tzinfo=tz)

        if tz != LOCAL_TZ:
            dt = dt.astimezone(LOCAL_TZ)

        bar: BarData = BarData(
            symbol=self.history_req.symbol,
            exchange=self.history_req.exchange,
            datetime=dt,
            interval=self.history_req.interval,
            volume=float(ib_bar.volume),
            open_price=ib_bar.open,
            high_price=ib_bar.high,
            low_price=ib_bar.low,
            close_price=ib_bar.close,
            adapter_name=self.adapter_name
        )
        if bar.volume < 0:
            bar.volume = 0

        self.history_buf.append(bar)

    def process_historical_data_end(self, reqId: int, start: str, end: str) -> None:
        """Process end of historical data."""
        self.history_condition.acquire()
        self.history_condition.notify()
        self.history_condition.release()

    def _get_next_reqid(self) -> int:
        """Get next request ID - this should be managed by the main API client."""
        # This is a placeholder - actual implementation should be in the main API client
        return 0
