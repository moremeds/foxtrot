"""
Account monitor analysis and summary tools.

Simplified facade that coordinates account analysis functionality through
specialized components for individual accounts, portfolios, historical tracking,
and report generation.
"""

import logging
from typing import Any, Dict, List

from foxtrot.util.object import AccountData
from .config import AccountMonitorConfig

# Import specialized analysis components
from .analysis.data_structures import AccountSummary, PortfolioSummary, CurrencyBreakdown, GatewayBreakdown
from .analysis.account_analyzer import IndividualAccountAnalyzer
from .analysis.portfolio_analyzer import PortfolioAnalyzer
from .analysis.historical_tracker import HistoricalTracker
from .analysis.report_generator import ReportGenerator
from .analysis.analysis_coordinator import AnalysisCoordinator

# Set up logging
logger = logging.getLogger(__name__)


class AccountAnalyzer:
    """
    Account analysis facade that coordinates comprehensive account analysis
    and reporting capabilities through specialized components.
    
    Features:
    - Individual account performance analysis
    - Portfolio composition analysis
    - Risk-adjusted performance metrics
    - Historical trend analysis
    - Comparative analysis across accounts
    - Performance attribution
    """
    
    def __init__(self, config: AccountMonitorConfig):
        """
        Initialize account analyzer facade.
        
        Args:
            config: Account monitor configuration
        """
        self.config = config
        
        # Initialize specialized analysis components
        self._init_analysis_components()

    def _init_analysis_components(self) -> None:
        """Initialize specialized analysis components."""
        # Individual analysis components
        self.account_analyzer = IndividualAccountAnalyzer()
        self.portfolio_analyzer = PortfolioAnalyzer()
        self.historical_tracker = HistoricalTracker()
        self.report_generator = ReportGenerator()
        
        # Analysis coordinator that handles complex operations
        self.analysis_coordinator = AnalysisCoordinator(
            self.account_analyzer,
            self.portfolio_analyzer,
            self.historical_tracker,
            self.report_generator
        )

    # Main Analysis Methods (delegate to specialized components)
    
    def analyze_account(self, account_data: AccountData) -> AccountSummary:
        """Analyze individual account performance and risk."""
        return self.account_analyzer.analyze_account(account_data)

    def analyze_portfolio(self, all_accounts: Dict[str, AccountData]) -> PortfolioSummary:
        """Analyze entire portfolio across all accounts."""
        return self.portfolio_analyzer.analyze_portfolio(all_accounts)

    # Historical Tracking Methods
    
    def add_account_history_entry(self, account_data: AccountData) -> None:
        """Add historical entry for an account."""
        self.historical_tracker.add_account_history_entry(account_data)

    def get_balance_history(self, account_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get balance history for a specific account."""
        return self.historical_tracker.get_balance_history(account_id, hours)

    # Report Generation Methods
    
    def get_currency_breakdown(self, all_accounts: Dict[str, AccountData]) -> Dict[str, CurrencyBreakdown]:
        """Get detailed breakdown by currency."""
        return self.report_generator.get_currency_breakdown(all_accounts)

    def get_gateway_breakdown(self, all_accounts: Dict[str, AccountData]) -> Dict[str, GatewayBreakdown]:
        """Get detailed breakdown by gateway."""
        return self.report_generator.get_gateway_breakdown(all_accounts)

    # Advanced Analysis Methods (delegate to analysis_coordinator)
    
    def get_performance_summary(self, all_accounts: Dict[str, AccountData]) -> str:
        """Get formatted performance summary string."""
        return self.analysis_coordinator.get_performance_summary(all_accounts)

    def get_detailed_performance_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """Get comprehensive performance report with multiple metrics."""
        return self.analysis_coordinator.get_detailed_performance_report(all_accounts)

    def get_currency_breakdown_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """Get formatted currency breakdown report."""
        return self.analysis_coordinator.get_currency_breakdown_report(all_accounts)

    def get_gateway_breakdown_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """Get formatted gateway breakdown report."""
        return self.analysis_coordinator.get_gateway_breakdown_report(all_accounts)

    def get_risk_summary_report(self, all_accounts: Dict[str, AccountData]) -> str:
        """Get formatted risk summary report."""
        return self.analysis_coordinator.get_risk_summary_report(all_accounts)

    def get_account_trend_analysis(self, account_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get trend analysis for a specific account."""
        return self.analysis_coordinator.get_account_trend_analysis(account_id, hours)

    def get_balance_change_analysis(self, account_id: str, hours: int = 24) -> Dict[str, float]:
        """Get balance change analysis for a specific account."""
        return self.analysis_coordinator.get_balance_change_analysis(account_id, hours)

    def get_comprehensive_analysis(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """Get comprehensive analysis combining multiple analysis types."""
        return self.analysis_coordinator.get_comprehensive_analysis(all_accounts)

    def get_risk_dashboard(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """Get risk-focused dashboard data."""
        return self.analysis_coordinator.get_risk_dashboard(all_accounts)

    def get_performance_dashboard(self, all_accounts: Dict[str, AccountData]) -> Dict[str, Any]:
        """Get performance-focused dashboard data."""
        return self.analysis_coordinator.get_performance_dashboard(all_accounts)

    # Component Access Methods for Advanced Usage
    
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

    def get_analysis_coordinator(self) -> AnalysisCoordinator:
        """Get analysis coordinator component."""
        return self.analysis_coordinator

    # Utility and Status Methods
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get statistics about the analysis system."""
        return self.analysis_coordinator.get_analysis_statistics()