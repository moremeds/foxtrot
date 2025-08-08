"""
Unit tests for modular trading components.

Tests the split trading components to ensure they maintain the same
functionality as the original monolithic trading_panel.py while
providing better modularity and testability.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

# Import our new modular components
from foxtrot.app.tui.components.trading.common import (
    OrderAction,
    TradingConstants, 
    TradingFormData,
    format_order_impact,
    get_symbol_suggestions
)

from foxtrot.app.tui.components.trading.input_widgets import (
    SymbolInput,
    PriceInput,
    VolumeInput
)

from foxtrot.app.tui.components.trading.order_preview import OrderPreviewPanel
from foxtrot.app.tui.components.trading.market_data_panel import MarketDataPanel


class TestTradingConstants:
    """Test trading constants and utilities."""
    
    def test_trading_constants_values(self):
        """Test that trading constants have expected values."""
        assert TradingConstants.DEFAULT_ORDER_TYPE == "MARKET"
        assert TradingConstants.DEFAULT_DIRECTION == "BUY"
        assert TradingConstants.MAX_PRICE == 1000000.0
        assert TradingConstants.MIN_PRICE == 0.0
        assert len(TradingConstants.MOCK_SYMBOLS) > 0
    
    def test_format_order_impact(self):
        """Test order impact formatting."""
        volume = Decimal("100")
        
        buy_impact = format_order_impact(volume, "BUY")
        sell_impact = format_order_impact(volume, "SELL")
        
        assert "increase" in buy_impact
        assert "100" in buy_impact
        assert "decrease" in sell_impact
        assert "100" in sell_impact
    
    def test_get_symbol_suggestions(self):
        """Test symbol suggestions functionality."""
        # Test with valid partial
        suggestions = get_symbol_suggestions("A", max_results=3)
        assert len(suggestions) <= 3
        assert all(s.startswith("A") for s in suggestions)
        
        # Test with short partial
        short_suggestions = get_symbol_suggestions("A")
        assert len(short_suggestions) <= 5
        
        # Test with empty partial
        empty_suggestions = get_symbol_suggestions("")
        assert len(empty_suggestions) == 0


class TestTradingFormData:
    """Test trading form data container."""
    
    def test_tradingformdata_initialization(self):
        """Test TradingFormData initialization with defaults."""
        form_data = TradingFormData()
        
        assert form_data.symbol == ""
        assert form_data.exchange == ""
        assert form_data.direction == TradingConstants.DEFAULT_DIRECTION
        assert form_data.order_type == TradingConstants.DEFAULT_ORDER_TYPE
        assert form_data.price is None
        assert form_data.volume is None
    
    def test_tradingformdata_custom_values(self):
        """Test TradingFormData with custom values."""
        price = Decimal("150.00")
        volume = Decimal("100")
        
        form_data = TradingFormData(
            symbol="AAPL",
            exchange="NASDAQ",
            direction="SELL",
            order_type="LIMIT",
            price=price,
            volume=volume
        )
        
        assert form_data.symbol == "AAPL"
        assert form_data.exchange == "NASDAQ"
        assert form_data.direction == "SELL"
        assert form_data.order_type == "LIMIT"
        assert form_data.price == price
        assert form_data.volume == volume
    
    def test_tradingformdata_dict_conversion(self):
        """Test conversion to/from dictionary."""
        original_data = {
            "symbol": "TSLA",
            "exchange": "NASDAQ",
            "direction": "BUY",
            "order_type": "MARKET",
            "price": Decimal("200.00"),
            "volume": Decimal("50")
        }
        
        # Test from_dict
        form_data = TradingFormData.from_dict(original_data)
        assert form_data.symbol == "TSLA"
        assert form_data.price == Decimal("200.00")
        
        # Test to_dict
        dict_data = form_data.to_dict()
        assert dict_data["symbol"] == "TSLA"
        assert dict_data["price"] == Decimal("200.00")


class TestSymbolInput:
    """Test enhanced symbol input widget."""
    
    def test_symbolinput_initialization(self):
        """Test SymbolInput initialization."""
        symbol_input = SymbolInput()
        
        assert symbol_input.contract_manager is None
        assert symbol_input.validator is not None
        assert symbol_input.suggestions == []
        assert symbol_input.last_validation_result is None
    
    @pytest.mark.asyncio
    async def test_symbolinput_validation(self):
        """Test symbol validation functionality."""
        symbol_input = SymbolInput()
        
        # Mock the validator to return a known result
        mock_result = Mock()
        mock_result.is_valid = True
        mock_result.errors = []
        
        symbol_input.validator.validate = Mock(return_value=mock_result)
        
        result = await symbol_input.validate_symbol("AAPL")
        
        assert result.is_valid is True
        assert result.errors == []
        assert symbol_input.last_validation_result == mock_result
    
    @pytest.mark.asyncio
    async def test_symbolinput_validation_error(self):
        """Test symbol validation with errors."""
        symbol_input = SymbolInput()
        
        # Mock the validator to raise an exception
        symbol_input.validator.validate = Mock(side_effect=ValueError("Test error"))
        
        result = await symbol_input.validate_symbol("INVALID")
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "Test error" in str(result.errors[0])
    
    @pytest.mark.asyncio 
    @pytest.mark.asyncio
    async def test_symbolinput_suggestions(self):
        """Test symbol suggestions functionality."""
        symbol_input = SymbolInput()
        
        suggestions = await symbol_input.get_suggestions("AAP")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5
        
        # Test with short input
        short_suggestions = await symbol_input.get_suggestions("A")
        assert len(short_suggestions) <= 5
        
        # Test with empty input
        empty_suggestions = await symbol_input.get_suggestions("")
        assert len(empty_suggestions) == 0
    
    def test_symbolinput_has_valid_value(self):
        """Test has_valid_value method."""
        symbol_input = SymbolInput()
        
        # No validation result yet
        assert symbol_input.has_valid_value() is False
        
        # Mock valid result
        mock_valid_result = Mock()
        mock_valid_result.is_valid = True
        symbol_input._last_validation_result = mock_valid_result
        
        assert symbol_input.has_valid_value() is True
        
        # Mock invalid result
        mock_invalid_result = Mock()
        mock_invalid_result.is_valid = False
        symbol_input._last_validation_result = mock_invalid_result
        
        assert symbol_input.has_valid_value() is False


class TestOrderPreviewPanel:
    """Test order preview panel functionality."""
    
    def test_orderpreviewpanel_initialization(self):
        """Test OrderPreviewPanel initialization."""
        preview_panel = OrderPreviewPanel()
        
        assert preview_panel.order_data == {}
        assert preview_panel.market_data == {}
        assert preview_panel.settings is not None
        assert preview_panel._last_calculation_error is None
    
    @pytest.mark.asyncio
    async def test_orderpreviewpanel_update_preview(self):
        """Test order preview update functionality."""
        preview_panel = OrderPreviewPanel()
        
        # Mock the calculation method to avoid complex dependencies
        preview_panel._calculate_and_display_preview = AsyncMock()
        
        await preview_panel.update_preview(
            symbol="AAPL",
            price=Decimal("150.00"),
            volume=Decimal("100"),
            order_type="LIMIT",
            direction="BUY"
        )
        
        # Verify order data was stored
        assert preview_panel.order_data["symbol"] == "AAPL"
        assert preview_panel.order_data["price"] == Decimal("150.00")
        assert preview_panel.order_data["volume"] == Decimal("100")
        assert preview_panel.order_data["order_type"] == "LIMIT"
        assert preview_panel.order_data["direction"] == "BUY"
        
        # Verify calculation was called
        preview_panel._calculate_and_display_preview.assert_called_once()
    
    def test_orderpreviewpanel_has_required_data(self):
        """Test required data validation."""
        preview_panel = OrderPreviewPanel()
        
        # No data
        preview_panel.order_data = {}
        assert preview_panel._has_required_data() is False
        
        # Missing volume
        preview_panel.order_data = {"symbol": "AAPL"}
        assert preview_panel._has_required_data() is False
        
        # Missing symbol
        preview_panel.order_data = {"volume": Decimal("100")}
        assert preview_panel._has_required_data() is False
        
        # Valid data
        preview_panel.order_data = {
            "symbol": "AAPL",
            "volume": Decimal("100")
        }
        assert preview_panel._has_required_data() is True
    
    @pytest.mark.asyncio
    async def test_orderpreviewpanel_get_effective_price(self):
        """Test effective price calculation."""
        preview_panel = OrderPreviewPanel()
        
        # Mock market price method
        preview_panel._get_market_price = AsyncMock(return_value=Decimal("150.00"))
        
        # Test with limit order and specified price
        price = await preview_panel._get_effective_price(Decimal("155.00"), "LIMIT")
        assert price == Decimal("155.00")
        
        # Test with market order (should use market price)
        price = await preview_panel._get_effective_price(None, "MARKET")
        assert price == Decimal("150.00")
        
        # Test with no price specified (should use market price)
        price = await preview_panel._get_effective_price(None, "LIMIT")
        assert price == Decimal("150.00")


class TestMarketDataPanel:
    """Test market data panel functionality."""
    
    def test_marketdatapanel_initialization(self):
        """Test MarketDataPanel initialization."""
        market_panel = MarketDataPanel()
        
        assert market_panel.current_symbol is None
        assert market_panel.market_data == {}
        assert len(market_panel.depth_levels) == 0  # Will be populated on compose
        assert market_panel._last_error is None
    
    @pytest.mark.asyncio
    async def test_marketdatapanel_update_symbol(self):
        """Test symbol update functionality."""
        market_panel = MarketDataPanel()
        
        # Mock methods to avoid complex dependencies
        market_panel._clear_market_data = Mock()
        market_panel._update_status = Mock()
        market_panel._fetch_and_display_market_data = AsyncMock()
        
        await market_panel.update_symbol("AAPL")
        
        assert market_panel.current_symbol == "AAPL"
        market_panel._clear_market_data.assert_called_once()
        market_panel._update_status.assert_called_with("Fetching data...")
        market_panel._fetch_and_display_market_data.assert_called_once()
    
    def test_marketdatapanel_validate_market_data(self):
        """Test market data validation."""
        market_panel = MarketDataPanel()
        
        # Valid data
        valid_data = {
            "symbol": "AAPL",
            "bid": Decimal("149.95"),
            "ask": Decimal("150.05"),
            "last": Decimal("150.00"),
            "volume": 1000000
        }
        assert market_panel._validate_market_data(valid_data) is True
        
        # Missing required field
        invalid_data = {
            "symbol": "AAPL",
            "bid": Decimal("149.95")
            # Missing ask, last, volume
        }
        assert market_panel._validate_market_data(invalid_data) is False
        
        # Invalid price relationship (bid >= ask)
        invalid_prices = {
            "symbol": "AAPL", 
            "bid": Decimal("150.05"),
            "ask": Decimal("149.95"),  # ask < bid (invalid)
            "last": Decimal("150.00"),
            "volume": 1000000
        }
        assert market_panel._validate_market_data(invalid_prices) is False
    
    def test_marketdatapanel_mock_depth_generation(self):
        """Test mock market depth generation."""
        market_panel = MarketDataPanel()
        
        depth = market_panel._generate_mock_depth()
        
        assert "bids" in depth
        assert "asks" in depth
        assert len(depth["bids"]) == 5
        assert len(depth["asks"]) == 5
        
        # Test bid prices are descending
        bid_prices = [level["price"] for level in depth["bids"]]
        assert bid_prices == sorted(bid_prices, reverse=True)
        
        # Test ask prices are ascending  
        ask_prices = [level["price"] for level in depth["asks"]]
        assert ask_prices == sorted(ask_prices)
    
    def test_marketdatapanel_utility_methods(self):
        """Test utility methods."""
        market_panel = MarketDataPanel()
        
        # Test get_current_symbol
        market_panel.current_symbol = "TSLA"
        assert market_panel.get_current_symbol() == "TSLA"
        
        # Test get_last_error
        market_panel._last_error = "Test error"
        assert market_panel.get_last_error() == "Test error"
        
        # Test has_valid_data
        market_panel.market_data = {"symbol": "AAPL"}
        market_panel._last_error = None
        assert market_panel.has_valid_data() is True
        
        market_panel._last_error = "Error occurred"
        assert market_panel.has_valid_data() is False


class TestComponentIntegration:
    """Test integration between components."""
    
    @pytest.mark.asyncio
    async def test_components_work_together(self):
        """Test that components can work together as intended."""
        # Create components
        symbol_input = SymbolInput()
        preview_panel = OrderPreviewPanel()
        market_panel = MarketDataPanel()
        
        # Mock dependencies to avoid complex setup
        symbol_input.validate_symbol = AsyncMock()
        symbol_input.validate_symbol.return_value = Mock(is_valid=True, errors=[])
        
        preview_panel._calculate_and_display_preview = AsyncMock()
        market_panel._fetch_and_display_market_data = AsyncMock()
        
        # Test workflow: validate symbol -> update preview -> update market data
        validation_result = await symbol_input.validate_symbol("AAPL")
        assert validation_result.is_valid
        
        await preview_panel.update_preview(
            symbol="AAPL",
            price=Decimal("150.00"),
            volume=Decimal("100")
        )
        assert preview_panel.order_data["symbol"] == "AAPL"
        
        await market_panel.update_symbol("AAPL") 
        assert market_panel.current_symbol == "AAPL"


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.confirm_orders = True
    return settings


@pytest.fixture  
def mock_event_engine():
    """Mock event engine for testing."""
    return Mock()


@pytest.fixture
def mock_main_engine():
    """Mock main engine for testing."""
    engine = Mock()
    engine.get_account = Mock(return_value=None)
    return engine


class TestBackwardCompatibility:
    """Test that the new modular structure maintains backward compatibility."""
    
    def test_imports_work(self):
        """Test that all expected components can be imported."""
        # Test that we can import from the package
        from foxtrot.app.tui.components.trading import (
            SymbolInput,
            OrderPreviewPanel, 
            MarketDataPanel,
            TradingConstants
        )
        
        # Test that classes can be instantiated
        symbol_input = SymbolInput()
        preview_panel = OrderPreviewPanel()
        market_panel = MarketDataPanel()
        
        assert symbol_input is not None
        assert preview_panel is not None  
        assert market_panel is not None
        assert TradingConstants.DEFAULT_ORDER_TYPE == "MARKET"
    
    def test_component_interfaces(self):
        """Test that components maintain expected interfaces."""
        symbol_input = SymbolInput()
        preview_panel = OrderPreviewPanel()
        market_panel = MarketDataPanel()
        
        # Test SymbolInput interface
        assert hasattr(symbol_input, 'validate_symbol')
        assert hasattr(symbol_input, 'get_suggestions')
        assert hasattr(symbol_input, 'has_valid_value')
        
        # Test OrderPreviewPanel interface
        assert hasattr(preview_panel, 'update_preview')
        assert hasattr(preview_panel, 'get_last_calculation_error')
        
        # Test MarketDataPanel interface
        assert hasattr(market_panel, 'update_symbol')
        assert hasattr(market_panel, 'get_current_symbol')
        assert hasattr(market_panel, 'has_valid_data')