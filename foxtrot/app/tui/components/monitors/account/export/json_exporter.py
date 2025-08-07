"""
JSON export functionality for account data.

Handles JSON file writing and formatting for account exports.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import asdict

from foxtrot.util.object import AccountData

from ..config import AccountMonitorConfig, AccountDisplaySettings
from ..analysis_facade import AccountSummary, PortfolioSummary
from ..messages import AccountExportCompleted

logger = logging.getLogger(__name__)


class JSONExporter:
    """Handles JSON export functionality for account data."""
    
    def __init__(
        self,
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        export_dir: Path,
        completion_callback=None
    ):
        """Initialize JSON exporter."""
        self.config = config
        self.display_settings = display_settings
        self.export_dir = Path(export_dir)
        self.completion_callback = completion_callback
    
    async def export_accounts_json(
        self,
        accounts: Dict[str, AccountData],
        account_summaries: Optional[Dict[str, AccountSummary]] = None,
        risk_metrics: Optional[Dict[str, Any]] = None,
        portfolio_summary: Optional[PortfolioSummary] = None,
        filename: Optional[str] = None
    ) -> str:
        """Export account data to JSON format."""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"account_data_{timestamp}.json"
            
            filepath = self.export_dir / filename
            
            # Prepare export data
            export_data = {
                "export_metadata": self._create_metadata(len(accounts)),
                "accounts": {},
                "portfolio_summary": None,
                "risk_metrics": risk_metrics,
                "display_settings": self._serialize_display_settings()
            }
            
            # Add account data
            for account_id, account_data in accounts.items():
                export_data["accounts"][account_id] = self._serialize_account_data(
                    account_data,
                    account_summaries.get(account_id) if account_summaries else None
                )
            
            # Add portfolio summary
            if portfolio_summary:
                export_data["portfolio_summary"] = asdict(portfolio_summary)
            
            # Write JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Notify completion
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath),
                    record_count=len(accounts),
                    export_type="json",
                    success=True
                )
                await self.completion_callback(completion_msg)
            
            logger.info(f"Exported {len(accounts)} accounts to JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"JSON export failed: {e}"
            logger.error(error_msg)
            
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath) if 'filepath' in locals() else "unknown",
                    record_count=0,
                    export_type="json",
                    success=False,
                    error=error_msg
                )
                await self.completion_callback(completion_msg)
            
            raise
    
    def _create_metadata(self, record_count: int) -> Dict[str, Any]:
        """Create export metadata."""
        return {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "source": "Foxtrot Trading Platform - Account Monitor",
            "filters_applied": self.display_settings.get_filter_summary(),
            "record_count": record_count
        }
    
    def _serialize_account_data(
        self,
        account_data: AccountData,
        account_summary: Optional[AccountSummary] = None
    ) -> Dict[str, Any]:
        """Serialize account data for JSON export."""
        serialized = asdict(account_data)
        
        # Add calculated fields
        serialized["equity"] = account_data.balance + account_data.net_pnl
        serialized["margin_ratio"] = self._calculate_margin_ratio(account_data)
        serialized["risk_level"] = self._calculate_risk_level(account_data)
        serialized["performance_score"] = self._calculate_performance_score(account_data)
        
        # Add summary data if available
        if account_summary:
            serialized["summary"] = asdict(account_summary)
        
        return serialized
    
    def _calculate_margin_ratio(self, account_data: AccountData) -> float:
        """Calculate margin ratio for account."""
        margin = getattr(account_data, 'margin', 0)
        if account_data.balance > 0:
            return margin / account_data.balance
        return 0.0
    
    def _calculate_risk_level(self, account_data: AccountData) -> str:
        """Calculate risk level for account."""
        margin_ratio = self._calculate_margin_ratio(account_data)
        if margin_ratio > 0.8:
            return "HIGH"
        elif margin_ratio > 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_performance_score(self, account_data: AccountData) -> float:
        """Calculate performance score for account."""
        performance_score = 50.0  # Base score
        if account_data.balance > 0:
            pnl_ratio = account_data.net_pnl / account_data.balance
            performance_score += min(max(pnl_ratio * 100, -25), 25)
        return performance_score
    
    def _serialize_display_settings(self) -> Dict[str, Any]:
        """Serialize display settings for export."""
        try:
            return {
                "filters": self.display_settings.get_filter_summary(),
                "sort_column": getattr(self.display_settings, 'sort_column', None),
                "sort_order": getattr(self.display_settings, 'sort_order', None),
                "columns_visible": getattr(self.display_settings, 'columns_visible', []),
                "refresh_rate": getattr(self.display_settings, 'refresh_rate', None)
            }
        except Exception as e:
            logger.warning(f"Failed to serialize display settings: {e}")
            return {"error": "Failed to serialize display settings"}