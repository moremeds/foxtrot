"""
Log engine for processing log events.
"""

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine_manager import BaseEngine
from foxtrot.util.event_type import EVENT_LOG
from foxtrot.util.logger import CRITICAL, DEBUG, ERROR, INFO, WARNING, logger
from foxtrot.util.object import LogData
from foxtrot.util.settings import SETTINGS


class LogEngine(BaseEngine):
    """
    Provides log event output function.
    """

    level_map: dict[int, str] = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARNING: "WARNING",
        ERROR: "ERROR",
        CRITICAL: "CRITICAL",
    }

    def __init__(self, main_engine, event_engine: EventEngine) -> None:
        """"""
        super().__init__(main_engine, event_engine, "log")

        self.active = SETTINGS["log.active"]

        self.register_log(EVENT_LOG)

    def process_log_event(self, event: Event) -> None:
        """Process log event"""
        if not self.active:
            return

        log: LogData = event.data
        level: str | int = self.level_map.get(log.level, log.level)
        logger.log(level, log.msg, adapter_name=log.adapter_name)

    def register_log(self, event_type: str) -> None:
        """Register log event handler"""
        self.event_engine.register(event_type, self.process_log_event)