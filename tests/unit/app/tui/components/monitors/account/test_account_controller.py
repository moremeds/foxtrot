"""
Unit tests for account monitor main controller.

Tests the orchestration of all modular components and backward compatibility.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from pathlib import Path
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.object import AccountData
from foxtrot.util.event_type import EVENT_ACCOUNT
from foxtrot.app.tui.components.monitors.account.account_controller import TUIAccountMonitor
from foxtrot.app.tui.components.monitors.account.config import (
    AccountMonitorConfig,
    AccountDisplaySettings
)


class TestTUIAccountMonitor:
    """Test cases for TUIAccountMonitor controller class."""
    
    @pytest.fixture
    def mock_event_engine(self):
        """Mock event engine for testing."""
        engine = Mock(spec=EventEngine)
        engine.register = Mock()
        return engine
    
    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data for testing."""
        return AccountData(
            vt_accountid="TEST.USD",
            balance=10000.0,
            available=8500.0,
            frozen=1500.0,
            net_pnl=250.0,
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
    
    @pytest.fixture
    def monitor(self, mock_event_engine, tmp_path):
        """Create account monitor for testing."""
        export_dir = tmp_path / "exports"
        return TUIAccountMonitor(mock_event_engine, export_dir)
    
    def test_monitor_initialization(self, monitor, mock_event_engine):
        """Test monitor initialization and component setup."""
        # Verify basic initialization
        assert monitor.event_engine == mock_event_engine
        assert isinstance(monitor.config, AccountMonitorConfig)
        assert isinstance(monitor.display_settings, AccountDisplaySettings)
        assert isinstance(monitor.account_data, dict)
        assert len(monitor.account_data) == 0
        assert monitor.is_running == False
        
        # Verify all components are initialized
        assert monitor.formatter is not None
        assert monitor.filter_manager is not None
        assert monitor.statistics is not None
        assert monitor.risk_manager is not None
        assert monitor.analyzer is not None
        assert monitor.exporter is not None
        assert monitor.action_handler is not None
        
        # Verify event registration
        mock_event_engine.register.assert_called_with(EVENT_ACCOUNT, monitor.on_account_update)
    
    def test_monitor_initialization_with_overrides(self, mock_event_engine, tmp_path):
        """Test monitor initialization with configuration overrides."""
        config_overrides = {
            'MARGIN_WARNING_THRESHOLD': 0.9,
            'BALANCE_WARNING_THRESHOLD': 2000.0
        }
        
        monitor = TUIAccountMonitor(
            mock_event_engine, 
            tmp_path / "exports",
            config_overrides
        )
        
        # Configuration should be updated with overrides
        assert monitor.config.MARGIN_WARNING_THRESHOLD == 0.9
        assert monitor.config.BALANCE_WARNING_THRESHOLD == 2000.0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitor(self, monitor):
        """Test starting and stopping the monitor."""
        # Initially not running
        assert monitor.is_running == False
        
        # Start monitor
        await monitor.start()
        assert monitor.is_running == True
        
        # Starting again should not change state
        await monitor.start()
        assert monitor.is_running == True
        
        # Stop monitor
        await monitor.stop()
        assert monitor.is_running == False
        
        # Stopping again should not change state
        await monitor.stop()
        assert monitor.is_running == False
    
    @pytest.mark.asyncio
    async def test_update_account(self, monitor, sample_account_data):
        """Test updating account data."""
        account_id = sample_account_data.vt_accountid
        
        # Initially no accounts
        assert len(monitor.account_data) == 0
        
        # Update account
        await monitor.update_account(sample_account_data)
        
        # Account should be stored
        assert len(monitor.account_data) == 1
        assert account_id in monitor.account_data
        assert monitor.account_data[account_id] == sample_account_data
    
    @pytest.mark.asyncio
    async def test_on_account_update_event(self, monitor, sample_account_data):
        """Test handling account update events."""
        # Start monitor to process events
        await monitor.start()
        
        # Create mock event
        mock_event = Mock()
        mock_event.data = sample_account_data
        
        # Process event
        await monitor.on_account_update(mock_event)
        
        # Account should be updated
        assert len(monitor.account_data) == 1
        assert sample_account_data.vt_accountid in monitor.account_data
    
    @pytest.mark.asyncio
    async def test_on_account_update_when_stopped(self, monitor, sample_account_data):
        """Test that events are ignored when monitor is stopped."""
        # Monitor should be stopped by default
        assert monitor.is_running == False
        
        mock_event = Mock()
        mock_event.data = sample_account_data
        
        # Process event while stopped
        await monitor.on_account_update(mock_event)
        
        # Account should not be processed
        assert len(monitor.account_data) == 0
    
    @pytest.mark.asyncio
    async def test_get_filtered_accounts(self, monitor, sample_account_data):
        """Test getting filtered account data."""
        # Add account data
        await monitor.update_account(sample_account_data)
        
        # Get filtered accounts (no filters initially)
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1
        assert sample_account_data.vt_accountid in filtered
        
        # Apply currency filter
        await monitor.apply_currency_filter("EUR")  # Different currency
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 0  # Should be filtered out
        
        # Remove filter
        await monitor.clear_all_filters()
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1  # Should be back
    
    @pytest.mark.asyncio
    async def test_get_formatted_account_data(self, monitor, sample_account_data):
        """Test getting formatted account data."""
        # Add account
        await monitor.update_account(sample_account_data)
        
        # Get formatted data
        formatted = await monitor.get_formatted_account_data(sample_account_data)
        
        assert isinstance(formatted, dict)
        assert len(formatted) > 0
        
        # Should contain basic fields
        expected_fields = ['balance', 'available', 'net_pnl', 'currency']
        for field in expected_fields:
            if hasattr(sample_account_data, field):
                assert field in formatted
    
    @pytest.mark.asyncio
    async def test_get_formatted_account_data_with_risk_metrics(self, monitor, sample_account_data):
        """Test formatted data with risk metrics included."""
        await monitor.update_account(sample_account_data)
        
        formatted = await monitor.get_formatted_account_data(
            sample_account_data, 
            include_risk_metrics=True
        )
        
        # Should include risk metrics
        risk_fields = ['margin_ratio', 'available_ratio', 'leverage']
        for field in risk_fields:
            if field in formatted:
                assert isinstance(formatted[field], str)  # Should be formatted strings
    
    @pytest.mark.asyncio
    async def test_get_portfolio_summary(self, monitor, sample_account_data):
        """Test getting portfolio summary."""
        await monitor.update_account(sample_account_data)
        
        portfolio_summary = await monitor.get_portfolio_summary()
        
        # Should return portfolio summary object
        assert hasattr(portfolio_summary, 'total_accounts')
        assert hasattr(portfolio_summary, 'total_balance')
        assert hasattr(portfolio_summary, 'total_equity')
        assert hasattr(portfolio_summary, 'risk_level')
    
    @pytest.mark.asyncio
    async def test_get_account_summaries(self, monitor, sample_account_data):
        """Test getting individual account summaries."""
        await monitor.update_account(sample_account_data)
        
        summaries = await monitor.get_account_summaries()
        
        assert isinstance(summaries, dict)
        assert sample_account_data.vt_accountid in summaries
        
        summary = summaries[sample_account_data.vt_accountid]
        assert hasattr(summary, 'account_id')
        assert hasattr(summary, 'current_balance')
        assert hasattr(summary, 'risk_level')
    
    @pytest.mark.asyncio
    async def test_get_statistics_summary(self, monitor, sample_account_data):
        """Test getting statistics summary."""
        await monitor.update_account(sample_account_data)
        
        stats_summary = await monitor.get_statistics_summary()
        
        assert isinstance(stats_summary, dict)
        assert 'statistics' in stats_summary
        assert 'performance' in stats_summary
        assert 'currency_breakdown' in stats_summary
        assert 'gateway_breakdown' in stats_summary
        assert 'last_updated' in stats_summary
    
    @pytest.mark.asyncio
    async def test_get_risk_summary(self, monitor, sample_account_data):
        """Test getting risk summary."""
        await monitor.update_account(sample_account_data)
        
        risk_summary = await monitor.get_risk_summary()
        
        assert isinstance(risk_summary, dict)
        assert 'portfolio_metrics' in risk_summary
        assert 'risk_level' in risk_summary
        assert 'active_warnings_count' in risk_summary
        assert 'last_assessment' in risk_summary
    
    # Filter Management Tests
    
    @pytest.mark.asyncio
    async def test_apply_currency_filter(self, monitor, sample_account_data):
        """Test applying currency filter."""
        await monitor.update_account(sample_account_data)
        
        # Apply USD filter (should match our sample data)
        await monitor.apply_currency_filter("USD")
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1
        
        # Apply EUR filter (should not match)
        await monitor.apply_currency_filter("EUR")
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 0
    
    @pytest.mark.asyncio
    async def test_apply_gateway_filter(self, monitor, sample_account_data):
        """Test applying gateway filter."""
        await monitor.update_account(sample_account_data)
        
        # Apply matching gateway filter
        await monitor.apply_gateway_filter("TEST_GATEWAY")
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1
        
        # Apply non-matching gateway filter
        await monitor.apply_gateway_filter("OTHER_GATEWAY")
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 0
    
    @pytest.mark.asyncio
    async def test_apply_min_balance_filter(self, monitor, sample_account_data):
        """Test applying minimum balance filter."""
        await monitor.update_account(sample_account_data)
        
        # Apply filter below account balance
        await monitor.apply_min_balance_filter(5000.0)
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1
        
        # Apply filter above account balance
        await monitor.apply_min_balance_filter(15000.0)
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 0
    
    @pytest.mark.asyncio
    async def test_clear_all_filters(self, monitor, sample_account_data):
        """Test clearing all filters."""
        await monitor.update_account(sample_account_data)
        
        # Apply multiple filters
        await monitor.apply_currency_filter("EUR")  # Won't match
        await monitor.apply_min_balance_filter(15000.0)  # Won't match
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 0  # All filtered out
        
        # Clear filters
        await monitor.clear_all_filters()
        
        filtered = await monitor.get_filtered_accounts()
        assert len(filtered) == 1  # Should be back
    
    # Display Settings Tests
    
    def test_display_settings_management(self, monitor):
        """Test display settings management."""
        # Test boolean settings
        monitor.set_show_zero_balances(False)
        assert monitor.display_settings.show_zero_balances == False
        
        monitor.set_group_by_currency(True)
        assert monitor.display_settings.group_by_currency == True
        
        monitor.set_show_percentage_changes(False)
        assert monitor.display_settings.show_percentage_changes == False
    
    # Action Handler Tests
    
    @pytest.mark.asyncio
    async def test_handle_keyboard_shortcut(self, monitor):
        """Test keyboard shortcut handling."""
        # Test known shortcut
        handled = await monitor.handle_keyboard_shortcut("f1")  # USD filter
        assert isinstance(handled, bool)
        
        # Test with context
        context = {"risk_metrics": {"margin_ratio": 0.5}}
        handled = await monitor.handle_keyboard_shortcut("f4", context)  # Show risk
        assert isinstance(handled, bool)
    
    def test_get_available_actions(self, monitor):
        """Test getting available actions."""
        actions = monitor.get_available_actions()
        
        assert isinstance(actions, dict)
        assert len(actions) > 0
        
        # Should contain common shortcuts
        expected_shortcuts = ["f1", "f2", "f3", "r", "e"]
        for shortcut in expected_shortcuts:
            assert shortcut in actions
    
    # Export Tests
    
    @pytest.mark.asyncio
    async def test_export_accounts_csv(self, monitor, sample_account_data, tmp_path):
        """Test CSV export functionality."""
        await monitor.update_account(sample_account_data)
        
        # Export to CSV
        csv_file = await monitor.export_accounts_csv()
        
        assert isinstance(csv_file, str)
        assert csv_file.endswith('.csv')
        
        # Verify file exists
        csv_path = Path(csv_file)
        assert csv_path.exists()
        assert csv_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    async def test_export_accounts_json(self, monitor, sample_account_data, tmp_path):
        """Test JSON export functionality."""
        await monitor.update_account(sample_account_data)
        
        # Export to JSON
        json_file = await monitor.export_accounts_json()
        
        assert isinstance(json_file, str)
        assert json_file.endswith('.json')
        
        # Verify file exists
        json_path = Path(json_file)
        assert json_path.exists()
        assert json_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    async def test_export_risk_analysis(self, monitor, sample_account_data, tmp_path):
        """Test risk analysis export."""
        await monitor.update_account(sample_account_data)
        
        # Export risk analysis
        risk_file = await monitor.export_risk_analysis()
        
        assert isinstance(risk_file, str)
        assert risk_file.endswith('.json')
        
        # Verify file exists
        risk_path = Path(risk_file)
        assert risk_path.exists()
        assert risk_path.stat().st_size > 0
    
    # Callback Tests
    
    @pytest.mark.asyncio
    async def test_callback_registration_and_triggering(self, monitor):
        """Test callback registration and triggering."""
        update_called = False
        message_called = False
        
        async def update_callback():
            nonlocal update_called
            update_called = True
        
        async def message_callback(message):
            nonlocal message_called
            message_called = True
        
        # Register callbacks
        monitor.register_update_callback(update_callback)
        monitor.register_message_callback(message_callback)
        
        # Trigger callbacks
        await monitor._trigger_display_update()
        await monitor._trigger_system_message("Test message")
        
        assert update_called == True
        assert message_called == True
    
    # Utility Method Tests
    
    def test_get_account_count(self, monitor, sample_account_data):
        """Test getting account count."""
        assert monitor.get_account_count() == 0
        
        # Add account
        monitor.account_data[sample_account_data.vt_accountid] = sample_account_data
        
        assert monitor.get_account_count() == 1
    
    @pytest.mark.asyncio
    async def test_get_filtered_account_count(self, monitor, sample_account_data):
        """Test getting filtered account count."""
        await monitor.update_account(sample_account_data)
        
        # No filters - should match total
        assert monitor.get_filtered_account_count() == 1
        
        # Apply filter that excludes account
        await monitor.apply_currency_filter("EUR")
        
        assert monitor.get_filtered_account_count() == 0
    
    def test_get_config_and_settings(self, monitor):
        """Test getting configuration and display settings."""
        config = monitor.get_config()
        assert isinstance(config, AccountMonitorConfig)
        assert config is monitor.config
        
        settings = monitor.get_display_settings()
        assert isinstance(settings, AccountDisplaySettings)
        assert settings is monitor.display_settings
    
    @pytest.mark.asyncio
    async def test_cleanup(self, monitor):
        """Test monitor cleanup."""
        # Start monitor
        await monitor.start()
        assert monitor.is_running == True
        
        # Cleanup
        await monitor.cleanup()
        
        # Should be stopped
        assert monitor.is_running == False


class TestAccountMonitorIntegration:
    """Integration tests for complete account monitor system."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, tmp_path):
        """Test complete account monitor workflow."""
        # Create monitor
        event_engine = Mock(spec=EventEngine)
        event_engine.register = Mock()
        
        monitor = TUIAccountMonitor(event_engine, tmp_path / "exports")
        
        # Start monitor
        await monitor.start()
        
        # Create multiple accounts
        accounts = [
            AccountData(
                vt_accountid="BINANCE.USD",
                balance=25000.0,
                available=22000.0,
                frozen=3000.0,
                net_pnl=1250.0,
                currency="USD",
                gateway_name="BINANCE",
                datetime=datetime.now()
            ),
            AccountData(
                vt_accountid="IB.EUR",
                balance=15000.0,
                available=14500.0,
                frozen=500.0,
                net_pnl=-350.0,
                currency="EUR",
                gateway_name="INTERACTIVE_BROKERS",
                datetime=datetime.now()
            ),
            AccountData(
                vt_accountid="BINANCE.BTC",
                balance=2.5,
                available=2.2,
                frozen=0.3,
                net_pnl=0.15,
                currency="BTC",
                gateway_name="BINANCE",
                datetime=datetime.now()
            )
        ]
        
        # Update all accounts
        for account in accounts:
            await monitor.update_account(account)
        
        # Verify all accounts are tracked
        assert monitor.get_account_count() == 3
        
        # Test filtering
        await monitor.apply_currency_filter("USD")
        assert monitor.get_filtered_account_count() == 1
        
        await monitor.apply_gateway_filter("BINANCE") 
        await monitor.clear_all_filters()
        
        # Test getting summaries
        portfolio_summary = await monitor.get_portfolio_summary()
        assert portfolio_summary.total_accounts == 3
        
        account_summaries = await monitor.get_account_summaries()
        assert len(account_summaries) == 3
        
        stats_summary = await monitor.get_statistics_summary()
        assert stats_summary['statistics']['total_accounts'] == 3
        
        risk_summary = await monitor.get_risk_summary()
        assert 'portfolio_metrics' in risk_summary
        
        # Test exports
        csv_file = await monitor.export_accounts_csv()
        json_file = await monitor.export_accounts_json()
        risk_file = await monitor.export_risk_analysis()
        
        # Verify all exports were created
        for file_path in [csv_file, json_file, risk_file]:
            assert Path(file_path).exists()
            assert Path(file_path).stat().st_size > 0
        
        # Cleanup
        await monitor.cleanup()
        assert monitor.is_running == False
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, tmp_path):
        """Test backward compatibility with original interface."""
        # The TUIAccountMonitor should work as a drop-in replacement
        # for the original monolithic implementation
        
        event_engine = Mock(spec=EventEngine)
        event_engine.register = Mock()
        
        # Should be able to create with minimal parameters
        monitor = TUIAccountMonitor(event_engine)
        
        # Should have all expected methods and properties
        expected_methods = [
            'start', 'stop', 'update_account', 'get_filtered_accounts',
            'apply_currency_filter', 'apply_gateway_filter', 'clear_all_filters',
            'export_accounts_csv', 'export_accounts_json', 'handle_keyboard_shortcut'
        ]
        
        for method_name in expected_methods:
            assert hasattr(monitor, method_name)
            assert callable(getattr(monitor, method_name))
        
        # Should work with the same event system
        sample_account = AccountData(
            vt_accountid="COMPAT.USD",
            balance=5000.0,
            available=4500.0,
            frozen=500.0,
            net_pnl=100.0,
            currency="USD",
            gateway_name="TEST",
            datetime=datetime.now()
        )
        
        await monitor.start()
        
        # Should handle events the same way
        mock_event = Mock()
        mock_event.data = sample_account
        await monitor.on_account_update(mock_event)
        
        # Should have processed the account
        assert monitor.get_account_count() == 1
        assert "COMPAT.USD" in monitor.account_data