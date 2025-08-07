"""
Account monitor data export functionality.

This module provides a simplified facade that coordinates specialized export functionality
through modular components. Each export format is handled by dedicated components.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from foxtrot.util.object import AccountData

from .config import AccountMonitorConfig, AccountDisplaySettings
from .analysis_facade import AccountSummary, PortfolioSummary
from .messages import AccountExportCompleted

# Import specialized export components
from .export.csv_exporter import CSVExporter
from .export.json_exporter import JSONExporter
from .export.risk_exporter import RiskExporter
from .export.portfolio_exporter import PortfolioExporter

# Set up logging
logger = logging.getLogger(__name__)


class AccountDataExporter:
    """
    Facade coordinator for account data export functionality.
    
    Delegates to specialized export components while maintaining backward compatibility.
    """
    
    def __init__(
        self, 
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        export_dir: Path
    ):
        """
        Initialize data exporter facade.
        
        Args:
            config: Account monitor configuration
            display_settings: Current display settings
            export_dir: Directory for export files
        """
        self.config = config
        self.display_settings = display_settings
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Export callbacks
        self.completion_callbacks: List[callable] = []
        
        # Initialize specialized export components
        self._init_exporters()
    
    def _init_exporters(self) -> None:
        """Initialize all specialized export components."""
        completion_callback = self._notify_completion
        
        self.csv_exporter = CSVExporter(
            self.config, 
            self.display_settings, 
            self.export_dir,
            completion_callback
        )
        
        self.json_exporter = JSONExporter(
            self.config, 
            self.display_settings, 
            self.export_dir,
            completion_callback
        )
        
        self.risk_exporter = RiskExporter(
            self.config, 
            self.display_settings, 
            self.export_dir,
            completion_callback
        )
        
        self.portfolio_exporter = PortfolioExporter(
            self.config, 
            self.display_settings, 
            self.export_dir,
            completion_callback
        )
    
    def register_completion_callback(self, callback: callable) -> None:
        """Register callback for export completion notifications."""
        if callback not in self.completion_callbacks:
            self.completion_callbacks.append(callback)
    
    async def _notify_completion(self, message: AccountExportCompleted) -> None:
        """Notify all registered callbacks of export completion."""
        for callback in self.completion_callbacks:
            try:
                await callback(message)
            except Exception as e:
                logger.error(f"Error in export completion callback: {e}")
    
    # CSV Export Methods
    async def export_accounts_csv(
        self,
        accounts: Dict[str, AccountData],
        risk_metrics: Optional[Dict[str, Any]] = None,
        portfolio_summary: Optional[PortfolioSummary] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Export account data to CSV format.
        
        Args:
            accounts: Dictionary of account data to export
            risk_metrics: Optional portfolio risk metrics
            portfolio_summary: Optional portfolio summary
            filename: Optional custom filename
            
        Returns:
            Path to created CSV file
        """
        return await self.csv_exporter.export_accounts_csv(
            accounts, risk_metrics, portfolio_summary, filename
        )
    
    # JSON Export Methods
    async def export_accounts_json(
        self,
        accounts: Dict[str, AccountData],
        account_summaries: Optional[Dict[str, AccountSummary]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None,
        portfolio_summary: Optional[PortfolioSummary] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Export account data to JSON format.
        
        Args:
            accounts: Dictionary of account data to export
            account_summaries: Optional account summaries
            risk_metrics: Optional risk metrics
            portfolio_summary: Optional portfolio summary
            filename: Optional custom filename
            
        Returns:
            Path to created JSON file
        """
        return await self.json_exporter.export_accounts_json(
            accounts, account_summaries, risk_metrics, portfolio_summary, filename
        )
    
    # Risk Analysis Export Methods
    async def export_risk_analysis(
        self,
        risk_metrics: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Export risk analysis data to JSON format.
        
        Args:
            risk_metrics: Current risk metrics
            filename: Optional custom filename
            
        Returns:
            Path to created file
        """
        return await self.risk_exporter.export_risk_analysis(risk_metrics, filename)
    
    # Portfolio Summary Export Methods
    async def export_portfolio_summary(
        self,
        portfolio_summary: PortfolioSummary,
        currency_breakdown: Optional[Dict[str, float]] = None,
        gateway_breakdown: Optional[Dict[str, int]] = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Export portfolio summary to JSON format.
        
        Args:
            portfolio_summary: Portfolio summary data
            currency_breakdown: Optional currency breakdown data
            gateway_breakdown: Optional gateway breakdown data
            filename: Optional custom filename
            
        Returns:
            Path to created file
        """
        return await self.portfolio_exporter.export_portfolio_summary(
            portfolio_summary, currency_breakdown, gateway_breakdown, filename
        )
    
    # Utility Methods
    def get_export_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["csv", "json", "risk_analysis", "portfolio_summary"]
    
    def get_export_directory(self) -> str:
        """Get export directory path."""
        return str(self.export_dir)
    
    async def cleanup_old_exports(self, days: int = 30) -> int:
        """
        Clean up export files older than specified days.
        
        Args:
            days: Number of days to retain files
            
        Returns:
            Number of files cleaned up
        """
        try:
            from datetime import datetime
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            cleaned_count = 0
            
            # Clean CSV and JSON files
            for pattern in ["*.csv", "*.json"]:
                for file_path in self.export_dir.glob(pattern):
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old export files")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old exports: {e}")
            return 0