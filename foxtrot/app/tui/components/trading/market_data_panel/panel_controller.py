"""
Market data panel controller for orchestrating data and UI operations.

This module provides the main orchestration logic for the market data panel,
coordinating between data handler and display manager.
"""

from typing import Any, Dict, List, Optional
import logging
from decimal import Decimal

from textual.containers import Container

from .data_handler import MarketDataHandler
from .display_manager import MarketDataDisplayManager

logger = logging.getLogger(__name__)


class MarketDataPanel(Container):
    """
    Panel displaying real-time market data for trading symbols.

    Features:
    - Real-time bid/ask prices
    - Last traded price with change indicators
    - Volume and daily statistics
    - Market depth display (5-level book)
    - Error handling and connection status
    - Automatic data refresh and formatting

    The panel provides essential market information needed for trading decisions
    and updates in real-time as market data is received.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Current state
        self.current_symbol: Optional[str] = None
        self.market_data: Dict[str, Any] = {}
        
        # Backward compatibility attributes
        self.depth_levels: List[Dict[str, Any]] = []
        self._last_error: Optional[str] = None

        # Modular components
        self.data_handler = MarketDataHandler()
        self.display_manager = MarketDataDisplayManager()

    def compose(self):
        """Create market data panel layout with organized sections."""
        # Use UI layout from display manager
        layout_generator = self.display_manager.ui_layout.compose()
        
        # Initialize component references after layout is created
        self.display_manager.initialize_components()
        
        return layout_generator

    async def update_symbol(self, symbol: str) -> None:
        """
        Update market data for a new trading symbol.
        
        Args:
            symbol: New trading symbol to display market data for
            
        Note:
            This method triggers a fresh data fetch and clears any
            previous data to avoid displaying stale information.
        """
        if symbol != self.current_symbol:
            self.current_symbol = symbol
            
            # Backward compatibility methods for tests
            self._clear_market_data()
            self._update_status("Fetching data...")
            await self._fetch_and_display_market_data()

    async def _fetch_and_display_market_data(self) -> None:
        """
        Fetch and display market data for the current symbol.
        
        This method handles the complete data fetch workflow including
        error handling, data validation, and UI updates.
        """
        if not self.current_symbol:
            self.display_manager.clear_market_data()
            self.display_manager.update_status("No symbol selected")
            return

        try:
            # Clear any previous errors
            self.data_handler.clear_error()
            
            # Fetch market data (mock implementation)
            market_data = await self.data_handler.fetch_market_data(self.current_symbol)
            
            # Validate and store data
            if self.data_handler.validate_market_data(market_data):
                self.market_data = market_data
                await self.display_manager.update_all_displays(market_data)
                self.display_manager.update_status("Connected")
            else:
                await self._handle_invalid_data()

        except Exception as e:
            await self._handle_fetch_error(e)

    async def _handle_fetch_error(self, error: Exception) -> None:
        """Handle market data fetch errors."""
        error_message = await self.data_handler.handle_fetch_error(error, self.current_symbol)
        self.display_manager.show_error(error_message)

    async def _handle_invalid_data(self) -> None:
        """Handle invalid or incomplete market data."""
        error_message = self.data_handler.handle_invalid_data()
        self.display_manager.show_error(error_message)
        self.display_manager.update_status("Data validation failed")
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error for testing and debugging."""
        # Check both sources for backward compatibility
        if self._last_error:
            return self._last_error
        return self.data_handler.get_last_error()
    
    def get_current_symbol(self) -> Optional[str]:
        """Get the currently displayed symbol."""
        return self.current_symbol
    
    def has_valid_data(self) -> bool:
        """Check if current market data is valid and up-to-date."""
        # Check both error sources for backward compatibility
        has_error = self._last_error is not None or self.data_handler.get_last_error() is not None
        return bool(self.market_data and not has_error)

    def get_current_price(self) -> Optional[Decimal]:
        """Get the current last price from market data."""
        last_price = self.market_data.get("last")
        return Decimal(str(last_price)) if last_price is not None else None

    # Backward compatibility methods for tests
    def _clear_market_data(self) -> None:
        """Clear current market data (backward compatibility)."""
        self.market_data.clear()
        self.depth_levels.clear()
        self._last_error = None

    def _update_status(self, status: str) -> None:
        """Update status display (backward compatibility)."""
        # This would update a status display in the UI
        pass


    def _validate_market_data(self, data: Dict[str, Any]) -> bool:
        """Validate market data structure (backward compatibility)."""
        required_fields = ["symbol", "bid", "ask", "last"]
        
        # Check required fields exist
        if not all(field in data for field in required_fields):
            return False
            
        # Check valid price relationships (bid should be less than ask)
        try:
            bid = data.get("bid")
            ask = data.get("ask")
            
            if bid is not None and ask is not None:
                # Convert to Decimal for comparison
                from decimal import Decimal
                bid_val = Decimal(str(bid))
                ask_val = Decimal(str(ask))
                
                if bid_val >= ask_val:  # Invalid: bid >= ask
                    return False
                    
        except (ValueError, TypeError, AttributeError):
            return False
            
        return True

    def _generate_mock_depth(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mock market depth data (backward compatibility)."""
        from decimal import Decimal
        import random
        
        # Mock depth with 5 levels on each side
        bids = []
        asks = []
        base_price = Decimal("150.00")
        
        # Bids (decreasing prices)
        for i in range(5):
            price = base_price - Decimal(f"0.{i+1:02d}")
            volume = random.randint(100, 1000) * 100
            bids.append({
                "price": price,
                "volume": volume
            })
            
        # Asks (increasing prices)  
        for i in range(5):
            price = base_price + Decimal(f"0.{i+1:02d}")
            volume = random.randint(100, 1000) * 100
            asks.append({
                "price": price,
                "volume": volume
            })
            
        return {"bids": bids, "asks": asks}