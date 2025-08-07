"""
Analysis coordinator component.

Handles coordination of analysis operations across multiple specialized
components and manages advanced analysis workflows.
"""

import logging
from typing import Any, Dict, List

from foxtrot.util.object import AccountData
from .data_structures import CurrencyBreakdown, GatewayBreakdown
from .account_analyzer import IndividualAccountAnalyzer
from .portfolio_analyzer import PortfolioAnalyzer
from .historical_tracker import HistoricalTracker
from .report_generator import ReportGenerator

# Set up logging
logger = logging.getLogger(__name__)


class AnalysisCoordinator:
    """Coordinates advanced analysis operations across multiple components."""
    
    def __init__(
        self,
        account_analyzer: IndividualAccountAnalyzer,
        portfolio_analyzer: PortfolioAnalyzer,
        historical_tracker: HistoricalTracker,
        report_generator: ReportGenerator
    ):
        """Initialize analysis coordinator."""
        self.account_analyzer = account_analyzer
        self.portfolio_analyzer = portfolio_analyzer
        self.historical_tracker = historical_tracker
        self.report_generator = report_generator

    # Advanced Analysis Methods (coordinate multiple components)
    
    def get_detailed_performance_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Get comprehensive performance report with multiple metrics.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Detailed formatted performance report
        """
        try:
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            return self.report_generator.get_detailed_performance_report(portfolio)
        except Exception as e:
            logger.error(f"Error generating detailed performance report: {e}")
            return "Detailed performance report unavailable"

    def get_currency_breakdown_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Get formatted currency breakdown report.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Formatted currency breakdown report
        """
        try:
            breakdown = self.report_generator.get_currency_breakdown(all_accounts)
            return self.report_generator.get_currency_breakdown_report(breakdown)
        except Exception as e:
            logger.error(f"Error generating currency breakdown report: {e}")
            return "Currency breakdown report unavailable"

    def get_gateway_breakdown_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Get formatted gateway breakdown report.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Formatted gateway breakdown report
        """
        try:
            breakdown = self.report_generator.get_gateway_breakdown(all_accounts)
            return self.report_generator.get_gateway_breakdown_report(breakdown)
        except Exception as e:
            logger.error(f"Error generating gateway breakdown report: {e}")
            return "Gateway breakdown report unavailable"

    def get_risk_summary_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Get formatted risk summary report.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Formatted risk summary report
        """
        try:
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            return self.report_generator.get_risk_summary_report(portfolio)
        except Exception as e:
            logger.error(f"Error generating risk summary report: {e}")
            return "Risk summary report unavailable"

    def get_performance_summary(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Get formatted performance summary string.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Formatted performance summary
        """
        try:
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            return self.report_generator.get_performance_summary(portfolio)
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return "Performance summary unavailable"

    def get_account_trend_analysis(self, account_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get trend analysis for a specific account.
        
        Args:
            account_id: Account identifier
            hours: Period in hours to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        return self.historical_tracker.get_trend_analysis(account_id, hours)

    def get_balance_change_analysis(self, account_id: str, hours: int = 24) -> Dict[str, float]:
        """
        Get balance change analysis for a specific account.
        
        Args:
            account_id: Account identifier
            hours: Period in hours to calculate change
            
        Returns:
            Dictionary with change statistics
        """
        return self.historical_tracker.calculate_balance_change(account_id, hours)

    def get_comprehensive_analysis(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """
        Get comprehensive analysis combining multiple analysis types.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        try:
            # Portfolio analysis
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            
            # Currency and gateway breakdowns
            currency_breakdown = self.report_generator.get_currency_breakdown(all_accounts)
            gateway_breakdown = self.report_generator.get_gateway_breakdown(all_accounts)
            
            # Individual account summaries
            account_summaries = {}
            for account_id, account_data in all_accounts.items():
                account_summaries[account_id] = self.account_analyzer.analyze_account(account_data)
            
            return {
                "portfolio": portfolio,
                "currency_breakdown": currency_breakdown,
                "gateway_breakdown": gateway_breakdown,
                "account_summaries": account_summaries,
                "analysis_timestamp": self.historical_tracker.get_statistics().get("last_cleanup")
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analysis: {e}")
            return {}

    def get_risk_dashboard(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """
        Get risk-focused dashboard data.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary with risk dashboard data
        """
        try:
            # Portfolio-level risk
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            
            # Individual account risks
            high_risk_accounts = []
            account_risk_scores = {}
            
            for account_id, account_data in all_accounts.items():
                risk_metrics = self.account_analyzer.calculate_risk_metrics(account_data)
                account_risk_scores[account_id] = risk_metrics.risk_score
                
                if risk_metrics.risk_level in ["critical", "high"]:
                    high_risk_accounts.append({
                        "account_id": account_id,
                        "risk_level": risk_metrics.risk_level,
                        "risk_score": risk_metrics.risk_score,
                        "balance": account_data.balance
                    })
            
            return {
                "portfolio_risk_level": portfolio.risk_level,
                "diversification_score": portfolio.diversification_score,
                "high_risk_accounts": high_risk_accounts,
                "account_risk_scores": account_risk_scores,
                "total_accounts": len(all_accounts),
                "accounts_at_risk": len(high_risk_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error generating risk dashboard: {e}")
            return {}

    def get_performance_dashboard(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """
        Get performance-focused dashboard data.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary with performance dashboard data
        """
        try:
            # Portfolio performance
            portfolio = self.portfolio_analyzer.analyze_portfolio(all_accounts)
            
            # Top performing accounts
            account_performances = []
            for account_id, account_data in all_accounts.items():
                performance = self.account_analyzer.get_account_performance_metrics(account_data)
                account_performances.append({
                    "account_id": account_id,
                    "performance_score": performance.performance_score,
                    "return_on_equity_pct": performance.return_on_equity_pct,
                    "balance": account_data.balance
                })
            
            # Sort by performance score
            account_performances.sort(key=lambda x: x["performance_score"], reverse=True)
            
            return {
                "portfolio_metrics": portfolio.performance_metrics,
                "total_equity": portfolio.total_equity,
                "total_pnl": portfolio.total_pnl,
                "top_performers": account_performances[:5],  # Top 5 performers
                "bottom_performers": account_performances[-3:],  # Bottom 3 performers
                "account_count": len(all_accounts)
            }
            
        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            return {}

    # Component Statistics and Status
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get comprehensive analysis system statistics."""
        try:
            historical_stats = self.historical_tracker.get_statistics()
            
            return {
                "historical_data": historical_stats,
                "components_status": {
                    "account_analyzer": "active" if self.account_analyzer else "inactive",
                    "portfolio_analyzer": "active" if self.portfolio_analyzer else "inactive",
                    "historical_tracker": "active" if self.historical_tracker else "inactive",
                    "report_generator": "active" if self.report_generator else "inactive"
                },
                "analysis_capabilities": {
                    "individual_account_analysis": True,
                    "portfolio_analysis": True,
                    "historical_tracking": True,
                    "report_generation": True,
                    "risk_assessment": True,
                    "performance_metrics": True
                }
            }
        except Exception as e:
            logger.error(f"Error getting analysis statistics: {e}")
            return {}

    # Component Access Methods
    
    def get_account_analyzer(self) -> IndividualAccountAnalyzer:
        """Get individual account analyzer component."""
        return self.account_analyzer

    def get_portfolio_analyzer(self) -> PortfolioAnalyzer:
        """Get portfolio analyzer component."""
        return self.portfolio_analyzer

    def get_historical_tracker(self) -> HistoricalTracker:
        """Get historical tracker component."""
        return self.historical_tracker

    def get_report_generator(self) -> ReportGenerator:
        """Get report generator component."""
        return self.report_generator