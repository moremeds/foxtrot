"""
Portfolio summary export functionality for account data.

Handles portfolio-level summary and analysis export.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import asdict

from ..config import AccountMonitorConfig, AccountDisplaySettings
from ..analysis_facade import PortfolioSummary
from ..messages import AccountExportCompleted

logger = logging.getLogger(__name__)


class PortfolioExporter:
    """Handles portfolio summary export functionality."""
    
    def __init__(
        self,
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        export_dir: Path,
        completion_callback=None
    ):
        """Initialize portfolio exporter."""
        self.config = config
        self.display_settings = display_settings
        self.export_dir = Path(export_dir)
        self.completion_callback = completion_callback
    
    async def export_portfolio_summary(
        self,
        portfolio_summary: PortfolioSummary,
        currency_breakdown: Optional[Dict[str, float]] = None,
        gateway_breakdown: Optional[Dict[str, int]] = None,
        filename: Optional[str] = None
    ) -> str:
        """Export portfolio summary to JSON format."""
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"portfolio_summary_{timestamp}.json"
            
            filepath = self.export_dir / filename
            
            # Prepare summary data
            summary_data = {
                "export_metadata": self._create_metadata(),
                "portfolio_summary": asdict(portfolio_summary),
                "currency_breakdown": currency_breakdown or {},
                "gateway_breakdown": gateway_breakdown or {},
                "analysis": self._generate_portfolio_analysis(
                    portfolio_summary, currency_breakdown, gateway_breakdown
                )
            }
            
            # Write JSON file
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Notify completion
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath),
                    record_count=1,
                    export_type="portfolio_summary",
                    success=True
                )
                await self.completion_callback(completion_msg)
            
            logger.info(f"Exported portfolio summary to {filepath}")
            return str(filepath)
            
        except Exception as e:
            error_msg = f"Portfolio summary export failed: {e}"
            logger.error(error_msg)
            
            if self.completion_callback:
                completion_msg = AccountExportCompleted(
                    filepath=str(filepath) if 'filepath' in locals() else "unknown",
                    record_count=0,
                    export_type="portfolio_summary",
                    success=False,
                    error=error_msg
                )
                await self.completion_callback(completion_msg)
            
            raise
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create export metadata for portfolio summary."""
        return {
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "type": "portfolio_summary",
            "source": "Foxtrot Trading Platform - Account Monitor"
        }
    
    def _generate_portfolio_analysis(
        self,
        portfolio_summary: PortfolioSummary,
        currency_breakdown: Optional[Dict[str, float]],
        gateway_breakdown: Optional[Dict[str, int]]
    ) -> Dict[str, Any]:
        """Generate portfolio analysis from summary data."""
        analysis = {
            "diversification_analysis": {},
            "risk_analysis": {},
            "performance_analysis": {}
        }
        
        try:
            # Diversification analysis
            currency_count = len(currency_breakdown) if currency_breakdown else 0
            gateway_count = len(gateway_breakdown) if gateway_breakdown else 0
            
            analysis["diversification_analysis"] = {
                "currency_count": currency_count,
                "gateway_count": gateway_count,
                "diversification_score": portfolio_summary.diversification_score,
                "diversification_level": self._assess_diversification_level(
                    currency_count, gateway_count, portfolio_summary.diversification_score
                )
            }
            
            # Risk analysis
            pnl_ratio = 0.0
            if portfolio_summary.total_balance > 0:
                pnl_ratio = portfolio_summary.total_pnl / portfolio_summary.total_balance
            
            analysis["risk_analysis"] = {
                "risk_level": portfolio_summary.risk_level,
                "total_equity": portfolio_summary.total_equity,
                "pnl_ratio": pnl_ratio,
                "risk_assessment": self._assess_risk_level(portfolio_summary.risk_level, pnl_ratio)
            }
            
            # Performance analysis
            analysis["performance_analysis"] = {
                "return_percentage": pnl_ratio * 100,
                "performance_category": self._categorize_performance(pnl_ratio),
                "account_efficiency": portfolio_summary.total_accounts / max(gateway_count, 1) if gateway_count else 0
            }
            
        except Exception as e:
            logger.warning(f"Error generating portfolio analysis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _assess_diversification_level(
        self,
        currency_count: int,
        gateway_count: int,
        diversification_score: float
    ) -> str:
        """Assess the diversification level of the portfolio."""
        if diversification_score >= 0.8 and currency_count >= 3 and gateway_count >= 2:
            return "EXCELLENT"
        elif diversification_score >= 0.6 and currency_count >= 2:
            return "GOOD"
        elif diversification_score >= 0.4:
            return "MODERATE"
        else:
            return "POOR"
    
    def _assess_risk_level(self, risk_level: str, pnl_ratio: float) -> str:
        """Provide risk level assessment."""
        if risk_level == "HIGH":
            return "High risk detected - consider risk reduction strategies"
        elif risk_level == "MEDIUM":
            if pnl_ratio < -0.1:
                return "Medium risk with negative performance - monitor closely"
            else:
                return "Medium risk level - acceptable with proper monitoring"
        else:
            return "Low risk level - well-managed portfolio"
    
    def _categorize_performance(self, pnl_ratio: float) -> str:
        """Categorize performance based on P&L ratio."""
        if pnl_ratio >= 0.15:
            return "EXCELLENT"
        elif pnl_ratio >= 0.05:
            return "GOOD"
        elif pnl_ratio >= -0.05:
            return "NEUTRAL"
        elif pnl_ratio >= -0.15:
            return "POOR"
        else:
            return "VERY_POOR"