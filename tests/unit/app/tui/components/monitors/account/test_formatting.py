"""
Unit tests for account monitor formatting module.

Tests data formatting, color coding, and display logic.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from foxtrot.util.object import AccountData
from foxtrot.app.tui.components.monitors.account.config import (
    AccountMonitorConfig,
    AccountDisplaySettings
)
from foxtrot.app.tui.components.monitors.account.formatting import (
    AccountDataFormatter,
    AccountRowStyler,
    AccountDisplayFormatter
)


# Note: ColorTheme and StyleSettings are handled internally by the color manager and TUI formatter
# rather than as separate classes in this implementation


class TestAccountRowStyler:
    """Test cases for AccountRowStyler class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AccountMonitorConfig)
        config.MARGIN_WARNING_THRESHOLD = 0.8
        config.BALANCE_WARNING_THRESHOLD = 1000.0
        return config
    
    @pytest.fixture
    def row_styler(self, mock_config):
        """Create row styler for testing."""
        return AccountRowStyler(mock_config)
    
    def test_styler_initialization(self, row_styler, mock_config):
        """Test row styler initialization."""
        assert row_styler.config == mock_config
        assert row_styler.color_manager is not None
    
    @pytest.mark.asyncio
    async def test_apply_row_styling(self, row_styler):
        """Test row styling application."""
        # Create mock account data
        account_data = Mock(spec=AccountData)
        account_data.balance = 5000.0
        account_data.available = 4000.0
        account_data.net_pnl = 150.0
        
        # Mock data table and display settings
        data_table = Mock()
        display_settings = Mock()
        display_settings.highlight_margin_warnings = True
        
        # Should not raise errors
        await row_styler.apply_row_styling(0, account_data, data_table, display_settings)


class TestAccountDisplayFormatter:
    """Test cases for AccountDisplayFormatter class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AccountMonitorConfig)
        config.STATISTICS_FIELDS = {
            'total_balance': {'format': 'currency'},
            'total_pnl': {'format': 'pnl'},
            'total_accounts': {'format': 'int'}
        }
        config.RISK_FIELDS = {
            'margin_ratio': {'format': 'percentage'},
            'risk_score': {'format': 'decimal_2'}
        }
        return config
    
    @pytest.fixture
    def display_formatter(self, mock_config):
        """Create display formatter for testing."""
        return AccountDisplayFormatter(mock_config)
    
    def test_display_formatter_initialization(self, display_formatter, mock_config):
        """Test display formatter initialization."""
        assert display_formatter.config == mock_config
        assert display_formatter.formatter is not None
    
    def test_format_title_bar(self, display_formatter):
        """Test title bar formatting."""
        statistics = {
            'total_balance': 25000.0,
            'total_available': 22000.0,
            'total_pnl': 1250.0
        }
        
        display_settings = Mock()
        display_settings.get_filter_summary = Mock(return_value="None")
        
        title = display_formatter.format_title_bar(statistics, display_settings)
        
        assert isinstance(title, str)
        assert "Account Monitor" in title
        assert "25,000" in title or "25000" in title
    
    def test_format_statistics_summary(self, display_formatter):
        """Test statistics summary formatting."""
        statistics = {
            'total_balance': 50000.0,
            'total_pnl': 2500.0,
            'total_accounts': 3
        }
        
        formatted = display_formatter.format_statistics_summary(statistics)
        
        assert isinstance(formatted, dict)
        assert 'total_balance' in formatted
        assert 'total_pnl' in formatted
        assert 'total_accounts' in formatted
    
    def test_format_risk_metrics(self, display_formatter):
        """Test risk metrics formatting."""
        risk_metrics = {
            'margin_ratio': 0.75,
            'risk_score': 7.25
        }
        
        formatted = display_formatter.format_risk_metrics(risk_metrics)
        
        assert isinstance(formatted, dict)
        assert 'margin_ratio' in formatted
        assert 'risk_score' in formatted


class TestAccountDataFormatter:
    """Test cases for AccountDataFormatter class."""
    
    @pytest.fixture
    def sample_account_data(self):
        """Sample account data for testing."""
        return AccountData(
            vt_accountid="TEST.USD",
            balance=10000.50,
            available=8500.25,
            frozen=1500.25,
            net_pnl=250.75,
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime(2023, 12, 1, 10, 30, 0)
        )
    
    @pytest.fixture
    def formatter(self):
        """Create formatter for testing."""
        return AccountDataFormatter()
    
    def test_formatter_initialization(self, formatter):
        """Test formatter initialization."""
        assert formatter.color_manager is not None
        assert formatter.config is not None
    
    def test_format_cell_content_currency(self, formatter):
        """Test currency cell formatting."""
        currency_config = {'cell': 'currency', 'precision': 2, 'width': 20}
        
        # Test positive amount
        result = formatter.format_cell_content(1234.567, currency_config)
        assert "1,234.57" in result or "1234.57" in result
        
        # Test negative amount
        result = formatter.format_cell_content(-567.89, currency_config)
        assert "-567.89" in result or "(567.89)" in result
        
        # Test zero
        result = formatter.format_cell_content(0.0, currency_config)
        assert "0.00" in result
    
    def test_format_cell_content_pnl(self, formatter):
        """Test P&L cell formatting."""
        pnl_config = {'cell': 'pnl', 'precision': 2, 'width': 20}
        
        # Test positive P&L
        result = formatter.format_cell_content(150.25, pnl_config)
        assert "150.25" in result
        
        # Test negative P&L  
        result = formatter.format_cell_content(-75.50, pnl_config)
        assert "-75.50" in result
        
        # Test zero P&L
        result = formatter.format_cell_content(0.0, pnl_config)
        assert "0.00" in result
    
    def test_format_cell_content_percentage(self, formatter):
        """Test percentage cell formatting."""
        pct_config = {'cell': 'percentage', 'precision': 2, 'width': 20}
        
        # Test positive percentage
        result = formatter.format_cell_content(0.1234, pct_config)
        assert "12.34%" in result
        
        # Test negative percentage
        result = formatter.format_cell_content(-0.0567, pct_config)
        assert "-5.67%" in result
        
        # Test zero percentage
        result = formatter.format_cell_content(0.0, pct_config)
        assert "-" in result  # Zero percentages return "-"
    
    def test_format_cell_content_datetime(self, formatter):
        """Test datetime cell formatting."""
        datetime_config = {'cell': 'datetime', 'width': 20}
        
        test_datetime = datetime(2023, 12, 1, 14, 30, 45)
        result = formatter.format_cell_content(test_datetime, datetime_config)
        
        # Should contain date and time components
        assert "2023" in result or "23" in result
        assert "12" in result
        assert "01" in result or "1" in result
    
    def test_format_cell_content_default(self, formatter):
        """Test default cell formatting."""
        default_config = {'cell': 'default', 'width': 10}
        
        # Test text
        result = formatter.format_cell_content("USD", default_config)
        assert result == "USD"
        
        # Test long text truncation
        long_text = "This is a very long text that should be truncated"
        result = formatter.format_cell_content(long_text, default_config)
        assert len(result) <= 10
    
    def test_handle_none_values(self, formatter):
        """Test handling of None/null values."""
        config = {'cell': 'currency', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content(None, config)
        assert result == "-"
        
        config = {'cell': 'default', 'width': 20}
        result = formatter.format_cell_content(None, config)
        assert result == "-"
    
    def test_precision_handling(self, formatter):
        """Test decimal precision handling."""
        # Test different precision levels
        config = {'cell': 'currency', 'precision': 0, 'width': 20}
        result = formatter.format_cell_content(1234.567, config)
        assert ".567" not in result  # Should be rounded to 0 decimals
        
        config = {'cell': 'currency', 'precision': 4, 'width': 20}
        result = formatter.format_cell_content(1234.5678, config)
        assert "1234.5678" in result or "1,234.5678" in result
    
    def test_error_handling(self, formatter):
        """Test error handling in formatting."""
        # Invalid config should not crash
        invalid_config = {'invalid': 'config'}
        result = formatter.format_cell_content("test", invalid_config)
        assert isinstance(result, str)
        
        # Should handle conversion errors gracefully
        config = {'cell': 'currency', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content("invalid_number", config)
        assert isinstance(result, str)


class TestFormatterIntegration:
    """Integration tests for formatter with real data."""
    
    def test_format_realistic_values(self):
        """Test formatting with realistic account values."""
        formatter = AccountDataFormatter()
        
        # Test realistic currency amounts
        large_balance_config = {'cell': 'currency', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content(25750.80, large_balance_config)
        assert "25,750" in result or "25750" in result
        
        # Test negative P&L formatting
        pnl_config = {'cell': 'pnl', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content(-125.75, pnl_config)
        assert "-125.75" in result
        
        # Test small percentage values
        pct_config = {'cell': 'percentage', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content(0.0234, pct_config)
        assert "2.34%" in result
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        formatter = AccountDataFormatter()
        
        # Test very large numbers
        config = {'cell': 'currency', 'precision': 2, 'width': 20}
        result = formatter.format_cell_content(1000000000.50, config)  # 1 billion
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Test very small numbers
        result = formatter.format_cell_content(0.01, config)
        assert "0.01" in result
        
        # Test empty string input for text
        text_config = {'cell': 'default', 'width': 20}
        result = formatter.format_cell_content("", text_config)
        assert result == ""
        
        # Test boolean values
        result = formatter.format_cell_content(True, text_config)
        assert result == "True"