"""
Performance tests for EventEngine.

Benchmarks event processing throughput, latency, and resource usage
under various load conditions with realistic trading scenarios.
"""

import pytest
import time
import threading
import statistics
import gc
import resource
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, defaultdict
from unittest.mock import Mock

from foxtrot.core.event_engine import Event, EventEngine, EVENT_TIMER, HandlerType


class PerformanceBenchmark:
    """Base class for performance benchmarks."""
    
    def __init__(self):
        self.metrics = {}
        
    def start_monitoring(self):
        """Start performance monitoring."""
        gc.collect()  # Clean memory before test
        self.start_time = time.time()
        try:
            # Try to get memory usage if available
            self.start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB on Linux
        except:
            self.start_memory = 0
        
    def stop_monitoring(self):
        """Stop monitoring and record metrics."""
        self.end_time = time.time()
        try:
            self.end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # MB on Linux
        except:
            self.end_memory = 0
        
        self.metrics['duration'] = self.end_time - self.start_time
        self.metrics['memory_delta'] = self.end_memory - self.start_memory
        
        return self.metrics


class TestEventEnginePerformance:
    """Performance tests for EventEngine throughput and latency."""
    
    def setup_method(self):
        """Setup fresh EventEngine for each test."""
        self.engine = EventEngine(0.1)
        self.benchmark = PerformanceBenchmark()
        
    def teardown_method(self):
        """Cleanup EventEngine after each test."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_event_processing_throughput(self):
        """Benchmark event processing throughput."""
        num_events = 10000
        processed_events = []
        processing_times = []
        
        def throughput_handler(event: Event) -> None:
            """Handler that records processing statistics."""
            process_time = time.time()
            processed_events.append(event.data)
            processing_times.append(process_time)
        
        # Register handler and start engine
        self.engine.register("throughput_test", throughput_handler)
        self.engine.start()
        
        # Start performance monitoring
        self.benchmark.start_monitoring()
        
        # Send events as fast as possible
        start_send_time = time.time()
        for i in range(num_events):
            event = Event("throughput_test", f"event_{i}")
            self.engine.put(event)
        end_send_time = time.time()
        
        # Wait for all events to be processed
        timeout = 30.0  # 30 second timeout
        start_wait = time.time()
        while len(processed_events) < num_events and (time.time() - start_wait) < timeout:
            time.sleep(0.01)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Calculate performance metrics
        send_duration = end_send_time - start_send_time
        total_duration = metrics['duration']
        
        events_per_second = num_events / total_duration
        send_rate = num_events / send_duration
        
        # Verify all events were processed
        assert len(processed_events) == num_events, f"Only {len(processed_events)}/{num_events} events processed"
        
        # Performance assertions
        assert events_per_second > 1000, f"Throughput too low: {events_per_second:.2f} events/sec"
        assert send_rate > 10000, f"Send rate too low: {send_rate:.2f} events/sec"
        
        # Memory usage should be reasonable (if available)
        if metrics['memory_delta'] > 0:
            assert metrics['memory_delta'] < 500, f"Excessive memory usage: {metrics['memory_delta']:.2f} MB"
        
        print(f"\nThroughput Benchmark Results:")
        print(f"  Events processed: {len(processed_events)}")
        print(f"  Total duration: {total_duration:.3f}s")
        print(f"  Events/second: {events_per_second:.2f}")
        print(f"  Send rate: {send_rate:.2f} events/sec")
        print(f"  Memory delta: {metrics['memory_delta']:.2f} MB")
    
    def test_event_processing_latency(self):
        """Benchmark event processing latency distribution."""
        num_events = 1000
        latencies = []
        
        def latency_handler(event: Event) -> None:
            """Handler that measures latency."""
            receive_time = time.time()
            send_time = float(event.data)
            latency = (receive_time - send_time) * 1000  # Convert to milliseconds
            latencies.append(latency)
        
        # Register handler and start engine
        self.engine.register("latency_test", latency_handler)
        self.engine.start()
        
        # Start monitoring
        self.benchmark.start_monitoring()
        
        # Send events with timestamps
        for i in range(num_events):
            send_time = time.time()
            event = Event("latency_test", str(send_time))
            self.engine.put(event)
            time.sleep(0.001)  # Small delay to spread events
        
        # Wait for processing to complete
        timeout = 10.0
        start_wait = time.time()
        while len(latencies) < num_events and (time.time() - start_wait) < timeout:
            time.sleep(0.01)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Calculate latency statistics
        assert len(latencies) == num_events, f"Only {len(latencies)}/{num_events} latencies measured"
        
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]
        p99_latency = sorted(latencies)[int(0.99 * len(latencies))]
        max_latency = max(latencies)
        
        # Performance assertions
        assert avg_latency < 10.0, f"Average latency too high: {avg_latency:.3f}ms"
        assert p95_latency < 20.0, f"P95 latency too high: {p95_latency:.3f}ms"
        assert p99_latency < 50.0, f"P99 latency too high: {p99_latency:.3f}ms"
        
        print(f"\nLatency Benchmark Results:")
        print(f"  Events processed: {len(latencies)}")
        print(f"  Average latency: {avg_latency:.3f}ms")
        print(f"  Median latency: {median_latency:.3f}ms")
        print(f"  P95 latency: {p95_latency:.3f}ms")
        print(f"  P99 latency: {p99_latency:.3f}ms")
        print(f"  Max latency: {max_latency:.3f}ms")
        print(f"  Memory delta: {metrics['memory_delta']:.2f} MB")
    
    def test_concurrent_throughput(self):
        """Benchmark throughput with multiple concurrent producers."""
        num_producers = 8
        events_per_producer = 1000
        total_events = num_producers * events_per_producer
        
        processed_events = []
        process_lock = threading.Lock()
        
        def concurrent_handler(event: Event) -> None:
            """Thread-safe handler for concurrent test."""
            with process_lock:
                processed_events.append(event.data)
        
        # Register handler and start engine
        self.engine.register("concurrent_test", concurrent_handler)
        self.engine.start()
        
        # Start monitoring
        self.benchmark.start_monitoring()
        
        def producer(producer_id):
            """Event producer function."""
            for i in range(events_per_producer):
                event = Event("concurrent_test", f"p{producer_id}_e{i}")
                self.engine.put(event)
        
        # Start all producers
        start_time = time.time()
        threads = []
        for producer_id in range(num_producers):
            thread = threading.Thread(target=producer, args=(producer_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all producers to finish
        for thread in threads:
            thread.join()
        
        send_duration = time.time() - start_time
        
        # Wait for all events to be processed
        timeout = 20.0
        start_wait = time.time()
        while len(processed_events) < total_events and (time.time() - start_wait) < timeout:
            time.sleep(0.01)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Calculate metrics
        total_duration = metrics['duration']
        events_per_second = total_events / total_duration
        send_rate = total_events / send_duration
        
        # Verify all events processed
        assert len(processed_events) == total_events, f"Only {len(processed_events)}/{total_events} events processed"
        
        # Performance assertions
        assert events_per_second > 800, f"Concurrent throughput too low: {events_per_second:.2f} events/sec"
        
        print(f"\nConcurrent Throughput Benchmark Results:")
        print(f"  Producers: {num_producers}")
        print(f"  Events per producer: {events_per_producer}")
        print(f"  Total events: {total_events}")
        print(f"  Events/second: {events_per_second:.2f}")
        print(f"  Send rate: {send_rate:.2f} events/sec")
        print(f"  Memory delta: {metrics['memory_delta']:.2f} MB")
    
    def test_handler_execution_overhead(self):
        """Benchmark overhead of handler execution patterns."""
        num_events = 5000
        
        # Test different handler complexity levels
        handler_results = {}
        
        def create_handler(complexity_level):
            """Create handler with specified complexity."""
            if complexity_level == "simple":
                def handler(event: Event) -> None:
                    pass  # Minimal handler
                return handler
            elif complexity_level == "moderate":
                def handler(event: Event) -> None:
                    # Some basic processing
                    data = event.data
                    result = str(data).upper()
                    len(result)
                return handler
            elif complexity_level == "complex":
                def handler(event: Event) -> None:
                    # More complex processing
                    data = str(event.data)
                    results = []
                    for i in range(10):
                        results.append(data + str(i))
                    len(results)
                return handler
        
        for complexity in ["simple", "moderate", "complex"]:
            handler = create_handler(complexity)
            event_type = f"handler_test_{complexity}"
            
            # Register handler and start engine
            engine = EventEngine(0.1)
            engine.register(event_type, handler)
            engine.start()
            
            # Benchmark this handler
            self.benchmark.start_monitoring()
            
            # Send events
            for i in range(num_events):
                event = Event(event_type, f"event_{i}")
                engine.put(event)
            
            # Wait for processing
            time.sleep(2.0)
            
            # Stop monitoring
            metrics = self.benchmark.stop_monitoring()
            
            engine.stop()
            
            events_per_second = num_events / metrics['duration']
            handler_results[complexity] = {
                'events_per_second': events_per_second,
                'duration': metrics['duration'],
                'memory_delta': metrics['memory_delta']
            }
        
        # Verify performance degrades with complexity as expected
        # Use tolerance to handle system performance variations
        simple_eps = handler_results['simple']['events_per_second']
        moderate_eps = handler_results['moderate']['events_per_second']
        complex_eps = handler_results['complex']['events_per_second']
        
        # Allow for 5% tolerance in performance comparisons to handle system variations
        tolerance = 0.05
        assert (simple_eps > moderate_eps * (1 - tolerance)), \
            f"Simple ({simple_eps:.2f}) should be faster than moderate ({moderate_eps:.2f})"
        assert (moderate_eps > complex_eps * (1 - tolerance)), \
            f"Moderate ({moderate_eps:.2f}) should be faster than complex ({complex_eps:.2f})"
        
        print(f"\nHandler Execution Overhead Results:")
        for complexity, results in handler_results.items():
            print(f"  {complexity.capitalize()} handler:")
            print(f"    Events/second: {results['events_per_second']:.2f}")
            print(f"    Duration: {results['duration']:.3f}s")
            print(f"    Memory delta: {results['memory_delta']:.2f} MB")
    
    def test_timer_precision_under_load(self):
        """Benchmark timer precision under various load conditions."""
        timer_intervals = []
        timer_timestamps = []
        load_events_processed = 0
        
        def timer_handler(event: Event) -> None:
            """Handler for timer events."""
            if event.type == EVENT_TIMER:
                current_time = time.time()
                timer_timestamps.append(current_time)
                
                if len(timer_timestamps) > 1:
                    interval = current_time - timer_timestamps[-2]
                    timer_intervals.append(interval)
        
        def load_handler(event: Event) -> None:
            """Handler that creates processing load."""
            nonlocal load_events_processed
            # Simulate some processing work
            data = str(event.data)
            for i in range(100):  # Create some CPU load
                result = data + str(i)
            load_events_processed += 1
        
        # Use precise timer interval for testing
        self.engine = EventEngine(0.05)  # 50ms timer
        
        # Register handlers
        self.engine.register(EVENT_TIMER, timer_handler)
        self.engine.register("load_test", load_handler)
        
        self.engine.start()
        
        # Start monitoring
        self.benchmark.start_monitoring()
        
        # Generate load while monitoring timer precision
        def generate_load():
            for i in range(500):
                event = Event("load_test", f"load_event_{i}")
                self.engine.put(event)
                if i % 50 == 0:  # Periodic bursts
                    time.sleep(0.001)
        
        load_thread = threading.Thread(target=generate_load)
        load_thread.start()
        
        # Let it run for a measurable period
        time.sleep(2.0)
        
        load_thread.join()
        
        # Continue monitoring timer without load
        time.sleep(1.0)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Analyze timer precision
        assert len(timer_intervals) >= 10, "Not enough timer intervals captured"
        
        expected_interval = 0.05  # 50ms
        avg_interval = statistics.mean(timer_intervals)
        interval_stddev = statistics.stdev(timer_intervals)
        max_deviation = max(abs(interval - expected_interval) for interval in timer_intervals)
        
        # Timer should maintain reasonable precision under load
        assert abs(avg_interval - expected_interval) < 0.01, f"Timer drift too high: {avg_interval:.3f}s vs {expected_interval:.3f}s"
        assert interval_stddev < 0.02, f"Timer jitter too high: {interval_stddev:.3f}s"
        assert max_deviation < 0.05, f"Max timer deviation too high: {max_deviation:.3f}s"
        
        print(f"\nTimer Precision Under Load Results:")
        print(f"  Expected interval: {expected_interval:.3f}s")
        print(f"  Average interval: {avg_interval:.3f}s")
        print(f"  Standard deviation: {interval_stddev:.3f}s")
        print(f"  Max deviation: {max_deviation:.3f}s")
        print(f"  Load events processed: {load_events_processed}")
        print(f"  Memory delta: {metrics['memory_delta']:.2f} MB")
    
    def test_memory_usage_scaling(self):
        """Test memory usage scaling with event queue size."""
        queue_sizes = [100, 500, 1000, 5000, 10000]
        memory_usage = {}
        
        def minimal_handler(event: Event) -> None:
            """Minimal handler that doesn't process events."""
            pass
        
        for queue_size in queue_sizes:
            # Create fresh engine
            engine = EventEngine(1.0)  # Slow timer to avoid processing
            engine.register("memory_test", minimal_handler)
            
            # Start monitoring
            benchmark = PerformanceBenchmark()
            benchmark.start_monitoring()
            
            # Fill queue without starting engine (no processing)
            for i in range(queue_size):
                event = Event("memory_test", f"event_{i}" * 10)  # Larger event data
                engine.put(event)
            
            # Measure memory
            metrics = benchmark.stop_monitoring()
            memory_usage[queue_size] = metrics['memory_delta']
            
            # Clean up
            del engine
            gc.collect()
        
        # Verify memory scales reasonably with queue size
        assert memory_usage[10000] > memory_usage[1000], "Memory should increase with queue size"
        assert memory_usage[5000] > memory_usage[500], "Memory should scale with queue size"
        
        # Memory usage should be reasonable (not excessive)
        memory_per_event = memory_usage[10000] / 10000 * 1024 * 1024  # Bytes per event
        assert memory_per_event < 1000, f"Excessive memory per event: {memory_per_event:.2f} bytes"
        
        print(f"\nMemory Usage Scaling Results:")
        for queue_size, memory_delta in memory_usage.items():
            print(f"  Queue size {queue_size}: {memory_delta:.2f} MB")
        
        memory_per_1k_events = memory_usage[1000] / 1000 * 1000  # MB per 1K events
        print(f"  Memory per 1K events: {memory_per_1k_events:.3f} MB")


class TestEventEngineStressTest:
    """Stress tests for EventEngine under extreme conditions."""
    
    def setup_method(self):
        """Setup for stress tests."""
        self.engine = EventEngine(0.01)  # Very fast timer for stress
        self.benchmark = PerformanceBenchmark()
        
    def teardown_method(self):
        """Cleanup after stress tests."""
        if hasattr(self, 'engine') and self.engine._active:
            self.engine.stop()
    
    def test_high_frequency_event_stress(self):
        """Stress test with high-frequency event generation."""
        duration_seconds = 5.0
        target_rate = 5000  # 5K events per second
        
        processed_count = 0
        processing_times = deque(maxlen=1000)  # Keep last 1000 processing times
        
        def stress_handler(event: Event) -> None:
            """Handler that tracks processing under stress."""
            nonlocal processed_count
            processing_times.append(time.time())
            processed_count += 1
        
        # Register handler and start engine
        self.engine.register("stress_test", stress_handler)
        self.engine.start()
        
        # Start monitoring
        self.benchmark.start_monitoring()
        
        # Generate high-frequency events
        def event_generator():
            end_time = time.time() + duration_seconds
            event_count = 0
            
            while time.time() < end_time:
                event = Event("stress_test", f"stress_{event_count}")
                self.engine.put(event)
                event_count += 1
                
                # Control rate
                if event_count % 100 == 0:
                    time.sleep(0.02)  # Brief pause every 100 events
        
        generator_thread = threading.Thread(target=event_generator)
        generator_thread.start()
        generator_thread.join()
        
        # Allow processing to complete
        time.sleep(2.0)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Calculate stress test results
        actual_rate = processed_count / duration_seconds
        
        # Verify system handled high load
        assert processed_count > target_rate * duration_seconds * 0.7, \
            f"Processed too few events under stress: {processed_count}"
        
        # Memory usage should remain reasonable
        assert metrics['memory_delta'] < 200, \
            f"Excessive memory usage under stress: {metrics['memory_delta']:.2f} MB"
        
        print(f"\nHigh Frequency Stress Test Results:")
        print(f"  Duration: {duration_seconds}s")
        print(f"  Events processed: {processed_count}")
        print(f"  Actual rate: {actual_rate:.2f} events/sec")
        print(f"  Target rate: {target_rate} events/sec")
        print(f"  Efficiency: {actual_rate/target_rate*100:.1f}%")
        print(f"  Memory delta: {metrics['memory_delta']:.2f} MB")
    
    def test_sustained_load(self):
        """Test sustained load over extended period."""
        duration_minutes = 1.0  # 1 minute sustained test
        duration_seconds = duration_minutes * 60
        
        processed_events = []
        start_memory = None
        memory_samples = []
        
        def sustained_handler(event: Event) -> None:
            """Handler for sustained load test."""
            processed_events.append(len(processed_events))
            
            # Sample memory usage periodically (simplified)
            if len(processed_events) % 1000 == 0:
                try:
                    current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
                    memory_samples.append(current_memory)
                except:
                    pass
        
        # Register handler and start engine
        self.engine.register("sustained_test", sustained_handler)
        self.engine.start()
        
        # Start monitoring
        self.benchmark.start_monitoring()
        try:
            start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except:
            start_memory = 0
        
        # Generate sustained load
        def sustained_generator():
            end_time = time.time() + duration_seconds
            event_count = 0
            
            while time.time() < end_time:
                # Send events in batches
                for i in range(50):
                    event = Event("sustained_test", f"sustained_{event_count}")
                    self.engine.put(event)
                    event_count += 1
                
                # Brief pause between batches
                time.sleep(0.1)
        
        generator_thread = threading.Thread(target=sustained_generator)
        generator_thread.start()
        generator_thread.join()
        
        # Allow final processing
        time.sleep(5.0)
        
        # Stop monitoring
        metrics = self.benchmark.stop_monitoring()
        
        self.engine.stop()
        
        # Analyze sustained performance
        events_per_second = len(processed_events) / duration_seconds
        
        # Check for memory stability (no significant growth)
        if len(memory_samples) > 2:
            memory_growth = memory_samples[-1] - memory_samples[0]
            memory_growth_rate = memory_growth / duration_minutes  # MB per minute
        else:
            memory_growth = 0
            memory_growth_rate = 0
        
        # Performance assertions
        assert len(processed_events) > 100, "Not enough events processed in sustained test"
        assert events_per_second > 10, f"Sustained throughput too low: {events_per_second:.2f} events/sec"
        assert memory_growth_rate < 50, f"Memory growth rate too high: {memory_growth_rate:.2f} MB/min"
        
        print(f"\nSustained Load Test Results:")
        print(f"  Duration: {duration_minutes:.1f} minutes")
        print(f"  Events processed: {len(processed_events)}")
        print(f"  Events/second: {events_per_second:.2f}")
        print(f"  Memory growth: {memory_growth:.2f} MB")
        print(f"  Memory growth rate: {memory_growth_rate:.2f} MB/min")
        print(f"  Final memory delta: {metrics['memory_delta']:.2f} MB")
        print(f"  Duration: {metrics['duration']:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])