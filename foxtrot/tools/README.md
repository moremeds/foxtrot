# Interactive Brokers Connection Tester

A comprehensive tool for testing Interactive Brokers TWS/Gateway connectivity and retrieving account information.

## Features

- **Connection Testing**: Validates TWS/Gateway connectivity with timeout handling
- **Account Information**: Retrieves and displays account balances, positions, and P&L data  
- **Retry Logic**: Automatic retry with configurable attempts and delays
- **Multiple Configuration Sources**: Environment variables, config files, command line arguments
- **Flexible Output**: Human-readable text or JSON format
- **Comprehensive Logging**: Configurable logging levels with optional file output
- **Error Handling**: Detailed error messages with troubleshooting guidance

## Quick Start

### Command Line Usage

```bash
# Basic test with default settings
python scripts/test_ib.py

# Test with custom host and port  
python scripts/test_ib.py --host 192.168.1.100 --port 7496

# Test with verbose output
python scripts/test_ib.py --verbose

# Output results in JSON format
python scripts/test_ib.py --json

# Use custom configuration file
python scripts/test_ib.py --config my_config.json
```

### Programmatic Usage

```python
from foxtrot.tools.config import load_config
from foxtrot.tools.enhanced_tester import run_test_with_retries
from foxtrot.tools.utils import setup_logging, create_summary_report

# Load configuration
config = load_config(host="127.0.0.1", port=7497, client_id=1)

# Setup logging
setup_logging(config.log_level, verbose=config.verbose)

# Run test
success, tester = run_test_with_retries(config)

if success:
    print("✅ Connection successful!")
    # Display account information
    report = create_summary_report(
        config=config,
        connection_successful=success, 
        account_data=tester.account_data,
        position_data=tester.position_data
    )
    print(report)
```

## Configuration

The tool supports multiple configuration methods with the following priority order:

1. **Command line arguments** (highest priority)
2. **Environment variables**  
3. **Configuration file**
4. **Default values** (lowest priority)

### Configuration File Format

Create a JSON configuration file:

```json
{
  "ib": {
    "host": "127.0.0.1",
    "port": 7497,
    "client_id": 1,
    "account": "",
    "connection_timeout": 30,
    "data_timeout": 10,
    "retry_attempts": 3,
    "retry_delay": 5,
    "log_level": "INFO",
    "verbose": false,
    "json_output": false
  }
}
```

### Environment Variables

```bash
export FOXTROT_IB_HOST="127.0.0.1"
export FOXTROT_IB_PORT="7497"
export FOXTROT_IB_CLIENT_ID="1"
export FOXTROT_IB_ACCOUNT=""
export FOXTROT_IB_CONNECTION_TIMEOUT="30"
export FOXTROT_IB_DATA_TIMEOUT="10"  
export FOXTROT_IB_RETRY_ATTEMPTS="3"
export FOXTROT_IB_RETRY_DELAY="5"
export FOXTROT_IB_LOG_LEVEL="INFO"
export FOXTROT_IB_VERBOSE="false"
export FOXTROT_IB_JSON_OUTPUT="false"
```

## Configuration Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `host` | TWS/Gateway host address | `127.0.0.1` | `FOXTROT_IB_HOST` |
| `port` | TWS/Gateway port number | `7497` | `FOXTROT_IB_PORT` |
| `client_id` | Client ID for connection | `1` | `FOXTROT_IB_CLIENT_ID` |
| `account` | Trading account (auto-detected if empty) | `""` | `FOXTROT_IB_ACCOUNT` |
| `connection_timeout` | Connection timeout in seconds | `30` | `FOXTROT_IB_CONNECTION_TIMEOUT` |
| `data_timeout` | Data collection timeout in seconds | `10` | `FOXTROT_IB_DATA_TIMEOUT` |
| `retry_attempts` | Number of retry attempts | `3` | `FOXTROT_IB_RETRY_ATTEMPTS` |
| `retry_delay` | Delay between retries in seconds | `5` | `FOXTROT_IB_RETRY_DELAY` |
| `log_level` | Logging level | `INFO` | `FOXTROT_IB_LOG_LEVEL` |
| `verbose` | Enable verbose output | `false` | `FOXTROT_IB_VERBOSE` |
| `json_output` | Output in JSON format | `false` | `FOXTROT_IB_JSON_OUTPUT` |

## Prerequisites

### Interactive Brokers Setup

1. **Install TWS or IB Gateway**
   - Download from [Interactive Brokers](https://www.interactivebrokers.com/en/trading/tws.php)
   - Install and configure with your account credentials

2. **Enable API Access**
   - In TWS: File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Set Socket port (default: 7497 for TWS, 4001 for Gateway)
   - Add your client computer's IP to trusted IPs if running remotely

3. **Account Permissions**
   - Ensure your account has API access enabled
   - Verify market data subscriptions if needed

### Python Dependencies

The tool uses the following dependencies (already included in foxtrot):

- `ibapi` - Interactive Brokers API
- `foxtrot` - Trading platform framework

## Output Examples

### Text Output

```
==========================================================
INTERACTIVE BROKERS CONNECTION TEST REPORT
==========================================================
Test Time: 2024-01-15 14:30:25

Configuration:
  Host:      127.0.0.1
  Port:      7497
  Client ID: 1
  Account:   auto-detected

Connection Successful: YES
Accounts Found:        1
Positions Found:       3

=== ACCOUNT INFORMATION ===

Account: DU12345.USD
  Balance:         $   50,000.00
  Available:       $   45,000.00
  Commission:      $       15.50
  Margin:          $        0.00
  Position P&L:    $      125.75
  Closed P&L:      $      850.25
==============================

=== POSITIONS ===
Symbol          Exchange   Dir   Volume     Price        P&L         
--------------------------------------------------------------------------------
SPY             SMART      LONG  100        $420.50      $125.75    
QQQ             SMART      LONG  50         $350.25      $75.50     
AAPL            SMART      LONG  25         $180.75      $-25.25    
====================
==========================================================
```

### JSON Output

```json
{
  "test_timestamp": "2024-01-15T14:30:25.123456",
  "configuration": {
    "host": "127.0.0.1",
    "port": 7497,
    "client_id": 1,
    "account": "auto-detected"
  },
  "connection_successful": true,
  "accounts_found": 1,
  "positions_found": 3,
  "error": null,
  "account_details": [
    {
      "account_id": "DU12345.USD",
      "balance": 50000.0,
      "available": 45000.0,
      "commission": 15.5,
      "margin": 0.0,
      "position_profit": 125.75,
      "close_profit": 850.25
    }
  ],
  "position_details": [
    {
      "symbol": "SPY",
      "exchange": "SMART",
      "direction": "LONG",
      "volume": 100,
      "price": 420.5,
      "pnl": 125.75
    }
  ]
}
```

## Troubleshooting

### Common Issues

**Connection refused errors:**
1. Ensure TWS or IB Gateway is running
2. Check that API connections are enabled
3. Verify host and port settings
4. Check firewall settings

**Authentication errors:**
1. Verify account has API access enabled
2. Check client ID is not already in use
3. Ensure account credentials are correct

**Timeout errors:**
1. Increase connection timeout setting
2. Check network connectivity
3. Try connecting during off-peak hours

**No data received:**
1. Check account permissions for market data
2. Verify account is logged in to TWS
3. Increase data timeout setting

### Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Connection test failed |
| 2 | Configuration error |
| 3 | User interrupted |
| 4 | Unexpected error |

## Development

### Project Structure

```
foxtrot/tools/
├── __init__.py              # Package initialization
├── config.py                # Configuration management  
├── utils.py                 # Utility functions
├── ib_tester.py             # Core connection tester
├── enhanced_tester.py       # Enhanced tester with retry logic
└── README.md               # This documentation

scripts/
└── test_ib.py              # Command-line interface

examples/
├── ib_config.json          # Example configuration
└── test_ib_connection.py   # Simple usage example
```

### Testing

```bash
# Run with verbose output for debugging
python scripts/test_ib.py --verbose --log-level DEBUG

# Test configuration validation  
python scripts/test_ib.py --create-config test_config.json
python scripts/test_ib.py --config test_config.json

# Test different connection scenarios
python scripts/test_ib.py --port 9999  # Should fail with connection error
```

## License

This tool is part of the Foxtrot trading platform framework.