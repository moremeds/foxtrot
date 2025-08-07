"""
Market data handler for fetching and validating market information.

This module provides pure data handling logic including data fetching,
validation, mock data generation, and error processing.
"""

from decimal import Decimal
from typing import Any, Dict, Optional, List
import logging

from ..common import TradingConstants

logger = logging.getLogger(__name__)


class MarketDataHandler:
    """
    Handles market data fetching and validation with no UI concerns.
    
    This class contains only data processing and business logic,
    with no presentation or display functionality.
    """

    def __init__(self):
        # Error tracking
        self._last_error: Optional[str] = None

    async def fetch_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch market data from data source.
        
        Args:
            symbol: Trading symbol to fetch data for
            
        Returns:
            Dictionary containing market data
            
        Note:
            In production, this would connect to real market data feeds.
            Currently returns mock data for demonstration.
        """
        # TODO: Replace with real market data integration
        # Example integrations:
        # - WebSocket connections to exchange feeds
        # - REST API calls for snapshot data
        # - FIX protocol connections for professional feeds
        
        # Mock market data with realistic values
        return {
            "symbol": symbol,
            "bid": Decimal("149.95"),
            "ask": Decimal("150.05"),
            "last": Decimal("150.00"),
            "volume": 1250000,
            "change": Decimal("1.25"),
            "change_percent": Decimal("0.84"),
            "high": Decimal("152.50"),
            "low": Decimal("148.75"),
            "open": Decimal("149.50"),
            "timestamp": "2024-01-15 15:30:25",
            "depth": self.generate_mock_depth()
        }

    def generate_mock_depth(self) -> Dict[str, List[Dict[str, Decimal]]]:
        """Generate mock market depth data for demonstration."""
        bid_levels = []
        ask_levels = []
        
        base_bid = Decimal("149.95")
        base_ask = Decimal("150.05")
        
        # Generate 5 bid levels (descending prices)
        for i in range(5):
            price = base_bid - Decimal(str(i * 0.01))
            size = Decimal(str(1000 + i * 500))
            bid_levels.append({"price": price, "size": size})
        
        # Generate 5 ask levels (ascending prices)  
        for i in range(5):
            price = base_ask + Decimal(str(i * 0.01))
            size = Decimal(str(1000 + i * 500))
            ask_levels.append({"price": price, "size": size})
            
        return {
            "bids": bid_levels,
            "asks": ask_levels
        }

    def validate_market_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate market data for completeness and consistency.
        
        Args:
            data: Market data dictionary to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ["symbol", "bid", "ask", "last", "volume"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in market data: {field}")
                return False
        
        # Validate price relationships
        try:
            bid = data["bid"]
            ask = data["ask"]
            last = data["last"]
            
            # Basic sanity checks
            if bid >= ask:
                logger.warning("Invalid market data: bid >= ask")
                return False
                
            if bid <= 0 or ask <= 0 or last <= 0:
                logger.warning("Invalid market data: non-positive prices")
                return False
                
        except (TypeError, KeyError) as e:
            logger.warning(f"Error validating market data prices: {e}")
            return False
            
        return True

    async def handle_fetch_error(self, error: Exception, symbol: Optional[str] = None) -> str:
        """
        Handle market data fetch errors with secure error reporting.
        
        Args:
            error: Exception that occurred during fetch
            symbol: Symbol being fetched (for logging)
            
        Returns:
            User-safe error message
        """
        try:
            from foxtrot.app.tui.security import SecurityAwareErrorHandler
            
            secure_error = SecurityAwareErrorHandler.handle_exception(
                error, "market_data_fetch"
            )
            
            self._last_error = secure_error.user_message
            
            logger.error(f"Market data fetch error for {symbol}: {error}")
            
            return secure_error.user_message
            
        except ImportError:
            # Fallback error handling
            error_msg = "Market data unavailable"
            self._last_error = error_msg
            logger.error(f"Market data fetch error for {symbol}: {error}")
            return error_msg

    def handle_invalid_data(self) -> str:
        """
        Handle invalid or incomplete market data.
        
        Returns:
            User-safe error message
        """
        error_msg = "Invalid market data received"
        self._last_error = error_msg
        return error_msg

    def get_last_error(self) -> Optional[str]:
        """Get the last error for testing and debugging."""
        return self._last_error

    def clear_error(self) -> None:
        """Clear the last error state."""
        self._last_error = None