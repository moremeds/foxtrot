"""
Market Data Panel for Trading Interface

This module provides a panel that displays real-time market data
for the selected trading symbol.
"""

from decimal import Decimal
from typing import Any, Optional

from textual.containers import Container, Vertical
from textual.widgets import Static

from foxtrot.app.tui.utils.formatters import format_number


class MarketDataPanel(Container):
    """
    Panel displaying real-time market data for the selected symbol.

    Shows:
    - Current bid/ask prices
    - Last traded price
    - Volume and change
    - Market depth (5-level)
    """

    def __init__(self, **kwargs):
        """Initialize the market data panel."""
        super().__init__(**kwargs)
        self.current_symbol: Optional[str] = None
        self.market_data: dict[str, Any] = {}

        # UI components
        self.bid_ask_label: Optional[Static] = None
        self.last_price_label: Optional[Static] = None
        self.volume_label: Optional[Static] = None
        self.depth_container: Optional[Container] = None
        self.depth_levels: list[Static] = []

    def compose(self):
        """Create market data panel layout."""
        with Vertical(classes="market-data"):
            yield Static("Market Data", classes="market-title")

            with Vertical(classes="market-content"):
                self.bid_ask_label = Static("Bid/Ask: -", classes="market-item")
                yield self.bid_ask_label

                self.last_price_label = Static("Last: -", classes="market-item")
                yield self.last_price_label

                self.volume_label = Static("Volume: -", classes="market-item")
                yield self.volume_label

                yield Static("Market Depth:", classes="depth-title")

                with Vertical(classes="depth-container") as depth_container:
                    self.depth_container = depth_container
                    for i in range(5):
                        depth_level = Static(f"Level {i+1}: -", classes="depth-level")
                        self.depth_levels.append(depth_level)
                        yield depth_level

    async def update_symbol(self, symbol: str):
        """
        Update market data for new symbol.

        Args:
            symbol: Trading symbol to fetch data for
        """
        self.current_symbol = symbol
        await self._fetch_market_data()

    async def _fetch_market_data(self):
        """Fetch and display market data for current symbol."""
        if not self.current_symbol:
            self._clear_market_data()
            return

        try:
            # TODO: Integrate with actual market data feed
            # Mock market data for demonstration
            self.market_data = {
                "bid": Decimal("149.95"),
                "ask": Decimal("150.05"),
                "last": Decimal("150.00"),
                "volume": 1250000,
                "change": Decimal("1.25"),
                "change_percent": Decimal("0.84"),
                "depth": [
                    {"bid": Decimal("149.94"), "ask": Decimal("150.06"), "bid_size": 100, "ask_size": 150},
                    {"bid": Decimal("149.93"), "ask": Decimal("150.07"), "bid_size": 200, "ask_size": 175},
                    {"bid": Decimal("149.92"), "ask": Decimal("150.08"), "bid_size": 300, "ask_size": 225},
                    {"bid": Decimal("149.91"), "ask": Decimal("150.09"), "bid_size": 150, "ask_size": 100},
                    {"bid": Decimal("149.90"), "ask": Decimal("150.10"), "bid_size": 500, "ask_size": 400},
                ]
            }

            await self._update_market_display()

        except Exception as e:
            self._show_error(f"Failed to fetch market data: {str(e)}")

    async def _update_market_display(self):
        """Update market data display with current data."""
        if not self.market_data:
            return

        # Update bid/ask
        if self.bid_ask_label:
            bid = self.market_data.get("bid")
            ask = self.market_data.get("ask")
            if bid and ask:
                spread = ask - bid
                self.bid_ask_label.update(
                    f"Bid/Ask: {bid} / {ask} (Spread: {spread:.2f})"
                )

        # Update last price with change
        if self.last_price_label:
            last = self.market_data.get("last")
            change = self.market_data.get("change")
            change_percent = self.market_data.get("change_percent")

            if last and change is not None and change_percent is not None:
                change_sign = "+" if change > 0 else ""
                color = "green" if change > 0 else "red" if change < 0 else "white"
                # Note: Textual styling would be applied via CSS classes
                self.last_price_label.update(
                    f"Last: {last} ({change_sign}{change} / {change_sign}{change_percent}%)"
                )

        # Update volume
        if self.volume_label:
            volume = self.market_data.get("volume")
            if volume:
                self.volume_label.update(f"Volume: {format_number(volume)}")

        # Update market depth
        depth_data = self.market_data.get("depth", [])
        for i, level_widget in enumerate(self.depth_levels):
            if i < len(depth_data):
                level = depth_data[i]
                bid = level.get("bid", "-")
                ask = level.get("ask", "-")
                bid_size = level.get("bid_size", "-")
                ask_size = level.get("ask_size", "-")
                level_widget.update(
                    f"L{i+1}: {bid_size}@{bid} | {ask}@{ask_size}"
                )
            else:
                level_widget.update(f"Level {i+1}: -")

    def _clear_market_data(self):
        """Clear all market data displays."""
        if self.bid_ask_label:
            self.bid_ask_label.update("Bid/Ask: -")
        if self.last_price_label:
            self.last_price_label.update("Last: -")
        if self.volume_label:
            self.volume_label.update("Volume: -")
        
        for level_widget in self.depth_levels:
            level_widget.update("Level: -")

    def _show_error(self, message: str):
        """
        Show error message in the panel.

        Args:
            message: Error message to display
        """
        if self.bid_ask_label:
            self.bid_ask_label.update(f"Error: {message}")

    async def refresh_data(self):
        """Refresh market data for current symbol."""
        if self.current_symbol:
            await self._fetch_market_data()

    def get_current_price(self) -> Optional[Decimal]:
        """
        Get the current market price.

        Returns:
            Current last traded price or None if unavailable
        """
        return self.market_data.get("last")

    def get_bid_ask(self) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Get current bid and ask prices.

        Returns:
            Tuple of (bid, ask) prices or (None, None) if unavailable
        """
        return self.market_data.get("bid"), self.market_data.get("ask")