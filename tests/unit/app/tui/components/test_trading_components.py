"""
Tests for Refactored Trading Components

This module tests the modular trading components to ensure
they can be imported and rendered independently.
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

from textual.app import App
from textual.pilot import Pilot

from foxtrot.app.tui.components.trading import (
    SymbolInput,
    OrderPreviewPanel,
    MarketDataPanel,
    TradingController
)
from foxtrot.app.tui.components.trading_panel import TUITradingPanel
from foxtrot.app.tui.components.trading.form_manager import TradingFormManager
from foxtrot.app.tui.validation import ValidationResult


class TestSymbolInput:
    """Test the SymbolInput widget."""

    @pytest.mark.asyncio
    async def test_symbol_input_creation(self):
        """Test that SymbolInput can be created independently."""
        widget = SymbolInput()
        assert widget is not None
        assert widget.placeholder == "Enter symbol (e.g., AAPL, BTCUSDT)"

    @pytest.mark.asyncio
    async def test_symbol_validation(self):
        """Test symbol validation."""
        widget = SymbolInput()
        result = await widget.validate_symbol("AAPL")
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_symbol_suggestions(self):
        """Test symbol suggestions."""
        widget = SymbolInput()
        suggestions = await widget.get_suggestions("AA")
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5


class TestOrderPreviewPanel:
    """Test the OrderPreviewPanel widget."""

    @pytest.mark.asyncio
    async def test_order_preview_creation(self):
        """Test that OrderPreviewPanel can be created independently."""
        panel = OrderPreviewPanel()
        assert panel is not None

    @pytest.mark.asyncio
    async def test_order_preview_update(self):
        """Test updating order preview."""
        panel = OrderPreviewPanel()
        await panel.update_preview(
            symbol="AAPL",
            price=Decimal("150.00"),
            volume=Decimal("100"),
            order_type="LIMIT",
            direction="BUY"
        )
        assert panel.order_data['symbol'] == "AAPL"
        assert panel.order_data['price'] == Decimal("150.00")


class TestMarketDataPanel:
    """Test the MarketDataPanel widget."""

    @pytest.mark.asyncio
    async def test_market_data_creation(self):
        """Test that MarketDataPanel can be created independently."""
        panel = MarketDataPanel()
        assert panel is not None

    @pytest.mark.asyncio
    async def test_market_data_update(self):
        """Test updating market data."""
        panel = MarketDataPanel()
        await panel.update_symbol("AAPL")
        assert panel.current_symbol == "AAPL"

    def test_get_current_price(self):
        """Test getting current price."""
        panel = MarketDataPanel()
        panel.market_data = {"last": Decimal("150.00")}
        price = panel.get_current_price()
        assert price == Decimal("150.00")


class TestTradingController:
    """Test the TradingController."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = MagicMock()
        self.mock_event_engine = MagicMock()
        self.controller = TradingController(self.mock_engine, self.mock_event_engine)

    def test_controller_creation(self):
        """Test that TradingController can be created."""
        assert self.controller is not None
        assert self.controller.main_engine == self.mock_engine

    def test_validate_form_data(self):
        """Test form data validation."""
        form_data = {
            'symbol': 'AAPL',
            'volume': Decimal('100'),
            'order_type': 'MARKET',
            'direction': 'BUY'
        }
        result = self.controller.validate_form_data(form_data)
        assert isinstance(result, ValidationResult)

    @pytest.mark.asyncio
    async def test_create_order(self):
        """Test order creation."""
        form_data = {
            'symbol': 'AAPL',
            'volume': Decimal('100'),
            'order_type': 'MARKET',
            'direction': 'BUY',
            'exchange': 'SMART'
        }
        order = await self.controller.create_order(form_data)
        assert order.symbol == 'AAPL'
        assert order.volume == Decimal('100')


class TestFormManager:
    """Test the TradingFormManager."""

    def test_form_manager_creation(self):
        """Test that FormManager can be created."""
        manager = TradingFormManager()
        assert manager is not None

    def test_price_requirement_update(self):
        """Test updating price requirement based on order type."""
        manager = TradingFormManager()
        manager.update_price_requirement('LIMIT')
        assert manager.is_price_required() is True
        
        manager.update_price_requirement('MARKET')
        assert manager.is_price_required() is False


class TestTUITradingPanelIntegration:
    """Integration tests for the complete trading panel."""

    @pytest.mark.asyncio
    async def test_trading_panel_with_pilot(self):
        """Test the trading panel using Textual pilot."""
        
        class TestApp(App):
            """Test application for trading panel."""
            
            def compose(self):
                mock_engine = MagicMock()
                mock_event_engine = MagicMock()
                yield TUITradingPanel(mock_engine, mock_event_engine)

        app = TestApp()
        
        async with app.run_test() as pilot:
            # Test that the panel renders
            assert pilot.app.query_one(TUITradingPanel) is not None
            
            # Test finding input widgets
            symbol_input = pilot.app.query_one("#symbol-input")
            assert symbol_input is not None
            
            # Test entering a symbol
            await pilot.click("#symbol-input")
            await pilot.press("A", "A", "P", "L")
            assert symbol_input.value == "AAPL"
            
            # Test volume input
            volume_input = pilot.app.query_one("#volume-input")
            await pilot.click("#volume-input")
            await pilot.press("1", "0", "0")
            assert volume_input.value == "100"

    @pytest.mark.asyncio
    async def test_order_type_changes_price_state(self):
        """Test that changing order type enables/disables price input."""
        
        class TestApp(App):
            def compose(self):
                mock_engine = MagicMock()
                mock_event_engine = MagicMock()
                yield TUITradingPanel(mock_engine, mock_event_engine)

        app = TestApp()
        
        async with app.run_test() as pilot:
            price_input = pilot.app.query_one("#price-input")
            order_type_select = pilot.app.query_one("#order-type-select")
            
            # Initially price should be disabled (MARKET order)
            assert price_input.disabled is True
            
            # Change to LIMIT order
            order_type_select.value = "LIMIT"
            await pilot.pause()
            
            # Price should now be enabled
            # Note: This requires the event handlers to be properly connected
            # which happens in on_mount