"""
Portfolio analysis component.

Handles portfolio-level analysis, aggregation, and risk assessment
across all accounts.
"""

import logging
from typing import Any, Dict
from collections import defaultdict

from foxtrot.util.object import AccountData
from .data_structures import PortfolioSummary, PerformanceMetrics
from .account_analyzer import IndividualAccountAnalyzer

# Set up logging
logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """Analyzes portfolio performance and risk across all accounts."""
    
    def __init__(self):
        """Initialize portfolio analyzer."""
        self.account_analyzer = IndividualAccountAnalyzer()
    
    def analyze_portfolio(self, all_accounts: Dict[str, AccountData]) -> PortfolioSummary:
        """
        Analyze entire portfolio across all accounts.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            PortfolioSummary with portfolio-level analysis
        """
        try:
            if not all_accounts:
                return self._empty_portfolio_summary()
            
            # Basic aggregations
            total_balance = sum(acc.balance for acc in all_accounts.values())
            total_available = sum(acc.available for acc in all_accounts.values())
            total_pnl = sum(acc.net_pnl for acc in all_accounts.values())
            total_equity = total_balance + total_pnl
            
            # Collect unique currencies and gateways
            currencies = list(set(acc.currency for acc in all_accounts.values()))
            gateways = list(set(acc.gateway_name for acc in all_accounts.values()))
            
            # Calculate portfolio risk level
            risk_level = self.calculate_portfolio_risk_level(all_accounts)
            
            # Calculate diversification score
            diversification_score = self.calculate_diversification_score(all_accounts)
            
            # Calculate performance metrics
            performance_metrics = self.calculate_portfolio_performance_metrics(all_accounts)
            
            return PortfolioSummary(
                total_accounts=len(all_accounts),
                total_balance=total_balance,
                total_available=total_available,
                total_equity=total_equity,
                total_pnl=total_pnl,
                currencies=currencies,
                gateways=gateways,
                risk_level=risk_level,
                diversification_score=diversification_score,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return self._empty_portfolio_summary()
    
    def _empty_portfolio_summary(self) -> PortfolioSummary:
        """Return empty portfolio summary for error cases."""
        return PortfolioSummary(
            total_accounts=0,
            total_balance=0.0,
            total_available=0.0,
            total_equity=0.0,
            total_pnl=0.0,
            currencies=[],
            gateways=[],
            risk_level="unknown",
            diversification_score=0.0,
            performance_metrics={}
        )
    
    def calculate_portfolio_risk_level(self, all_accounts: Dict[str, AccountData]) -> str:
        """
        Calculate overall portfolio risk level using weighted average.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Portfolio risk level (critical, high, medium, low, unknown)
        """
        try:
            risk_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
            
            # Calculate total balance for weighting
            total_balance = sum(acc.balance for acc in all_accounts.values())
            if total_balance <= 0:
                return "unknown"
            
            # Calculate weighted average risk score
            weighted_risk = 0
            for account_data in all_accounts.values():
                risk_metrics = self.account_analyzer.calculate_risk_metrics(account_data)
                risk_score = risk_scores.get(risk_metrics.risk_level, 0)
                weight = account_data.balance / total_balance
                weighted_risk += risk_score * weight
            
            # Map weighted score back to risk level
            if weighted_risk >= 3.5:
                return "critical"
            elif weighted_risk >= 2.5:
                return "high"
            elif weighted_risk >= 1.5:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"Error calculating portfolio risk level: {e}")
            return "medium"
    
    def calculate_diversification_score(self, all_accounts: Dict[str, AccountData]) -> float:
        """
        Calculate portfolio diversification score (0-100).
        
        Higher scores indicate better diversification across currencies,
        gateways, and account distribution.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Diversification score between 0 and 100
        """
        try:
            if len(all_accounts) <= 1:
                return 0.0
            
            score = 0.0
            total_balance = sum(acc.balance for acc in all_accounts.values())
            
            if total_balance <= 0:
                return 0.0
            
            # Currency diversification (40 points max)
            score += self._calculate_currency_diversification(all_accounts, total_balance)
            
            # Gateway diversification (30 points max)  
            score += self._calculate_gateway_diversification(all_accounts, total_balance)
            
            # Account count bonus (30 points max)
            account_count_score = min(30, len(all_accounts) * 5)  # 5 points per account, max 30
            score += account_count_score
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Error calculating diversification score: {e}")
            return 0.0
    
    def _calculate_currency_diversification(self, all_accounts: Dict[str, AccountData], total_balance: float) -> float:
        """Calculate currency diversification component (0-40 points)."""
        currency_balances = defaultdict(float)
        
        for account_data in all_accounts.values():
            currency_balances[account_data.currency] += account_data.balance
        
        # Calculate currency concentration using Herfindahl-Hirschman Index
        currency_weights = [bal / total_balance for bal in currency_balances.values()]
        currency_hhi = sum(w**2 for w in currency_weights)
        
        # Lower HHI = more diversified, convert to score (0-40 points)
        currency_score = 40 * (1 - currency_hhi)
        return max(0, currency_score)
    
    def _calculate_gateway_diversification(self, all_accounts: Dict[str, AccountData], total_balance: float) -> float:
        """Calculate gateway diversification component (0-30 points)."""
        gateway_balances = defaultdict(float)
        
        for account_data in all_accounts.values():
            gateway_balances[account_data.gateway_name] += account_data.balance
        
        # Calculate gateway concentration using Herfindahl-Hirschman Index
        gateway_weights = [bal / total_balance for bal in gateway_balances.values()]
        gateway_hhi = sum(w**2 for w in gateway_weights)
        
        # Lower HHI = more diversified, convert to score (0-30 points)
        gateway_score = 30 * (1 - gateway_hhi)
        return max(0, gateway_score)
    
    def calculate_portfolio_performance_metrics(self, all_accounts: Dict[str, AccountData]) -> Dict[str, float]:
        """
        Calculate comprehensive portfolio performance metrics.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary of performance metrics
        """
        try:
            metrics = {}
            
            total_balance = sum(acc.balance for acc in all_accounts.values())
            total_pnl = sum(acc.net_pnl for acc in all_accounts.values())
            
            # Return on equity calculations
            if total_balance > 0:
                metrics["return_on_equity"] = total_pnl / total_balance
                metrics["return_on_equity_pct"] = (total_pnl / total_balance) * 100
            else:
                metrics["return_on_equity"] = 0.0
                metrics["return_on_equity_pct"] = 0.0
            
            # Risk-adjusted return calculation
            portfolio_risk = self.calculate_portfolio_risk_level(all_accounts)
            risk_level_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 2}
            risk_adjustment = risk_level_scores.get(portfolio_risk, 2)
            
            if risk_adjustment > 0:
                metrics["risk_adjusted_return"] = metrics["return_on_equity"] / risk_adjustment
            else:
                metrics["risk_adjusted_return"] = 0.0
            
            # Profit factor (simplified calculation)
            if total_pnl != 0:
                metrics["profit_factor"] = max(0.1, 1.0 + metrics["return_on_equity"])
            else:
                metrics["profit_factor"] = 1.0
            
            # Portfolio efficiency metrics
            metrics["diversification_score"] = self.calculate_diversification_score(all_accounts)
            metrics["account_efficiency"] = self._calculate_account_efficiency(all_accounts)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating portfolio performance metrics: {e}")
            return {}
    
    def _calculate_account_efficiency(self, all_accounts: Dict[str, AccountData]) -> float:
        """Calculate how efficiently accounts are being utilized."""
        try:
            if not all_accounts:
                return 0.0
            
            # Calculate average utilization across accounts
            total_utilization = 0.0
            valid_accounts = 0
            
            for account_data in all_accounts.values():
                if account_data.balance > 0:
                    utilization = (account_data.balance - account_data.available) / account_data.balance
                    total_utilization += min(1.0, utilization)  # Cap at 100%
                    valid_accounts += 1
            
            if valid_accounts > 0:
                avg_utilization = total_utilization / valid_accounts
                # Convert to efficiency score (0-100), optimal around 60-80% utilization
                if 0.6 <= avg_utilization <= 0.8:
                    return 100.0  # Optimal efficiency
                elif avg_utilization < 0.6:
                    return avg_utilization / 0.6 * 100  # Underutilization penalty
                else:
                    return max(0, 100 - (avg_utilization - 0.8) * 500)  # Over-utilization penalty
            
            return 50.0  # Default if no valid accounts
            
        except Exception as e:
            logger.error(f"Error calculating account efficiency: {e}")
            return 50.0