"""
Engine management functionality for MainEngine.
"""

from typing import TypeVar

from foxtrot.core.event_engine import EventEngine

EngineType = TypeVar("EngineType", bound="BaseEngine")


class BaseEngine:
    """
    Abstract class for implementing a function engine.
    """

    def __init__(
        self,
        main_engine: "MainEngine",  # type: ignore
        event_engine: EventEngine,
        engine_name: str,
    ) -> None:
        """"""
        self.main_engine = main_engine
        self.event_engine: EventEngine = event_engine
        self.engine_name: str = engine_name

    def close(self) -> None:
        """"""
        return


class EngineManager:
    """
    Manages engine lifecycle and operations.
    """

    def __init__(self, main_engine, event_engine: EventEngine, write_log_func) -> None:
        """Initialize engine manager."""
        self.main_engine = main_engine
        self.event_engine: EventEngine = event_engine
        self.write_log = write_log_func
        self.engines: dict[str, BaseEngine] = {}

    def add_engine(self, engine_class: type[EngineType]) -> EngineType:
        """
        Add function engine.
        """
        engine: EngineType = engine_class(self.main_engine, self.event_engine)  # type: ignore
        self.engines[engine.engine_name] = engine
        return engine

    def get_engine(self, engine_name: str) -> BaseEngine | None:
        """
        Return engine object by name.
        """
        engine: BaseEngine | None = self.engines.get(engine_name, None)
        if not engine:
            self.write_log(f"Engine not found: {engine_name}")
        return engine

    def close(self) -> None:
        """
        Close all engines.
        """
        for engine in self.engines.values():
            engine.close()