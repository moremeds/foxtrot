from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from types import ModuleType

from util.constants import Exchange, Interval
from util.object import BarData, TickData
from util.settings import SETTINGS
from util.utility import ZoneInfo
from util.logger import create_foxtrot_logger, get_component_logger

DB_TZ = ZoneInfo(SETTINGS["database.timezone"])


def convert_tz(dt: datetime) -> datetime:
    """
    Convert timezone of datetime object to DB_TZ.
    """
    dt = dt.astimezone(DB_TZ)
    return dt.replace(tzinfo=None)


@dataclass
class BarOverview:
    """
    Overview of bar data stored in database.
    """

    symbol: str = ""
    exchange: Exchange | None = None
    interval: Interval | None = None
    count: int = 0
    start: datetime | None = None
    end: datetime | None = None


@dataclass
class TickOverview:
    """
    Overview of tick data stored in database.
    """

    symbol: str = ""
    exchange: Exchange | None = None
    count: int = 0
    start: datetime | None = None
    end: datetime | None = None


class BaseDatabase(ABC):
    """
    Abstract database class for connecting to different database.
    """

    @abstractmethod
    def save_bar_data(self, bars: list[BarData], stream: bool = False) -> bool:
        """
        Save bar data into database.
        """

    @abstractmethod
    def save_tick_data(self, ticks: list[TickData], stream: bool = False) -> bool:
        """
        Save tick data into database.
        """

    @abstractmethod
    def load_bar_data(
        self, symbol: str, exchange: Exchange, interval: Interval, start: datetime, end: datetime
    ) -> list[BarData]:
        """
        Load bar data from database.
        """

    @abstractmethod
    def load_tick_data(
        self, symbol: str, exchange: Exchange, start: datetime, end: datetime
    ) -> list[TickData]:
        """
        Load tick data from database.
        """

    @abstractmethod
    def delete_bar_data(self, symbol: str, exchange: Exchange, interval: Interval) -> int:
        """
        Delete all bar data with given symbol + exchange + interval.
        """

    @abstractmethod
    def delete_tick_data(self, symbol: str, exchange: Exchange) -> int:
        """
        Delete all tick data with given symbol + exchange.
        """

    @abstractmethod
    def get_bar_overview(self) -> list[BarOverview]:
        """
        Return bar data avaible in database.
        """

    @abstractmethod
    def get_tick_overview(self) -> list[TickOverview]:
        """
        Return tick data avaible in database.
        """


database: BaseDatabase | None = None


def get_database() -> BaseDatabase:
    """"""
    # Return database object if already inited
    global database
    if database:
        return database
    
    foxtrot_logger = create_foxtrot_logger()
    logger = get_component_logger("DatabaseManager", foxtrot_logger)

    # Read database related global setting
    database_name: str = SETTINGS["database.name"]
    module_name: str = f"silvertine_{database_name}"

    # Try to import database module
    try:
        module: ModuleType = import_module(module_name)
    except ModuleNotFoundError:
        # MIGRATION: Replace print with WARNING logging for database fallback
        logger.warning(
            "Database driver not found, falling back to SQLite",
            extra={
                "requested_driver": module_name,
                "fallback_driver": "silvertine_sqlite"
            }
        )
        print(f"Can't find database driver {module_name}, using default SQLite database")
        module = import_module("silvertine_sqlite")

    # Create database object from module
    database = module.Database()
    if database is None:
        raise RuntimeError("Failed to initialize database object from module.")
    return database
