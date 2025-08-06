"""
Binance API Client - Central coordinator for all Binance operations.

This module provides a central coordinator that manages all manager interactions
and the CCXT exchange instance lifecycle. It serves as the primary interface
for all Binance API operations.
"""

from typing import TYPE_CHECKING, Any, Optional

import ccxt
try:
    import ccxtpro
except ImportError:
    ccxtpro = None

from foxtrot.core.event_engine import EventEngine
from foxtrot.util.logger import get_adapter_logger

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
        self._logger = get_adapter_logger(f"Binance{adapter_name}")

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

            if not api_key or not secret:
                self._log_error("Missing API credentials")
                return False

            exchange_config = {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
            }
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
        """Close connection and cleanup resources."""
        try:
            if self.market_data:
                self.market_data.close()

            # Close CCXT Pro exchange if available
            if self.exchange_pro and hasattr(self.exchange_pro, "close"):
                import asyncio
                # Need to close async exchange in a sync context
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Schedule the close for later
                        asyncio.create_task(self.exchange_pro.close())
                    else:
                        # Run the close synchronously
                        loop.run_until_complete(self.exchange_pro.close())
                except Exception:
                    # If no event loop, create one temporarily
                    asyncio.run(self.exchange_pro.close())
                    
            if self.exchange and hasattr(self.exchange, "close"):
                # Close any open connections
                self.exchange.close()

            self._log_info("Binance connection closed")

        except Exception as e:
            self._log_error(f"Error closing connection: {str(e)}")
        finally:
            # Always set connected to False regardless of cleanup success
            self.connected = False

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
