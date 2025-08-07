"""
Account and contract management objects for trading platform.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .base_objects import BaseData, INFO
from .constants import Exchange, OptionType, Product


@dataclass
class AccountData(BaseData):
    """
    Account data contains information about balance, frozen and
    available.
    """

    accountid: str

    balance: float = 0
    frozen: float = 0

    def __post_init__(self) -> None:
        """"""
        self.available: float = self.balance - self.frozen
        self.vt_accountid: str = f"{self.adapter_name}.{self.accountid}"


@dataclass
class ContractData(BaseData):
    """
    Contract data contains basic information about each contract traded.
    """

    symbol: str
    exchange: Exchange
    name: str
    product: Product
    size: float
    pricetick: float

    min_volume: float = 1  # minimum order volume
    max_volume: float | None = None  # maximum order volume
    stop_supported: bool = False  # whether server supports stop order
    net_position: bool = False  # whether adapter uses net position volume
    history_data: bool = False  # whether adapter provides bar history data

    option_strike: float | None = None
    option_underlying: str | None = None  # vt_symbol of underlying contract
    option_type: OptionType | None = None
    option_listed: datetime | None = None
    option_expiry: datetime | None = None
    option_portfolio: str | None = None
    option_index: str | None = None  # for identifying options with same strike price

    def __post_init__(self) -> None:
        """"""
        self.vt_symbol: str = f"{self.symbol}.{self.exchange.value}"


@dataclass
class LogData(BaseData):
    """
    Log data is used for recording log messages on GUI or in log files.
    """

    msg: str
    level: int = INFO

    def __post_init__(self) -> None:
        """"""
        self.time: datetime = datetime.now()