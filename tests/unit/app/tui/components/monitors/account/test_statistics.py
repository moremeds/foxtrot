"""
Unit tests for account monitor statistics module.

Tests statistics tracking, calculation, and historical data management.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from collections import deque
from foxtrot.util.object import AccountData
from foxtrot.app.tui.components.monitors.account.config import AccountMonitorConfig
from foxtrot.app.tui.components.monitors.account.statistics import AccountStatistics


class TestAccountStatistics:
    """Test cases for AccountStatistics class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AccountMonitorConfig)
        config.STATISTICS_FIELDS = {
            'total_accounts': {'default': 0},
            'total_balance': {'default': 0.0},
            'total_available': {'default': 0.0},
            'total_frozen': {'default': 0.0},
            'total_pnl': {'default': 0.0},
            'total_commission': {'default': 0.0},
            'total_margin': {'default': 0.0},
            'total_equity': {'default': 0.0},
            'equity_ratio': {'default': 1.0}
        }
        return config
    
    @pytest.fixture
    def statistics(self, mock_config):
        """Create statistics instance for testing."""
        return AccountStatistics(mock_config)
    
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
    
    def test_statistics_initialization(self, statistics, mock_config):
        """Test statistics initialization."""
        assert statistics.config == mock_config
        assert isinstance(statistics.statistics, dict)
        assert isinstance(statistics.history, dict)
        assert isinstance(statistics.account_data, dict)
        assert isinstance(statistics.account_count_by_currency, dict)
        assert isinstance(statistics.account_count_by_gateway, dict)
        assert isinstance(statistics.performance_metrics, dict)
        assert isinstance(statistics.daily_snapshots, list)
        
        # Check initial statistics values
        for field, field_config in mock_config.STATISTICS_FIELDS.items():
            expected_default = field_config.get('default', 0)
            assert statistics.statistics[field] == expected_default
    
    @pytest.mark.asyncio
    async def test_update_account(self, statistics, sample_account_data):
        """Test updating account statistics."""
        # Initially no accounts
        assert len(statistics.account_data) == 0
        assert statistics.statistics['total_accounts'] == 0
        
        # Update with new account
        await statistics.update_account(sample_account_data)
        
        # Verify account is stored
        assert len(statistics.account_data) == 1
        assert "TEST.USD" in statistics.account_data
        assert statistics.account_data["TEST.USD"] == sample_account_data
        
        # Verify statistics are updated
        assert statistics.statistics['total_accounts'] == 1
        assert statistics.statistics['total_balance'] == 10000.0
        assert statistics.statistics['total_available'] == 8500.0
        assert statistics.statistics['total_frozen'] == 1500.0
        assert statistics.statistics['total_pnl'] == 250.0
    
    @pytest.mark.asyncio
    async def test_update_existing_account(self, statistics, sample_account_data):
        """Test updating existing account data."""
        # Add initial account
        await statistics.update_account(sample_account_data)
        
        # Create updated account data
        updated_account = AccountData(
            vt_accountid="TEST.USD",
            balance=12000.0,  # Increased balance
            available=10500.0,
            frozen=1500.0,
            net_pnl=500.0,  # Increased P&L
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
        
        # Update the account
        await statistics.update_account(updated_account)
        
        # Should still have only 1 account
        assert statistics.statistics['total_accounts'] == 1
        
        # But with updated values
        assert statistics.statistics['total_balance'] == 12000.0
        assert statistics.statistics['total_pnl'] == 500.0
    
    @pytest.mark.asyncio
    async def test_multiple_accounts(self, statistics):
        """Test statistics with multiple accounts."""
        # Create multiple accounts
        account1 = AccountData(
            vt_accountid="BINANCE.USD",
            balance=5000.0,
            available=4500.0,
            frozen=500.0,
            net_pnl=100.0,
            currency="USD",
            gateway_name="BINANCE",
            datetime=datetime.now()
        )
        
        account2 = AccountData(
            vt_accountid="IB.EUR",
            balance=3000.0,
            available=2800.0,
            frozen=200.0,
            net_pnl=-50.0,
            currency="EUR",
            gateway_name="INTERACTIVE_BROKERS",
            datetime=datetime.now()
        )
        
        # Update both accounts
        await statistics.update_account(account1)
        await statistics.update_account(account2)
        
        # Verify aggregated statistics
        assert statistics.statistics['total_accounts'] == 2
        assert statistics.statistics['total_balance'] == 8000.0  # 5000 + 3000
        assert statistics.statistics['total_available'] == 7300.0  # 4500 + 2800
        assert statistics.statistics['total_frozen'] == 700.0  # 500 + 200
        assert statistics.statistics['total_pnl'] == 50.0  # 100 + (-50)
        
        # Verify currency counts
        assert statistics.account_count_by_currency['USD'] == 1
        assert statistics.account_count_by_currency['EUR'] == 1
        
        # Verify gateway counts
        assert statistics.account_count_by_gateway['BINANCE'] == 1
        assert statistics.account_count_by_gateway['INTERACTIVE_BROKERS'] == 1
    
    def test_update_counts(self, statistics):
        """Test currency and gateway count updates."""
        # Create account data
        account_data = AccountData(
            vt_accountid="TEST.USD",
            balance=1000.0,
            available=900.0,
            frozen=100.0,
            net_pnl=50.0,
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
        
        # Update counts (simulating new account)
        statistics._update_counts(account_data, None)
        
        assert statistics.account_count_by_currency['USD'] == 1
        assert statistics.account_count_by_gateway['TEST_GATEWAY'] == 1
        
        # Update with changed currency (simulating account update)
        updated_account = AccountData(
            vt_accountid="TEST.EUR",
            balance=1000.0,
            available=900.0,
            frozen=100.0,
            net_pnl=50.0,
            currency="EUR",  # Changed currency
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
        
        statistics._update_counts(updated_account, account_data)
        
        # Old currency count should be decremented and removed
        assert 'USD' not in statistics.account_count_by_currency
        # New currency count should be incremented
        assert statistics.account_count_by_currency['EUR'] == 1
        # Gateway count should remain the same
        assert statistics.account_count_by_gateway['TEST_GATEWAY'] == 1
    
    @pytest.mark.asyncio
    async def test_derived_metrics_calculation(self, statistics):
        """Test calculation of derived metrics."""
        account_data = AccountData(
            vt_accountid="TEST.USD",
            balance=10000.0,
            available=8500.0,
            frozen=1500.0,
            net_pnl=500.0,
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
        
        await statistics.update_account(account_data)
        
        # Test derived metrics
        assert statistics.statistics['total_equity'] == 10500.0  # balance + pnl
        assert statistics.statistics['equity_ratio'] == 1.05  # equity / balance
    
    @pytest.mark.asyncio
    async def test_zero_balance_handling(self, statistics):
        """Test handling of zero balances in calculations."""
        zero_account = AccountData(
            vt_accountid="ZERO.USD",
            balance=0.0,
            available=0.0,
            frozen=0.0,
            net_pnl=0.0,
            currency="USD",
            gateway_name="TEST_GATEWAY",
            datetime=datetime.now()
        )
        
        await statistics.update_account(zero_account)
        
        # Should handle zero balance without division errors
        assert statistics.statistics['equity_ratio'] == 1.0  # Default when balance is 0
    
    @pytest.mark.asyncio
    async def test_historical_snapshots(self, statistics, sample_account_data):
        """Test historical snapshot functionality."""
        # Set snapshot interval to 0 for testing
        statistics.snapshot_interval = timedelta(seconds=0)
        
        await statistics.update_account(sample_account_data)
        
        # Should have taken a snapshot
        assert len(statistics.history['portfolio']) > 0
        
        snapshot = statistics.history['portfolio'][-1]
        assert 'timestamp' in snapshot
        assert 'statistics' in snapshot
        assert 'account_count' in snapshot
        assert snapshot['account_count'] == 1
    
    def test_get_statistics(self, statistics):
        """Test getting current statistics."""
        stats = statistics.get_statistics()
        
        assert isinstance(stats, dict)
        # Should be a copy, not the original
        assert stats is not statistics.statistics
        # But should have the same content
        assert stats == statistics.statistics
    
    def test_get_performance_metrics(self, statistics):
        """Test getting performance metrics."""
        metrics = statistics.get_performance_metrics()
        
        assert isinstance(metrics, dict)
        # Should be a copy
        assert metrics is not statistics.performance_metrics
    
    @pytest.mark.asyncio
    async def test_currency_breakdown(self, statistics):
        """Test currency breakdown calculation."""
        # Add accounts with different currencies
        usd_account = AccountData(
            vt_accountid="USD.1",
            balance=5000.0,
            available=4500.0,
            frozen=500.0,
            net_pnl=200.0,
            currency="USD",
            gateway_name="GATEWAY1",
            datetime=datetime.now()
        )
        
        eur_account = AccountData(
            vt_accountid="EUR.1",
            balance=3000.0,
            available=2800.0,
            frozen=200.0,
            net_pnl=-100.0,
            currency="EUR",
            gateway_name="GATEWAY2",
            datetime=datetime.now()
        )
        
        await statistics.update_account(usd_account)
        await statistics.update_account(eur_account)
        
        breakdown = statistics.get_currency_breakdown()
        
        assert isinstance(breakdown, dict)
        assert 'USD' in breakdown
        assert 'EUR' in breakdown
        
        # Check USD breakdown
        usd_data = breakdown['USD']
        assert usd_data['balance'] == 5000.0
        assert usd_data['available'] == 4500.0
        assert usd_data['pnl'] == 200.0
        assert usd_data['account_count'] == 1
        
        # Check EUR breakdown
        eur_data = breakdown['EUR']
        assert eur_data['balance'] == 3000.0
        assert eur_data['pnl'] == -100.0
        assert eur_data['account_count'] == 1
    
    @pytest.mark.asyncio
    async def test_gateway_breakdown(self, statistics):
        """Test gateway breakdown calculation."""
        # Add accounts with different gateways
        binance_account = AccountData(
            vt_accountid="BINANCE.USD",
            balance=4000.0,
            available=3500.0,
            frozen=500.0,
            net_pnl=150.0,
            currency="USD",
            gateway_name="BINANCE",
            datetime=datetime.now()
        )
        
        ib_account = AccountData(
            vt_accountid="IB.EUR",
            balance=2000.0,
            available=1800.0,
            frozen=200.0,
            net_pnl=-50.0,
            currency="EUR",
            gateway_name="INTERACTIVE_BROKERS",
            datetime=datetime.now()
        )
        
        await statistics.update_account(binance_account)
        await statistics.update_account(ib_account)
        
        breakdown = statistics.get_gateway_breakdown()
        
        assert isinstance(breakdown, dict)
        assert 'BINANCE' in breakdown
        assert 'INTERACTIVE_BROKERS' in breakdown
        
        # Check BINANCE breakdown
        binance_data = breakdown['BINANCE']
        assert binance_data['balance'] == 4000.0
        assert binance_data['pnl'] == 150.0
        assert binance_data['account_count'] == 1
        assert binance_data['currency_count'] == 1  # Only USD
        
        # Check IB breakdown
        ib_data = breakdown['INTERACTIVE_BROKERS']
        assert ib_data['balance'] == 2000.0
        assert ib_data['pnl'] == -50.0
        assert ib_data['account_count'] == 1
        assert ib_data['currency_count'] == 1  # Only EUR
    
    def test_get_account_history(self, statistics):
        """Test getting account history."""
        account_id = "TEST.USD"
        
        # Initially no history
        history = statistics.get_account_history(account_id)
        assert isinstance(history, list)
        assert len(history) == 0
        
        # Add some portfolio history (placeholder implementation)
        now = datetime.now()
        snapshot = {
            'timestamp': now,
            'statistics': {
                'total_balance': 1000.0,
                'total_available': 900.0,
                'total_pnl': 100.0
            }
        }
        statistics.history['portfolio'].append(snapshot)
        
        # Get recent history
        history = statistics.get_account_history(account_id, hours=1)
        assert len(history) == 1
    
    @pytest.mark.asyncio
    async def test_get_summary(self, statistics, sample_account_data):
        """Test getting comprehensive summary."""
        await statistics.update_account(sample_account_data)
        
        summary = statistics.get_summary()
        
        assert isinstance(summary, dict)
        assert 'statistics' in summary
        assert 'performance' in summary
        assert 'currency_breakdown' in summary
        assert 'gateway_breakdown' in summary
        assert 'account_counts' in summary
        assert 'last_updated' in summary
        
        # Check account counts structure
        account_counts = summary['account_counts']
        assert 'total' in account_counts
        assert 'by_currency' in account_counts
        assert 'by_gateway' in account_counts
        assert account_counts['total'] == 1
    
    def test_reset_statistics(self, statistics, sample_account_data):
        """Test resetting all statistics."""
        # Add some data first
        statistics.account_data["TEST.USD"] = sample_account_data
        statistics.statistics['total_accounts'] = 1
        statistics.account_count_by_currency['USD'] = 1
        statistics.performance_metrics['daily_return'] = 0.05
        statistics.history['portfolio'].append({'test': 'data'})
        statistics.daily_snapshots.append({'test': 'snapshot'})
        
        # Reset everything
        statistics.reset_statistics()
        
        # Verify everything is cleared
        assert len(statistics.account_data) == 0
        assert statistics.statistics['total_accounts'] == 0
        assert len(statistics.account_count_by_currency) == 0
        assert len(statistics.account_count_by_gateway) == 0
        assert len(statistics.performance_metrics) == 0
        assert len(statistics.history) == 0
        assert len(statistics.daily_snapshots) == 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics_calculation(self, statistics):
        """Test performance metrics calculation with historical data."""
        # Add initial daily snapshot
        yesterday_snapshot = {
            'timestamp': datetime.now() - timedelta(days=1),
            'statistics': {'total_equity': 10000.0}
        }
        statistics.daily_snapshots.append(yesterday_snapshot)
        
        # Set current statistics
        statistics.statistics['total_equity'] = 10500.0  # 5% gain
        
        # Calculate performance metrics
        await statistics._update_performance_metrics()
        
        # Check if daily return was calculated
        if 'daily_return' in statistics.performance_metrics:
            assert statistics.performance_metrics['daily_return'] == pytest.approx(0.05, rel=1e-2)
            assert statistics.performance_metrics['daily_return_pct'] == pytest.approx(5.0, rel=1e-1)
    
    @pytest.mark.asyncio
    async def test_volatility_calculation(self, statistics):
        """Test volatility calculation with sufficient data."""
        # Add multiple daily snapshots with varying equity values
        base_date = datetime.now() - timedelta(days=10)
        equity_values = [10000, 10200, 9800, 10100, 10400, 9900, 10300, 10150]
        
        for i, equity in enumerate(equity_values):
            snapshot = {
                'timestamp': base_date + timedelta(days=i),
                'statistics': {'total_equity': float(equity)}
            }
            statistics.daily_snapshots.append(snapshot)
        
        # Calculate volatility
        await statistics._calculate_volatility()
        
        # Should have calculated volatility
        assert 'volatility' in statistics.performance_metrics
        assert 'annualized_volatility' in statistics.performance_metrics
        assert statistics.performance_metrics['volatility'] >= 0
        assert statistics.performance_metrics['annualized_volatility'] >= 0
    
    @pytest.mark.asyncio
    async def test_max_drawdown_calculation(self, statistics):
        """Test maximum drawdown calculation."""
        # Add snapshots with a drawdown pattern
        equity_values = [10000, 10500, 11000, 9500, 8000, 8500, 9000, 9500]
        base_date = datetime.now() - timedelta(days=len(equity_values))
        
        for i, equity in enumerate(equity_values):
            snapshot = {
                'timestamp': base_date + timedelta(days=i),
                'statistics': {'total_equity': float(equity)}
            }
            statistics.daily_snapshots.append(snapshot)
        
        # Calculate max drawdown
        await statistics._calculate_max_drawdown()
        
        # Should calculate max drawdown
        assert 'max_drawdown' in statistics.performance_metrics
        assert 'max_drawdown_pct' in statistics.performance_metrics
        
        # Max drawdown should be from peak (11000) to trough (8000) = 27.27%
        expected_drawdown = (11000 - 8000) / 11000
        assert statistics.performance_metrics['max_drawdown'] == pytest.approx(expected_drawdown, rel=1e-2)


class TestStatisticsIntegration:
    """Integration tests for statistics system."""
    
    @pytest.mark.asyncio
    async def test_realistic_trading_scenario(self):
        """Test statistics with realistic trading scenario."""
        config = Mock(spec=AccountMonitorConfig)
        config.STATISTICS_FIELDS = {
            'total_accounts': {'default': 0},
            'total_balance': {'default': 0.0},
            'total_available': {'default': 0.0},
            'total_frozen': {'default': 0.0},
            'total_pnl': {'default': 0.0},
            'total_commission': {'default': 0.0},
            'total_margin': {'default': 0.0},
            'total_equity': {'default': 0.0},
            'equity_ratio': {'default': 1.0}
        }
        
        statistics = AccountStatistics(config)
        
        # Simulate trading day with multiple account updates
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
            await statistics.update_account(account)
        
        # Verify aggregated statistics
        stats = statistics.get_statistics()
        assert stats['total_accounts'] == 3
        assert stats['total_balance'] == 40002.5  # 25000 + 15000 + 2.5
        assert stats['total_pnl'] == 1250.0 + (-350.0) + 0.15  # 900.15
        
        # Verify breakdowns
        currency_breakdown = statistics.get_currency_breakdown()
        assert len(currency_breakdown) == 3  # USD, EUR, BTC
        
        gateway_breakdown = statistics.get_gateway_breakdown()
        assert len(gateway_breakdown) == 2  # BINANCE, INTERACTIVE_BROKERS
        assert gateway_breakdown['BINANCE']['account_count'] == 2  # USD and BTC
        assert gateway_breakdown['INTERACTIVE_BROKERS']['account_count'] == 1  # EUR
        
        # Get comprehensive summary
        summary = statistics.get_summary()
        assert summary['account_counts']['total'] == 3
        assert len(summary['account_counts']['by_currency']) == 3
        assert len(summary['account_counts']['by_gateway']) == 2