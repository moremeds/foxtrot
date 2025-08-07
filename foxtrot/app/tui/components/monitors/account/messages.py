"""
Account monitor message classes and event definitions.

This module defines custom message classes for account monitor events,
enabling type-safe communication between components.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from textual.message import Message

from foxtrot.util.object import AccountData


class AccountMonitorMessage(Message):
    """Base class for all account monitor messages."""
    
    def __init__(self) -> None:
        """Initialize with timestamp."""
        super().__init__()
        self.timestamp = datetime.now()


class AccountProcessed(AccountMonitorMessage):
    """
    Message sent when an account is successfully processed.
    
    This message is emitted after an account data update has been
    processed and displayed in the monitor.
    """
    
    def __init__(self, account_data: AccountData) -> None:
        """
        Initialize with processed account data.
        
        Args:
            account_data: The AccountData that was processed
        """
        super().__init__()
        self.account_data = account_data
        self.account_id = account_data.vt_accountid
        self.balance = account_data.balance
        self.available = account_data.available
        self.currency = account_data.currency


class AccountWarning(AccountMonitorMessage):
    """
    Message sent when an account warning is triggered.
    
    Warnings can be triggered by low balances, high margin usage,
    significant losses, or other risk-related conditions.
    """
    
    WARNING_TYPES = {
        "LOW_BALANCE": "Low Available Balance",
        "HIGH_MARGIN": "High Margin Usage", 
        "SIGNIFICANT_LOSS": "Significant Loss",
        "MARGIN_CALL": "Margin Call Risk",
        "RISK_THRESHOLD": "Risk Threshold Exceeded"
    }
    
    def __init__(
        self, 
        account_data: AccountData, 
        warning: str, 
        warning_type: str = "GENERAL",
        severity: str = "medium"
    ) -> None:
        """
        Initialize warning message.
        
        Args:
            account_data: The AccountData that triggered the warning
            warning: Human-readable warning message
            warning_type: Type of warning (see WARNING_TYPES)
            severity: Warning severity (low, medium, high, critical)
        """
        super().__init__()
        self.account_data = account_data
        self.warning = warning
        self.warning_type = warning_type
        self.severity = severity.lower()
        self.account_id = account_data.vt_accountid
        
        # Validate severity level
        if self.severity not in ["low", "medium", "high", "critical"]:
            self.severity = "medium"
    
    @property
    def display_message(self) -> str:
        """Get formatted display message."""
        severity_icon = {
            "low": "ℹ️",
            "medium": "⚠️", 
            "high": "🔥",
            "critical": "🚨"
        }.get(self.severity, "⚠️")
        
        return f"{severity_icon} {self.warning}"
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical warning."""
        return self.severity == "critical"


class AccountSelected(AccountMonitorMessage):
    """
    Message sent when an account is selected for detailed operations.
    
    This message can be used to update trading panels or other components
    when a user selects a specific account.
    """
    
    def __init__(self, account_data: AccountData, action: str = "select") -> None:
        """
        Initialize account selection message.
        
        Args:
            account_data: The selected AccountData
            action: Action performed (select, focus, activate)
        """
        super().__init__()
        self.account_data = account_data
        self.action = action
        self.account_id = account_data.vt_accountid


class AccountStatisticsUpdated(AccountMonitorMessage):
    """
    Message sent when account statistics are recalculated.
    
    This message contains summary statistics for all accounts
    being monitored.
    """
    
    def __init__(self, statistics: Dict[str, Any], risk_metrics: Dict[str, Any]) -> None:
        """
        Initialize statistics update message.
        
        Args:
            statistics: Updated account statistics
            risk_metrics: Updated risk metrics
        """
        super().__init__()
        self.statistics = statistics.copy()
        self.risk_metrics = risk_metrics.copy()
        
        # Calculate derived metrics
        self.total_equity = (
            self.statistics.get("total_balance", 0) + 
            self.statistics.get("total_pnl", 0)
        )
        self.portfolio_value = self.total_equity
        
    @property
    def has_warnings(self) -> bool:
        """Check if statistics indicate warning conditions."""
        margin_ratio = self.risk_metrics.get("margin_ratio", 0)
        risk_utilization = self.risk_metrics.get("risk_utilization", 0)
        
        return margin_ratio > 0.8 or risk_utilization > 0.75


class AccountFilterChanged(AccountMonitorMessage):
    """
    Message sent when account filters are modified.
    
    This message notifies components about filter changes
    so they can update their display accordingly.
    """
    
    def __init__(
        self, 
        filter_type: str, 
        filter_value: Any, 
        active_filters: Dict[str, Any]
    ) -> None:
        """
        Initialize filter change message.
        
        Args:
            filter_type: Type of filter changed (currency, gateway, balance, etc.)
            filter_value: New filter value (None if cleared)
            active_filters: Dictionary of all currently active filters
        """
        super().__init__()
        self.filter_type = filter_type
        self.filter_value = filter_value
        self.active_filters = active_filters.copy()
        self.is_cleared = filter_value is None
        self.has_filters = bool(active_filters)


class AccountExportCompleted(AccountMonitorMessage):
    """
    Message sent when account data export is completed.
    
    This message provides information about the export operation
    and can be used to display success/failure notifications.
    """
    
    def __init__(
        self, 
        filepath: str, 
        record_count: int, 
        export_type: str = "csv",
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Initialize export completion message.
        
        Args:
            filepath: Path to the exported file
            record_count: Number of records exported
            export_type: Type of export (csv, json, xlsx)
            success: Whether export was successful
            error: Error message if export failed
        """
        super().__init__()
        self.filepath = filepath
        self.record_count = record_count
        self.export_type = export_type.lower()
        self.success = success
        self.error = error
    
    @property
    def display_message(self) -> str:
        """Get formatted display message."""
        if self.success:
            return f"Exported {self.record_count} accounts to {self.filepath}"
        else:
            return f"Export failed: {self.error or 'Unknown error'}"


class AccountRiskAlert(AccountMonitorMessage):
    """
    Message sent when account risk conditions require immediate attention.
    
    This is a higher-priority message than AccountWarning, typically
    used for margin calls or critical risk situations.
    """
    
    ALERT_TYPES = {
        "MARGIN_CALL": "Margin Call",
        "LIQUIDATION_RISK": "Liquidation Risk",  
        "BALANCE_CRITICAL": "Critical Balance",
        "SYSTEM_RISK": "System Risk Alert"
    }
    
    def __init__(
        self,
        account_data: AccountData,
        alert_type: str,
        alert_message: str,
        recommended_action: Optional[str] = None
    ) -> None:
        """
        Initialize risk alert message.
        
        Args:
            account_data: Account data that triggered the alert
            alert_type: Type of risk alert (see ALERT_TYPES)
            alert_message: Detailed alert message
            recommended_action: Suggested action to take
        """
        super().__init__()
        self.account_data = account_data
        self.alert_type = alert_type
        self.alert_message = alert_message
        self.recommended_action = recommended_action
        self.account_id = account_data.vt_accountid
        self.requires_immediate_attention = True
        
    @property
    def display_message(self) -> str:
        """Get formatted display message with urgency indicator."""
        return f"🚨 RISK ALERT: {self.alert_message}"
    
    @property
    def alert_level(self) -> str:
        """Get alert level for UI styling."""
        critical_types = {"MARGIN_CALL", "LIQUIDATION_RISK"}
        return "critical" if self.alert_type in critical_types else "high"