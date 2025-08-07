"""
Unit tests for account monitor configuration module.

Tests configuration management, validation, and display settings.
"""

import pytest
from foxtrot.app.tui.components.monitors.account.config import (
    AccountMonitorConfig, 
    AccountDisplaySettings
)


class TestAccountMonitorConfig:
    """Test cases for AccountMonitorConfig class."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = AccountMonitorConfig()
        
        # Test essential configuration values
        assert hasattr(config, 'EVENT_TYPE')
        assert hasattr(config, 'DATA_KEY')
        assert hasattr(config, 'MONITOR_NAME')
        assert hasattr(config, 'HEADERS')
        assert hasattr(config, 'STATISTICS_FIELDS')
        
        # Test threshold values
        assert config.MARGIN_WARNING_THRESHOLD > 0
        assert config.BALANCE_WARNING_THRESHOLD > 0
        assert config.PNL_WARNING_THRESHOLD < 0  # Should be negative for loss threshold
    
    def test_headers_configuration(self):
        """Test headers configuration structure."""
        config = AccountMonitorConfig()
        headers = config.HEADERS
        
        # Verify headers structure
        assert isinstance(headers, dict)
        assert len(headers) > 0
        
        # Check essential fields exist
        required_fields = ['vt_accountid', 'currency', 'balance', 'available']
        for field in required_fields:
            assert field in headers, f"Required field {field} missing from headers"
        
        # Check header configuration structure
        for field_name, field_config in headers.items():
            assert 'display' in field_config
            assert 'cell' in field_config
            assert isinstance(field_config['display'], str)
    
    def test_statistics_fields_configuration(self):
        """Test statistics fields configuration."""
        config = AccountMonitorConfig()
        stats_fields = config.STATISTICS_FIELDS
        
        assert isinstance(stats_fields, dict)
        assert len(stats_fields) > 0
        
        # Check essential statistics fields
        required_stats = ['total_accounts', 'total_balance', 'total_pnl']
        for field in required_stats:
            assert field in stats_fields, f"Required stat field {field} missing"
    
    def test_update_from_dict(self):
        """Test configuration updates from dictionary."""
        config = AccountMonitorConfig()
        original_threshold = config.MARGIN_WARNING_THRESHOLD
        
        # Update configuration
        updates = {'MARGIN_WARNING_THRESHOLD': 0.9}
        config.update_from_dict(updates)
        
        assert config.MARGIN_WARNING_THRESHOLD == 0.9
        assert config.MARGIN_WARNING_THRESHOLD != original_threshold
    
    def test_get_field_config(self):
        """Test getting field configuration."""
        config = AccountMonitorConfig()
        
        # Test existing field
        balance_config = config.get_field_config('balance')
        assert balance_config is not None
        assert 'display' in balance_config
        
        # Test non-existing field
        invalid_config = config.get_field_config('nonexistent_field')
        assert invalid_config is None
    
    def test_validation(self):
        """Test configuration validation."""
        config = AccountMonitorConfig()
        
        # Test valid configuration
        assert config.validate() == True
        
        # Test invalid configuration
        config.MARGIN_WARNING_THRESHOLD = -1  # Invalid negative threshold
        assert config.validate() == False


class TestAccountDisplaySettings:
    """Test cases for AccountDisplaySettings class."""
    
    def test_default_settings(self):
        """Test default display settings."""
        settings = AccountDisplaySettings()
        
        # Test boolean settings
        assert isinstance(settings.show_zero_balances, bool)
        assert isinstance(settings.group_by_currency, bool)
        assert isinstance(settings.show_percentage_changes, bool)
        assert isinstance(settings.highlight_margin_warnings, bool)
        assert isinstance(settings.auto_scroll_to_updates, bool)
        
        # Test filter settings
        assert settings.currency_filter is None or isinstance(settings.currency_filter, str)
        assert settings.gateway_filter is None or isinstance(settings.gateway_filter, str)
        assert settings.min_balance_filter is None or isinstance(settings.min_balance_filter, float)
    
    def test_currency_filter_setting(self):
        """Test currency filter setting."""
        settings = AccountDisplaySettings()
        
        # Test setting currency filter
        settings.set_currency_filter("USD")
        assert settings.currency_filter == "USD"
        
        # Test clearing currency filter
        settings.set_currency_filter(None)
        assert settings.currency_filter is None
    
    def test_gateway_filter_setting(self):
        """Test gateway filter setting."""
        settings = AccountDisplaySettings()
        
        # Test setting gateway filter
        settings.set_gateway_filter("BINANCE")
        assert settings.gateway_filter == "BINANCE"
        
        # Test clearing gateway filter
        settings.set_gateway_filter(None)
        assert settings.gateway_filter is None
    
    def test_min_balance_filter_setting(self):
        """Test minimum balance filter setting."""
        settings = AccountDisplaySettings()
        
        # Test setting min balance filter
        settings.set_min_balance_filter(1000.0)
        assert settings.min_balance_filter == 1000.0
        
        # Test clearing min balance filter
        settings.set_min_balance_filter(None)
        assert settings.min_balance_filter is None
    
    def test_filter_summary(self):
        """Test filter summary generation."""
        settings = AccountDisplaySettings()
        
        # Test empty filters
        summary = settings.get_filter_summary()
        assert "None" in summary or "No filters" in summary
        
        # Test with filters applied
        settings.set_currency_filter("USD")
        settings.set_min_balance_filter(500.0)
        summary = settings.get_filter_summary()
        
        assert "USD" in summary
        assert "500" in summary
    
    def test_reset_filters(self):
        """Test resetting all filters."""
        settings = AccountDisplaySettings()
        
        # Apply some filters
        settings.set_currency_filter("EUR")
        settings.set_gateway_filter("INTERACTIVE")
        settings.set_min_balance_filter(1000.0)
        
        # Reset filters
        settings.reset_filters()
        
        # Verify all filters are cleared
        assert settings.currency_filter is None
        assert settings.gateway_filter is None
        assert settings.min_balance_filter is None
    
    def test_copy_settings(self):
        """Test copying display settings."""
        original = AccountDisplaySettings()
        original.show_zero_balances = False
        original.set_currency_filter("JPY")
        
        # Copy settings
        copy = original.copy()
        
        # Verify copy has same values
        assert copy.show_zero_balances == original.show_zero_balances
        assert copy.currency_filter == original.currency_filter
        
        # Verify they are separate objects
        assert copy is not original
        
        # Verify modifying copy doesn't affect original
        copy.show_zero_balances = True
        assert original.show_zero_balances == False
    
    def test_to_dict_from_dict(self):
        """Test serialization to/from dictionary."""
        settings = AccountDisplaySettings()
        settings.show_zero_balances = False
        settings.set_currency_filter("GBP")
        settings.set_min_balance_filter(250.0)
        
        # Convert to dictionary
        settings_dict = settings.to_dict()
        
        # Verify dictionary structure
        assert isinstance(settings_dict, dict)
        assert 'show_zero_balances' in settings_dict
        assert 'currency_filter' in settings_dict
        assert 'min_balance_filter' in settings_dict
        
        # Create new settings from dictionary
        new_settings = AccountDisplaySettings.from_dict(settings_dict)
        
        # Verify values match
        assert new_settings.show_zero_balances == settings.show_zero_balances
        assert new_settings.currency_filter == settings.currency_filter
        assert new_settings.min_balance_filter == settings.min_balance_filter


@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return AccountMonitorConfig()


@pytest.fixture
def sample_display_settings():
    """Provide sample display settings for tests."""
    return AccountDisplaySettings()


# Integration tests
class TestConfigIntegration:
    """Integration tests for configuration components."""
    
    def test_config_with_display_settings(self, sample_config, sample_display_settings):
        """Test configuration working with display settings."""
        # Test that config and settings work together
        field_config = sample_config.get_field_config('balance')
        assert field_config is not None
        
        # Test display settings filters
        sample_display_settings.set_currency_filter("USD")
        assert sample_display_settings.currency_filter == "USD"
        
        # Verify they can coexist
        assert sample_config.validate()
        assert sample_display_settings.get_filter_summary() is not None