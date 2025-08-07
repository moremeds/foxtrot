"""
Individual account analysis component.

Handles risk assessment and performance scoring for individual accounts.
"""

import logging
from typing import Any, Dict

from foxtrot.util.object import AccountData
from .data_structures import AccountSummary, RiskMetrics, PerformanceMetrics

# Set up logging
logger = logging.getLogger(__name__)


class IndividualAccountAnalyzer:
    """Analyzes individual account performance and risk."""
    
    def __init__(self):
        """Initialize individual account analyzer."""
        pass
    
    def analyze_account(self, account_data: AccountData) -> AccountSummary:
        """
        Analyze individual account performance and risk.
        
        Args:
            account_data: Account data to analyze
            
        Returns:
            AccountSummary with analysis results
        """
        try:
            # Calculate risk level and metrics
            risk_metrics = self.calculate_risk_metrics(account_data)
            
            # Calculate performance score
            performance_score = self.calculate_performance_score(account_data, risk_metrics.risk_level)
            
            return AccountSummary(
                account_id=account_data.vt_accountid,
                currency=account_data.currency,
                gateway=account_data.gateway_name,
                current_balance=account_data.balance,
                available_balance=account_data.available,
                frozen_balance=account_data.frozen,
                net_pnl=account_data.net_pnl,
                margin_used=getattr(account_data, 'margin', 0),
                last_updated=account_data.datetime,
                risk_level=risk_metrics.risk_level,
                performance_score=performance_score
            )
            
        except Exception as e:
            logger.error(f"Error analyzing account {account_data.vt_accountid}: {e}")
            # Return basic summary on error
            return AccountSummary(
                account_id=account_data.vt_accountid,
                currency=account_data.currency,
                gateway=account_data.gateway_name,
                current_balance=account_data.balance,
                available_balance=account_data.available,
                frozen_balance=account_data.frozen,
                net_pnl=account_data.net_pnl,
                margin_used=0,
                last_updated=account_data.datetime,
                risk_level="unknown",
                performance_score=0.0
            )
    
    def calculate_risk_metrics(self, account_data: AccountData) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for an account.
        
        Args:
            account_data: Account data to analyze
            
        Returns:
            RiskMetrics with detailed risk assessment
        """
        try:
            # Available balance ratio
            if account_data.balance > 0:
                available_ratio = account_data.available / account_data.balance
            else:
                available_ratio = 0.0
            
            # Margin usage ratio
            margin = getattr(account_data, 'margin', 0)
            if account_data.balance > 0:
                margin_ratio = margin / account_data.balance
            else:
                margin_ratio = 0.0
            
            # P&L impact relative to balance
            if account_data.balance > 0:
                pnl_impact = abs(account_data.net_pnl) / account_data.balance
            else:
                pnl_impact = 0.0
            
            # Calculate risk level
            risk_level = self._assess_risk_level(available_ratio, margin_ratio, pnl_impact)
            
            # Calculate numeric risk score (0-100, higher = more risky)
            risk_score = self._calculate_risk_score(available_ratio, margin_ratio, pnl_impact)
            
            return RiskMetrics(
                available_ratio=available_ratio,
                margin_ratio=margin_ratio,
                pnl_impact=pnl_impact,
                risk_level=risk_level,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return RiskMetrics(
                available_ratio=0.0,
                margin_ratio=0.0,
                pnl_impact=0.0,
                risk_level="unknown",
                risk_score=50.0
            )
    
    def _assess_risk_level(self, available_ratio: float, margin_ratio: float, pnl_impact: float) -> str:
        """Assess risk level based on key ratios."""
        # Critical risk conditions
        if margin_ratio > 0.8 or available_ratio < 0.1 or pnl_impact > 0.2:
            return "critical"
        
        # High risk conditions  
        elif margin_ratio > 0.6 or available_ratio < 0.3 or pnl_impact > 0.1:
            return "high"
        
        # Medium risk conditions
        elif margin_ratio > 0.4 or available_ratio < 0.5 or pnl_impact > 0.05:
            return "medium"
        
        # Low risk (good conditions)
        else:
            return "low"
    
    def _calculate_risk_score(self, available_ratio: float, margin_ratio: float, pnl_impact: float) -> float:
        """Calculate numeric risk score (0-100, higher = more risky)."""
        try:
            score = 0.0
            
            # Margin usage contribution (0-40 points)
            score += min(margin_ratio * 50, 40)
            
            # Available balance contribution (0-30 points)
            # Lower available ratio = higher risk
            if available_ratio < 1.0:
                score += (1.0 - available_ratio) * 30
            
            # P&L impact contribution (0-30 points)
            score += min(pnl_impact * 150, 30)
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            return 50.0
    
    def calculate_performance_score(self, account_data: AccountData, risk_level: str) -> float:
        """
        Calculate performance score (0-100) for an account.
        
        Args:
            account_data: Account data to analyze
            risk_level: Risk level from risk analysis
            
        Returns:
            Performance score between 0 and 100
        """
        try:
            score = 50.0  # Base score
            
            # P&L contribution (±30 points)
            if account_data.balance > 0:
                pnl_ratio = account_data.net_pnl / account_data.balance
                score += min(max(pnl_ratio * 300, -30), 30)  # Scale and cap
            
            # Risk adjustment (-20 points for high risk)
            risk_penalties = {"critical": -20, "high": -15, "medium": -5, "low": 0, "unknown": -10}
            score += risk_penalties.get(risk_level, -10)
            
            # Balance utilization efficiency (+20 points for good balance management)
            if account_data.balance > 0:
                utilization = (account_data.balance - account_data.available) / account_data.balance
                if utilization < 0.5:  # Good utilization range
                    score += 20 * (1 - utilization * 2)
            
            # Ensure score is within valid range
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 50.0
    
    def get_account_performance_metrics(self, account_data: AccountData) -> PerformanceMetrics:
        """
        Calculate detailed performance metrics for an account.
        
        Args:
            account_data: Account data to analyze
            
        Returns:
            PerformanceMetrics with detailed performance analysis
        """
        try:
            # Calculate return on equity
            if account_data.balance > 0:
                roe = account_data.net_pnl / account_data.balance
                roe_pct = roe * 100
            else:
                roe = 0.0
                roe_pct = 0.0
            
            # Calculate risk-adjusted return
            risk_metrics = self.calculate_risk_metrics(account_data)
            risk_adjustment = max(1.0, risk_metrics.risk_score / 25)  # Higher risk = higher divisor
            risk_adjusted_return = roe / risk_adjustment
            
            # Calculate profit factor (simplified)
            if account_data.net_pnl > 0:
                profit_factor = 1.0 + abs(roe)
            else:
                profit_factor = max(0.1, 1.0 + roe)  # Minimum 0.1 to avoid division by zero
            
            # Calculate overall performance score
            performance_score = self.calculate_performance_score(account_data, risk_metrics.risk_level)
            
            return PerformanceMetrics(
                return_on_equity=roe,
                return_on_equity_pct=roe_pct,
                risk_adjusted_return=risk_adjusted_return,
                profit_factor=profit_factor,
                performance_score=performance_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return PerformanceMetrics(
                return_on_equity=0.0,
                return_on_equity_pct=0.0,
                risk_adjusted_return=0.0,
                profit_factor=1.0,
                performance_score=50.0
            )