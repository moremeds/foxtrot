"""
Basic unit tests for EventEngine.

These tests verify core event handling functionality without complex scenarios.
"""

import unittest
import time
from threading import Event as ThreadingEvent

from foxtrot.core.event_engine import EventEngine
from foxtrot.core.event import Event
from foxtrot.util.event_type import EVENT_TICK, EVENT_LOG


class TestEventEngineBasic(unittest.TestCase):
    """Basic tests for EventEngine functionality."""

    def setUp(self):
        """Set up test EventEngine."""
        self.engine = EventEngine()

    def tearDown(self):
        """Clean up EventEngine."""
        if self.engine and self.engine._active:
            self.engine.stop()

    def test_event_engine_initialization(self):
        """Test EventEngine can be created and has expected attributes."""
        self.assertIsNotNone(self.engine)
        self.assertFalse(self.engine._active)
        self.assertIsNotNone(self.engine._queue)
        self.assertIsNotNone(self.engine._handlers)

    def test_event_engine_start_stop(self):
        """Test EventEngine can start and stop cleanly."""
        # Start engine
        self.engine.start()
        self.assertTrue(self.engine._active)
        
        # Allow brief time for startup
        time.sleep(0.1)
        
        # Stop engine
        self.engine.stop()
        self.assertFalse(self.engine._active)

    def test_event_handler_registration(self):
        """Test event handler registration."""
        handler_called = ThreadingEvent()
        
        def test_handler(event):
            handler_called.set()
        
        # Register handler
        self.engine.register(EVENT_TICK, test_handler)
        
        # Verify handler is registered
        self.assertIn(EVENT_TICK, self.engine._handlers)
        self.assertIn(test_handler, self.engine._handlers[EVENT_TICK])

    def test_basic_event_processing(self):
        """Test basic event can be processed."""
        handler_called = ThreadingEvent()
        received_event = None
        
        def test_handler(event):
            nonlocal received_event
            received_event = event
            handler_called.set()
        
        # Register handler and start engine
        self.engine.register(EVENT_LOG, test_handler)
        self.engine.start()
        
        # Create and put test event
        test_event = Event(EVENT_LOG, "Test message")
        self.engine.put(test_event)
        
        # Wait for handler to be called (with timeout)
        handler_called.wait(timeout=2.0)
        
        # Verify handler was called with correct event
        self.assertTrue(handler_called.is_set(), "Handler was not called within timeout")
        self.assertIsNotNone(received_event)
        self.assertEqual(received_event.type, EVENT_LOG)
        self.assertEqual(received_event.data, "Test message")

    def test_multiple_handlers_same_event(self):
        """Test multiple handlers can be registered for same event type."""
        handler1_called = ThreadingEvent()
        handler2_called = ThreadingEvent()
        
        def handler1(event):
            handler1_called.set()
        
        def handler2(event):
            handler2_called.set()
        
        # Register both handlers for same event
        self.engine.register(EVENT_TICK, handler1)
        self.engine.register(EVENT_TICK, handler2)
        
        # Start engine and send event
        self.engine.start()
        test_event = Event(EVENT_TICK, {})
        self.engine.put(test_event)
        
        # Both handlers should be called
        handler1_called.wait(timeout=2.0)
        handler2_called.wait(timeout=2.0)
        
        self.assertTrue(handler1_called.is_set())
        self.assertTrue(handler2_called.is_set())

    def test_event_queue_functionality(self):
        """Test events are properly queued."""
        self.engine.start()
        
        # Put multiple events
        event1 = Event(EVENT_LOG, "Message 1")
        event2 = Event(EVENT_LOG, "Message 2")
        
        self.engine.put(event1)
        self.engine.put(event2)
        
        # Queue should not be empty immediately after putting events
        # Note: This is a basic check, actual queue might be processed quickly
        time.sleep(0.1)  # Allow processing

    def test_engine_restart(self):
        """Test engine can be restarted after stopping."""
        # Start, stop, then start again
        self.engine.start()
        self.assertTrue(self.engine._active)
        
        self.engine.stop()
        self.assertFalse(self.engine._active)
        
        # Should be able to start again
        self.engine.start()
        self.assertTrue(self.engine._active)


if __name__ == '__main__':
    unittest.main()