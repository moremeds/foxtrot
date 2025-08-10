"""
Binance API Client - Central coordinator for all Binance operations.

This module provides a central coordinator that manages all manager interactions
and the CCXT exchange instance lifecycle. It serves as the primary interface
for all Binance API operations.
"""

from typing import TYPE_CHECKING, Any, Optional
import asyncio

import ccxt
try:
    import ccxtpro
except ImportError:
    ccxtpro = None

from foxtrot.core.event_engine import EventEngine
from foxtrot.util.logger import get_adapter_logger, create_foxtrot_logger

if TYPE_CHECKING:
    from .account_manager import BinanceAccountManager
    from .contract_manager import BinanceContractManager
    from .historical_data import BinanceHistoricalData
    from .market_data import BinanceMarketData
    from .order_manager import BinanceOrderManager


class BinanceApiClient:
    """
    Central coordinator for all Binance adapter operations.

    This class manages the CCXT exchange instance, coordinates all manager
    interactions, and provides callback interfaces for events.
    """

    def __init__(self, event_engine: EventEngine, adapter_name: str):
        """Initialize the API client."""
        self.event_engine = event_engine
        self.adapter_name = adapter_name
        # Back-reference to adapter (set by adapter on init)
        self.adapter: Any | None = None

        # CCXT exchange instances
        self.exchange: ccxt.binance | None = None
        self.exchange_pro: Optional["ccxtpro.binance"] = None
        
        # WebSocket configuration
        self.use_websocket = False
        self.websocket_enabled_symbols: set[str] = set()

        # Manager instances (initialized later)
        self.account_manager: BinanceAccountManager | None = None
        self.order_manager: BinanceOrderManager | None = None
        self.market_data: BinanceMarketData | None = None
        self.historical_data: BinanceHistoricalData | None = None
        self.contract_manager: BinanceContractManager | None = None

        # Connection state
        self.connected = False
        
        # Adapter-specific logger
        self._foxtrot_logger = create_foxtrot_logger()
        self._logger = get_adapter_logger(f"Binance{adapter_name}", self._foxtrot_logger)

    def initialize_managers(self) -> None:
        """Initialize all manager instances."""
        # Import here to avoid circular imports
        from .account_manager import BinanceAccountManager
        from .contract_manager import BinanceContractManager
        from .historical_data import BinanceHistoricalData
        from .market_data import BinanceMarketData
        from .order_manager import BinanceOrderManager

        self.account_manager = BinanceAccountManager(self)
        self.order_manager = BinanceOrderManager(self)
        self.market_data = BinanceMarketData(self)
        self.historical_data = BinanceHistoricalData(self)
        self.contract_manager = BinanceContractManager(self)

    def connect(self, settings: dict[str, Any]) -> bool:
        """
        Connect to Binance API using provided settings.

        Args:
            settings: Dictionary containing API credentials and configuration

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Initialize CCXT exchange
            api_key = settings.get("API Key", "")
            secret = settings.get("Secret", "")
            sandbox = settings.get("Sandbox", False)
            options = settings.get("options", {})
            
            # Check WebSocket configuration with feature flags
            global_ws_enabled = settings.get("websocket.enabled", False)
            binance_ws_enabled = settings.get("websocket.binance.enabled", True)
            self.use_websocket = global_ws_enabled and binance_ws_enabled
            
            # Load WebSocket symbols configuration
            websocket_symbols = settings.get("websocket.binance.symbols", [])
            if websocket_symbols:
                self.websocket_enabled_symbols = set(websocket_symbols)

            # Public market-data only mode (no API key/secret required)
            public_only: bool = bool(
                settings.get("Public Market Data Only")
                or settings.get("public_market_data_only")
            )

            # Validate API credentials only if not in public-only mode
            exchange_config: dict[str, Any] = {"enableRateLimit": True}
            if not public_only:
                validation_result = self._validate_api_credentials(api_key, secret)
                if not validation_result["valid"]:
                    self._log_error(
                        f"Invalid API credentials: {validation_result['reason']}"
                    )
                    return False
                exchange_config["apiKey"] = api_key
                exchange_config["secret"] = secret
            if options:
                exchange_config["options"] = options

            # Initialize standard CCXT exchange
            self.exchange = ccxt.binance(exchange_config)
            self.exchange.set_sandbox_mode(sandbox)
            
            # Initialize CCXT Pro exchange if WebSocket is enabled
            if self.use_websocket and ccxtpro:
                self.exchange_pro = ccxtpro.binance(exchange_config)
                self.exchange_pro.set_sandbox_mode(sandbox)
                self._log_info("WebSocket support enabled via CCXT Pro")
            elif self.use_websocket and not ccxtpro:
                self._log_warning("WebSocket requested but ccxtpro not available, falling back to HTTP polling")
                self.use_websocket = False

            # Initialize managers
            self.initialize_managers()

            # Test connection
            markets = self.exchange.load_markets()
            if not markets:
                self._log_error("Failed to load markets")
                return False

            self.connected = True
            self._log_info("Successfully connected to Binance")
            return True

        except Exception as e:
            self._log_error(f"Connection failed: {str(e)}")
            return False

    def close(self) -> None:
        """Close connection and cleanup resources with proper error handling."""
        cleanup_errors = []
        
        # Close market data manager
        if self.market_data:
            try:
                self.market_data.close()
                self._log_debug("Market data manager closed successfully")
            except Exception as e:
                error_msg = f"Failed to close market data manager: {str(e)}"
                self._log_error(error_msg)
                cleanup_errors.append(error_msg)

        # Close CCXT Pro exchange (async)
        if self.exchange_pro and hasattr(self.exchange_pro, "close"):
            try:
                self._close_async_exchange()
                self._log_debug("CCXT Pro exchange closed successfully")
            except Exception as e:
                error_msg = f"Failed to close CCXT Pro exchange: {str(e)}"
                self._log_error(error_msg)
                cleanup_errors.append(error_msg)
                    
        # Close standard CCXT exchange
        if self.exchange and hasattr(self.exchange, "close"):
            try:
                self.exchange.close()
                self._log_debug("CCXT exchange closed successfully")
            except Exception as e:
                error_msg = f"Failed to close CCXT exchange: {str(e)}"
                self._log_error(error_msg)
                cleanup_errors.append(error_msg)

        # Set connected to False regardless of cleanup success
        self.connected = False
        
        # Log final status
        if cleanup_errors:
            self._log_warning(f"Connection closed with {len(cleanup_errors)} errors")
        else:
            self._log_info("Binance connection closed successfully")
    
    def _close_async_exchange(self) -> None:
        """
        Close async exchange with proper event loop handling.
        
        This method handles the complexity of closing an async resource
        from a potentially sync context.
        """
        import asyncio
        
        # Try to get the current event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists, create one temporarily
            self._log_debug("No event loop found, creating temporary loop for cleanup")
            asyncio.run(self.exchange_pro.close())
            return
        
        # Check if the loop is running
        if loop.is_running():
            # We're in an async context, schedule the close
            self._log_debug("Scheduling async close in running event loop")
            task = asyncio.create_task(self.exchange_pro.close())
            # Add a callback to log completion
            task.add_done_callback(self._on_async_close_complete)
        else:
            # We're in a sync context with a non-running loop
            self._log_debug("Running async close in non-running event loop")
            try:
                loop.run_until_complete(self.exchange_pro.close())
            except RuntimeError as e:
                # Loop might be closed, create a new one
                self._log_debug(f"Event loop error: {e}, using asyncio.run")
                asyncio.run(self.exchange_pro.close())
    
    def _on_async_close_complete(self, task: asyncio.Task) -> None:
        """
        Callback for async close task completion.
        
        Args:
            task: The completed async task
        """
        try:
            # Check if the task raised an exception
            exception = task.exception()
            if exception:
                self._log_error(f"Async close failed: {exception}")
            else:
                self._log_debug("Async close completed successfully")
        except Exception as e:
            self._log_error(f"Error in async close callback: {e}")

    def _validate_api_credentials(self, api_key: str, secret: str) -> dict:
        """
        Validate API credentials format and content.
        
        Args:
            api_key: Binance API key
            secret: Binance API secret
            
        Returns:
            Dictionary with 'valid' (bool) and 'reason' (str) keys
        """
        import re
        
        # Check if credentials are provided
        if not api_key or not secret:
            return {"valid": False, "reason": "Missing API key or secret"}
        
        # Check API key format
        # Binance API keys are typically 64 characters long and alphanumeric
        if not isinstance(api_key, str):
            return {"valid": False, "reason": "API key must be a string"}
        
        if len(api_key) < 20 or len(api_key) > 100:
            return {"valid": False, "reason": f"API key length {len(api_key)} is invalid (expected 20-100 characters)"}
        
        # Check if API key contains only valid characters (alphanumeric, dash, underscore)
        if not re.match(r'^[A-Za-z0-9\-_]+$', api_key):
            return {"valid": False, "reason": "API key contains invalid characters"}
        
        # Check secret format
        if not isinstance(secret, str):
            return {"valid": False, "reason": "Secret must be a string"}
        
        if len(secret) < 20 or len(secret) > 100:
            return {"valid": False, "reason": f"Secret length {len(secret)} is invalid (expected 20-100 characters)"}
        
        # Check if secret contains only valid characters
        if not re.match(r'^[A-Za-z0-9\-_]+$', secret):
            return {"valid": False, "reason": "Secret contains invalid characters"}
        
        # Check for common placeholder values
        placeholder_values = ["your_api_key", "your_secret", "xxx", "api_key", "secret", 
                             "YOUR_API_KEY", "YOUR_SECRET", "<api_key>", "<secret>"]
        if api_key.lower() in [p.lower() for p in placeholder_values]:
            return {"valid": False, "reason": "API key appears to be a placeholder value"}
        
        if secret.lower() in [p.lower() for p in placeholder_values]:
            return {"valid": False, "reason": "Secret appears to be a placeholder value"}
        
        # All validations passed
        return {"valid": True, "reason": "Credentials format validated"}

    def _log_info(self, message: str) -> None:
        """Log info message."""
        # MIGRATION: Replace print with INFO logging
        self._logger.info(message)

    def _log_error(self, message: str) -> None:
        """Log error message."""
        # MIGRATION: Replace print with ERROR logging
        self._logger.error(message)
        
    def _log_warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
    
    def _log_debug(self, message: str) -> None:
        """Log debug message."""
        self._logger.debug(message)
        
    def is_websocket_enabled(self, symbol: Optional[str] = None) -> bool:
        """
        Check if WebSocket is enabled for a given symbol.
        
        Args:
            symbol: Symbol to check. If None, returns general WebSocket status.
            
        Returns:
            True if WebSocket is enabled for the symbol/globally
        """
        if not self.use_websocket or not self.exchange_pro:
            return False
            
        if symbol is None:
            return True
            
        # Check if symbol is in the enabled list (empty list means all symbols)
        return not self.websocket_enabled_symbols or symbol in self.websocket_enabled_symbols
