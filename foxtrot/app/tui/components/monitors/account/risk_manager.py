"""
Account monitor risk management and warning system.

This module handles risk assessment, threshold monitoring,
and warning generation for account safety and compliance.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum

from foxtrot.util.object import AccountData
from .config import AccountMonitorConfig
from .messages import AccountWarning, AccountRiskAlert

# Set up logging
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(Enum):
    """Risk category enumeration."""
    BALANCE = "balance"
    MARGIN = "margin"
    PNL = "pnl"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"
    LIQUIDITY = "liquidity"


class RiskThreshold:
    """Represents a risk threshold with monitoring logic."""
    
    def __init__(
        self,
        name: str,
        category: RiskCategory,
        threshold_value: float,
        risk_level: RiskLevel,
        comparison: str = "greater",  # greater, less, equal
        message_template: str = "",
        recovery_threshold: Optional[float] = None
    ):
        """
        Initialize risk threshold.
        
        Args:
            name: Threshold name
            category: Risk category
            threshold_value: Threshold value to monitor
            risk_level: Risk level when threshold is breached
            comparison: Type of comparison (greater, less, equal)
            message_template: Template for warning message
            recovery_threshold: Threshold for clearing the warning
        """
        self.name = name
        self.category = category
        self.threshold_value = threshold_value
        self.risk_level = risk_level
        self.comparison = comparison
        self.message_template = message_template
        self.recovery_threshold = recovery_threshold or threshold_value
        self.is_active = False
        self.triggered_time: Optional[datetime] = None
        self.last_check_time: Optional[datetime] = None
    
    def check_threshold(self, value: float, context: Dict[str, Any] = None) -> bool:
        """
        Check if threshold is breached.
        
        Args:
            value: Value to check against threshold
            context: Additional context for message formatting
            
        Returns:
            True if threshold is breached
        """
        self.last_check_time = datetime.now()
        
        if self.comparison == "greater":
            breached = value > self.threshold_value
        elif self.comparison == "less":
            breached = value < self.threshold_value
        elif self.comparison == "equal":
            breached = abs(value - self.threshold_value) < 1e-6
        else:
            breached = False
        
        # Handle state transitions
        if breached and not self.is_active:
            self.is_active = True
            self.triggered_time = datetime.now()
        elif not breached and self.is_active:
            # Check recovery threshold
            recovery_breached = self._check_recovery(value)
            if not recovery_breached:
                self.is_active = False
                self.triggered_time = None
        
        return breached
    
    def _check_recovery(self, value: float) -> bool:
        """Check if recovery threshold is still breached."""
        if self.comparison == "greater":
            return value > self.recovery_threshold
        elif self.comparison == "less":
            return value < self.recovery_threshold
        else:
            return abs(value - self.recovery_threshold) < 1e-6
    
    def format_message(self, value: float, context: Dict[str, Any] = None) -> str:
        """Format warning message with current value and context."""
        context = context or {}
        context.update({"value": value, "threshold": self.threshold_value})
        
        try:
            return self.message_template.format(**context)
        except (KeyError, ValueError):
            return f"{self.name}: {value} (threshold: {self.threshold_value})"


class AccountRiskManager:
    """
    Manages risk assessment and warning generation for account monitoring.
    
    Features:
    - Configurable risk thresholds
    - Multi-level risk assessment
    - Warning generation and tracking
    - Risk metric calculation
    - Alert escalation
    - Risk trend analysis
    """
    
    def __init__(self, config: AccountMonitorConfig):
        """
        Initialize risk manager.
        
        Args:
            config: Account monitor configuration
        """
        self.config = config
        self.thresholds: Dict[str, RiskThreshold] = {}
        self.active_warnings: Dict[str, List[AccountWarning]] = {}
        self.risk_metrics: Dict[str, Any] = {}
        self.risk_history: List[Dict[str, Any]] = []
        
        # Warning callbacks
        self.warning_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Initialize default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self) -> None:
        """Set up default risk thresholds from configuration."""
        # Balance thresholds
        self.add_threshold(RiskThreshold(
            name="low_balance",
            category=RiskCategory.BALANCE,
            threshold_value=self.config.BALANCE_WARNING_THRESHOLD,
            risk_level=RiskLevel.MEDIUM,
            comparison="less",
            message_template="Low available balance: ${value:,.2f} (threshold: ${threshold:,.2f})",
            recovery_threshold=self.config.BALANCE_WARNING_THRESHOLD * 1.2
        ))
        
        # Margin thresholds
        self.add_threshold(RiskThreshold(
            name="high_margin_ratio",
            category=RiskCategory.MARGIN,
            threshold_value=self.config.MARGIN_WARNING_THRESHOLD,
            risk_level=RiskLevel.HIGH,
            comparison="greater",
            message_template="High margin usage: {value:.1%} (threshold: {threshold:.1%})",
            recovery_threshold=self.config.MARGIN_WARNING_THRESHOLD * 0.9
        ))
        
        self.add_threshold(RiskThreshold(
            name="critical_margin_ratio",
            category=RiskCategory.MARGIN,
            threshold_value=0.95,  # 95% margin usage is critical
            risk_level=RiskLevel.CRITICAL,
            comparison="greater",
            message_template="CRITICAL: Margin usage at {value:.1%} - Liquidation risk!",
            recovery_threshold=0.90
        ))
        
        # P&L thresholds
        self.add_threshold(RiskThreshold(
            name="significant_loss",
            category=RiskCategory.PNL,
            threshold_value=self.config.PNL_WARNING_THRESHOLD,
            risk_level=RiskLevel.HIGH,
            comparison="less",
            message_template="Significant loss: ${value:,.2f} (threshold: ${threshold:,.2f})"
        ))
        
        # Leverage thresholds
        self.add_threshold(RiskThreshold(
            name="high_leverage",
            category=RiskCategory.LEVERAGE,
            threshold_value=5.0,  # 5x leverage warning
            risk_level=RiskLevel.MEDIUM,
            comparison="greater",
            message_template="High leverage: {value:.2f}x (threshold: {threshold:.2f}x)"
        ))
        
        self.add_threshold(RiskThreshold(
            name="excessive_leverage",
            category=RiskCategory.LEVERAGE,
            threshold_value=10.0,  # 10x leverage critical
            risk_level=RiskLevel.CRITICAL,
            comparison="greater",
            message_template="EXCESSIVE leverage: {value:.2f}x - High risk!"
        ))
    
    def add_threshold(self, threshold: RiskThreshold) -> None:
        """Add a risk threshold to monitoring."""
        self.thresholds[threshold.name] = threshold
    
    def remove_threshold(self, threshold_name: str) -> None:
        """Remove a risk threshold from monitoring."""
        self.thresholds.pop(threshold_name, None)
    
    async def assess_account_risk(self, account_data: AccountData) -> List[AccountWarning]:
        """
        Assess risk for a single account and generate warnings.
        
        Args:
            account_data: Account data to assess
            
        Returns:
            List of warning messages generated
        """
        warnings = []
        account_id = account_data.vt_accountid
        
        try:
            # Calculate risk metrics for this account
            risk_metrics = await self._calculate_account_risk_metrics(account_data)
            
            # Check all thresholds
            for threshold_name, threshold in self.thresholds.items():
                warning = await self._check_threshold_for_account(
                    threshold, account_data, risk_metrics
                )
                if warning:
                    warnings.append(warning)
            
            # Update active warnings for this account
            self.active_warnings[account_id] = warnings
            
            # Generate alerts for critical warnings
            for warning in warnings:
                if warning.severity == "critical":
                    alert = AccountRiskAlert(
                        account_data=account_data,
                        alert_type="CRITICAL_RISK",
                        alert_message=warning.warning,
                        recommended_action=self._get_recommended_action(warning.warning_type)
                    )
                    await self._trigger_alert(alert)
            
            return warnings
            
        except Exception as e:
            logger.error(f"Error assessing account risk for {account_id}: {e}")
            return []
    
    async def _calculate_account_risk_metrics(self, account_data: AccountData) -> Dict[str, float]:
        """Calculate risk metrics for an account."""
        metrics = {}
        
        try:
            # Available balance ratio
            if account_data.balance > 0:
                metrics["available_ratio"] = account_data.available / account_data.balance
            else:
                metrics["available_ratio"] = 0.0
            
            # Margin ratio
            margin = getattr(account_data, 'margin', 0)
            if account_data.balance > 0:
                metrics["margin_ratio"] = margin / account_data.balance
            else:
                metrics["margin_ratio"] = 0.0
            
            # Leverage calculation
            if account_data.available > 0:
                metrics["leverage"] = margin / account_data.available
            else:
                metrics["leverage"] = 0.0
            
            # P&L as percentage of balance
            if account_data.balance > 0:
                metrics["pnl_ratio"] = account_data.net_pnl / account_data.balance
            else:
                metrics["pnl_ratio"] = 0.0
            
            # Risk utilization (frozen + margin as % of balance)
            if account_data.balance > 0:
                total_risk_exposure = account_data.frozen + margin
                metrics["risk_utilization"] = total_risk_exposure / account_data.balance
            else:
                metrics["risk_utilization"] = 0.0
                
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
        
        return metrics
    
    async def _check_threshold_for_account(
        self, 
        threshold: RiskThreshold, 
        account_data: AccountData, 
        risk_metrics: Dict[str, float]
    ) -> Optional[AccountWarning]:
        """Check a specific threshold against account data."""
        try:
            # Get the value to check based on threshold category
            if threshold.category == RiskCategory.BALANCE:
                check_value = account_data.available
            elif threshold.category == RiskCategory.MARGIN:
                check_value = risk_metrics.get("margin_ratio", 0.0)
            elif threshold.category == RiskCategory.PNL:
                check_value = account_data.net_pnl
            elif threshold.category == RiskCategory.LEVERAGE:
                check_value = risk_metrics.get("leverage", 0.0)
            else:
                return None
            
            # Check threshold
            context = {
                "account_id": account_data.vt_accountid,
                "currency": account_data.currency,
                "balance": account_data.balance
            }
            
            if threshold.check_threshold(check_value, context):
                message = threshold.format_message(check_value, context)
                warning_type = self._get_warning_type(threshold.category, threshold.risk_level)
                
                return AccountWarning(
                    account_data=account_data,
                    warning=message,
                    warning_type=warning_type,
                    severity=threshold.risk_level.value
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking threshold {threshold.name}: {e}")
            return None
    
    def _get_warning_type(self, category: RiskCategory, risk_level: RiskLevel) -> str:
        """Get warning type string based on category and risk level."""
        if risk_level == RiskLevel.CRITICAL:
            if category == RiskCategory.MARGIN:
                return "MARGIN_CALL"
            elif category == RiskCategory.BALANCE:
                return "BALANCE_CRITICAL"
            else:
                return "SYSTEM_RISK"
        else:
            return {
                RiskCategory.BALANCE: "LOW_BALANCE",
                RiskCategory.MARGIN: "HIGH_MARGIN",
                RiskCategory.PNL: "SIGNIFICANT_LOSS",
                RiskCategory.LEVERAGE: "HIGH_LEVERAGE",
                RiskCategory.CONCENTRATION: "RISK_THRESHOLD",
                RiskCategory.LIQUIDITY: "RISK_THRESHOLD"
            }.get(category, "GENERAL")
    
    def _get_recommended_action(self, warning_type: str) -> str:
        """Get recommended action for a warning type."""
        actions = {
            "MARGIN_CALL": "Deposit funds immediately or close positions to reduce margin usage",
            "BALANCE_CRITICAL": "Deposit funds to maintain minimum balance requirements",
            "HIGH_MARGIN": "Consider reducing position sizes or adding margin",
            "SIGNIFICANT_LOSS": "Review trading strategy and consider risk management measures",
            "HIGH_LEVERAGE": "Reduce leverage by closing positions or adding margin",
            "SYSTEM_RISK": "Contact support immediately - system risk detected"
        }
        return actions.get(warning_type, "Monitor account closely and take appropriate action")
    
    async def calculate_portfolio_risk_metrics(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """
        Calculate portfolio-level risk metrics.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Portfolio risk metrics
        """
        try:
            total_balance = sum(acc.balance for acc in all_accounts.values())
            total_available = sum(acc.available for acc in all_accounts.values())
            total_margin = sum(getattr(acc, 'margin', 0) for acc in all_accounts.values())
            total_pnl = sum(acc.net_pnl for acc in all_accounts.values())
            
            # Calculate portfolio metrics
            metrics = {
                "total_balance": total_balance,
                "total_available": total_available,
                "total_margin": total_margin,
                "total_pnl": total_pnl,
                "total_equity": total_balance + total_pnl,
                "account_count": len(all_accounts)
            }
            
            if total_balance > 0:
                metrics["margin_ratio"] = total_margin / total_balance
                metrics["pnl_ratio"] = total_pnl / total_balance
                metrics["utilization_ratio"] = (total_balance - total_available) / total_balance
            else:
                metrics["margin_ratio"] = 0.0
                metrics["pnl_ratio"] = 0.0
                metrics["utilization_ratio"] = 0.0
            
            if total_available > 0:
                metrics["leverage_ratio"] = total_margin / total_available
            else:
                metrics["leverage_ratio"] = 0.0
            
            # Risk level assessment
            metrics["risk_level"] = self._assess_portfolio_risk_level(metrics)
            
            # Store in risk metrics
            self.risk_metrics = metrics
            
            # Add to history
            self._add_risk_history_entry(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating portfolio risk metrics: {e}")
            return {}
    
    def _assess_portfolio_risk_level(self, metrics: Dict[str, Any]) -> str:
        """Assess overall portfolio risk level."""
        try:
            margin_ratio = metrics.get("margin_ratio", 0)
            pnl_ratio = metrics.get("pnl_ratio", 0)
            leverage_ratio = metrics.get("leverage_ratio", 0)
            
            # Critical conditions
            if margin_ratio > 0.9 or pnl_ratio < -0.2 or leverage_ratio > 20:
                return RiskLevel.CRITICAL.value
            
            # High risk conditions
            if margin_ratio > 0.7 or pnl_ratio < -0.1 or leverage_ratio > 10:
                return RiskLevel.HIGH.value
            
            # Medium risk conditions
            if margin_ratio > 0.5 or pnl_ratio < -0.05 or leverage_ratio > 5:
                return RiskLevel.MEDIUM.value
            
            return RiskLevel.LOW.value
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk level: {e}")
            return RiskLevel.MEDIUM.value
    
    def _add_risk_history_entry(self, metrics: Dict[str, Any]) -> None:
        """Add entry to risk history for trend analysis."""
        entry = {
            "timestamp": datetime.now(),
            "metrics": metrics.copy()
        }
        
        self.risk_history.append(entry)
        
        # Keep only last 24 hours of history (assuming 5-minute intervals)
        max_entries = 24 * 12  # 288 entries
        if len(self.risk_history) > max_entries:
            self.risk_history.pop(0)
    
    async def _trigger_alert(self, alert: AccountRiskAlert) -> None:
        """Trigger a risk alert to all registered callbacks."""
        try:
            for callback in self.alert_callbacks:
                await callback(alert)
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    def register_warning_callback(self, callback: Callable) -> None:
        """Register callback for warning notifications."""
        if callback not in self.warning_callbacks:
            self.warning_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register callback for alert notifications."""
        if callback not in self.alert_callbacks:
            self.alert_callbacks.append(callback)
    
    def get_active_warnings(self, account_id: Optional[str] = None) -> List[AccountWarning]:
        """
        Get active warnings for an account or all accounts.
        
        Args:
            account_id: Specific account ID or None for all
            
        Returns:
            List of active warnings
        """
        if account_id:
            return self.active_warnings.get(account_id, [])
        else:
            all_warnings = []
            for warnings in self.active_warnings.values():
                all_warnings.extend(warnings)
            return all_warnings
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary."""
        return {
            "portfolio_metrics": self.risk_metrics.copy(),
            "active_warnings_count": sum(len(warnings) for warnings in self.active_warnings.values()),
            "critical_warnings_count": sum(
                1 for warnings in self.active_warnings.values()
                for warning in warnings
                if warning.is_critical
            ),
            "risk_level": self.risk_metrics.get("risk_level", "unknown"),
            "last_assessment": datetime.now()
        }