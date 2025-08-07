"""
Unit tests for account monitor risk management module.

Tests risk assessment, threshold monitoring, and warning generation.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from foxtrot.util.object import AccountData
from foxtrot.app.tui.components.monitors.account.config import AccountMonitorConfig
from foxtrot.app.tui.components.monitors.account.risk_manager import (
    RiskLevel,
    RiskCategory,
    RiskThreshold,
    AccountRiskManager
)
from foxtrot.app.tui.components.monitors.account.messages import AccountWarning


class TestRiskLevel:
    """Test cases for RiskLevel enum."""
    
    def test_risk_level_values(self):
        """Test risk level enum values."""
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


class TestRiskCategory:
    """Test cases for RiskCategory enum."""
    
    def test_risk_category_values(self):
        """Test risk category enum values."""
        assert RiskCategory.BALANCE.value == "balance"
        assert RiskCategory.MARGIN.value == "margin"
        assert RiskCategory.PNL.value == "pnl"
        assert RiskCategory.LEVERAGE.value == "leverage"
        assert RiskCategory.CONCENTRATION.value == "concentration"
        assert RiskCategory.LIQUIDITY.value == "liquidity"


class TestRiskThreshold:
    """Test cases for RiskThreshold class."""
    
    def test_threshold_initialization(self):
        """Test risk threshold initialization."""
        threshold = RiskThreshold(
            name="test_threshold",
            category=RiskCategory.BALANCE,
            threshold_value=1000.0,
            risk_level=RiskLevel.HIGH,
            comparison="less",
            message_template="Balance too low: ${value:.2f}"
        )
        
        assert threshold.name == "test_threshold"
        assert threshold.category == RiskCategory.BALANCE
        assert threshold.threshold_value == 1000.0
        assert threshold.risk_level == RiskLevel.HIGH
        assert threshold.comparison == "less"
        assert threshold.message_template == "Balance too low: ${value:.2f}"
        assert threshold.is_active == False
        assert threshold.triggered_time is None
    
    def test_threshold_check_greater(self):
        """Test threshold checking with 'greater' comparison."""
        threshold = RiskThreshold(
            name="high_margin",
            category=RiskCategory.MARGIN,
            threshold_value=0.8,
            risk_level=RiskLevel.HIGH,
            comparison="greater"
        )
        
        # Test value above threshold
        assert threshold.check_threshold(0.85) == True
        assert threshold.is_active == True
        assert threshold.triggered_time is not None
        
        # Test value below threshold
        assert threshold.check_threshold(0.75) == False
        assert threshold.is_active == False
        assert threshold.triggered_time is None
    
    def test_threshold_check_less(self):
        """Test threshold checking with 'less' comparison."""
        threshold = RiskThreshold(
            name="low_balance",
            category=RiskCategory.BALANCE,
            threshold_value=500.0,
            risk_level=RiskLevel.MEDIUM,
            comparison="less"
        )
        
        # Test value below threshold
        assert threshold.check_threshold(300.0) == True
        assert threshold.is_active == True
        
        # Test value above threshold
        assert threshold.check_threshold(700.0) == False
        assert threshold.is_active == False
    
    def test_threshold_check_equal(self):
        """Test threshold checking with 'equal' comparison."""
        threshold = RiskThreshold(
            name="exact_value",
            category=RiskCategory.PNL,
            threshold_value=0.0,
            risk_level=RiskLevel.MEDIUM,
            comparison="equal"
        )
        
        # Test exact match
        assert threshold.check_threshold(0.0) == True
        assert threshold.is_active == True
        
        # Test near match (within tolerance)
        assert threshold.check_threshold(1e-7) == True
        
        # Test non-match
        assert threshold.check_threshold(0.1) == False
    
    def test_threshold_recovery(self):
        """Test threshold recovery mechanism."""
        threshold = RiskThreshold(
            name="margin_recovery",
            category=RiskCategory.MARGIN,
            threshold_value=0.8,
            risk_level=RiskLevel.HIGH,
            comparison="greater",
            recovery_threshold=0.75  # Lower than trigger threshold
        )
        
        # Trigger threshold
        assert threshold.check_threshold(0.85) == True
        assert threshold.is_active == True
        
        # Value still above recovery threshold - should remain active
        assert threshold.check_threshold(0.78) == False  # Below trigger but above recovery
        assert threshold.is_active == True
        
        # Value below recovery threshold - should deactivate
        assert threshold.check_threshold(0.70) == False
        assert threshold.is_active == False
    
    def test_message_formatting(self):
        """Test threshold message formatting."""
        threshold = RiskThreshold(
            name="balance_warning",
            category=RiskCategory.BALANCE,
            threshold_value=1000.0,
            risk_level=RiskLevel.MEDIUM,
            comparison="less",
            message_template="Low balance: ${value:,.2f} (threshold: ${threshold:,.2f})"
        )
        
        context = {"account_id": "TEST.USD"}
        message = threshold.format_message(750.50, context)
        
        assert "750.50" in message
        assert "1,000.00" in message or "1000.00" in message
    
    def test_message_formatting_fallback(self):
        """Test message formatting fallback for invalid templates."""
        threshold = RiskThreshold(
            name="test",
            category=RiskCategory.BALANCE,
            threshold_value=100.0,
            risk_level=RiskLevel.LOW,
            message_template="Invalid template {nonexistent_key}"
        )
        
        # Should fall back to default format
        message = threshold.format_message(50.0)
        assert "test:" in message
        assert "50" in message
        assert "100" in message


class TestAccountRiskManager:
    """Test cases for AccountRiskManager class."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock(spec=AccountMonitorConfig)
        config.MARGIN_WARNING_THRESHOLD = 0.8
        config.BALANCE_WARNING_THRESHOLD = 1000.0
        config.PNL_WARNING_THRESHOLD = -500.0
        return config
    
    @pytest.fixture
    def risk_manager(self, mock_config):
        """Create risk manager for testing."""
        return AccountRiskManager(mock_config)
    
    @pytest.fixture
    def sample_account_data(self):
        """Create sample account data."""
        account = Mock(spec=AccountData)
        account.vt_accountid = "TEST.USD"
        account.balance = 10000.0
        account.available = 8000.0
        account.frozen = 2000.0
        account.net_pnl = 250.0
        account.margin = 3000.0
        account.currency = "USD"
        account.gateway_name = "TEST_GATEWAY"
        account.datetime = datetime.now()
        return account
    
    def test_risk_manager_initialization(self, risk_manager, mock_config):
        """Test risk manager initialization."""
        assert risk_manager.config == mock_config
        assert isinstance(risk_manager.thresholds, dict)
        assert isinstance(risk_manager.active_warnings, dict)
        assert isinstance(risk_manager.risk_metrics, dict)
        assert isinstance(risk_manager.risk_history, list)
        
        # Should have default thresholds
        assert len(risk_manager.thresholds) > 0
        threshold_names = list(risk_manager.thresholds.keys())
        expected_thresholds = ["low_balance", "high_margin_ratio", "critical_margin_ratio", 
                              "significant_loss", "high_leverage", "excessive_leverage"]
        
        for expected in expected_thresholds:
            assert expected in threshold_names
    
    def test_add_remove_threshold(self, risk_manager):
        """Test adding and removing custom thresholds."""
        initial_count = len(risk_manager.thresholds)
        
        # Add custom threshold
        custom_threshold = RiskThreshold(
            name="custom_test",
            category=RiskCategory.BALANCE,
            threshold_value=2000.0,
            risk_level=RiskLevel.LOW
        )
        
        risk_manager.add_threshold(custom_threshold)
        assert len(risk_manager.thresholds) == initial_count + 1
        assert "custom_test" in risk_manager.thresholds
        
        # Remove threshold
        risk_manager.remove_threshold("custom_test")
        assert len(risk_manager.thresholds) == initial_count
        assert "custom_test" not in risk_manager.thresholds
    
    @pytest.mark.asyncio
    async def test_calculate_account_risk_metrics(self, risk_manager, sample_account_data):
        """Test account risk metrics calculation."""
        metrics = await risk_manager._calculate_account_risk_metrics(sample_account_data)
        
        assert isinstance(metrics, dict)
        assert "available_ratio" in metrics
        assert "margin_ratio" in metrics
        assert "leverage" in metrics
        assert "pnl_ratio" in metrics
        assert "risk_utilization" in metrics
        
        # Verify calculations
        assert metrics["available_ratio"] == 0.8  # 8000/10000
        assert metrics["margin_ratio"] == 0.3  # 3000/10000
        assert metrics["leverage"] == 0.375  # 3000/8000
        assert metrics["pnl_ratio"] == 0.025  # 250/10000
        assert metrics["risk_utilization"] == 0.5  # (2000+3000)/10000
    
    @pytest.mark.asyncio
    async def test_assess_account_risk(self, risk_manager, sample_account_data):
        """Test complete account risk assessment."""
        warnings = await risk_manager.assess_account_risk(sample_account_data)
        
        assert isinstance(warnings, list)
        # With normal sample data, should not trigger any warnings
        assert len(warnings) == 0
        
        # Verify warnings are stored
        assert sample_account_data.vt_accountid in risk_manager.active_warnings
        assert len(risk_manager.active_warnings[sample_account_data.vt_accountid]) == 0
    
    @pytest.mark.asyncio
    async def test_assess_high_risk_account(self, risk_manager):
        """Test risk assessment for high-risk account."""
        # Create high-risk account
        high_risk_account = Mock(spec=AccountData)
        high_risk_account.vt_accountid = "HIGHRISK.USD"
        high_risk_account.balance = 1000.0
        high_risk_account.available = 100.0  # Very low available
        high_risk_account.frozen = 900.0
        high_risk_account.net_pnl = -800.0  # Large loss
        high_risk_account.margin = 950.0  # High margin usage
        high_risk_account.currency = "USD"
        high_risk_account.gateway_name = "TEST_GATEWAY"
        high_risk_account.datetime = datetime.now()
        
        warnings = await risk_manager.assess_account_risk(high_risk_account)
        
        # Should trigger multiple warnings
        assert len(warnings) > 0
        
        # Check for specific warning types
        warning_types = [w.warning_type for w in warnings if hasattr(w, 'warning_type')]
        
        # Should include high margin and significant loss warnings
        assert any("MARGIN" in wt for wt in warning_types)
    
    @pytest.mark.asyncio
    async def test_portfolio_risk_metrics(self, risk_manager):
        """Test portfolio-level risk metrics calculation."""
        # Create multiple accounts
        accounts = {
            "ACCOUNT1": Mock(spec=AccountData),
            "ACCOUNT2": Mock(spec=AccountData)
        }
        
        # Configure first account
        accounts["ACCOUNT1"].balance = 10000.0
        accounts["ACCOUNT1"].available = 8000.0
        accounts["ACCOUNT1"].margin = 2000.0
        accounts["ACCOUNT1"].net_pnl = 500.0
        
        # Configure second account
        accounts["ACCOUNT2"].balance = 5000.0
        accounts["ACCOUNT2"].available = 4500.0
        accounts["ACCOUNT2"].margin = 500.0
        accounts["ACCOUNT2"].net_pnl = -200.0
        
        metrics = await risk_manager.calculate_portfolio_risk_metrics(accounts)
        
        assert isinstance(metrics, dict)
        assert metrics["total_balance"] == 15000.0
        assert metrics["total_available"] == 12500.0
        assert metrics["total_margin"] == 2500.0
        assert metrics["total_pnl"] == 300.0
        assert metrics["total_equity"] == 15300.0
        
        # Verify calculated ratios
        assert metrics["margin_ratio"] == pytest.approx(2500.0/15000.0, rel=1e-3)
        assert metrics["pnl_ratio"] == pytest.approx(300.0/15000.0, rel=1e-3)
        
        # Should assign risk level
        assert "risk_level" in metrics
        assert metrics["risk_level"] in ["low", "medium", "high", "critical"]
    
    def test_assess_portfolio_risk_level(self, risk_manager):
        """Test portfolio risk level assessment."""
        # Test low risk scenario
        low_risk_metrics = {
            "margin_ratio": 0.3,
            "pnl_ratio": 0.05,
            "leverage_ratio": 2.0
        }
        risk_level = risk_manager._assess_portfolio_risk_level(low_risk_metrics)
        assert risk_level == "low"
        
        # Test high risk scenario
        high_risk_metrics = {
            "margin_ratio": 0.75,
            "pnl_ratio": -0.12,
            "leverage_ratio": 12.0
        }
        risk_level = risk_manager._assess_portfolio_risk_level(high_risk_metrics)
        assert risk_level == "high"
        
        # Test critical risk scenario
        critical_risk_metrics = {
            "margin_ratio": 0.95,
            "pnl_ratio": -0.25,
            "leverage_ratio": 25.0
        }
        risk_level = risk_manager._assess_portfolio_risk_level(critical_risk_metrics)
        assert risk_level == "critical"
    
    def test_get_warning_type(self, risk_manager):
        """Test warning type classification."""
        # Test critical margin warning
        warning_type = risk_manager._get_warning_type(RiskCategory.MARGIN, RiskLevel.CRITICAL)
        assert warning_type == "MARGIN_CALL"
        
        # Test critical balance warning
        warning_type = risk_manager._get_warning_type(RiskCategory.BALANCE, RiskLevel.CRITICAL)
        assert warning_type == "BALANCE_CRITICAL"
        
        # Test high margin warning
        warning_type = risk_manager._get_warning_type(RiskCategory.MARGIN, RiskLevel.HIGH)
        assert warning_type == "HIGH_MARGIN"
        
        # Test low balance warning
        warning_type = risk_manager._get_warning_type(RiskCategory.BALANCE, RiskLevel.MEDIUM)
        assert warning_type == "LOW_BALANCE"
    
    def test_get_recommended_action(self, risk_manager):
        """Test recommended action generation."""
        # Test margin call action
        action = risk_manager._get_recommended_action("MARGIN_CALL")
        assert "deposit funds" in action.lower() or "close positions" in action.lower()
        
        # Test balance critical action
        action = risk_manager._get_recommended_action("BALANCE_CRITICAL")
        assert "deposit funds" in action.lower()
        
        # Test unknown warning type fallback
        action = risk_manager._get_recommended_action("UNKNOWN_WARNING")
        assert "monitor" in action.lower()
    
    def test_get_active_warnings(self, risk_manager):
        """Test retrieving active warnings."""
        # Add test warnings
        test_warning = Mock()
        test_warning.warning = "Test warning"
        test_warning.severity = "medium"
        
        risk_manager.active_warnings["TEST.USD"] = [test_warning]
        
        # Get warnings for specific account
        account_warnings = risk_manager.get_active_warnings("TEST.USD")
        assert len(account_warnings) == 1
        assert account_warnings[0] == test_warning
        
        # Get all warnings
        all_warnings = risk_manager.get_active_warnings()
        assert len(all_warnings) == 1
        assert all_warnings[0] == test_warning
        
        # Get warnings for non-existent account
        empty_warnings = risk_manager.get_active_warnings("NONEXISTENT")
        assert len(empty_warnings) == 0
    
    def test_get_risk_summary(self, risk_manager):
        """Test risk summary generation."""
        # Add test data
        risk_manager.risk_metrics = {
            "risk_level": "medium",
            "margin_ratio": 0.5
        }
        
        test_warning = Mock()
        test_warning.is_critical = True
        risk_manager.active_warnings["TEST.USD"] = [test_warning]
        
        summary = risk_manager.get_risk_summary()
        
        assert isinstance(summary, dict)
        assert "portfolio_metrics" in summary
        assert "active_warnings_count" in summary
        assert "critical_warnings_count" in summary
        assert "risk_level" in summary
        assert "last_assessment" in summary
        
        assert summary["active_warnings_count"] == 1
        assert summary["critical_warnings_count"] == 1
        assert summary["risk_level"] == "medium"
    
    def test_risk_history_management(self, risk_manager):
        """Test risk history tracking."""
        initial_length = len(risk_manager.risk_history)
        
        # Add risk history entry
        test_metrics = {"risk_level": "low", "margin_ratio": 0.3}
        risk_manager._add_risk_history_entry(test_metrics)
        
        assert len(risk_manager.risk_history) == initial_length + 1
        
        latest_entry = risk_manager.risk_history[-1]
        assert "timestamp" in latest_entry
        assert "metrics" in latest_entry
        assert latest_entry["metrics"]["risk_level"] == "low"
    
    @pytest.mark.asyncio
    async def test_callback_registration_and_triggering(self, risk_manager):
        """Test callback registration and triggering."""
        warning_callback_called = False
        alert_callback_called = False
        
        async def warning_callback(warning):
            nonlocal warning_callback_called
            warning_callback_called = True
        
        async def alert_callback(alert):
            nonlocal alert_callback_called
            alert_callback_called = True
        
        # Register callbacks
        risk_manager.register_warning_callback(warning_callback)
        risk_manager.register_alert_callback(alert_callback)
        
        # Create critical risk account to trigger alert
        critical_account = Mock(spec=AccountData)
        critical_account.vt_accountid = "CRITICAL.USD"
        critical_account.balance = 1000.0
        critical_account.available = 50.0
        critical_account.margin = 950.0  # 95% margin usage - critical
        critical_account.net_pnl = -500.0
        critical_account.currency = "USD"
        critical_account.gateway_name = "TEST"
        critical_account.datetime = datetime.now()
        
        # Assess risk (should trigger critical warnings and alerts)
        warnings = await risk_manager.assess_account_risk(critical_account)
        
        # Should have triggered alert callback for critical warnings
        if any(hasattr(w, 'severity') and w.severity == "critical" for w in warnings):
            assert alert_callback_called == True


class TestRiskThresholdIntegration:
    """Integration tests for risk threshold system."""
    
    @pytest.mark.asyncio
    async def test_realistic_trading_risk_scenario(self):
        """Test risk management with realistic trading scenario."""
        config = Mock(spec=AccountMonitorConfig)
        config.MARGIN_WARNING_THRESHOLD = 0.7  # 70% margin warning
        config.BALANCE_WARNING_THRESHOLD = 500.0  # $500 minimum balance
        config.PNL_WARNING_THRESHOLD = -1000.0  # $1000 loss threshold
        
        risk_manager = AccountRiskManager(config)
        
        # Scenario 1: Healthy account
        healthy_account = Mock(spec=AccountData)
        healthy_account.vt_accountid = "HEALTHY.USD"
        healthy_account.balance = 50000.0
        healthy_account.available = 45000.0
        healthy_account.margin = 15000.0  # 30% margin usage - safe
        healthy_account.net_pnl = 2500.0  # Profitable
        healthy_account.currency = "USD"
        healthy_account.gateway_name = "BINANCE"
        healthy_account.datetime = datetime.now()
        
        warnings = await risk_manager.assess_account_risk(healthy_account)
        assert len(warnings) == 0  # Should be no warnings
        
        # Scenario 2: Risky but manageable account
        risky_account = Mock(spec=AccountData)
        risky_account.vt_accountid = "RISKY.USD"
        risky_account.balance = 10000.0
        risky_account.available = 3000.0
        risky_account.margin = 7500.0  # 75% margin usage - high risk
        risky_account.net_pnl = -500.0  # Small loss
        risky_account.currency = "USD"
        risky_account.gateway_name = "INTERACTIVE_BROKERS"
        risky_account.datetime = datetime.now()
        
        warnings = await risk_manager.assess_account_risk(risky_account)
        assert len(warnings) > 0  # Should have margin warning
        
        # Scenario 3: Critical account requiring immediate attention
        critical_account = Mock(spec=AccountData)
        critical_account.vt_accountid = "CRITICAL.USD"
        critical_account.balance = 2000.0
        critical_account.available = 100.0
        critical_account.margin = 1900.0  # 95% margin usage - critical
        critical_account.net_pnl = -1200.0  # Significant loss
        critical_account.currency = "USD"
        critical_account.gateway_name = "BINANCE"
        critical_account.datetime = datetime.now()
        
        warnings = await risk_manager.assess_account_risk(critical_account)
        assert len(warnings) > 1  # Should have multiple warnings
        
        # Should have critical severity warnings
        critical_warnings = [w for w in warnings if hasattr(w, 'severity') and w.severity == "critical"]
        assert len(critical_warnings) > 0
        
        # Test portfolio risk assessment
        all_accounts = {
            "HEALTHY.USD": healthy_account,
            "RISKY.USD": risky_account,
            "CRITICAL.USD": critical_account
        }
        
        portfolio_metrics = await risk_manager.calculate_portfolio_risk_metrics(all_accounts)
        
        # Portfolio should reflect mixed risk levels
        assert portfolio_metrics["risk_level"] in ["medium", "high"]  # Due to critical account
        assert portfolio_metrics["total_balance"] == 62000.0
        assert portfolio_metrics["total_margin"] == 24400.0
        assert portfolio_metrics["margin_ratio"] > 0.3  # Should be concerning