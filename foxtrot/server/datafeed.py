from collections.abc import Callable
from importlib import import_module
from types import ModuleType

from util.object import BarData, HistoryRequest, TickData
from util.settings import SETTINGS
from util.logger import create_foxtrot_logger, get_component_logger


class BaseDatafeed:
    """
    Abstract datafeed class for connecting to different datafeed.
    """

    def init(self, output: Callable[[str], None] = print) -> bool:
        """
        Initialize datafeed service connection.
        """
        return False

    def query_bar_history(
        self, req: HistoryRequest, output: Callable[[str], None] = print
    ) -> list[BarData]:
        """
        Query history bar data.
        """
        output("Query K-line data failed: no correct configuration of data service")
        return []

    def query_tick_history(
        self, req: HistoryRequest, output: Callable[[str], None] = print
    ) -> list[TickData]:
        """
        Query history tick data.
        """
        output("Query Tick data failed: no correct configuration of data service")
        return []


datafeed: BaseDatafeed | None = None


def get_datafeed() -> BaseDatafeed:
    """"""
    # Return datafeed object if already inited
    global datafeed
    if datafeed is not None:
        return datafeed
    
    foxtrot_logger = create_foxtrot_logger()
    logger = get_component_logger("DatafeedManager", foxtrot_logger)

    # Read datafeed related global setting
    datafeed_name: str = SETTINGS["datafeed.name"]

    if not datafeed_name:
        datafeed = BaseDatafeed()

        # MIGRATION: Replace print with WARNING logging for missing datafeed config
        logger.warning("No datafeed service configured in global settings")
        print(
            "No data service configured, please modify the datafeed related content in the global configuration"
        )
    else:
        module_name: str = f"vnpy_{datafeed_name}"

        # Try to import datafeed module
        try:
            module: ModuleType = import_module(module_name)

            # Create datafeed object from module
            datafeed = module.Datafeed()
        # Use base class if failed
        except ModuleNotFoundError:
            datafeed = BaseDatafeed()

            # MIGRATION: Replace print with ERROR logging for missing datafeed module
            logger.error(
                "Datafeed module not found",
                extra={
                    "module_name": module_name,
                    "datafeed_name": datafeed_name
                }
            )
            print(
                f"Can't load data service module, please run pip install {module_name} to try install"
            )

    return datafeed
