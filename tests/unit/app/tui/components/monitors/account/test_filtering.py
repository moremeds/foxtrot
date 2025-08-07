"""
Unit tests for account monitor filtering module.

Tests filter management, validation, and application logic.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime
from foxtrot.util.object import AccountData
from foxtrot.app.tui.components.monitors.account.config import (
    AccountMonitorConfig,
    AccountDisplaySettings
)
from foxtrot.app.tui.components.monitors.account.filtering import (
    AccountFilter,
    CurrencyFilter,
    GatewayFilter,
    AccountFilterManager
)


class TestAccountFilter:
    """Test cases for base AccountFilter class."""
    
    def test_filter_initialization(self):
        """Test basic filter initialization."""
        filter_obj = AccountFilter(name="test_filter", active=True)
        
        assert filter_obj.name == "test_filter"
        assert filter_obj.active == True
        assert filter_obj.created_at is not None
        assert isinstance(filter_obj.created_at, datetime)
    
    def test_filter_activation(self):
        """Test filter activation/deactivation."""
        filter_obj = AccountFilter(name="test_filter", active=False)
        
        # Test activation
        filter_obj.activate()
        assert filter_obj.active == True
        
        # Test deactivation
        filter_obj.deactivate()
        assert filter_obj.active == False
    
    def test_base_apply_method(self):
        """Test that base apply method raises NotImplementedError."""
        filter_obj = AccountFilter(name="test_filter")
        account_data = Mock(spec=AccountData)
        
        with pytest.raises(NotImplementedError):
            filter_obj.apply(account_data)


class TestCurrencyFilter:
    """Test cases for CurrencyFilter class."""
    
    def test_currency_filter_initialization(self):
        """Test currency filter initialization."""
        currency_filter = CurrencyFilter(currency="USD")
        
        assert currency_filter.name == "currency_USD"
        assert currency_filter.currency == "USD"
        assert currency_filter.active == True
    
    def test_currency_filter_apply(self):
        """Test currency filter application."""
        currency_filter = CurrencyFilter(currency="USD")
        
        # Create test account data
        usd_account = Mock(spec=AccountData)
        usd_account.currency = "USD"
        
        eur_account = Mock(spec=AccountData)
        eur_account.currency = "EUR"
        
        # Test filter application
        assert currency_filter.apply(usd_account) == True
        assert currency_filter.apply(eur_account) == False
    
    def test_currency_filter_case_insensitive(self):
        """Test currency filter case insensitivity."""
        currency_filter = CurrencyFilter(currency="usd")  # lowercase
        
        usd_account = Mock(spec=AccountData)
        usd_account.currency = "USD"  # uppercase
        
        assert currency_filter.apply(usd_account) == True
    
    def test_currency_filter_inactive(self):
        """Test inactive currency filter."""
        currency_filter = CurrencyFilter(currency="USD", active=False)
        
        eur_account = Mock(spec=AccountData)
        eur_account.currency = "EUR"
        
        # Inactive filter should pass all accounts
        assert currency_filter.apply(eur_account) == True


class TestGatewayFilter:
    """Test cases for GatewayFilter class."""
    
    def test_gateway_filter_initialization(self):
        """Test gateway filter initialization."""
        gateway_filter = GatewayFilter(gateway="BINANCE")
        
        assert gateway_filter.name == "gateway_BINANCE"
        assert gateway_filter.gateway == "BINANCE"
    
    def test_gateway_filter_apply(self):
        """Test gateway filter application."""
        gateway_filter = GatewayFilter(gateway="BINANCE")
        
        binance_account = Mock(spec=AccountData)
        binance_account.gateway_name = "BINANCE"
        
        ib_account = Mock(spec=AccountData)
        ib_account.gateway_name = "INTERACTIVE_BROKERS"
        
        assert gateway_filter.apply(binance_account) == True
        assert gateway_filter.apply(ib_account) == False


# Note: BalanceFilter and MarginFilter are handled within AccountFilterManager
# rather than as separate classes in this implementation


class TestAccountFilterManager:
    """Test cases for AccountFilterManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AccountMonitorConfig)
        return config
    
    @pytest.fixture
    def mock_display_settings(self):
        """Mock display settings for testing."""
        settings = Mock(spec=AccountDisplaySettings)
        settings.show_zero_balances = True
        settings.currency_filter = None
        settings.gateway_filter = None
        settings.min_balance_filter = None
        return settings
    
    @pytest.fixture
    def filter_manager(self, mock_display_settings):
        """Create filter manager for testing."""
        return AccountFilterManager(mock_display_settings)
    
    def test_filter_manager_initialization(self, filter_manager):
        """Test filter manager initialization."""
        assert filter_manager.display_settings is not None
        assert isinstance(filter_manager.active_filters, list)
        assert len(filter_manager.active_filters) == 0
    
    def test_add_currency_filter(self, filter_manager, mock_display_settings):
        """Test adding currency filter."""
        # Add currency filter
        filter_manager.add_currency_filter("USD")
        
        assert len(filter_manager.active_filters) == 1
        assert mock_display_settings.currency_filter == "USD"
        
        # Verify filter type
        currency_filter = filter_manager.active_filters[0]
        assert isinstance(currency_filter, CurrencyFilter)
        assert currency_filter.currency == "USD"
    
    def test_add_gateway_filter(self, filter_manager, mock_display_settings):
        """Test adding gateway filter."""
        filter_manager.add_gateway_filter("BINANCE")
        
        assert len(filter_manager.active_filters) == 1
        assert mock_display_settings.gateway_filter == "BINANCE"
        
        gateway_filter = filter_manager.active_filters[0]
        assert isinstance(gateway_filter, GatewayFilter)
        assert gateway_filter.gateway == "BINANCE"
    
    def test_add_min_balance_filter(self, filter_manager, mock_display_settings):
        """Test adding minimum balance filter."""
        filter_manager.add_min_balance_filter(1000.0)
        
        assert len(filter_manager.active_filters) == 1
        assert mock_display_settings.min_balance_filter == 1000.0
        
        balance_filter = filter_manager.active_filters[0]
        assert hasattr(balance_filter, 'min_balance')  # MinBalanceFilter created internally
        assert balance_filter.min_balance == 1000.0
    
    def test_add_margin_filter(self, filter_manager):
        """Test adding margin filter."""
        filter_manager.add_margin_filter(50.0)
        
        assert len(filter_manager.active_filters) == 1
        
        margin_filter = filter_manager.active_filters[0]
        assert hasattr(margin_filter, 'min_margin')  # MarginAccountFilter created internally
        assert margin_filter.min_margin == 50.0
    
    def test_remove_filter(self, filter_manager):
        """Test removing specific filter."""
        # Add multiple filters
        filter_manager.add_currency_filter("USD")
        filter_manager.add_gateway_filter("BINANCE")
        
        assert len(filter_manager.active_filters) == 2
        
        # Remove currency filter
        filter_manager.remove_filter("currency_USD")
        
        assert len(filter_manager.active_filters) == 1
        assert filter_manager.active_filters[0].name == "gateway_BINANCE"
    
    def test_clear_all_filters(self, filter_manager, mock_display_settings):
        """Test clearing all filters."""
        # Add multiple filters
        filter_manager.add_currency_filter("EUR")
        filter_manager.add_min_balance_filter(500.0)
        
        assert len(filter_manager.active_filters) == 2
        
        # Clear all filters
        filter_manager.clear_all_filters()
        
        assert len(filter_manager.active_filters) == 0
        assert mock_display_settings.currency_filter is None
        assert mock_display_settings.min_balance_filter is None
    
    def test_apply_all_filters(self, filter_manager):
        """Test applying all active filters to account data."""
        # Add filters
        filter_manager.add_currency_filter("USD")
        filter_manager.add_min_balance_filter(1000.0)
        
        # Test account that passes all filters
        passing_account = Mock(spec=AccountData)
        passing_account.currency = "USD"
        passing_account.balance = 2000.0
        
        # Test account that fails currency filter
        failing_currency = Mock(spec=AccountData)
        failing_currency.currency = "EUR"
        failing_currency.balance = 2000.0
        
        # Test account that fails balance filter
        failing_balance = Mock(spec=AccountData)
        failing_balance.currency = "USD"
        failing_balance.balance = 500.0
        
        assert filter_manager.apply_all_filters(passing_account) == True
        assert filter_manager.apply_all_filters(failing_currency) == False
        assert filter_manager.apply_all_filters(failing_balance) == False
    
    def test_zero_balance_visibility(self, filter_manager, mock_display_settings):
        """Test zero balance visibility setting."""
        # Create zero balance account
        zero_account = Mock(spec=AccountData)
        zero_account.balance = 0.0
        zero_account.currency = "USD"
        
        # Test showing zero balances (default)
        mock_display_settings.show_zero_balances = True
        filter_manager.set_zero_balance_visibility(True)
        assert filter_manager.apply_all_filters(zero_account) == True
        
        # Test hiding zero balances
        mock_display_settings.show_zero_balances = False
        filter_manager.set_zero_balance_visibility(False)
        assert filter_manager.apply_all_filters(zero_account) == False
    
    def test_filter_caching(self, filter_manager):
        """Test filter result caching."""
        # Add a filter
        filter_manager.add_currency_filter("USD")
        
        # Create test account
        test_account = Mock(spec=AccountData)
        test_account.currency = "USD"
        test_account.vt_accountid = "TEST.USD"
        
        # First call should compute result
        result1 = filter_manager.apply_all_filters(test_account)
        
        # Second call should use cached result
        result2 = filter_manager.apply_all_filters(test_account)
        
        assert result1 == result2 == True
        
        # Verify cache was used (check internal cache if accessible)
        if hasattr(filter_manager, '_filter_cache'):
            assert len(filter_manager._filter_cache) > 0
    
    def test_get_active_filter_summary(self, filter_manager):
        """Test getting summary of active filters."""
        # No filters initially
        summary = filter_manager.get_active_filter_summary()
        assert "No active filters" in summary or summary == ""
        
        # Add filters
        filter_manager.add_currency_filter("USD")
        filter_manager.add_min_balance_filter(1000.0)
        
        summary = filter_manager.get_active_filter_summary()
        assert "USD" in summary
        assert "1000" in summary or "1,000" in summary
    
    def test_validate_filters(self, filter_manager):
        """Test filter validation."""
        # Add valid filters
        filter_manager.add_currency_filter("USD")
        filter_manager.add_min_balance_filter(100.0)
        
        # Should pass validation
        is_valid, errors = filter_manager.validate_filters()
        assert is_valid == True
        assert len(errors) == 0


class TestFilterIntegration:
    """Integration tests for filter system."""
    
    @pytest.fixture
    def sample_accounts(self):
        """Create sample account data for testing."""
        # Create mock accounts to avoid constructor issues
        account1 = Mock(spec=AccountData)
        account1.vt_accountid = "BINANCE.USD"
        account1.balance = 5000.0
        account1.available = 4500.0
        account1.frozen = 500.0
        account1.net_pnl = 150.0
        account1.currency = "USD"
        account1.gateway_name = "BINANCE"
        account1.datetime = datetime.now()
        
        account2 = Mock(spec=AccountData)
        account2.vt_accountid = "IB.EUR"
        account2.balance = 0.0
        account2.available = 0.0
        account2.frozen = 0.0
        account2.net_pnl = -25.0
        account2.currency = "EUR"
        account2.gateway_name = "INTERACTIVE_BROKERS"
        account2.datetime = datetime.now()
        
        account3 = Mock(spec=AccountData)
        account3.vt_accountid = "BINANCE.BTC"
        account3.balance = 2.5
        account3.available = 2.0
        account3.frozen = 0.5
        account3.net_pnl = 0.25
        account3.currency = "BTC"
        account3.gateway_name = "BINANCE"
        account3.datetime = datetime.now()
        
        return [account1, account2, account3]
    
    def test_multiple_filter_combinations(self, sample_accounts):
        """Test various filter combinations on sample data."""
        settings = Mock(spec=AccountDisplaySettings)
        settings.show_zero_balances = True
        settings.currency_filter = None
        settings.gateway_filter = None
        settings.min_balance_filter = None
        
        manager = AccountFilterManager(settings)
        
        # Test 1: Currency filter only
        manager.add_currency_filter("USD")
        usd_results = [acc for acc in sample_accounts if manager.apply_all_filters(acc)]
        assert len(usd_results) == 1
        assert usd_results[0].currency == "USD"
        
        # Test 2: Gateway filter only
        manager.clear_all_filters()
        manager.add_gateway_filter("BINANCE")
        binance_results = [acc for acc in sample_accounts if manager.apply_all_filters(acc)]
        assert len(binance_results) == 2  # USD and BTC accounts
        
        # Test 3: Balance filter only (hide zero balances)
        manager.clear_all_filters()
        manager.set_zero_balance_visibility(False)
        nonzero_results = [acc for acc in sample_accounts if manager.apply_all_filters(acc)]
        assert len(nonzero_results) == 2  # Excludes EUR account with 0 balance
        
        # Test 4: Combined filters
        manager.clear_all_filters()
        manager.add_currency_filter("USD")
        manager.add_min_balance_filter(1000.0)
        combined_results = [acc for acc in sample_accounts if manager.apply_all_filters(acc)]
        assert len(combined_results) == 1  # Only USD account with >$1000