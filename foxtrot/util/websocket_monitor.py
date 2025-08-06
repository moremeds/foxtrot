"""
WebSocket monitoring and metrics collection.

This module provides utilities for monitoring WebSocket performance,
connection health, and collecting metrics for alerting.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Deque
import statistics

from foxtrot.util.logger import get_component_logger


@dataclass
class WebSocketMetrics:
    """Container for WebSocket performance metrics."""
    
    # Connection metrics
    connection_state: str = "disconnected"
    last_connect_time: float = 0.0
    last_disconnect_time: float = 0.0
    total_connections: int = 0
    total_disconnections: int = 0
    
    # Latency metrics (rolling window)
    latencies: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    
    # Throughput metrics
    messages_received: int = 0
    bytes_received: int = 0
    last_message_time: float = 0.0
    
    # Error metrics
    total_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    last_error_time: float = 0.0
    
    # Reconnection metrics
    reconnection_attempts: int = 0
    successful_reconnections: int = 0
    failed_reconnections: int = 0
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics."""
        if not self.latencies:
            return {
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        latency_list = list(self.latencies)
        return {
            "mean": statistics.mean(latency_list),
            "median": statistics.median(latency_list),
            "min": min(latency_list),
            "max": max(latency_list),
            "p95": statistics.quantiles(latency_list, n=20)[18] if len(latency_list) > 20 else max(latency_list),
            "p99": statistics.quantiles(latency_list, n=100)[98] if len(latency_list) > 100 else max(latency_list)
        }
        
    def get_uptime(self) -> float:
        """Get connection uptime in seconds."""
        if self.connection_state != "connected" or self.last_connect_time == 0:
            return 0.0
        return time.time() - self.last_connect_time
        
    def get_error_rate(self, window_seconds: float = 60.0) -> float:
        """Get error rate per minute."""
        if self.total_errors == 0:
            return 0.0
            
        current_time = time.time()
        if self.last_error_time == 0:
            return 0.0
            
        time_window = min(window_seconds, current_time - self.last_error_time)
        if time_window <= 0:
            return 0.0
            
        return (self.total_errors / time_window) * 60.0


class WebSocketMonitor:
    """
    Monitor WebSocket connections and collect performance metrics.
    
    Features:
    - Real-time latency tracking
    - Connection health monitoring
    - Error rate calculation
    - Alert threshold checking
    """
    
    def __init__(self, adapter_name: str):
        """Initialize the monitor."""
        self.adapter_name = adapter_name
        self.logger = get_component_logger(f"{adapter_name}Monitor")
        
        # Metrics storage
        self.metrics: Dict[str, WebSocketMetrics] = {}
        
        # Alert thresholds
        self.alert_thresholds = {
            "latency_warning": 100.0,      # ms
            "latency_critical": 200.0,     # ms
            "error_rate_warning": 5.0,     # errors per minute
            "error_rate_critical": 10.0,   # errors per minute
            "uptime_minimum": 300.0,       # 5 minutes
        }
        
        # Alert callbacks
        self.alert_callbacks: List[callable] = []
        
    def get_or_create_metrics(self, symbol: str) -> WebSocketMetrics:
        """Get or create metrics for a symbol."""
        if symbol not in self.metrics:
            self.metrics[symbol] = WebSocketMetrics()
        return self.metrics[symbol]
        
    def record_connection(self, symbol: str) -> None:
        """Record successful connection."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.connection_state = "connected"
        metrics.last_connect_time = time.time()
        metrics.total_connections += 1
        
    def record_disconnection(self, symbol: str) -> None:
        """Record disconnection."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.connection_state = "disconnected"
        metrics.last_disconnect_time = time.time()
        metrics.total_disconnections += 1
        
    def record_message(self, symbol: str, latency_ms: float, message_size: int = 0) -> None:
        """Record received message with latency."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.messages_received += 1
        metrics.bytes_received += message_size
        metrics.last_message_time = time.time()
        metrics.latencies.append(latency_ms)
        
        # Check latency alerts
        if latency_ms > self.alert_thresholds["latency_critical"]:
            self._trigger_alert("latency_critical", symbol, latency_ms)
        elif latency_ms > self.alert_thresholds["latency_warning"]:
            self._trigger_alert("latency_warning", symbol, latency_ms)
            
    def record_error(self, symbol: str, error_type: str) -> None:
        """Record error occurrence."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.total_errors += 1
        metrics.last_error_time = time.time()
        
        if error_type not in metrics.errors_by_type:
            metrics.errors_by_type[error_type] = 0
        metrics.errors_by_type[error_type] += 1
        
        # Check error rate
        error_rate = metrics.get_error_rate()
        if error_rate > self.alert_thresholds["error_rate_critical"]:
            self._trigger_alert("error_rate_critical", symbol, error_rate)
        elif error_rate > self.alert_thresholds["error_rate_warning"]:
            self._trigger_alert("error_rate_warning", symbol, error_rate)
            
    def record_reconnection_attempt(self, symbol: str) -> None:
        """Record reconnection attempt."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.reconnection_attempts += 1
        
    def record_reconnection_success(self, symbol: str) -> None:
        """Record successful reconnection."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.successful_reconnections += 1
        metrics.connection_state = "connected"
        metrics.last_connect_time = time.time()
        
    def record_reconnection_failure(self, symbol: str) -> None:
        """Record failed reconnection."""
        metrics = self.get_or_create_metrics(symbol)
        metrics.failed_reconnections += 1
        
    def get_symbol_metrics(self, symbol: str) -> Optional[WebSocketMetrics]:
        """Get metrics for a specific symbol."""
        return self.metrics.get(symbol)
        
    def get_all_metrics(self) -> Dict[str, WebSocketMetrics]:
        """Get all collected metrics."""
        return self.metrics.copy()
        
    def get_summary(self) -> Dict[str, any]:
        """Get summary of all monitored connections."""
        total_connected = sum(1 for m in self.metrics.values() if m.connection_state == "connected")
        total_symbols = len(self.metrics)
        
        all_latencies = []
        total_messages = 0
        total_errors = 0
        
        for metrics in self.metrics.values():
            all_latencies.extend(list(metrics.latencies))
            total_messages += metrics.messages_received
            total_errors += metrics.total_errors
            
        latency_stats = {}
        if all_latencies:
            latency_stats = {
                "mean": statistics.mean(all_latencies),
                "median": statistics.median(all_latencies),
                "min": min(all_latencies),
                "max": max(all_latencies),
            }
            
        return {
            "timestamp": datetime.now().isoformat(),
            "adapter": self.adapter_name,
            "connections": {
                "total": total_symbols,
                "connected": total_connected,
                "disconnected": total_symbols - total_connected
            },
            "latency": latency_stats,
            "throughput": {
                "total_messages": total_messages,
                "total_errors": total_errors,
                "error_rate": (total_errors / total_messages * 100) if total_messages > 0 else 0
            }
        }
        
    def add_alert_callback(self, callback: callable) -> None:
        """Add callback for alerts."""
        self.alert_callbacks.append(callback)
        
    def _trigger_alert(self, alert_type: str, symbol: str, value: float) -> None:
        """Trigger alert callbacks."""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "adapter": self.adapter_name,
            "alert_type": alert_type,
            "symbol": symbol,
            "value": value,
            "threshold": self.alert_thresholds.get(alert_type)
        }
        
        self.logger.warning(f"Alert triggered: {alert_type} for {symbol} - value: {value}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
                
    def reset_metrics(self, symbol: Optional[str] = None) -> None:
        """Reset metrics for a symbol or all symbols."""
        if symbol:
            if symbol in self.metrics:
                self.metrics[symbol] = WebSocketMetrics()
        else:
            self.metrics.clear()