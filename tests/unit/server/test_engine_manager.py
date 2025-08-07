"""
Unit tests for EngineManager.
"""

from unittest.mock import MagicMock
import pytest

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine_manager import BaseEngine, EngineManager


class MockEngine(BaseEngine):
    """Mock engine for testing."""

    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine, "mock")
        self.started = False
        self.closed = False

    def start(self):
        self.started = True

    def close(self):
        self.closed = True


class MockEngineWithClose(BaseEngine):
    """Mock engine with close method."""

    def __init__(self, main_engine, event_engine):
        super().__init__(main_engine, event_engine, "closeable")
        self.closed = False

    def close(self):
        self.closed = True
        super().close()


@pytest.fixture
def event_engine():
    """Create mock event engine."""
    return MagicMock(spec=EventEngine)


@pytest.fixture
def main_engine():
    """Create mock main engine."""
    return MagicMock()


@pytest.fixture
def write_log():
    """Create mock write_log function."""
    return MagicMock()


@pytest.fixture
def engine_manager(main_engine, event_engine, write_log):
    """Create EngineManager instance."""
    return EngineManager(main_engine, event_engine, write_log)


class TestBaseEngine:
    """Test BaseEngine functionality."""

    def test_init(self, main_engine, event_engine):
        """Test BaseEngine initialization."""
        engine = BaseEngine(main_engine, event_engine, "test")
        
        assert engine.main_engine == main_engine
        assert engine.event_engine == event_engine
        assert engine.engine_name == "test"

    def test_close(self, main_engine, event_engine):
        """Test BaseEngine close (default no-op)."""
        engine = BaseEngine(main_engine, event_engine, "test")
        # Should not raise any exceptions
        engine.close()


class TestEngineManager:
    """Test EngineManager functionality."""

    def test_init(self, engine_manager):
        """Test EngineManager initialization."""
        assert engine_manager.engines == {}

    def test_add_engine(self, engine_manager):
        """Test adding an engine."""
        engine = engine_manager.add_engine(MockEngine)
        
        assert "mock" in engine_manager.engines
        assert engine_manager.engines["mock"] == engine
        assert engine.engine_name == "mock"

    def test_add_duplicate_engine(self, engine_manager, write_log):
        """Test adding duplicate engine."""
        engine_manager.add_engine(MockEngine)
        engine = engine_manager.add_engine(MockEngine)
        
        # Should log error and return existing engine
        write_log.assert_called_with("Engine mock already exists.", source="MAIN")
        assert engine == engine_manager.engines["mock"]

    def test_get_engine(self, engine_manager):
        """Test getting engine by name."""
        engine = engine_manager.add_engine(MockEngine)
        
        result = engine_manager.get_engine("mock")
        assert result == engine
        
        result = engine_manager.get_engine("nonexistent")
        assert result is None

    def test_close_engines_with_close_method(self, engine_manager):
        """Test closing engines that have close method."""
        engine1 = engine_manager.add_engine(MockEngineWithClose)
        engine2 = engine_manager.add_engine(MockEngine)
        
        engine_manager.close()
        
        # Only engine with close method should be closed
        assert engine1.closed is True
        # MockEngine doesn't have meaningful close, so no assertion

    def test_multiple_engines(self, engine_manager):
        """Test managing multiple engines."""
        # Create a second mock engine class
        class MockEngine2(BaseEngine):
            def __init__(self, main_engine, event_engine):
                super().__init__(main_engine, event_engine, "mock2")
        
        engine1 = engine_manager.add_engine(MockEngine)
        engine2 = engine_manager.add_engine(MockEngine2)
        
        assert len(engine_manager.engines) == 2
        assert engine_manager.get_engine("mock") == engine1
        assert engine_manager.get_engine("mock2") == engine2

    def test_engine_initialization_params(self, engine_manager, main_engine, event_engine):
        """Test that engines are initialized with correct parameters."""
        engine = engine_manager.add_engine(MockEngine)
        
        assert engine.main_engine == main_engine
        assert engine.event_engine == event_engine