"""
Market data UI layout and component initialization.

This module handles UI layout creation and initial component setup
for the market data panel.
"""

from typing import List, Optional
from textual.containers import Container, Vertical
from textual.widgets import Static


class MarketDataUILayout:
    """
    Handles UI layout and component initialization for market data display.
    
    This class focuses solely on creating the UI structure and initializing
    widget references for the market data panel.
    """

    def __init__(self):
        # UI component references
        self.bid_ask_label: Optional[Static] = None
        self.last_price_label: Optional[Static] = None
        self.volume_label: Optional[Static] = None
        self.depth_container: Optional[Container] = None
        self.status_label: Optional[Static] = None
        
        # Market depth widgets (5 levels)
        self.depth_levels: List[Static] = []

    def compose(self):
        """Create market data panel layout with organized sections."""
        with Vertical(classes="market-data"):
            yield Static("Market Data", classes="market-title")
            
            # Connection status
            self.status_label = Static("Disconnected", classes="status-disconnected")
            yield self.status_label

            with Vertical(classes="market-content"):
                # Price information
                self.bid_ask_label = Static("Bid/Ask: -", classes="market-item price-info")
                yield self.bid_ask_label

                self.last_price_label = Static("Last: -", classes="market-item price-info")
                yield self.last_price_label

                self.volume_label = Static("Volume: -", classes="market-item volume-info")
                yield self.volume_label

                # Market depth section
                yield Static("Market Depth:", classes="depth-title")

                with Vertical(classes="depth-container") as depth_container:
                    self.depth_container = depth_container
                    
                    # Create 5 depth levels
                    for i in range(5):
                        depth_widget = Static(f"Level {i+1}: -", classes="depth-level")
                        self.depth_levels.append(depth_widget)
                        yield depth_widget

    def get_ui_components(self) -> dict:
        """Get references to all UI components."""
        return {
            'bid_ask_label': self.bid_ask_label,
            'last_price_label': self.last_price_label,
            'volume_label': self.volume_label,
            'depth_container': self.depth_container,
            'status_label': self.status_label,
            'depth_levels': self.depth_levels
        }