"""
App management functionality for MainEngine.
"""

from foxtrot.server.engine_manager import BaseEngine, BaseApp


class AppManager:
    """
    Manages app lifecycle and operations.
    """

    def __init__(self, add_engine_func) -> None:
        """Initialize app manager."""
        self.add_engine = add_engine_func
        self.apps: dict[str, BaseApp] = {}

    def add_app(self, app_class: type[BaseApp]) -> BaseEngine | None:
        """
        Add app.
        """
        app: BaseApp = app_class()
        self.apps[app.app_name] = app

        if app.engine_class:
            engine: BaseEngine = self.add_engine(app.engine_class)
            return engine
        return None

    def get_all_apps(self) -> list[BaseApp]:
        """
        Get all app objects.
        """
        return list(self.apps.values())