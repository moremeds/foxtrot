# Foxtrot Performance Monitoring & Observability Plan

**Document Version:** 1.0  
**Date:** August 6, 2025

## Overview

This document outlines a comprehensive performance monitoring and observability system inspired by Nautilus Trader's structured logging and metrics collection, adapted for Foxtrot's Python-native environment. The plan transforms Foxtrot's basic logging into a production-grade monitoring framework.

---

## Current State Assessment

**Existing Monitoring:**
- Basic logging with `foxtrot/util/logger.py`
- Simple console output
- No structured metrics collection
- Limited performance visibility
- Manual performance investigation

**Key Gaps:**
- No structured logging format
- Missing performance metrics collection
- Lack of real-time monitoring dashboards
- No automated performance alerts
- Limited operational visibility

---

## Structured Logging Enhancement

### Enhanced Logging Framework

Building upon existing `logger.py` with structured data support:

```python
# foxtrot/util/structured_logger.py
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from threading import local

class StructuredLogger:
    """Enhanced logger with structured data support and context management"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Add structured formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)
        
        # Thread-local context storage
        self._local = local()
    
    @property
    def context(self) -> Dict[str, Any]:
        """Get current thread's context"""
        if not hasattr(self._local, 'context'):
            self._local.context = {}
        return self._local.context
    
    def log(
        self, 
        level: int, 
        message: str, 
        **kwargs
    ):
        """Log with structured data"""
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": logging.getLevelName(level),
            "logger": self.logger.name,
            "message": message,
            "context": {**self.context, **kwargs}
        }
        
        self.logger.log(level, json.dumps(record, default=str))
    
    def info(self, message: str, **kwargs):
        """Log info with structured context"""
        self.log(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error with structured context"""
        self.log(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning with structured context"""
        self.log(logging.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug with structured context"""
        self.log(logging.DEBUG, message, **kwargs)
    
    @contextmanager
    def context_manager(self, **context_data):
        """Add context data for nested operations"""
        old_context = self.context.copy()
        self.context.update(context_data)
        try:
            yield
        finally:
            self.context.clear()
            self.context.update(old_context)
    
    def timer(self, operation_name: str, **context):
        """Context manager for timing operations"""
        return LoggerTimer(self, operation_name, context)

class LoggerTimer:
    """Context manager for timing operations with structured logging"""
    
    def __init__(self, logger: StructuredLogger, operation_name: str, context: Dict[str, Any]):
        self.logger = logger
        self.operation_name = operation_name
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.debug(
            f"Operation started: {self.operation_name}",
            operation=self.operation_name,
            event="start",
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            
            if exc_type:
                self.logger.error(
                    f"Operation failed: {self.operation_name}",
                    operation=self.operation_name,
                    event="error",
                    duration_ms=duration_ms,
                    exception=str(exc_val),
                    **self.context
                )
            else:
                self.logger.info(
                    f"Operation completed: {self.operation_name}",
                    operation=self.operation_name,
                    event="complete",
                    duration_ms=duration_ms,
                    **self.context
                )

class StructuredFormatter(logging.Formatter):
    """Formatter for structured log output"""
    
    def format(self, record):
        # If record.msg is already JSON, return as-is
        try:
            json.loads(record.msg)
            return record.msg
        except (json.JSONDecodeError, TypeError):
            # Fall back to standard formatting for non-structured logs
            return super().format(record)

# Usage examples in adapters:
class BinanceAdapter(BaseAdapter):
    
    def __init__(self):
        super().__init__()
        self.logger = StructuredLogger("foxtrot.adapter.binance")
    
    def connect(self):
        with self.logger.context_manager(
            adapter="binance",
            operation="connect"
        ):
            with self.logger.timer("connection_attempt"):
                try:
                    # Connection logic
                    self._perform_connection()
                    self.logger.info(
                        "Adapter connected successfully",
                        status="connected",
                        attempt_number=1
                    )
                except Exception as e:
                    self.logger.error(
                        "Connection failed",
                        error=str(e),
                        status="failed"
                    )
                    raise
    
    def submit_order(self, order):
        with self.logger.context_manager(
            adapter="binance",
            operation="submit_order",
            order_id=order.vt_orderid,
            symbol=order.symbol
        ):
            with self.logger.timer("order_submission", order_type=order.type.value):
                try:
                    result = self._submit_order_impl(order)
                    self.logger.info(
                        "Order submitted successfully",
                        venue_order_id=result.venue_order_id,
                        quantity=order.volume,
                        price=order.price
                    )
                    return result
                except Exception as e:
                    self.logger.error(
                        "Order submission failed",
                        error=str(e),
                        quantity=order.volume,
                        price=order.price
                    )
                    raise
```

---

## Metrics Collection System

### High-Performance Metrics Framework

```python
# foxtrot/util/metrics.py
import time
import threading
from typing import Dict, Optional, List, Callable, Any
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

class MetricType(Enum):
    COUNTER = "counter"     # Monotonically increasing values
    GAUGE = "gauge"        # Point-in-time values
    HISTOGRAM = "histogram" # Distribution of values
    TIMER = "timer"        # Duration measurements

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class HistogramData:
    """Histogram metric aggregation"""
    count: int = 0
    sum: float = 0.0
    min: float = float('inf')
    max: float = float('-inf')
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_value(self, value: float):
        self.count += 1
        self.sum += value
        self.min = min(self.min, value)
        self.max = max(self.max, value)
        self.values.append(value)
    
    def get_percentiles(self, percentiles: List[float] = None) -> Dict[str, float]:
        """Calculate percentiles (50th, 95th, 99th by default)"""
        if not self.values:
            return {}
        
        if percentiles is None:
            percentiles = [50, 95, 99]
        
        sorted_values = sorted(self.values)
        result = {}
        
        for p in percentiles:
            index = int(len(sorted_values) * p / 100)
            index = min(index, len(sorted_values) - 1)
            result[f"p{p}"] = sorted_values[index]
        
        return result

class MetricsCollector:
    """Thread-safe, high-performance metrics collection system"""
    
    def __init__(self, max_metrics_per_name: int = 10000):
        self.max_metrics_per_name = max_metrics_per_name
        
        # Metric storage by type
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, Metric] = {}
        self._histograms: Dict[str, HistogramData] = defaultdict(HistogramData)
        self._metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_metrics_per_name)
        )
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Listeners for real-time monitoring
        self._listeners: List[Callable[[Metric], None]] = []
    
    def counter(self, name: str, value: float = 1.0, **tags) -> None:
        """Record counter metric (monotonically increasing)"""
        metric = self._create_metric(name, MetricType.COUNTER, value, tags)
        
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            self._counters[tag_key] += value
            self._record_metric(metric)
    
    def gauge(self, name: str, value: float, **tags) -> None:
        """Record gauge metric (point-in-time value)"""
        metric = self._create_metric(name, MetricType.GAUGE, value, tags)
        
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            self._gauges[tag_key] = metric
            self._record_metric(metric)
    
    def histogram(self, name: str, value: float, **tags) -> None:
        """Record histogram metric (value distribution)"""
        metric = self._create_metric(name, MetricType.HISTOGRAM, value, tags)
        
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            self._histograms[tag_key].add_value(value)
            self._record_metric(metric)
    
    def timer(self, name: str, **tags) -> 'MetricsTimer':
        """Context manager for timing operations"""
        return MetricsTimer(self, name, tags)
    
    def add_listener(self, listener: Callable[[Metric], None]) -> None:
        """Add listener for real-time metric updates"""
        with self._lock:
            self._listeners.append(listener)
    
    def get_counter_value(self, name: str, **tags) -> float:
        """Get current counter value"""
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            return self._counters.get(tag_key, 0.0)
    
    def get_gauge_value(self, name: str, **tags) -> Optional[float]:
        """Get current gauge value"""
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            metric = self._gauges.get(tag_key)
            return metric.value if metric else None
    
    def get_histogram_stats(self, name: str, **tags) -> Dict[str, Any]:
        """Get histogram statistics"""
        with self._lock:
            tag_key = self._generate_tag_key(name, tags)
            histogram = self._histograms.get(tag_key)
            
            if not histogram or histogram.count == 0:
                return {}
            
            stats = {
                "count": histogram.count,
                "sum": histogram.sum,
                "min": histogram.min,
                "max": histogram.max,
                "avg": histogram.sum / histogram.count if histogram.count > 0 else 0
            }
            
            # Add percentiles
            stats.update(histogram.get_percentiles())
            
            return stats
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "gauges": {k: v.value for k, v in self._gauges.items()},
                "histograms": {
                    k: self.get_histogram_stats_from_data(v) 
                    for k, v in self._histograms.items()
                },
                "timestamp": time.time()
            }
            
            return summary
    
    def get_histogram_stats_from_data(self, histogram: HistogramData) -> Dict[str, Any]:
        """Helper to get stats from histogram data"""
        if histogram.count == 0:
            return {}
        
        return {
            "count": histogram.count,
            "sum": histogram.sum,
            "min": histogram.min,
            "max": histogram.max,
            "avg": histogram.sum / histogram.count,
            **histogram.get_percentiles()
        }
    
    def _create_metric(self, name: str, metric_type: MetricType, value: float, tags: Dict[str, str]) -> Metric:
        """Create metric object"""
        return Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=time.time(),
            tags=tags
        )
    
    def _generate_tag_key(self, name: str, tags: Dict[str, str]) -> str:
        """Generate unique key for metric with tags"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def _record_metric(self, metric: Metric) -> None:
        """Record metric and notify listeners"""
        self._metrics_history[metric.name].append(metric)
        
        # Notify listeners
        for listener in self._listeners:
            try:
                listener(metric)
            except Exception:
                # Don't let listener exceptions break metrics collection
                pass

class MetricsTimer:
    """High-precision context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.perf_counter() - self.start_time) * 1000
            
            # Record as histogram for statistical analysis
            self.collector.histogram(f"{self.name}.duration_ms", duration_ms, **self.tags)
            
            # Also record success/failure
            status = "error" if exc_type else "success"
            self.collector.counter(f"{self.name}.calls", tags={**self.tags, "status": status})

# Global metrics collector
metrics = MetricsCollector()

# Usage examples throughout the system:
class EventEngine:
    
    def put(self, event):
        with metrics.timer("event_engine.put", event_type=event.type):
            # Record event throughput
            metrics.counter("events.processed", event_type=event.type)
            
            # Record queue size
            metrics.gauge("event_engine.queue_size", self._queue.qsize())
            
            # Actual event processing
            self._queue.put(event)

class BinanceAdapter(BaseAdapter):
    
    def submit_order(self, order):
        # Record order attempts
        metrics.counter("adapter.orders.attempted", adapter="binance", symbol=order.symbol)
        
        with metrics.timer("adapter.order_submission", adapter="binance"):
            try:
                result = self._submit_order_impl(order)
                
                # Record successful orders
                metrics.counter("adapter.orders.successful", adapter="binance", symbol=order.symbol)
                
                # Record order size distribution
                metrics.histogram("adapter.order_size", order.volume, adapter="binance")
                
                return result
                
            except Exception as e:
                # Record failures
                metrics.counter("adapter.orders.failed", adapter="binance", error=type(e).__name__)
                raise
    
    def on_tick(self, tick):
        # Record market data metrics
        metrics.counter("market_data.ticks_received", adapter="binance", symbol=tick.symbol)
        metrics.gauge("market_data.latest_price", tick.last_price, symbol=tick.symbol)
        
        # Record spread
        if tick.bid_price_1 and tick.ask_price_1:
            spread = tick.ask_price_1 - tick.bid_price_1
            metrics.histogram("market_data.spread", spread, symbol=tick.symbol)
```

---

## Real-Time Monitoring Dashboard

### Metrics Export and Visualization

```python
# foxtrot/util/metrics_exporter.py
import json
import time
from typing import Dict, Any, List
from threading import Thread, Event
from http.server import HTTPServer, BaseHTTPRequestHandler
from foxtrot.util.metrics import metrics

class MetricsHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for metrics endpoint"""
    
    def do_GET(self):
        """Handle GET requests for metrics"""
        if self.path == "/metrics":
            self.send_metrics_response()
        elif self.path == "/health":
            self.send_health_response()
        else:
            self.send_error(404, "Not Found")
    
    def send_metrics_response(self):
        """Send metrics in JSON format"""
        try:
            metrics_data = metrics.get_metrics_summary()
            response = json.dumps(metrics_data, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode())
        except Exception as e:
            self.send_error(500, f"Internal Server Error: {str(e)}")
    
    def send_health_response(self):
        """Send health check response"""
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - getattr(self.server, 'start_time', time.time())
        }
        
        response = json.dumps(health_data)
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

class MetricsServer:
    """HTTP server for exposing metrics"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None
        self.thread = None
        self.stop_event = Event()
    
    def start(self):
        """Start metrics server in background thread"""
        self.server = HTTPServer(('localhost', self.port), MetricsHTTPHandler)
        self.server.start_time = time.time()
        
        self.thread = Thread(target=self._run_server, daemon=True)
        self.thread.start()
        
        print(f"Metrics server started on http://localhost:{self.port}/metrics")
    
    def stop(self):
        """Stop metrics server"""
        if self.server:
            self.server.shutdown()
            self.stop_event.set()
        
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run_server(self):
        """Run server loop"""
        try:
            self.server.serve_forever()
        except Exception as e:
            print(f"Metrics server error: {e}")

# Simple dashboard HTML (could be served from /dashboard endpoint)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Foxtrot Metrics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric-group { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .metric-title { font-weight: bold; margin-bottom: 10px; }
        .metric-value { font-size: 1.2em; color: #2ecc71; }
        .metric-chart { height: 300px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Foxtrot Trading Platform - Metrics Dashboard</h1>
    
    <div id="metrics-container">
        <div class="metric-group">
            <div class="metric-title">System Health</div>
            <div id="health-status">Loading...</div>
        </div>
        
        <div class="metric-group">
            <div class="metric-title">Event Processing</div>
            <div id="events-chart" class="metric-chart"></div>
        </div>
        
        <div class="metric-group">
            <div class="metric-title">Order Processing</div>
            <div id="orders-chart" class="metric-chart"></div>
        </div>
        
        <div class="metric-group">
            <div class="metric-title">Performance Metrics</div>
            <div id="performance-chart" class="metric-chart"></div>
        </div>
    </div>

    <script>
        // Auto-refresh metrics every 5 seconds
        setInterval(updateDashboard, 5000);
        updateDashboard(); // Initial load
        
        async function updateDashboard() {
            try {
                const response = await fetch('/metrics');
                const data = await response.json();
                
                updateHealthStatus(data);
                updateEventChart(data);
                updateOrderChart(data);
                updatePerformanceChart(data);
                
            } catch (error) {
                console.error('Failed to update dashboard:', error);
                document.getElementById('health-status').innerHTML = 
                    '<span style="color: red;">Error loading metrics</span>';
            }
        }
        
        function updateHealthStatus(data) {
            const container = document.getElementById('health-status');
            const uptime = Math.round((Date.now() / 1000) - data.timestamp + (data.uptime || 0));
            container.innerHTML = `
                <div>Status: <span style="color: green;">Healthy</span></div>
                <div>Uptime: ${uptime} seconds</div>
                <div>Last Update: ${new Date().toLocaleTimeString()}</div>
            `;
        }
        
        // Additional chart update functions...
    </script>
</body>
</html>
"""

# Integration with MainEngine
class MainEngine:
    
    def __init__(self, event_engine):
        super().__init__(event_engine)
        
        # Start metrics collection
        self.metrics_server = MetricsServer(port=8080)
        
        # Add metrics listeners for real-time monitoring
        metrics.add_listener(self._on_metric_update)
    
    def init_engines(self):
        """Enhanced initialization with metrics"""
        with metrics.timer("main_engine.initialization"):
            super().init_engines()
            
            # Start metrics server
            self.metrics_server.start()
            
            # Record initialization metrics
            metrics.counter("main_engine.initialized")
            metrics.gauge("engines.count", len(self.engines))
    
    def _on_metric_update(self, metric):
        """Handle real-time metric updates"""
        # Could trigger alerts based on metric values
        if metric.name == "adapter.orders.failed" and metric.value > 10:
            self.write_log("High order failure rate detected", level=logging.WARNING)
        
        # Could trigger circuit breakers
        if "latency" in metric.name and metric.value > 1000:  # 1 second
            self.write_log(f"High latency detected: {metric.name} = {metric.value}ms", 
                          level=logging.WARNING)
```

---

## Performance Alerting System

### Automated Performance Monitoring

```python
# foxtrot/util/alerting.py
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import time
from foxtrot.util.metrics import Metric, metrics
from foxtrot.util.structured_logger import StructuredLogger

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AlertRule:
    """Performance alert rule definition"""
    name: str
    metric_name: str
    condition: Callable[[float], bool]
    level: AlertLevel
    message_template: str
    cooldown_seconds: float = 300  # 5 minutes default cooldown
    
    # State tracking
    last_triggered: Optional[float] = None
    triggered_count: int = 0

class PerformanceAlertManager:
    """Manages performance-based alerting"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.logger = StructuredLogger("performance_alerts")
        
        # Register default performance rules
        self._setup_default_rules()
        
        # Register as metrics listener
        metrics.add_listener(self._check_metric_alerts)
    
    def _setup_default_rules(self):
        """Setup default performance alert rules"""
        
        # High latency alerts
        self.add_rule(AlertRule(
            name="high_order_latency",
            metric_name="adapter.order_submission.duration_ms",
            condition=lambda value: value > 1000,  # > 1 second
            level=AlertLevel.WARNING,
            message_template="High order submission latency: {value:.2f}ms"
        ))
        
        self.add_rule(AlertRule(
            name="critical_order_latency", 
            metric_name="adapter.order_submission.duration_ms",
            condition=lambda value: value > 5000,  # > 5 seconds
            level=AlertLevel.CRITICAL,
            message_template="Critical order submission latency: {value:.2f}ms"
        ))
        
        # High error rates
        self.add_rule(AlertRule(
            name="high_order_failure_rate",
            metric_name="adapter.orders.failed",
            condition=self._high_failure_rate_condition,
            level=AlertLevel.ERROR,
            message_template="High order failure rate detected"
        ))
        
        # Memory usage alerts
        self.add_rule(AlertRule(
            name="high_memory_usage",
            metric_name="system.memory_usage_mb",
            condition=lambda value: value > 500,  # > 500MB
            level=AlertLevel.WARNING,
            message_template="High memory usage: {value:.2f}MB"
        ))
        
        # Queue size alerts
        self.add_rule(AlertRule(
            name="large_event_queue",
            metric_name="event_engine.queue_size",
            condition=lambda value: value > 1000,
            level=AlertLevel.WARNING,
            message_template="Large event queue size: {value} events"
        ))
    
    def add_rule(self, rule: AlertRule):
        """Add custom alert rule"""
        self.rules.append(rule)
        self.logger.info(
            "Performance alert rule added",
            rule_name=rule.name,
            metric=rule.metric_name,
            level=rule.level.value
        )
    
    def _check_metric_alerts(self, metric: Metric):
        """Check metric against all alert rules"""
        for rule in self.rules:
            if rule.metric_name == metric.name or rule.metric_name in metric.name:
                self._evaluate_rule(rule, metric)
    
    def _evaluate_rule(self, rule: AlertRule, metric: Metric):
        """Evaluate alert rule against metric"""
        current_time = time.time()
        
        # Check cooldown period
        if rule.last_triggered and (current_time - rule.last_triggered) < rule.cooldown_seconds:
            return
        
        # Evaluate condition
        try:
            if rule.condition(metric.value):
                self._trigger_alert(rule, metric, current_time)
        except Exception as e:
            self.logger.error(
                "Alert rule evaluation failed",
                rule_name=rule.name,
                error=str(e)
            )
    
    def _trigger_alert(self, rule: AlertRule, metric: Metric, current_time: float):
        """Trigger alert for rule violation"""
        rule.last_triggered = current_time
        rule.triggered_count += 1
        
        # Format message
        message = rule.message_template.format(
            value=metric.value,
            metric=metric.name,
            **metric.tags
        )
        
        # Log alert based on level
        if rule.level == AlertLevel.CRITICAL:
            self.logger.error(
                f"CRITICAL ALERT: {message}",
                alert_rule=rule.name,
                metric_name=metric.name,
                metric_value=metric.value,
                trigger_count=rule.triggered_count,
                **metric.tags
            )
        elif rule.level == AlertLevel.ERROR:
            self.logger.error(
                f"ERROR ALERT: {message}",
                alert_rule=rule.name,
                metric_name=metric.name,
                metric_value=metric.value,
                **metric.tags
            )
        elif rule.level == AlertLevel.WARNING:
            self.logger.warning(
                f"WARNING ALERT: {message}",
                alert_rule=rule.name,
                metric_name=metric.name,
                metric_value=metric.value,
                **metric.tags
            )
        else:
            self.logger.info(
                f"INFO ALERT: {message}",
                alert_rule=rule.name,
                metric_name=metric.name,
                metric_value=metric.value,
                **metric.tags
            )
    
    def _high_failure_rate_condition(self, current_failures: float) -> bool:
        """Complex condition for failure rate analysis"""
        # Get recent success count
        success_count = metrics.get_counter_value("adapter.orders.successful")
        total_orders = success_count + current_failures
        
        if total_orders < 10:  # Not enough data
            return False
        
        failure_rate = current_failures / total_orders
        return failure_rate > 0.1  # > 10% failure rate

# Global alert manager
alert_manager = PerformanceAlertManager()
```

---

## Success Metrics

### Performance Monitoring Quality Indicators
- **Metrics Collection Coverage**: 95% of critical operations instrumented
- **Dashboard Response Time**: <2 seconds for metrics endpoint
- **Alert Accuracy**: >90% of alerts actionable, <5% false positives
- **Performance Visibility**: 100% of system bottlenecks identifiable through metrics

### Operational Benefits
- **Mean Time to Detection**: <1 minute for performance issues
- **Troubleshooting Efficiency**: 50% reduction in investigation time
- **Proactive Issue Prevention**: 80% of performance issues caught before user impact
- **System Understanding**: Comprehensive operational visibility for optimization

This comprehensive performance monitoring system transforms Foxtrot's observability from basic logging to production-grade monitoring, enabling proactive performance management while maintaining Python simplicity.