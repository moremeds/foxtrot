"""
Utility functions for IB connection testing.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, TYPE_CHECKING

from foxtrot.util.object import AccountData, PositionData

if TYPE_CHECKING:
    from .config import IBConfig


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None, verbose: bool = False) -> None:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to log to
        verbose: Whether to use verbose formatting
    """
    # Configure log format
    if verbose:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    else:
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    # Set up logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Reduce noise from IB API
    logging.getLogger("ibapi").setLevel(logging.WARNING)


def format_account_data(account_data: Dict[str, AccountData], json_output: bool = False) -> str:
    """Format account data for display.
    
    Args:
        account_data: Dictionary of account data by account ID
        json_output: Whether to format as JSON
        
    Returns:
        Formatted account data string
    """
    if not account_data:
        return "No account data received" if not json_output else json.dumps({"accounts": []})
    
    if json_output:
        accounts = []
        for account_id, account in account_data.items():
            accounts.append({
                "account_id": account_id,
                "balance": account.balance,
                "available": account.available,
                "commission": account.commission,
                "margin": account.margin,
                "position_profit": account.position_profit,
                "close_profit": account.close_profit
            })
        return json.dumps({"accounts": accounts}, indent=2)
    
    # Text format
    lines = ["", "=== ACCOUNT INFORMATION ==="]
    
    for account_id, account in account_data.items():
        lines.extend([
            f"",
            f"Account: {account_id}",
            f"  Balance:         ${account.balance:>12,.2f}",
            f"  Available:       ${account.available:>12,.2f}",
            f"  Commission:      ${account.commission:>12,.2f}",
            f"  Margin:          ${account.margin:>12,.2f}",
            f"  Position P&L:    ${account.position_profit:>12,.2f}",
            f"  Closed P&L:      ${account.close_profit:>12,.2f}"
        ])
    
    lines.append("=" * 30)
    return "\n".join(lines)


def format_position_data(position_data: Dict[str, PositionData], json_output: bool = False) -> str:
    """Format position data for display.
    
    Args:
        position_data: Dictionary of position data by symbol
        json_output: Whether to format as JSON
        
    Returns:
        Formatted position data string
    """
    if not position_data:
        return "No positions" if not json_output else json.dumps({"positions": []})
    
    if json_output:
        positions = []
        for position in position_data.values():
            positions.append({
                "symbol": position.symbol,
                "exchange": position.exchange.value,
                "direction": position.direction.value,
                "volume": position.volume,
                "price": position.price,
                "pnl": position.pnl
            })
        return json.dumps({"positions": positions}, indent=2)
    
    # Text format
    lines = ["", "=== POSITIONS ==="]
    
    if position_data:
        lines.append(f"{'Symbol':<15} {'Exchange':<10} {'Direction':<5} {'Volume':<10} {'Price':<12} {'P&L':<12}")
        lines.append("-" * 80)
        
        for position in position_data.values():
            lines.append(
                f"{position.symbol:<15} "
                f"{position.exchange.value:<10} "
                f"{position.direction.value:<5} "
                f"{position.volume:<10.0f} "
                f"${position.price:<11.2f} "
                f"${position.pnl:<11.2f}"
            )
    
    lines.append("=" * 20)
    return "\n".join(lines)


def format_connection_status(status: str, details: Optional[str] = None) -> str:
    """Format connection status message.
    
    Args:
        status: Connection status
        details: Optional additional details
        
    Returns:
        Formatted status message
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] Connection Status: {status.upper()}"
    
    if details:
        message += f" - {details}"
    
    return message


def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message for display.
    
    Args:
        error: Exception that occurred
        context: Optional context about where the error occurred
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"ERROR in {context}: {error_type} - {error_msg}"
    else:
        return f"ERROR: {error_type} - {error_msg}"


def create_summary_report(
    config: "IBConfig",
    connection_successful: bool,
    account_data: Dict[str, AccountData],
    position_data: Dict[str, PositionData],
    error_message: Optional[str] = None,
    json_output: bool = False
) -> str:
    """Create a summary report of the test results.
    
    Args:
        config: Configuration used for the test
        connection_successful: Whether connection was successful
        account_data: Account data collected
        position_data: Position data collected
        error_message: Optional error message if test failed
        json_output: Whether to format as JSON
        
    Returns:
        Formatted summary report
    """
    if json_output:
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "configuration": {
                "host": config.host,
                "port": config.port,
                "client_id": config.client_id,
                "account": config.account or "auto-detected"
            },
            "connection_successful": connection_successful,
            "accounts_found": len(account_data),
            "positions_found": len(position_data),
            "error": error_message
        }
        
        if account_data:
            report["account_details"] = json.loads(format_account_data(account_data, True))["accounts"]
        
        if position_data:
            report["position_details"] = json.loads(format_position_data(position_data, True))["positions"]
        
        return json.dumps(report, indent=2)
    
    # Text format
    lines = [
        "=" * 60,
        "INTERACTIVE BROKERS CONNECTION TEST REPORT",
        "=" * 60,
        f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Configuration:",
        f"  Host:      {config.host}",
        f"  Port:      {config.port}",
        f"  Client ID: {config.client_id}",
        f"  Account:   {config.account or 'auto-detected'}",
        "",
        f"Connection Successful: {'YES' if connection_successful else 'NO'}",
        f"Accounts Found:        {len(account_data)}",
        f"Positions Found:       {len(position_data)}"
    ]
    
    if error_message:
        lines.extend(["", f"Error: {error_message}"])
    
    if account_data:
        lines.append(format_account_data(account_data, False))
    
    if position_data:
        lines.append(format_position_data(position_data, False))
    
    lines.append("=" * 60)
    return "\n".join(lines)


def validate_tws_connection(host: str, port: int) -> bool:
    """Check if TWS/Gateway is running and accepting connections.
    
    Args:
        host: TWS host address
        port: TWS port number
        
    Returns:
        True if connection is possible, False otherwise
    """
    import socket
    
    try:
        with socket.create_connection((host, port), timeout=5):
            return True
    except (socket.error, OSError):
        return False


def get_troubleshooting_tips(error_context: str) -> str:
    """Get troubleshooting tips based on error context.
    
    Args:
        error_context: Context where the error occurred
        
    Returns:
        Troubleshooting tips
    """
    tips = {
        "connection": [
            "1. Ensure TWS or IB Gateway is running",
            "2. Check that API connections are enabled in TWS (File > Global Configuration > API > Settings)",
            "3. Verify the host and port settings match your TWS configuration",
            "4. Check that the client ID is not already in use",
            "5. Ensure your firewall allows connections to the specified port"
        ],
        "authentication": [
            "1. Check that your IB account has API access enabled",
            "2. Verify you're using the correct account credentials",
            "3. Ensure your account has the necessary permissions",
            "4. Try connecting with the same credentials through TWS first"
        ],
        "data": [
            "1. Check that your account has market data subscriptions",
            "2. Verify account permissions for the requested data",
            "3. Ensure TWS is logged in and connected to market data servers",
            "4. Try increasing the data timeout setting"
        ],
        "timeout": [
            "1. Increase the connection timeout setting",
            "2. Check network connectivity to IB servers",
            "3. Verify TWS/Gateway is responding normally",
            "4. Try connecting during off-peak hours"
        ]
    }
    
    context_tips = tips.get(error_context, ["Check the error message for specific guidance"])
    
    return "Troubleshooting tips:\n" + "\n".join(f"  {tip}" for tip in context_tips)