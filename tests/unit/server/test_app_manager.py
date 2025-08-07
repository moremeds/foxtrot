"""
Unit tests for AppManager.
"""

from unittest.mock import MagicMock
import pytest

from foxtrot.app.app import BaseApp
from foxtrot.server.app_manager import AppManager
from foxtrot.server.engine_manager import BaseEngine


class MockApp(BaseApp):
    """Mock app for testing."""

    app_name = "mock_app"
    app_module = "mock_module"
    app_path = "mock_path"
    display_name = "Mock App"
    engine_class = None

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class MockEngine(BaseEngine):
    """Mock engine for testing."""

    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine, "mock_engine")


class MockAppWithEngine(BaseApp):
    """Mock app with associated engine."""

    app_name = "app_with_engine"
    app_module = "mock_module"
    app_path = "mock_path"
    display_name = "App With Engine"
    engine_class = MockEngine


@pytest.fixture
def add_engine():
    """Create mock add_engine function."""
    return MagicMock()


@pytest.fixture
def app_manager(add_engine):
    """Create AppManager instance."""
    return AppManager(add_engine)


class TestAppManager:
    """Test AppManager functionality."""

    def test_init(self, app_manager):
        """Test AppManager initialization."""
        assert app_manager.apps == {}

    def test_add_app_without_engine(self, app_manager):
        """Test adding an app without engine."""
        engine = app_manager.add_app(MockApp)
        
        assert "mock_app" in app_manager.apps
        assert isinstance(app_manager.apps["mock_app"], MockApp)
        assert engine is None

    def test_add_app_with_engine(self, app_manager, add_engine):
        """Test adding an app with associated engine."""
        mock_engine_instance = MockEngine(None, None)
        add_engine.return_value = mock_engine_instance
        
        engine = app_manager.add_app(MockAppWithEngine)
        
        assert "app_with_engine" in app_manager.apps
        assert isinstance(app_manager.apps["app_with_engine"], MockAppWithEngine)
        add_engine.assert_called_once_with(MockEngine)
        assert engine == mock_engine_instance

    def test_add_duplicate_app(self, app_manager):
        """Test adding duplicate app."""
        engine1 = app_manager.add_app(MockApp)
        engine2 = app_manager.add_app(MockApp)
        
        # Should return None for duplicate
        assert engine1 is None
        assert engine2 is None
        # But app should still be in dictionary
        assert "mock_app" in app_manager.apps

    def test_get_all_apps(self, app_manager):
        """Test getting all apps."""
        app_manager.add_app(MockApp)
        app_manager.add_app(MockAppWithEngine)
        
        apps = app_manager.get_all_apps()
        assert len(apps) == 2
        assert any(isinstance(app, MockApp) for app in apps)
        assert any(isinstance(app, MockAppWithEngine) for app in apps)

    def test_get_all_apps_empty(self, app_manager):
        """Test getting all apps when none exist."""
        apps = app_manager.get_all_apps()
        assert apps == []

    def test_multiple_apps_management(self, app_manager, add_engine):
        """Test managing multiple apps."""
        mock_engine = MockEngine(None, None)
        add_engine.return_value = mock_engine
        
        # Add multiple apps
        app_manager.add_app(MockApp)
        app_manager.add_app(MockAppWithEngine)
        
        # Verify both apps are tracked
        assert len(app_manager.apps) == 2
        assert "mock_app" in app_manager.apps
        assert "app_with_engine" in app_manager.apps
        
        # Verify correct instances
        assert isinstance(app_manager.apps["mock_app"], MockApp)
        assert isinstance(app_manager.apps["app_with_engine"], MockAppWithEngine)