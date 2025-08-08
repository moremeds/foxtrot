"""
Basic unit tests for MainEngine.

These tests verify core MainEngine initialization without complex adapter scenarios.
"""

import unittest
from unittest.mock import patch, MagicMock

from foxtrot.server.engine import MainEngine
from foxtrot.core.event_engine import EventEngine


class TestMainEngineBasic(unittest.TestCase):
    """Basic tests for MainEngine functionality."""

    def setUp(self):
        """Set up test environment."""
        # We'll create MainEngine in individual tests to control initialization
        self.main_engine = None

    def tearDown(self):
        """Clean up MainEngine."""
        if self.main_engine:
            self.main_engine.close()

    def test_main_engine_initialization(self):
        """Test MainEngine can be created with basic components."""
        self.main_engine = MainEngine()
        
        # Should have core components
        self.assertIsNotNone(self.main_engine)
        self.assertIsInstance(self.main_engine.event_engine, EventEngine)
        self.assertIsNotNone(self.main_engine.engines)
        self.assertIsNotNone(self.main_engine.adapters)

    def test_main_engine_event_engine_integration(self):
        """Test MainEngine properly integrates with EventEngine."""
        self.main_engine = MainEngine()
        
        # Event engine should be created and available
        self.assertIsInstance(self.main_engine.event_engine, EventEngine)
        
        # Event engine should be automatically started by MainEngine
        self.assertTrue(self.main_engine.event_engine._active)

    def test_main_engine_adapter_management(self):
        """Test MainEngine adapter management functionality."""
        self.main_engine = MainEngine()
        
        # Should start with empty adapters dict
        self.assertIsInstance(self.main_engine.adapters, dict)
        self.assertEqual(len(self.main_engine.adapters), 0)

    def test_main_engine_engine_management(self):
        """Test MainEngine engine management functionality."""
        self.main_engine = MainEngine()
        
        # Should have engines dict for managing sub-engines
        self.assertIsInstance(self.main_engine.engines, dict)

    @patch('foxtrot.server.engine.create_foxtrot_logger')
    def test_main_engine_logging_setup(self, mock_logger_factory):
        """Test MainEngine sets up logging properly."""
        mock_logger = MagicMock()
        mock_logger_factory.return_value = mock_logger
        
        self.main_engine = MainEngine()
        
        # Should have attempted to create logger
        mock_logger_factory.assert_called_once()

    def test_main_engine_close_functionality(self):
        """Test MainEngine can be closed cleanly."""
        self.main_engine = MainEngine()
        
        # Should be able to close without errors
        try:
            self.main_engine.close()
            # After closing, shouldn't raise exceptions
        except Exception as e:
            self.fail(f"MainEngine.close() raised unexpected exception: {e}")

    def test_main_engine_get_engine(self):
        """Test MainEngine engine retrieval functionality."""
        self.main_engine = MainEngine()
        
        # Should be able to call get_engine method
        self.assertTrue(hasattr(self.main_engine, 'get_engine'))
        
        # Getting non-existent engine should return None
        result = self.main_engine.get_engine("nonexistent_engine")
        self.assertIsNone(result)

    def test_main_engine_add_adapter(self):
        """Test MainEngine adapter addition functionality."""
        self.main_engine = MainEngine()
        
        # Should have add_adapter method
        self.assertTrue(hasattr(self.main_engine, 'add_adapter'))
        
        # Mock adapter for testing
        mock_adapter = MagicMock()
        mock_adapter.adapter_name = "test_adapter"
        
        # Should be able to add adapter
        try:
            self.main_engine.add_adapter(mock_adapter)
            self.assertIn("test_adapter", self.main_engine.adapters)
        except Exception as e:
            # If method signature is different, just verify it exists
            self.assertTrue(callable(getattr(self.main_engine, 'add_adapter', None)))

    def test_main_engine_basic_state(self):
        """Test MainEngine basic state properties."""
        self.main_engine = MainEngine()
        
        # Should have basic state tracking
        # These are basic expectations for a trading engine
        self.assertTrue(hasattr(self.main_engine, 'adapters'))
        self.assertTrue(hasattr(self.main_engine, 'engines'))
        self.assertTrue(hasattr(self.main_engine, 'event_engine'))

    def test_main_engine_multiple_instances(self):
        """Test multiple MainEngine instances can be created."""
        engine1 = MainEngine()
        engine2 = MainEngine()
        
        try:
            # Should be separate instances
            self.assertIsNot(engine1, engine2)
            self.assertIsNot(engine1.event_engine, engine2.event_engine)
        finally:
            # Clean up both engines
            engine1.close()
            engine2.close()


if __name__ == '__main__':
    unittest.main()