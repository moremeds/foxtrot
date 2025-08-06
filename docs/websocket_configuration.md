# WebSocket Configuration Guide

This guide explains how to configure and use WebSocket streaming for the Foxtrot trading platform.

## Overview

WebSocket streaming provides real-time market data with significantly lower latency compared to HTTP polling:
- **HTTP Polling**: ~100-200ms latency, 1 update/second
- **WebSocket Streaming**: ~30-50ms latency, 10+ updates/second

## Configuration

WebSocket settings are configured in `vt_setting.json`. Here's a complete configuration example:

```json
{
  // Global WebSocket enable/disable
  "websocket.enabled": true,
  
  // Per-adapter settings
  "websocket.binance.enabled": true,
  "websocket.binance.symbols": [],  // Empty = all symbols, or ["BTCUSDT", "ETHUSDT"]
  
  // Reconnection settings
  "websocket.reconnect.max_attempts": 50,
  "websocket.reconnect.base_delay": 1.0,
  "websocket.reconnect.max_delay": 60.0,
  
  // Connection health monitoring
  "websocket.heartbeat.interval": 30.0,
  
  // Circuit breaker (automatic HTTP fallback)
  "websocket.circuit_breaker.failure_threshold": 5,
  "websocket.circuit_breaker.recovery_timeout": 60.0
}
```

## Feature Flags

### Global Enable/Disable
- `websocket.enabled`: Master switch for all WebSocket functionality
- Default: `false` (disabled for backward compatibility)

### Per-Adapter Control
- `websocket.binance.enabled`: Enable WebSocket for Binance adapter
- Default: `true` (enabled when global WebSocket is on)

### Symbol Filtering
- `websocket.binance.symbols`: List of symbols to use WebSocket for
- Empty list `[]` means all symbols use WebSocket
- Example: `["BTCUSDT", "ETHUSDT"]` - only these symbols use WebSocket

## Reconnection Settings

### Exponential Backoff
- `websocket.reconnect.base_delay`: Initial delay between reconnection attempts (seconds)
- `websocket.reconnect.max_delay`: Maximum delay between attempts (seconds)
- `websocket.reconnect.max_attempts`: Maximum number of reconnection attempts

### Example Reconnection Timeline
1. 1st attempt: 1 second delay
2. 2nd attempt: 2 seconds delay
3. 3rd attempt: 4 seconds delay
4. 4th attempt: 8 seconds delay
5. 5th attempt: 16 seconds delay
6. 6th attempt: 32 seconds delay
7. 7th+ attempts: 60 seconds delay (max)

## Circuit Breaker

The circuit breaker pattern provides automatic fallback to HTTP polling when WebSocket encounters persistent errors.

### Settings
- `websocket.circuit_breaker.failure_threshold`: Number of failures before triggering fallback
- `websocket.circuit_breaker.recovery_timeout`: Time to wait before attempting WebSocket again (seconds)

### States
1. **CLOSED**: Normal operation, WebSocket active
2. **OPEN**: Too many failures, using HTTP fallback
3. **HALF_OPEN**: Testing if WebSocket has recovered

## Rollback Procedures

### Quick Disable (No Code Changes)
1. Edit `vt_setting.json`:
   ```json
   {
     "websocket.enabled": false
   }
   ```
2. Restart the application

### Per-Adapter Disable
1. Edit `vt_setting.json`:
   ```json
   {
     "websocket.enabled": true,
     "websocket.binance.enabled": false
   }
   ```
2. Restart the application

### Per-Symbol Fallback
1. If specific symbols have issues, limit WebSocket to working symbols:
   ```json
   {
     "websocket.binance.symbols": ["BTCUSDT", "ETHUSDT"]
   }
   ```
2. Restart the application

## Monitoring

### Log Messages
WebSocket operations are logged with the adapter name:
- `BinanceAdapter: WebSocket connection established`
- `BinanceAdapterWebSocket: Reconnecting...`
- `BinanceAdapterError: WebSocket error...`

### Connection Status
Monitor WebSocket health through:
- Connection state changes
- Heartbeat monitoring
- Error statistics
- Circuit breaker state

### Key Metrics
1. **Latency**: Time from server timestamp to local reception
2. **Update Rate**: Number of ticks per second
3. **Connection Uptime**: Time since last reconnection
4. **Error Rate**: Errors per minute

## Troubleshooting

### WebSocket Not Connecting
1. Check `websocket.enabled` is `true`
2. Verify `websocket.binance.enabled` is `true`
3. Check network connectivity
4. Verify API credentials support WebSocket

### High Latency
1. Check network conditions
2. Verify server location
3. Consider reducing number of subscribed symbols

### Frequent Disconnections
1. Increase `websocket.reconnect.max_attempts`
2. Check for rate limiting
3. Verify API key permissions

### Fallback to HTTP
1. Check circuit breaker state in logs
2. Look for persistent errors
3. Manually reset by restarting application

## Performance Expectations

### Latency Improvements
- HTTP Polling: 100-200ms average
- WebSocket: 30-50ms average
- Improvement: ~50-70% reduction

### Data Freshness
- HTTP: 1 update per second (polling interval)
- WebSocket: 10-20 updates per second (real-time)
- Improvement: 10-20x more data points

### Resource Usage
- CPU: Slightly higher due to more updates
- Memory: Minimal increase
- Network: More efficient (no polling overhead)