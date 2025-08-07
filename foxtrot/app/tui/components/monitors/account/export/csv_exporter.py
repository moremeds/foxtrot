"""
CSV export functionality for account data.

Handles CSV file writing and formatting for account exports.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from foxtrot.util.object import AccountData
from foxtrot.app.tui.utils.formatters import TUIFormatter

from ..config import AccountMonitorConfig, AccountDisplaySettings
from ..analysis_facade import AccountSummary, PortfolioSummary
from ..messages import AccountExportCompleted

logger = logging.getLogger(__name__)


class CSVExporter:
    """Handles CSV export functionality for account data."""
    
    def __init__(
        self,
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        export_dir: Path,
        completion_callback=None
    ):
        """Initialize CSV exporter."""
        self.config = config
        self.display_settings = display_settings
        self.export_dir = Path(export_dir)
        self.completion_callback = completion_callback
    
    async def export_accounts_csv(
        self,
        accounts: Dict[str, AccountData],
        risk_metrics: Optional[Dict[str, Any]] = None,
        portfolio_summary: Optional[PortfolioSummary] = None,
        filename: Optional[str] = None
    ) -> str:
        """Export account data to CSV format."""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"account_balances_{timestamp}.csv"
            
            filepath = self.export_dir / filename
            
            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = self._get_csv_headers()
                writer.writerow(headers)
                
                # Write account data rows
                is_first_row = True
                for account_id, account_data in accounts.items():
                    row = self._format_account_row(account_data, is_first_row)
                    writer.writerow(row)
                    is_first_row = False
                
                # Write summary section if available
                if portfolio_summary:
                    await self._write_summary_section(writer, portfolio_summary)
                
                # Write risk metrics section if available
                if risk_metrics:
                    await self._write_risk_section(writer, risk_metrics)
            
            # Notify completion
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath),
                    record_count=len(accounts),
                    export_type="csv",
                    success=True
                )
                await self.completion_callback(completion_msg)
            
            logger.info(f"Exported {len(accounts)} accounts to CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"CSV export failed: {e}"
            logger.error(error_msg)
            
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath) if 'filepath' in locals() else "unknown",
                    record_count=0,
                    export_type="csv",
                    success=False,
                    error=error_msg
                )
                await self.completion_callback(completion_msg)
            
            raise
    
    def _get_csv_headers(self) -> List[str]:
        """Get CSV headers based on configuration."""
        headers = ["account_id"]
        
        # Add configured field columns
        for field_name in self.config.export_fields:
            headers.append(field_name)
        
        # Add calculated columns
        headers.extend([
            "equity", "margin_ratio", "risk_level", "performance_score"
        ])
        
        # Add metadata columns
        headers.extend(["export_timestamp", "filters_applied"])
        
        return headers
    
    def _format_account_row(self, account_data: AccountData, is_first_row: bool = False) -> List[str]:
        """Format a single account data row for CSV."""
        row = [account_data.accountid]
        
        # Add configured fields
        for field_name in self.config.export_fields:
            value = getattr(account_data, field_name, "")
            
            # Format specific fields
            if field_name in ["balance", "frozen", "available"]:
                formatted_value = f"{float(value):.2f}" if value else "0.00"
            elif field_name == "net_pnl":
                formatted_value = f"{float(value):+.2f}" if value else "0.00"
            elif field_name == "datetime":
                formatted_value = value.isoformat() if hasattr(value, 'isoformat') else str(value)
            else:
                formatted_value = str(value)
            
            row.append(formatted_value)
        
        # Add calculated fields
        equity = account_data.balance + account_data.net_pnl
        row.append(f"{equity:.2f}")
        
        # Margin ratio
        margin_ratio = 0.0
        margin = getattr(account_data, 'margin', 0)
        if account_data.balance > 0:
            margin_ratio = margin / account_data.balance
        row.append(f"{margin_ratio:.1%}")
        
        # Risk level
        risk_level = self._calculate_risk_level(margin_ratio)
        row.append(risk_level)
        
        # Performance score
        performance_score = self._calculate_performance_score(account_data)
        row.append(f"{performance_score:.1f}")
        
        # Metadata (only on first row)
        if is_first_row:
            row.extend([
                datetime.now().isoformat(),
                self.display_settings.get_filter_summary()
            ])
        else:
            row.extend(["", ""])
        
        return row
    
    def _calculate_risk_level(self, margin_ratio: float) -> str:
        """Calculate risk level based on margin ratio."""
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
    
    async def _write_summary_section(self, writer: csv.writer, portfolio_summary: PortfolioSummary) -> None:
        """Write portfolio summary section to CSV."""
        writer.writerow([])  # Empty row separator
        writer.writerow(["PORTFOLIO SUMMARY"])
        writer.writerow(["Total Accounts", portfolio_summary.total_accounts])
        writer.writerow(["Total Balance", f"{portfolio_summary.total_balance:.2f}"])
        writer.writerow(["Total Equity", f"{portfolio_summary.total_equity:.2f}"])
        writer.writerow(["Total PnL", f"{portfolio_summary.total_pnl:+.2f}"])
        writer.writerow(["Risk Level", portfolio_summary.risk_level])
    
    async def _write_risk_section(self, writer: csv.writer, risk_metrics: Dict[str, Any]) -> None:
        """Write risk metrics section to CSV."""
        writer.writerow([])  # Empty row separator
        writer.writerow(["RISK METRICS"])
        
        for metric_name, metric_value in risk_metrics.items():
            formatted_value = str(metric_value)
            if isinstance(metric_value, float):
                formatted_value = f"{metric_value:.4f}"
            writer.writerow([metric_name, formatted_value])