"""
Main engine module for the trading platform.

This module has been refactored to use separate manager classes:
- adapter_manager.py: Adapter lifecycle and operations
- engine_manager.py: Engine coordination
- app_manager.py: App lifecycle management
- oms_engine.py: Order Management System
- email_engine.py: Email notifications
- log_engine.py: Logging functionality
"""

from collections.abc import Callable
import os

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.interfaces import IEngine, IAdapter, IEventEngine
from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.util.logger import FoxtrotLogger, create_foxtrot_logger
from foxtrot.util.settings import FoxtrotSettings, create_foxtrot_settings
from foxtrot.server.adapter_manager import AdapterManager
from foxtrot.server.app_manager import AppManager
from foxtrot.server.email_engine import EmailEngine
from foxtrot.server.engine_manager import BaseEngine, BaseApp, EngineManager
from foxtrot.server.log_engine import LogEngine
from foxtrot.server.oms_engine import OmsEngine
from foxtrot.util.converter import OffsetConverter
from foxtrot.util.constants import Exchange
from foxtrot.util.event_type import EVENT_LOG
from foxtrot.util.object import (
    AccountData,
    BarData,
    CancelRequest,
    ContractData,
    HistoryRequest,
    LogData,
    OrderData,
    OrderRequest,
    PositionData,
    QuoteData,
    QuoteRequest,
    SubscribeRequest,
    TickData,
    TradeData,
)
from foxtrot.util.utility import TRADER_DIR


class MainEngine(IEngine):
    """
    Acts as the core of the trading platform.
    """

    def __init__(self, event_engine: IEventEngine | None = None, foxtrot_logger: FoxtrotLogger | None = None, foxtrot_settings: FoxtrotSettings | None = None) -> None:
        """
        Initialize MainEngine as the central dependency container.
        
        Args:
            event_engine: Optional EventEngine instance for dependency injection
            foxtrot_logger: Optional FoxtrotLogger instance for dependency injection  
            foxtrot_settings: Optional FoxtrotSettings instance for dependency injection
        """
        # Create or use provided settings (dependency container pattern)
        if foxtrot_settings is None:
            foxtrot_settings = create_foxtrot_settings()
        self.foxtrot_settings = foxtrot_settings
        
        # Create or use provided logger (dependency container pattern)
        if foxtrot_logger is None:
            foxtrot_logger = create_foxtrot_logger()
        self.foxtrot_logger = foxtrot_logger
        
        # Create or use provided event engine with logger dependency
        if event_engine:
            self.event_engine: EventEngine = event_engine
        else:
            self.event_engine = EventEngine(foxtrot_logger=foxtrot_logger)
        self.event_engine.start()

        # Initialize managers
        self.adapter_manager: AdapterManager = AdapterManager(self.event_engine, self.write_log)
        self.engine_manager: EngineManager = EngineManager(
            self, self.event_engine, self.write_log
        )
        self.app_manager: AppManager = AppManager(self.engine_manager.add_engine)

        # For backward compatibility
        self.adapters = self.adapter_manager.adapters
        self.engines = self.engine_manager.engines
        self.apps = self.app_manager.apps
        self.exchanges = self.adapter_manager.exchanges

        os.chdir(TRADER_DIR)  # Change working directory
        self.init_engines()  # Initialize function engines

    def init_engines(self) -> None:
        """
        Init all engines.
        """
        self.add_engine(LogEngine)

        oms_engine: OmsEngine = self.add_engine(OmsEngine)
        self.get_tick: Callable[[str], TickData | None] = oms_engine.get_tick
        self.get_order: Callable[[str], OrderData | None] = oms_engine.get_order
        self.get_trade: Callable[[str], TradeData | None] = oms_engine.get_trade
        self.get_position: Callable[[str], PositionData | None] = oms_engine.get_position
        self.get_account: Callable[[str], AccountData | None] = oms_engine.get_account
        self.get_contract: Callable[[str], ContractData | None] = oms_engine.get_contract
        self.get_quote: Callable[[str], QuoteData | None] = oms_engine.get_quote
        self.get_all_ticks: Callable[[], list[TickData]] = oms_engine.get_all_ticks
        self.get_all_orders: Callable[[], list[OrderData]] = oms_engine.get_all_orders
        self.get_all_trades: Callable[[], list[TradeData]] = oms_engine.get_all_trades
        self.get_all_positions: Callable[[], list[PositionData]] = oms_engine.get_all_positions
        self.get_all_accounts: Callable[[], list[AccountData]] = oms_engine.get_all_accounts
        self.get_all_contracts: Callable[[], list[ContractData]] = oms_engine.get_all_contracts
        self.get_all_quotes: Callable[[], list[QuoteData]] = oms_engine.get_all_quotes
        self.get_all_active_orders: Callable[[], list[OrderData]] = oms_engine.get_all_active_orders
        self.get_all_active_quotes: Callable[[], list[QuoteData]] = oms_engine.get_all_active_quotes
        self.update_order_request: Callable[[OrderRequest, str, str], None] = (
            oms_engine.update_order_request
        )
        self.convert_order_request: Callable[
            [OrderRequest, str, bool, bool], list[OrderRequest]
        ] = oms_engine.convert_order_request
        self.get_converter: Callable[[str], OffsetConverter | None] = oms_engine.get_converter

        email_engine: EmailEngine = self.add_engine(EmailEngine)
        self.send_email: Callable[[str, str, str | None], None] = email_engine.send_email

    def write_log(self, msg: str, source: str = "") -> None:
        """
        Put log event with specific message.
        """
        log: LogData = LogData(msg=msg, adapter_name=source)
        event: Event = Event(EVENT_LOG, log)
        self.event_engine.put(event)

    # Delegate to managers (for backward compatibility)
    def add_engine(self, engine_class) -> BaseEngine:
        """Add function engine."""
        return self.engine_manager.add_engine(engine_class)

    def add_adapter(self, adapter_class: type[IAdapter], adapter_name: str = "") -> IAdapter:
        """Add adapter."""
        return self.adapter_manager.add_adapter(adapter_class, adapter_name)

    def add_app(self, app_class: type[BaseApp]) -> BaseEngine:
        """Add app."""
        return self.app_manager.add_app(app_class)

    def get_adapter(self, adapter_name: str) -> IAdapter | None:
        """Return adapter object by name."""
        return self.adapter_manager.get_adapter(adapter_name)

    def get_engine(self, engine_name: str) -> BaseEngine | None:
        """Return engine object by name."""
        return self.engine_manager.get_engine(engine_name)

    def get_default_setting(self, adapter_name: str) -> dict[str, str | bool | int | float] | None:
        """Get default setting dict of a specific gateway."""
        return self.adapter_manager.get_default_setting(adapter_name)

    def get_all_gateway_names(self) -> list[str]:
        """Get all names of gateway added in main engine."""
        return self.adapter_manager.get_all_gateway_names()

    def get_all_apps(self) -> list[BaseApp]:
        """Get all app objects."""
        return self.app_manager.get_all_apps()

    def get_all_exchanges(self) -> list[Exchange]:
        """Get all exchanges."""
        return self.adapter_manager.get_all_exchanges()

    def connect(self, setting: dict[str, str | bool | int | float], adapter_name: str) -> None:
        """Start connection of a specific adapter."""
        self.adapter_manager.connect(setting, adapter_name)

    def subscribe(self, req: SubscribeRequest, adapter_name: str) -> None:
        """Subscribe tick data update of a specific adapter."""
        self.adapter_manager.subscribe(req, adapter_name)

    def send_order(self, req: OrderRequest, adapter_name: str) -> str:
        """Send new order request to a specific gateway."""
        return self.adapter_manager.send_order(req, adapter_name)

    def cancel_order(self, req: CancelRequest, adapter_name: str) -> None:
        """Send cancel order request to a specific gateway."""
        self.adapter_manager.cancel_order(req, adapter_name)

    def send_quote(self, req: QuoteRequest, adapter_name: str) -> str:
        """Send new quote request to a specific gateway."""
        return self.adapter_manager.send_quote(req, adapter_name)

    def cancel_quote(self, req: CancelRequest, adapter_name: str) -> None:
        """Send cancel quote request to a specific gateway."""
        self.adapter_manager.cancel_quote(req, adapter_name)

    def query_history(self, req: HistoryRequest, adapter_name: str) -> list[BarData]:
        """Query history data from a specific gateway."""
        return self.adapter_manager.query_history(req, adapter_name)  # type: ignore

    def close(self) -> None:
        """
        Make sure every gateway and app is closed properly before
        programme exit.
        """
        # Stop event engine first to prevent new events.
        self.event_engine.stop()

        for app in self.apps.values():
            app.close()

        self.adapter_manager.close()
        self.engine_manager.close()


# Re-export for backward compatibility
__all__ = ["MainEngine", "BaseEngine"]