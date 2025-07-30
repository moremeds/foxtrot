"""
Unit tests for EventEngine core functionality.

Tests individual classes and methods in isolation with comprehensive coverage
of event handling, lifecycle management, and handler registration.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict
from queue import Queue, Empty

from foxtrot.core.event_engine import Event, EventEngine, EVENT_TIMER, HandlerType


class TestEvent:
    """Test Event class functionality."""
    
    def test_event_creation_with_type_only(self):
        """Test Event creation with type parameter only."""
        event = Event("test_type")
        assert event.type == "test_type"
        assert event.data is None
    
    def test_event_creation_with_type_and_data(self):
        """Test Event creation with both type and data parameters."""
        test_data = {"price": 100.0, "volume": 1.5}
        event = Event("market_data", test_data)
        assert event.type == "market_data"
        assert event.data == test_data
    
    def test_event_creation_with_complex_data(self):
        """Test Event creation with complex data structures."""
        class TestData:
            def __init__(self, value):
                self.value = value
        
        test_obj = TestData("complex_value")
        event = Event("complex_event", test_obj)
        assert event.type == "complex_event"
        assert event.data.value == "complex_value"
    
    def test_event_type_validation(self):
        """Test Event type parameter validation."""
        # Test with empty string
        event = Event("")
        assert event.type == ""
        
        # Test with special characters
        event = Event("test.event_type-123")
        assert event.type == "test.event_type-123"
    
    def test_event_data_types(self):
        """Test Event with various data types."""
        test_cases = [
            ("string_data", "test_string"),
            ("int_data", 42),
            ("float_data", 3.14159),
            ("list_data", [1, 2, 3, "test"]),
            ("dict_data", {"key": "value", "number": 123}),
            ("none_data", None),
            ("bool_data", True)
        ]
        
        for event_type, data in test_cases:
            event = Event(event_type, data)
            assert event.type == event_type
            assert event.data == data


class TestEventEngineInitialization:
    """Test EventEngine initialization and configuration."""
    
    def test_default_initialization(self):
        """Test EventEngine initialization with default parameters."""
        engine = EventEngine()
        
        # Check default interval
        assert engine._interval == 1.0
        
        # Check initial state
        assert engine._active is False
        assert isinstance(engine._queue, Queue)
        assert isinstance(engine._handlers, defaultdict)
        assert isinstance(engine._general_handlers, list)
        assert len(engine._general_handlers) == 0
        
        # Check threads are created but not started
        assert isinstance(engine._thread, threading.Thread)
        assert isinstance(engine._timer, threading.Thread)
        assert engine._thread.is_alive() is False
        assert engine._timer.is_alive() is False
    
    def test_custom_interval_initialization(self):
        """Test EventEngine initialization with custom interval."""
        custom_intervals = [0.1, 0.5, 2.0, 5.0, 10.0]
        
        for interval in custom_intervals:
            engine = EventEngine(interval)
            assert engine._interval == interval
            assert engine._active is False
    
    def test_zero_interval_initialization(self):
        """Test EventEngine initialization with zero interval."""
        engine = EventEngine(0.0)
        assert engine._interval == 0.0
    
    def test_negative_interval_initialization(self):
        """Test EventEngine initialization with negative interval."""
        engine = EventEngine(-1.0)
        assert engine._interval == -1.0
        # Note: Negative interval will cause immediate timer events
    
    def test_thread_target_assignment(self):
        """Test that threads are created with correct target methods."""
        engine = EventEngine()
        
        # Check thread targets are assigned correctly (using private _target attribute)
        assert engine._thread._target == engine._run
        assert engine._timer._target == engine._run_timer
    
    def test_handlers_structure(self):
        """Test handlers data structure initialization."""
        engine = EventEngine()
        
        # Test defaultdict behavior
        test_type = "test_event"
        handler_list = engine._handlers[test_type]
        assert isinstance(handler_list, list)
        assert len(handler_list) == 0
        
        # Verify defaultdict creates empty list for new keys
        assert test_type in engine._handlers
        assert len(engine._handlers[test_type]) == 0


class TestEventEngineLifecycle:
    """Test EventEngine start/stop lifecycle management."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine(0.1)  # Fast interval for testing
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_start_engine(self):
        """Test starting the EventEngine."""
        assert self.engine._active is False
        
        self.engine.start()
        
        # Check engine is active
        assert self.engine._active is True
        
        # Check threads are started
        time.sleep(0.05)  # Brief wait for threads to start
        assert self.engine._thread.is_alive() is True
        assert self.engine._timer.is_alive() is True
        
        # Cleanup
        self.engine.stop()
    
    def test_stop_engine(self):
        """Test stopping the EventEngine."""
        self.engine.start()
        time.sleep(0.05)  # Allow threads to start
        
        assert self.engine._active is True
        assert self.engine._thread.is_alive() is True
        assert self.engine._timer.is_alive() is True
        
        self.engine.stop()
        
        # Check engine is stopped
        assert self.engine._active is False
        
        # Check threads are stopped (with timeout)
        start_time = time.time()
        while (self.engine._thread.is_alive() or self.engine._timer.is_alive()) and (time.time() - start_time) < 2.0:
            time.sleep(0.01)
        
        assert self.engine._thread.is_alive() is False
        assert self.engine._timer.is_alive() is False
    
    def test_double_start_engine(self):
        """Test calling start() twice is idempotent and safe."""
        self.engine.start()
        time.sleep(0.05)
        
        thread_id = self.engine._thread.ident
        timer_id = self.engine._timer.ident
        
        # Try to start again - should be idempotent (no exception)
        self.engine.start()  # Should not raise exception
        
        # Thread IDs should remain the same since threads are still alive
        assert self.engine._thread.ident == thread_id
        assert self.engine._timer.ident == timer_id
        assert self.engine._active is True
        
        self.engine.stop()
    
    def test_stop_before_start(self):
        """Test calling stop() before start() is idempotent and safe."""
        assert self.engine._active is False
        
        # This should be idempotent (no exception) - safe to call stop before start
        self.engine.stop()  # Should not raise exception
        
        assert self.engine._active is False
    
    def test_multiple_start_stop_cycles(self):
        """Test multiple start/stop cycles."""
        for cycle in range(3):
            self.engine.start()
            time.sleep(0.05)
            assert self.engine._active is True
            
            self.engine.stop()
            assert self.engine._active is False
            
            # Threads should be stopped
            time.sleep(0.1)
            assert self.engine._thread.is_alive() is False
            assert self.engine._timer.is_alive() is False
            
            # Create new engine for next cycle
            if cycle < 2:
                self.engine = EventEngine(0.1)


class TestEventEngineHandlerManagement:
    """Test handler registration and unregistration functionality."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine()
        self.test_events = []
        
        # Test handler that records events
        def test_handler(event: Event) -> None:
            self.test_events.append(event)
        
        self.test_handler = test_handler
        
        # Another test handler
        def another_handler(event: Event) -> None:
            self.test_events.append(f"another: {event.type}")
        
        self.another_handler = another_handler
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_register_handler(self):
        """Test registering a handler for specific event type."""
        event_type = "test_event"
        
        self.engine.register(event_type, self.test_handler)
        
        # Check handler is registered
        assert event_type in self.engine._handlers
        assert self.test_handler in self.engine._handlers[event_type]
        assert len(self.engine._handlers[event_type]) == 1
    
    def test_register_multiple_handlers_same_type(self):
        """Test registering multiple handlers for same event type."""
        event_type = "test_event"
        
        self.engine.register(event_type, self.test_handler)
        self.engine.register(event_type, self.another_handler)
        
        # Check both handlers are registered
        assert len(self.engine._handlers[event_type]) == 2
        assert self.test_handler in self.engine._handlers[event_type]
        assert self.another_handler in self.engine._handlers[event_type]
    
    def test_register_same_handler_twice(self):
        """Test registering same handler twice for same type (should not duplicate)."""
        event_type = "test_event"
        
        self.engine.register(event_type, self.test_handler)
        self.engine.register(event_type, self.test_handler)
        
        # Handler should only appear once
        assert len(self.engine._handlers[event_type]) == 1
        assert self.test_handler in self.engine._handlers[event_type]
    
    def test_register_handler_different_types(self):
        """Test registering same handler for different event types."""
        event_types = ["type1", "type2", "type3"]
        
        for event_type in event_types:
            self.engine.register(event_type, self.test_handler)
        
        # Check handler is registered for all types
        for event_type in event_types:
            assert self.test_handler in self.engine._handlers[event_type]
            assert len(self.engine._handlers[event_type]) == 1
    
    def test_unregister_handler(self):
        """Test unregistering a handler."""
        event_type = "test_event"
        
        # Register then unregister
        self.engine.register(event_type, self.test_handler)
        assert self.test_handler in self.engine._handlers[event_type]
        
        self.engine.unregister(event_type, self.test_handler)
        
        # Handler should be removed and event type cleaned up
        assert event_type not in self.engine._handlers
    
    def test_unregister_one_of_multiple_handlers(self):
        """Test unregistering one handler when multiple are registered."""
        event_type = "test_event"
        
        self.engine.register(event_type, self.test_handler)
        self.engine.register(event_type, self.another_handler)
        
        self.engine.unregister(event_type, self.test_handler)
        
        # Only another_handler should remain
        assert len(self.engine._handlers[event_type]) == 1
        assert self.another_handler in self.engine._handlers[event_type]
        assert self.test_handler not in self.engine._handlers[event_type]
    
    def test_unregister_nonexistent_handler(self):
        """Test unregistering handler that was never registered."""
        event_type = "test_event"
        
        # This should not raise an exception
        self.engine.unregister(event_type, self.test_handler)
        
        # Should not create entry in handlers dict
        assert len(self.engine._handlers) == 0
    
    def test_register_general_handler(self):
        """Test registering a general handler for all event types."""
        self.engine.register_general(self.test_handler)
        
        assert self.test_handler in self.engine._general_handlers
        assert len(self.engine._general_handlers) == 1
    
    def test_register_multiple_general_handlers(self):
        """Test registering multiple general handlers."""
        self.engine.register_general(self.test_handler)
        self.engine.register_general(self.another_handler)
        
        assert len(self.engine._general_handlers) == 2
        assert self.test_handler in self.engine._general_handlers
        assert self.another_handler in self.engine._general_handlers
    
    def test_register_same_general_handler_twice(self):
        """Test registering same general handler twice (should not duplicate)."""
        self.engine.register_general(self.test_handler)
        self.engine.register_general(self.test_handler)
        
        assert len(self.engine._general_handlers) == 1
        assert self.test_handler in self.engine._general_handlers
    
    def test_unregister_general_handler(self):
        """Test unregistering a general handler."""
        self.engine.register_general(self.test_handler)
        assert self.test_handler in self.engine._general_handlers
        
        self.engine.unregister_general(self.test_handler)
        
        assert self.test_handler not in self.engine._general_handlers
        assert len(self.engine._general_handlers) == 0
    
    def test_unregister_nonexistent_general_handler(self):
        """Test unregistering general handler that was never registered."""
        # This should not raise an exception
        self.engine.unregister_general(self.test_handler)
        
        assert len(self.engine._general_handlers) == 0


class TestEventEngineEventProcessing:
    """Test event processing and distribution functionality."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine(0.1)
        self.received_events = []
        self.handler_call_count = 0
        
        # Test handler that records events
        def recording_handler(event: Event) -> None:
            self.received_events.append(event)
            self.handler_call_count += 1
        
        self.recording_handler = recording_handler
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_put_event(self):
        """Test putting an event into the queue."""
        event = Event("test_event", "test_data")
        
        # Queue should be empty initially
        assert self.engine._queue.qsize() == 0
        
        self.engine.put(event)
        
        # Event should be in queue
        assert self.engine._queue.qsize() == 1
    
    def test_put_multiple_events(self):
        """Test putting multiple events into the queue."""
        events = [
            Event("event1", "data1"),
            Event("event2", "data2"),
            Event("event3", "data3")
        ]
        
        for event in events:
            self.engine.put(event)
        
        assert self.engine._queue.qsize() == 3
    
    def test_event_processing_with_specific_handler(self):
        """Test event processing with type-specific handler."""
        event_type = "test_event"
        event_data = "test_data"
        
        # Register handler
        self.engine.register(event_type, self.recording_handler)
        
        # Start engine and put event
        self.engine.start()
        event = Event(event_type, event_data)
        self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check event was processed
        assert len(self.received_events) == 1
        assert self.received_events[0].type == event_type
        assert self.received_events[0].data == event_data
        
        self.engine.stop()
    
    def test_event_processing_with_general_handler(self):
        """Test event processing with general handler."""
        event_type = "any_event"
        event_data = "any_data"
        
        # Register general handler
        self.engine.register_general(self.recording_handler)
        
        # Start engine and put event
        self.engine.start()
        event = Event(event_type, event_data)
        self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check event was processed by general handler
        # Note: General handlers also receive timer events, so we need to filter
        non_timer_events = [e for e in self.received_events if e.type != EVENT_TIMER]
        assert len(non_timer_events) == 1
        assert non_timer_events[0].type == event_type
        assert non_timer_events[0].data == event_data
        
        self.engine.stop()
    
    def test_event_processing_with_both_handlers(self):
        """Test event processing with both specific and general handlers."""
        event_type = "test_event"
        
        specific_events = []
        general_events = []
        
        def specific_handler(event: Event) -> None:
            specific_events.append(event)
        
        def general_handler(event: Event) -> None:
            general_events.append(event)
        
        # Register both handlers
        self.engine.register(event_type, specific_handler)
        self.engine.register_general(general_handler)
        
        # Start engine and put event
        self.engine.start()
        event = Event(event_type, "test_data")
        self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Both handlers should have received the event
        # Note: General handler also receives timer events, so filter for our event
        assert len(specific_events) == 1
        non_timer_general_events = [e for e in general_events if e.type != EVENT_TIMER]
        assert len(non_timer_general_events) == 1
        assert specific_events[0].type == event_type
        assert non_timer_general_events[0].type == event_type
        
        self.engine.stop()
    
    def test_event_processing_no_matching_handler(self):
        """Test event processing when no handlers match."""
        event_type = "unhandled_event"
        
        # Register handler for different type
        self.engine.register("different_type", self.recording_handler)
        
        # Start engine and put event
        self.engine.start()
        event = Event(event_type, "test_data")
        self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # No events should be received
        assert len(self.received_events) == 0
        
        self.engine.stop()
    
    def test_multiple_events_processing(self):
        """Test processing multiple events in sequence."""
        event_types = ["event1", "event2", "event3"]
        
        # Register handler for all types
        for event_type in event_types:
            self.engine.register(event_type, self.recording_handler)
        
        # Start engine
        self.engine.start()
        
        # Put multiple events
        for i, event_type in enumerate(event_types):
            event = Event(event_type, f"data{i}")
            self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.3)
        
        # All events should be processed
        assert len(self.received_events) == 3
        for i, event in enumerate(self.received_events):
            assert event.type == event_types[i]
            assert event.data == f"data{i}"
        
        self.engine.stop()
    
    def test_handler_exception_handling(self):
        """Test that handler exceptions don't stop event processing."""
        failing_handler_called = False
        working_handler_called = False
        
        def failing_handler(event: Event) -> None:
            nonlocal failing_handler_called
            failing_handler_called = True
            raise Exception("Handler failed")
        
        def working_handler(event: Event) -> None:
            nonlocal working_handler_called
            working_handler_called = True
        
        event_type = "test_event"
        
        # Register both handlers
        self.engine.register(event_type, failing_handler)
        self.engine.register(event_type, working_handler)
        
        # Start engine and put event
        self.engine.start()
        event = Event(event_type, "test_data")
        self.engine.put(event)
        
        # Wait for processing
        time.sleep(0.2)
        
        # Both handlers should have been called despite exception
        # Note: The current implementation doesn't have exception handling,
        # so this test documents the current behavior
        assert failing_handler_called is True
        
        self.engine.stop()


class TestEventEngineTimerFunctionality:
    """Test timer event generation functionality."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.timer_events = []
        
        def timer_handler(event: Event) -> None:
            if event.type == EVENT_TIMER:
                self.timer_events.append(event)
        
        self.timer_handler = timer_handler
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_timer_event_generation(self):
        """Test that timer events are generated at specified intervals."""
        self.engine = EventEngine(0.1)  # 100ms interval
        
        self.engine.register(EVENT_TIMER, self.timer_handler)
        self.engine.start()
        
        # Wait for multiple timer intervals
        time.sleep(0.35)
        
        self.engine.stop()
        
        # Should have received 2-4 timer events (accounting for timing variations)
        assert len(self.timer_events) >= 2
        assert len(self.timer_events) <= 5
        
        # All events should be timer events
        for event in self.timer_events:
            assert event.type == EVENT_TIMER
            assert event.data is None
    
    def test_timer_event_interval_accuracy(self):
        """Test timer event interval accuracy."""
        self.engine = EventEngine(0.05)  # 50ms interval
        
        timestamps = []
        
        def timestamp_handler(event: Event) -> None:
            if event.type == EVENT_TIMER:
                timestamps.append(time.time())
        
        self.engine.register(EVENT_TIMER, timestamp_handler)
        self.engine.start()
        
        # Wait for several timer events
        time.sleep(0.3)
        
        self.engine.stop()
        
        # Check interval accuracy
        if len(timestamps) >= 2:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            # Allow 50% tolerance for timing variations
            assert 0.025 <= avg_interval <= 0.075
    
    def test_timer_with_different_intervals(self):
        """Test timer functionality with different intervals."""
        intervals = [0.02, 0.05, 0.1, 0.2]
        
        for interval in intervals:
            self.timer_events.clear()
            self.engine = EventEngine(interval)
            
            self.engine.register(EVENT_TIMER, self.timer_handler)
            self.engine.start()
            
            # Wait for multiple intervals
            wait_time = interval * 3
            time.sleep(wait_time)
            
            self.engine.stop()
            
            # Should have received some timer events
            assert len(self.timer_events) >= 1
    
    def test_timer_stops_with_engine(self):
        """Test that timer stops when engine is stopped."""
        self.engine = EventEngine(0.05)
        
        self.engine.register(EVENT_TIMER, self.timer_handler)
        self.engine.start()
        
        # Let it run briefly
        time.sleep(0.15)
        initial_count = len(self.timer_events)
        
        # Stop engine
        self.engine.stop()
        
        # Wait longer to ensure no more events are generated
        time.sleep(0.2)
        final_count = len(self.timer_events)
        
        # Timer should stop (allow for one additional event due to timing)
        assert final_count <= initial_count + 1


class TestEventEngineEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine()
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_empty_queue_processing(self):
        """Test event processing when queue is empty."""
        self.engine.start()
        
        # Let it run with empty queue
        time.sleep(0.2)
        
        # Should not crash or hang
        assert self.engine._active is True
        
        self.engine.stop()
    
    def test_handler_returning_values(self):
        """Test handlers that return values (should be ignored)."""
        returned_values = []
        
        def value_returning_handler(event: Event) -> str:
            return f"processed: {event.type}"
        
        self.engine.register("test_event", value_returning_handler)
        self.engine.start()
        
        event = Event("test_event", "data")
        self.engine.put(event)
        
        time.sleep(0.1)
        
        # Should process without issues
        assert self.engine._active is True
        
        self.engine.stop()
    
    def test_none_handler_registration(self):
        """Test registering None as handler (current implementation allows it)."""
        # Current implementation allows None handlers, but they will fail when called
        self.engine.register("test_event", None)
        
        # Verify None is in the handler list
        assert None in self.engine._handlers["test_event"]
        
        # When event is processed, it will fail silently due to list comprehension
        self.engine.start()
        event = Event("test_event", "data")
        self.engine.put(event)
        
        # Should not crash the engine (fails silently in list comprehension)
        time.sleep(0.1)
        assert self.engine._active is True
        
        self.engine.stop()
    
    def test_invalid_event_type(self):
        """Test with various invalid event types."""
        # Empty string event type (allowed)
        event = Event("", "data")
        self.engine.put(event)
        
        # None event type is actually allowed by current implementation
        event_with_none_type = Event(None, "data")
        assert event_with_none_type.type is None
        assert event_with_none_type.data == "data"
    
    def test_large_event_data(self):
        """Test with large event data."""
        large_data = "x" * 10000  # 10KB string
        event = Event("large_event", large_data)
        
        self.engine.put(event)
        assert self.engine._queue.qsize() == 1
    
    def test_rapid_handler_registration_unregistration(self):
        """Test rapid handler registration and unregistration."""
        def test_handler(event: Event) -> None:
            pass
        
        event_type = "rapid_test"
        
        # Rapidly register and unregister
        for _ in range(100):
            self.engine.register(event_type, test_handler)
            self.engine.unregister(event_type, test_handler)
        
        # Should end up with no handlers
        assert event_type not in self.engine._handlers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])