"""
Account monitor controller that orchestrates all modular components.

This module provides the main TUIAccountMonitor class that coordinates
all specialized components while maintaining backward compatibility.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

from foxtrot.core.event_engine import EventEngine
from foxtrot.util.object import AccountData
from foxtrot.util.event_type import EVENT_ACCOUNT

from .config import AccountMonitorConfig, AccountDisplaySettings
from .messages import AccountMonitorMessage, AccountExportCompleted
from .formatting import AccountDataFormatter
from .filtering import AccountFilterManager
from .statistics import AccountStatistics
from .risk_manager import AccountRiskManager
from .analysis_facade import AccountAnalyzer, AccountSummary, PortfolioSummary
from .actions_facade import AccountActionHandler
from .export_facade import AccountDataExporter

# Set up logging
logger = logging.getLogger(__name__)


class TUIAccountMonitor:
    """
    Main account monitor controller that orchestrates all modular components.
    
    This class maintains the original interface while using the new modular
    architecture internally. It coordinates between:
    - Configuration and display settings
    - Data formatting and filtering
    - Statistics tracking and analysis
    - Risk management and warnings
    - UI actions and export functionality
    """
    
    def __init__(
        self,
        event_engine: EventEngine,
        export_dir: Optional[Path] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize account monitor with all components.
        
        Args:
            event_engine: Event engine for receiving account updates
            export_dir: Directory for export files
            config_overrides: Optional configuration overrides
        """
        self.event_engine = event_engine
        
        # Initialize configuration and display settings
        self.config = AccountMonitorConfig()
        if config_overrides:
            self.config.update_from_dict(config_overrides)
        
        self.display_settings = AccountDisplaySettings()
        
        # Initialize all component modules
        self._init_components(export_dir or Path.cwd() / "exports")
        
        # State management
        self.account_data: Dict[str, AccountData] = {}
        self.is_running = False
        
        # Event callbacks
        self.update_callbacks: List[Callable] = []
        self.message_callbacks: List[Callable] = []
        
        # Register for account events
        self.event_engine.register(EVENT_ACCOUNT, self.on_account_update)
        
        logger.info("Account monitor initialized with modular architecture")
    
    def _init_components(self, export_dir: Path) -> None:
        """Initialize all modular components."""
        # Core functionality components
        self.formatter = AccountDataFormatter(self.config, self.display_settings)
        self.filter_manager = AccountFilterManager(self.config, self.display_settings)
        self.statistics = AccountStatistics(self.config)
        self.risk_manager = AccountRiskManager(self.config)
        self.analyzer = AccountAnalyzer(self.config)
        self.exporter = AccountDataExporter(self.config, self.display_settings, export_dir)
        
        # UI interaction component
        self.action_handler = AccountActionHandler(
            self.config, self.display_settings, self.filter_manager
        )
        
        # Set up component callbacks and connections
        self._setup_component_connections()
    
    def _setup_component_connections(self) -> None:
        """Set up connections between components."""
        # Set callbacks for action handler
        self.action_handler.set_message_callback(self._handle_system_message)
        self.action_handler.set_update_callback(self._trigger_display_update)
        self.action_handler.set_refresh_callback(self._refresh_account_data)
        
        # Set up export completion callbacks
        self.exporter.register_completion_callback(self._handle_export_completion)
        
        # Set up risk manager alert callbacks
        self.risk_manager.register_alert_callback(self._handle_risk_alert)
    
    async def start(self) -> None:
        """Start the account monitor."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Account monitor started")
        await self._trigger_system_message("Account monitor started")
    
    async def stop(self) -> None:
        """Stop the account monitor."""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Account monitor stopped")
        await self._trigger_system_message("Account monitor stopped")
    
    async def on_account_update(self, event) -> None:
        """
        Handle account data updates from event engine.
        
        Args:
            event: Account update event
        """
        if not self.is_running:
            return
        
        try:
            account_data: AccountData = event.data
            await self.update_account(account_data)
            
        except Exception as e:
            logger.error(f"Error handling account update: {e}")
            await self._trigger_system_message(f"Error updating account data: {e}")
    
    async def update_account(self, account_data: AccountData) -> None:
        """
        Update account data and refresh all components.
        
        Args:
            account_data: New or updated account data
        """
        try:
            account_id = account_data.vt_accountid
            
            # Store account data
            self.account_data[account_id] = account_data
            
            # Update all components
            await self._update_all_components(account_data)
            
            # Trigger display update
            await self._trigger_display_update()
            
        except Exception as e:
            logger.error(f"Error updating account {account_data.vt_accountid}: {e}")
    
    async def _update_all_components(self, account_data: AccountData) -> None:
        """Update all components with new account data."""
        # Update statistics
        await self.statistics.update_account(account_data)
        
        # Add to historical tracking
        self.analyzer.add_account_history_entry(account_data)
        
        # Assess risks
        warnings = await self.risk_manager.assess_account_risk(account_data)
        if warnings:
            for warning in warnings:
                await self._handle_account_warning(warning)
    
    async def get_filtered_accounts(self) -> Dict[str, AccountData]:
        """
        Get account data filtered by current filter settings.
        
        Returns:
            Dictionary of filtered account data
        """
        filtered_accounts = {}
        
        for account_id, account_data in self.account_data.items():
            if self.filter_manager.apply_all_filters(account_data):
                filtered_accounts[account_id] = account_data
        
        return filtered_accounts
    
    async def get_formatted_account_data(
        self, 
        account_data: AccountData,
        include_risk_metrics: bool = True
    ) -> Dict[str, str]:
        """
        Get formatted account data for display.
        
        Args:
            account_data: Account data to format
            include_risk_metrics: Whether to include risk metrics
            
        Returns:
            Dictionary of formatted field values
        """
        formatted_data = {}
        
        # Get basic formatted fields
        for field_name, field_config in self.config.HEADERS.items():
            value = getattr(account_data, field_name, "")
            formatted_value = self.formatter.format_cell_content(value, field_config)
            formatted_data[field_name] = formatted_value
        
        # Add calculated fields if requested
        if include_risk_metrics:
            risk_metrics = await self.risk_manager._calculate_account_risk_metrics(account_data)
            formatted_data.update(self._format_risk_metrics(risk_metrics))
        
        return formatted_data
    
    def _format_risk_metrics(self, risk_metrics: Dict[str, float]) -> Dict[str, str]:
        """Format risk metrics for display."""
        formatted = {}
        
        if "margin_ratio" in risk_metrics:
            formatted["margin_ratio"] = f"{risk_metrics['margin_ratio']:.1%}"
        
        if "available_ratio" in risk_metrics:
            formatted["available_ratio"] = f"{risk_metrics['available_ratio']:.1%}"
        
        if "leverage" in risk_metrics:
            formatted["leverage"] = f"{risk_metrics['leverage']:.2f}x"
        
        return formatted
    
    async def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Portfolio summary with analysis
        """
        filtered_accounts = await self.get_filtered_accounts()
        return self.analyzer.analyze_portfolio(filtered_accounts)
    
    async def get_account_summaries(self) -> Dict[str, AccountSummary]:
        """
        Get individual account summaries.
        
        Returns:
            Dictionary mapping account IDs to their summaries
        """
        summaries = {}
        filtered_accounts = await self.get_filtered_accounts()
        
        for account_id, account_data in filtered_accounts.items():
            summaries[account_id] = self.analyzer.analyze_account(account_data)
        
        return summaries
    
    async def get_statistics_summary(self) -> Dict[str, Any]:
        """Get current statistics summary."""
        return self.statistics.get_summary()
    
    async def get_risk_summary(self) -> Dict[str, Any]:
        """Get current risk summary."""
        # Calculate portfolio risk metrics
        await self.risk_manager.calculate_portfolio_risk_metrics(self.account_data)
        return self.risk_manager.get_risk_summary()
    
    # Filter Management Methods
    
    async def apply_currency_filter(self, currency: Optional[str]) -> None:
        """Apply currency filter."""
        self.filter_manager.add_currency_filter(currency)
        await self._trigger_display_update()
    
    async def apply_gateway_filter(self, gateway: Optional[str]) -> None:
        """Apply gateway filter."""
        self.filter_manager.add_gateway_filter(gateway)
        await self._trigger_display_update()
    
    async def apply_min_balance_filter(self, min_balance: Optional[float]) -> None:
        """Apply minimum balance filter."""
        self.filter_manager.add_min_balance_filter(min_balance)
        await self._trigger_display_update()
    
    async def clear_all_filters(self) -> None:
        """Clear all active filters."""
        self.filter_manager.clear_all_filters()
        await self._trigger_display_update()
    
    # Display Setting Methods
    
    def set_show_zero_balances(self, show: bool) -> None:
        """Set whether to show zero balance accounts."""
        self.display_settings.show_zero_balances = show
        self.filter_manager.set_zero_balance_visibility(show)
    
    def set_group_by_currency(self, group: bool) -> None:
        """Set whether to group accounts by currency."""
        self.display_settings.group_by_currency = group
    
    def set_show_percentage_changes(self, show: bool) -> None:
        """Set whether to show percentage changes."""
        self.display_settings.show_percentage_changes = show
    
    # Action Handler Methods (delegate to action_handler)
    
    async def handle_keyboard_shortcut(self, key: str, context: Dict[str, Any] = None) -> bool:
        """Handle keyboard shortcut."""
        return await self.action_handler.handle_keyboard_shortcut(key, context)
    
    def get_available_actions(self) -> Dict[str, str]:
        """Get available keyboard actions."""
        return self.action_handler.get_available_actions()
    
    # Export Methods
    
    async def export_accounts_csv(self, filename: Optional[str] = None) -> str:
        """Export accounts to CSV format."""
        filtered_accounts = await self.get_filtered_accounts()
        portfolio_summary = await self.get_portfolio_summary()
        risk_summary = await self.get_risk_summary()
        
        return await self.exporter.export_accounts_csv(
            filtered_accounts,
            risk_summary.get("portfolio_metrics", {}),
            portfolio_summary,
            filename
        )
    
    async def export_accounts_json(self, filename: Optional[str] = None) -> str:
        """Export accounts to JSON format."""
        filtered_accounts = await self.get_filtered_accounts()
        account_summaries = await self.get_account_summaries()
        portfolio_summary = await self.get_portfolio_summary()
        risk_summary = await self.get_risk_summary()
        
        return await self.exporter.export_accounts_json(
            filtered_accounts,
            account_summaries,
            risk_summary.get("portfolio_metrics", {}),
            portfolio_summary,
            filename
        )
    
    async def export_risk_analysis(self, filename: Optional[str] = None) -> str:
        """Export risk analysis data."""
        risk_summary = await self.get_risk_summary()
        active_warnings = {
            account_id: self.risk_manager.get_active_warnings(account_id)
            for account_id in self.account_data.keys()
        }
        
        return await self.exporter.export_risk_analysis(
            risk_summary.get("portfolio_metrics", {}),
            self.risk_manager.risk_history,
            active_warnings,
            filename
        )
    
    # Event Callback Registration
    
    def register_update_callback(self, callback: Callable) -> None:
        """Register callback for display updates."""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def register_message_callback(self, callback: Callable) -> None:
        """Register callback for system messages."""
        if callback not in self.message_callbacks:
            self.message_callbacks.append(callback)
    
    # Internal Event Handling
    
    async def _trigger_display_update(self) -> None:
        """Trigger display update callbacks."""
        try:
            for callback in self.update_callbacks:
                await callback()
        except Exception as e:
            logger.error(f"Error in display update callback: {e}")
    
    async def _trigger_system_message(self, message: str) -> None:
        """Trigger system message callbacks."""
        try:
            for callback in self.message_callbacks:
                await callback(message)
        except Exception as e:
            logger.error(f"Error in message callback: {e}")
    
    async def _handle_system_message(self, message: str) -> None:
        """Handle system messages from components."""
        await self._trigger_system_message(message)
    
    async def _handle_account_warning(self, warning) -> None:
        """Handle account warnings from risk manager."""
        message = f"⚠️  {warning.account_data.vt_accountid}: {warning.warning}"
        await self._trigger_system_message(message)
    
    async def _handle_risk_alert(self, alert) -> None:
        """Handle critical risk alerts."""
        message = f"🚨 ALERT - {alert.account_data.vt_accountid}: {alert.alert_message}"
        await self._trigger_system_message(message)
        logger.warning(f"Risk alert: {alert.alert_message}")
    
    async def _handle_export_completion(self, completion_msg: AccountExportCompleted) -> None:
        """Handle export completion notifications."""
        if completion_msg.success:
            message = f"✅ Export completed: {completion_msg.filepath} ({completion_msg.record_count} records)"
        else:
            message = f"❌ Export failed: {completion_msg.error}"
        
        await self._trigger_system_message(message)
    
    async def _refresh_account_data(self) -> None:
        """Refresh account data from sources."""
        # This would typically trigger a data refresh from the adapters
        # For now, just update all components with current data
        try:
            for account_data in self.account_data.values():
                await self._update_all_components(account_data)
            
            await self._trigger_system_message("Account data refreshed")
            
        except Exception as e:
            logger.error(f"Error refreshing account data: {e}")
            await self._trigger_system_message("Error refreshing account data")
    
    # Utility Methods
    
    def get_account_count(self) -> int:
        """Get total number of accounts."""
        return len(self.account_data)
    
    def get_filtered_account_count(self) -> int:
        """Get number of accounts after filtering."""
        count = 0
        for account_data in self.account_data.values():
            if self.filter_manager.apply_all_filters(account_data):
                count += 1
        return count
    
    def get_config(self) -> AccountMonitorConfig:
        """Get current configuration."""
        return self.config
    
    def get_display_settings(self) -> AccountDisplaySettings:
        """Get current display settings."""
        return self.display_settings
    
    async def cleanup(self) -> None:
        """Cleanup resources and stop monitoring."""
        await self.stop()
        
        # Clean up old export files
        try:
            await self.exporter.cleanup_old_exports(days=30)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        logger.info("Account monitor cleanup completed")