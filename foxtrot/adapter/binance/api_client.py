"""
Binance API Client - Central coordinator for all Binance operations.

This module provides a central coordinator that manages all manager interactions
and the CCXT exchange instance lifecycle. It serves as the primary interface
for all Binance API operations.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

import ccxt

from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange

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
        
        # CCXT exchange instance
        self.exchange: Optional[ccxt.binance] = None
        
        # Manager instances (initialized later)
        self.account_manager: Optional["BinanceAccountManager"] = None
        self.order_manager: Optional["BinanceOrderManager"] = None
        self.market_data: Optional["BinanceMarketData"] = None
        self.historical_data: Optional["BinanceHistoricalData"] = None
        self.contract_manager: Optional["BinanceContractManager"] = None
        
        # Connection state
        self.connected = False
        
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
        
    def connect(self, settings: Dict[str, Any]) -> bool:
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
            
            if not api_key or not secret:
                self._log_error("Missing API credentials")
                return False
                
            self.exchange = ccxt.binance({
                "apiKey": api_key,
                "secret": secret,
                "sandbox": sandbox,
                "enableRateLimit": True,
            })
            
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
                
            if self.exchange:
                # Close any open connections
                if hasattr(self.exchange, 'close'):
                    self.exchange.close()
                    
            self._log_info("Binance connection closed")
            
        except Exception as e:
            self._log_error(f"Error closing connection: {str(e)}")
        finally:
            # Always set connected to False regardless of cleanup success
            self.connected = False
            
    def _log_info(self, message: str) -> None:
        """Log info message."""
        print(f"[{self.adapter_name}] INFO: {message}")
        
    def _log_error(self, message: str) -> None:
        """Log error message."""
        print(f"[{self.adapter_name}] ERROR: {message}")