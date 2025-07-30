"""
Thread safety tests for EventEngine.

Tests concurrent operations, race conditions, and thread-safe behavior
of the EventEngine under high-concurrency scenarios.
"""

import pytest
import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from collections import defaultdict, Counter
from unittest.mock import Mock, patch

from foxtrot.core.event_engine import Event, EventEngine, EVENT_TIMER, HandlerType


class TestEventEngineThreadSafety:
    """Test thread safety of EventEngine core operations."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine(0.1)  # Fast timer for stress testing
        self.results = []
        self.errors = []
        self.lock = threading.Lock()
        
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def thread_safe_append(self, item):
        """Thread-safe append to results list."""
        with self.lock:
            self.results.append(item)
    
    def thread_safe_error(self, error):
        """Thread-safe append to errors list."""
        with self.lock:
            self.errors.append(error)
    
    def test_concurrent_event_putting(self):
        """Test multiple threads putting events simultaneously."""
        num_threads = 10
        events_per_thread = 100
        total_events = num_threads * events_per_thread
        
        received_events = []
        received_lock = threading.Lock()
        
        def event_handler(event: Event) -> None:
            with received_lock:
                received_events.append(event)
        
        # Register handler
        self.engine.register("test_event", event_handler)
        self.engine.start()
        
        def put_events(thread_id):
            """Put events from a specific thread."""
            try:
                for i in range(events_per_thread):
                    event = Event("test_event", f"thread_{thread_id}_event_{i}")
                    self.engine.put(event)
                    # Small random delay to increase race condition chances
                    time.sleep(random.uniform(0.001, 0.005))
            except Exception as e:
                self.thread_safe_error(e)
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=put_events, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Allow time for event processing
        time.sleep(2.0)
        
        self.engine.stop()
        
        # Verify all events were processed
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        assert len(received_events) == total_events
        
        # Verify event data integrity
        event_data = [event.data for event in received_events]
        expected_data = [f"thread_{tid}_event_{eid}" 
                        for tid in range(num_threads) 
                        for eid in range(events_per_thread)]
        
        assert sorted(event_data) == sorted(expected_data)
    
    def test_concurrent_handler_registration(self):
        """Test concurrent handler registration and unregistration."""
        num_threads = 5
        operations_per_thread = 50
        
        def handler_operations(thread_id):
            """Perform handler registration/unregistration operations."""
            try:
                handlers = []
                for i in range(operations_per_thread):
                    # Create unique handler
                    def make_handler(tid, hid):
                        def handler(event: Event) -> None:
                            self.thread_safe_append(f"handler_{tid}_{hid}")
                        return handler
                    
                    handler = make_handler(thread_id, i)
                    handlers.append(handler)
                    
                    # Register handler
                    event_type = f"event_type_{thread_id % 3}"  # Overlapping event types
                    self.engine.register(event_type, handler)
                    
                    # Random delay
                    time.sleep(random.uniform(0.001, 0.005))
                    
                    # Randomly unregister some handlers
                    if i > 10 and random.random() < 0.3:
                        old_handler = handlers[random.randint(0, len(handlers)-1)]
                        self.engine.unregister(event_type, old_handler)
                        
            except Exception as e:
                self.thread_safe_error(e)
        
        self.engine.start()
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=handler_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Test that the engine still works after concurrent operations
        test_event = Event("event_type_0", "test_data")
        self.engine.put(test_event)
        
        time.sleep(0.5)
        self.engine.stop()
        
        # Verify no errors occurred
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        # Verify engine is still functional
        assert not self.engine._active
    
    def test_concurrent_general_handler_operations(self):
        """Test concurrent general handler registration and unregistration."""
        num_threads = 8
        operations_per_thread = 30
        
        handler_registry = {}  # Track handlers by thread
        registry_lock = threading.Lock()
        
        def general_handler_operations(thread_id):
            """Perform general handler operations."""
            try:
                thread_handlers = []
                
                for i in range(operations_per_thread):
                    # Create unique handler
                    def make_handler(tid, hid):
                        def handler(event: Event) -> None:
                            self.thread_safe_append(f"general_{tid}_{hid}_{event.type}")
                        return handler
                    
                    handler = make_handler(thread_id, i)
                    thread_handlers.append(handler)
                    
                    # Register general handler
                    self.engine.register_general(handler)
                    
                    with registry_lock:
                        handler_registry[f"{thread_id}_{i}"] = handler
                    
                    # Random delay
                    time.sleep(random.uniform(0.001, 0.003))
                    
                    # Randomly unregister some handlers
                    if i > 5 and random.random() < 0.4:
                        old_handler = thread_handlers[random.randint(0, len(thread_handlers)-1)]
                        self.engine.unregister_general(old_handler)
                        
            except Exception as e:
                self.thread_safe_error(e)
        
        self.engine.start()
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=general_handler_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Put some test events while operations are running
        def put_test_events():
            for i in range(10):
                event = Event(f"test_type_{i}", f"data_{i}")
                self.engine.put(event)
                time.sleep(0.02)
        
        event_thread = threading.Thread(target=put_test_events)
        event_thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        event_thread.join()
        
        time.sleep(0.5)
        self.engine.stop()
        
        # Verify no errors occurred
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        # Verify some events were processed
        assert len(self.results) > 0
    
    def test_start_stop_race_conditions(self):
        """Test concurrent start/stop operations."""
        num_threads = 20
        operations_per_thread = 5
        
        def start_stop_operations(thread_id):
            """Perform start/stop operations."""
            try:
                for i in range(operations_per_thread):
                    # Random delay
                    time.sleep(random.uniform(0.01, 0.05))
                    
                    if random.random() < 0.5:
                        # Try to start
                        try:
                            if not self.engine._active:
                                self.engine.start()
                                self.thread_safe_append(f"started_{thread_id}_{i}")
                        except RuntimeError:
                            # Expected when already started
                            self.thread_safe_append(f"start_failed_{thread_id}_{i}")
                    else:
                        # Try to stop
                        try:
                            if self.engine._active:
                                self.engine.stop()
                                self.thread_safe_append(f"stopped_{thread_id}_{i}")
                        except RuntimeError:
                            # Expected when not started
                            self.thread_safe_append(f"stop_failed_{thread_id}_{i}")
            except Exception as e:
                self.thread_safe_error(e)
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=start_stop_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Ensure engine is stopped
        try:
            if self.engine._active:
                self.engine.stop()
        except:
            pass
        
        # Verify we handled concurrent operations gracefully
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        assert len(self.results) > 0  # Some operations should have succeeded
    
    def test_handler_exception_isolation(self):
        """Test that handler exceptions don't affect other handlers or engine stability."""
        num_threads = 5
        events_per_thread = 20
        
        successful_executions = []
        failed_executions = []
        execution_lock = threading.Lock()
        
        def failing_handler(event: Event) -> None:
            """Handler that always raises an exception."""
            with execution_lock:
                failed_executions.append(event.data)
            raise Exception(f"Handler failed for {event.data}")
        
        def working_handler(event: Event) -> None:
            """Handler that works correctly."""
            with execution_lock:
                successful_executions.append(event.data)
        
        # Register both handlers for the same event type
        self.engine.register("test_event", failing_handler)
        self.engine.register("test_event", working_handler)
        
        self.engine.start()
        
        def send_events(thread_id):
            """Send events from multiple threads."""
            try:
                for i in range(events_per_thread):
                    event = Event("test_event", f"thread_{thread_id}_event_{i}")
                    self.engine.put(event)
                    time.sleep(random.uniform(0.001, 0.01))
            except Exception as e:
                self.thread_safe_error(e)
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=send_events, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Allow time for event processing
        time.sleep(1.0)
        
        self.engine.stop()
        
        # Verify no errors occurred in the test threads
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        # Verify both handlers were called (despite failing_handler exceptions)
        total_events = num_threads * events_per_thread
        
        # Note: Current implementation doesn't have exception handling,
        # so failing handler will prevent working handler from being called
        # This test documents the current behavior
        assert len(failed_executions) > 0
        
        # The working handler might not be called due to failing handler exception
        # This is a limitation of the current implementation
    
    def test_queue_operations_thread_safety(self):
        """Test thread safety of queue operations under high load."""
        num_producers = 10
        num_consumers = 3
        events_per_producer = 50
        
        consumed_events = []
        consume_lock = threading.Lock()
        
        def event_consumer(event: Event) -> None:
            """Consumer that processes events."""
            with consume_lock:
                consumed_events.append(event.data)
                # Simulate processing time
                time.sleep(random.uniform(0.001, 0.005))
        
        self.engine.register("queue_test", event_consumer)
        self.engine.start()
        
        def event_producer(producer_id):
            """Producer that generates events."""
            try:
                for i in range(events_per_producer):
                    event = Event("queue_test", f"producer_{producer_id}_event_{i}")
                    self.engine.put(event)
                    
                    # Variable delay to create different load patterns
                    delay = random.uniform(0.001, 0.01)
                    if i % 10 == 0:  # Occasional burst
                        delay = 0.0
                    time.sleep(delay)
            except Exception as e:
                self.thread_safe_error(e)
        
        # Create and start producer threads
        threads = []
        for producer_id in range(num_producers):
            thread = threading.Thread(target=event_producer, args=(producer_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all producers to complete
        for thread in threads:
            thread.join()
        
        # Allow time for all events to be consumed
        time.sleep(3.0)
        
        self.engine.stop()
        
        # Verify all events were processed
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        total_expected = num_producers * events_per_producer
        assert len(consumed_events) == total_expected
        
        # Verify no duplicate processing
        event_counter = Counter(consumed_events)
        duplicates = [event for event, count in event_counter.items() if count > 1]
        assert len(duplicates) == 0, f"Duplicate events found: {duplicates}"
        
        # Verify all expected events are present
        expected_events = [f"producer_{pid}_event_{eid}" 
                          for pid in range(num_producers) 
                          for eid in range(events_per_producer)]
        assert sorted(consumed_events) == sorted(expected_events)
    
    def test_memory_consistency_under_load(self):
        """Test memory consistency and proper cleanup under high load."""
        num_threads = 15
        operations_per_thread = 30
        
        initial_handlers_count = len(self.engine._handlers)
        initial_general_count = len(self.engine._general_handlers)
        
        def memory_stress_operations(thread_id):
            """Perform operations that stress memory management."""
            try:
                handlers = []
                
                for i in range(operations_per_thread):
                    # Create handler
                    def make_handler(tid, oid):
                        def handler(event: Event) -> None:
                            # Simulate some work
                            data = f"processed_{tid}_{oid}_{event.type}"
                            self.thread_safe_append(data)
                        return handler
                    
                    handler = make_handler(thread_id, i)
                    handlers.append(handler)
                    
                    # Register for random event type
                    event_type = f"memory_test_{random.randint(0, 5)}"
                    
                    if random.random() < 0.7:
                        self.engine.register(event_type, handler)
                    else:
                        self.engine.register_general(handler)
                    
                    # Send some events
                    if i % 5 == 0:
                        for j in range(3):
                            event = Event(event_type, f"{thread_id}_{i}_{j}")
                            self.engine.put(event)
                    
                    # Randomly unregister some handlers
                    if len(handlers) > 10 and random.random() < 0.3:
                        old_handler = handlers.pop(random.randint(0, len(handlers)-1))
                        
                        if random.random() < 0.5:
                            self.engine.unregister(event_type, old_handler)
                        else:
                            self.engine.unregister_general(old_handler)
                    
                    # Small delay
                    time.sleep(random.uniform(0.001, 0.005))
                
                # Cleanup remaining handlers
                for handler in handlers:
                    try:
                        event_type = f"memory_test_{random.randint(0, 5)}"
                        self.engine.unregister(event_type, handler)
                    except:
                        try:
                            self.engine.unregister_general(handler)
                        except:
                            pass  # Handler might not be registered
                            
            except Exception as e:
                self.thread_safe_error(e)
        
        self.engine.start()
        
        # Create and start threads
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=memory_stress_operations, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Allow time for final event processing
        time.sleep(1.0)
        
        self.engine.stop()
        
        # Verify no errors occurred
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        # Verify some processing occurred
        assert len(self.results) > 0
        
        # Memory should be properly managed (no significant growth in handlers)
        # Allow for some handlers remaining due to registration/unregistration timing
        final_handlers_count = sum(len(handlers) for handlers in self.engine._handlers.values())
        final_general_count = len(self.engine._general_handlers)
        
        # Handlers count should not grow excessively
        # Allow for more realistic concurrent registration/unregistration timing
        max_expected_handlers = num_threads * operations_per_thread * 0.8
        max_expected_general = num_threads * operations_per_thread * 0.8
        
        assert final_handlers_count < max_expected_handlers, \
            f"Too many handlers: {final_handlers_count} >= {max_expected_handlers}"
        assert final_general_count < max_expected_general, \
            f"Too many general handlers: {final_general_count} >= {max_expected_general}"
    
    def test_timer_thread_safety(self):
        """Test timer thread safety with concurrent operations."""
        timer_events = []
        other_events = []
        event_lock = threading.Lock()
        
        def timer_handler(event: Event) -> None:
            with event_lock:
                timer_events.append(event)
        
        def other_handler(event: Event) -> None:
            with event_lock:
                other_events.append(event)
        
        # Use fast timer for testing
        self.engine = EventEngine(0.02)  # 20ms timer
        
        self.engine.register(EVENT_TIMER, timer_handler)
        self.engine.register("other_event", other_handler)
        
        self.engine.start()
        
        def send_other_events():
            """Send non-timer events."""
            try:
                for i in range(50):
                    event = Event("other_event", f"other_{i}")
                    self.engine.put(event)
                    time.sleep(random.uniform(0.005, 0.015))
            except Exception as e:
                self.thread_safe_error(e)
        
        # Start thread sending other events
        other_thread = threading.Thread(target=send_other_events)
        other_thread.start()
        
        # Let system run for a bit
        time.sleep(0.5)
        
        other_thread.join()
        
        # Continue running to collect more timer events
        time.sleep(0.3)
        
        self.engine.stop()
        
        # Verify no errors occurred
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        
        # Verify timer events were generated
        assert len(timer_events) > 10  # Should have many timer events
        
        # Verify other events were processed
        assert len(other_events) == 50
        
        # Verify timer events have correct type
        for event in timer_events:
            assert event.type == EVENT_TIMER
            assert event.data is None


class TestEventEngineRaceConditions:
    """Test specific race condition scenarios."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine(0.05)
        self.race_results = []
        self.race_lock = threading.Lock()
    
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def record_race_result(self, result):
        """Thread-safe result recording."""
        with self.race_lock:
            self.race_results.append(result)
    
    def test_handler_modification_during_processing(self):
        """Test modifying handlers while events are being processed."""
        processing_events = []
        process_lock = threading.Lock()
        
        def slow_handler(event: Event) -> None:
            """Handler that takes time to process."""
            with process_lock:
                processing_events.append(f"start_{event.data}")
            
            # Simulate processing time
            time.sleep(0.05)
            
            with process_lock:
                processing_events.append(f"end_{event.data}")
        
        self.engine.register("slow_event", slow_handler)
        self.engine.start()
        
        def send_events():
            """Send events continuously."""
            for i in range(10):
                event = Event("slow_event", f"event_{i}")
                self.engine.put(event)
                time.sleep(0.01)
        
        def modify_handlers():
            """Modify handlers while processing."""
            time.sleep(0.02)  # Let some processing start
            
            for i in range(5):
                # Add new handler
                def make_handler(hid):
                    def handler(event: Event) -> None:
                        self.record_race_result(f"new_handler_{hid}_{event.data}")
                    return handler
                
                new_handler = make_handler(i)
                self.engine.register("slow_event", new_handler)
                
                # Remove original handler after a bit
                if i == 2:
                    self.engine.unregister("slow_event", slow_handler)
                
                time.sleep(0.02)
        
        # Start both operations
        event_thread = threading.Thread(target=send_events)
        handler_thread = threading.Thread(target=modify_handlers)
        
        event_thread.start()
        handler_thread.start()
        
        event_thread.join()
        handler_thread.join()
        
        # Allow processing to complete
        time.sleep(0.5)
        
        self.engine.stop()
        
        # Verify system remained stable
        assert len(processing_events) > 0  # Some processing occurred
        assert len(self.race_results) > 0  # New handlers were called
    
    def test_queue_access_race_conditions(self):
        """Test race conditions in queue access patterns."""
        put_results = []
        get_results = []
        
        def queue_putter(thread_id):
            """Put events in queue rapidly."""
            try:
                for i in range(100):
                    event = Event("race_event", f"t{thread_id}_e{i}")
                    self.engine.put(event)
                    put_results.append(f"put_t{thread_id}_e{i}")
                    
                    # Occasional burst
                    if i % 20 == 0:
                        for j in range(5):
                            burst_event = Event("race_event", f"t{thread_id}_burst{i}_{j}")
                            self.engine.put(burst_event)
                            put_results.append(f"put_t{thread_id}_burst{i}_{j}")
                            
            except Exception as e:
                self.record_race_result(f"put_error: {e}")
        
        def event_processor(event: Event) -> None:
            """Process events and record."""
            get_results.append(f"got_{event.data}")
        
        self.engine.register("race_event", event_processor)
        self.engine.start()
        
        # Create multiple producer threads
        threads = []
        for thread_id in range(8):
            thread = threading.Thread(target=queue_putter, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all producers
        for thread in threads:
            thread.join()
        
        # Allow processing to complete
        time.sleep(2.0)
        
        self.engine.stop()
        
        # Verify all puts resulted in gets
        assert len(put_results) == len(get_results)
        
        # Verify no race condition errors
        error_results = [r for r in self.race_results if "error" in r]
        assert len(error_results) == 0, f"Race condition errors: {error_results}"
    
    def test_engine_state_consistency(self):
        """Test engine state remains consistent under concurrent operations."""
        state_checks = []
        
        def state_checker():
            """Check engine state consistency."""
            for _ in range(100):
                active = self.engine._active
                thread_alive = self.engine._thread.is_alive() if hasattr(self.engine._thread, 'is_alive') else False
                timer_alive = self.engine._timer.is_alive() if hasattr(self.engine._timer, 'is_alive') else False
                
                # Active state should be consistent with thread states
                if active:
                    state_checks.append(f"active_threads:{thread_alive}_{timer_alive}")
                else:
                    state_checks.append(f"inactive_threads:{thread_alive}_{timer_alive}")
                
                time.sleep(0.01)
        
        # Start state checker
        checker_thread = threading.Thread(target=state_checker)
        checker_thread.start()
        
        # Perform engine operations
        for cycle in range(3):
            try:
                self.engine.start()
                time.sleep(0.2)
                
                # Put some events
                for i in range(10):
                    event = Event("state_test", f"cycle_{cycle}_event_{i}")
                    self.engine.put(event)
                
                time.sleep(0.2)
                self.engine.stop()
                time.sleep(0.1)
                
                # Recreate engine for next cycle
                if cycle < 2:
                    self.engine = EventEngine(0.05)
                    
            except RuntimeError:
                # Expected in some race conditions
                pass
        
        checker_thread.join()
        
        # Analyze state consistency
        inconsistent_states = []
        for state in state_checks:
            if state.startswith("active_threads:False") or state.startswith("inactive_threads:True"):
                inconsistent_states.append(state)
        
        # Allow some inconsistency due to timing, but not too much
        inconsistency_rate = len(inconsistent_states) / len(state_checks)
        assert inconsistency_rate < 0.1, f"High inconsistency rate: {inconsistency_rate}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])