"""
Analysis report generation component.

Handles the generation of formatted reports, summaries, and breakdowns
for account and portfolio analysis.
"""

import logging
from typing import Any, Dict
from collections import defaultdict

from foxtrot.util.object import AccountData
from foxtrot.app.tui.utils.formatters import TUIFormatter
from .data_structures import CurrencyBreakdown, GatewayBreakdown, PortfolioSummary

# Set up logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates formatted reports and breakdowns for account analysis."""
    
    def __init__(self):
        """Initialize report generator."""
        pass
    
    def get_currency_breakdown(self, all_accounts: Dict[str, AccountData]) -> Dict[str, CurrencyBreakdown]:
        """
        Get detailed breakdown by currency.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary with currency-specific statistics
        """
        try:
            currency_data = defaultdict(lambda: CurrencyBreakdown(
                balance=0.0,
                available=0.0,
                frozen=0.0,
                pnl=0.0,
                account_count=0,
                avg_balance=0.0,
                weight=0.0
            ))
            
            total_balance = sum(acc.balance for acc in all_accounts.values())
            
            # Aggregate data by currency
            for account_data in all_accounts.values():
                currency = account_data.currency
                breakdown = currency_data[currency]
                
                breakdown.balance += account_data.balance
                breakdown.available += account_data.available
                breakdown.frozen += account_data.frozen
                breakdown.pnl += account_data.net_pnl
                breakdown.account_count += 1
            
            # Calculate derived metrics
            for currency, breakdown in currency_data.items():
                if breakdown.account_count > 0:
                    breakdown.avg_balance = breakdown.balance / breakdown.account_count
                if total_balance > 0:
                    breakdown.weight = breakdown.balance / total_balance
            
            return dict(currency_data)
            
        except Exception as e:
            logger.error(f"Error generating currency breakdown: {e}")
            return {}
    
    def get_gateway_breakdown(self, all_accounts: Dict[str, AccountData]) -> Dict[str, GatewayBreakdown]:
        """
        Get detailed breakdown by gateway.
        
        Args:
            all_accounts: Dictionary of all account data
            
        Returns:
            Dictionary with gateway-specific statistics
        """
        try:
            gateway_data = defaultdict(lambda: GatewayBreakdown(
                balance=0.0,
                available=0.0,
                pnl=0.0,
                account_count=0,
                currency_count=0,
                avg_balance=0.0,
                weight=0.0
            ))
            
            gateway_currencies = defaultdict(set)
            total_balance = sum(acc.balance for acc in all_accounts.values())
            
            # Aggregate data by gateway
            for account_data in all_accounts.values():
                gateway = account_data.gateway_name
                breakdown = gateway_data[gateway]
                
                breakdown.balance += account_data.balance
                breakdown.available += account_data.available
                breakdown.pnl += account_data.net_pnl
                breakdown.account_count += 1
                
                # Track unique currencies per gateway
                gateway_currencies[gateway].add(account_data.currency)
            
            # Calculate derived metrics
            for gateway, breakdown in gateway_data.items():
                if breakdown.account_count > 0:
                    breakdown.avg_balance = breakdown.balance / breakdown.account_count
                if total_balance > 0:
                    breakdown.weight = breakdown.balance / total_balance
                breakdown.currency_count = len(gateway_currencies[gateway])
            
            return dict(gateway_data)
            
        except Exception as e:
            logger.error(f"Error generating gateway breakdown: {e}")
            return {}
    
    def get_performance_summary(self, portfolio: PortfolioSummary) -> str:
        """
        Get formatted performance summary string.
        
        Args:
            portfolio: Portfolio summary data
            
        Returns:
            Formatted performance summary
        """
        try:
            # Format key financial metrics
            equity_str = TUIFormatter.format_currency(portfolio.total_equity)
            pnl_str = TUIFormatter.format_pnl(portfolio.total_pnl)
            
            # Calculate return percentage
            if portfolio.total_balance > 0:
                return_pct = (portfolio.total_pnl / portfolio.total_balance) * 100
                return_str = f"{return_pct:+.2f}%"
            else:
                return_str = "N/A"
            
            # Format summary string
            summary = (
                f"Portfolio: {portfolio.total_accounts} accounts, "
                f"Equity: {equity_str}, "
                f"P&L: {pnl_str} ({return_str}), "
                f"Risk: {portfolio.risk_level.upper()}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return "Performance summary unavailable"
    
    def get_detailed_performance_report(self, portfolio: PortfolioSummary) -> str:
        """
        Get detailed performance report with multiple metrics.
        
        Args:
            portfolio: Portfolio summary data
            
        Returns:
            Detailed formatted performance report
        """
        try:
            lines = []
            lines.append("=== PORTFOLIO PERFORMANCE REPORT ===")
            lines.append("")
            
            # Basic portfolio metrics
            lines.append("Portfolio Overview:")
            lines.append(f"  Total Accounts: {portfolio.total_accounts}")
            lines.append(f"  Total Equity: {TUIFormatter.format_currency(portfolio.total_equity)}")
            lines.append(f"  Total Balance: {TUIFormatter.format_currency(portfolio.total_balance)}")
            lines.append(f"  Total P&L: {TUIFormatter.format_pnl(portfolio.total_pnl)}")
            lines.append("")
            
            # Performance metrics
            if portfolio.performance_metrics:
                lines.append("Performance Metrics:")
                metrics = portfolio.performance_metrics
                
                if "return_on_equity_pct" in metrics:
                    lines.append(f"  Return on Equity: {metrics['return_on_equity_pct']:.2f}%")
                
                if "risk_adjusted_return" in metrics:
                    lines.append(f"  Risk-Adjusted Return: {metrics['risk_adjusted_return']:.4f}")
                
                if "profit_factor" in metrics:
                    lines.append(f"  Profit Factor: {metrics['profit_factor']:.2f}")
                
                lines.append("")
            
            # Risk and diversification
            lines.append("Risk Assessment:")
            lines.append(f"  Risk Level: {portfolio.risk_level.upper()}")
            lines.append(f"  Diversification Score: {portfolio.diversification_score:.1f}/100")
            lines.append("")
            
            # Currency and gateway distribution
            lines.append("Distribution:")
            lines.append(f"  Currencies: {len(portfolio.currencies)} ({', '.join(portfolio.currencies)})")
            lines.append(f"  Gateways: {len(portfolio.gateways)} ({', '.join(portfolio.gateways)})")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating detailed performance report: {e}")
            return "Detailed performance report unavailable"
    
    def get_currency_breakdown_report(self, currency_breakdown: Dict[str, CurrencyBreakdown]) -> str:
        """
        Get formatted currency breakdown report.
        
        Args:
            currency_breakdown: Currency breakdown data
            
        Returns:
            Formatted currency breakdown report
        """
        try:
            if not currency_breakdown:
                return "No currency data available"
            
            lines = []
            lines.append("=== CURRENCY BREAKDOWN ===")
            lines.append("")
            
            # Sort by balance descending
            sorted_currencies = sorted(
                currency_breakdown.items(), 
                key=lambda x: x[1].balance, 
                reverse=True
            )
            
            for currency, breakdown in sorted_currencies:
                lines.append(f"{currency}:")
                lines.append(f"  Balance: {TUIFormatter.format_currency(breakdown.balance)}")
                lines.append(f"  Available: {TUIFormatter.format_currency(breakdown.available)}")
                lines.append(f"  P&L: {TUIFormatter.format_pnl(breakdown.pnl)}")
                lines.append(f"  Accounts: {breakdown.account_count}")
                lines.append(f"  Weight: {breakdown.weight:.1%}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating currency breakdown report: {e}")
            return "Currency breakdown report unavailable"
    
    def get_gateway_breakdown_report(self, gateway_breakdown: Dict[str, GatewayBreakdown]) -> str:
        """
        Get formatted gateway breakdown report.
        
        Args:
            gateway_breakdown: Gateway breakdown data
            
        Returns:
            Formatted gateway breakdown report
        """
        try:
            if not gateway_breakdown:
                return "No gateway data available"
            
            lines = []
            lines.append("=== GATEWAY BREAKDOWN ===")
            lines.append("")
            
            # Sort by balance descending
            sorted_gateways = sorted(
                gateway_breakdown.items(),
                key=lambda x: x[1].balance,
                reverse=True
            )
            
            for gateway, breakdown in sorted_gateways:
                lines.append(f"{gateway}:")
                lines.append(f"  Balance: {TUIFormatter.format_currency(breakdown.balance)}")
                lines.append(f"  Available: {TUIFormatter.format_currency(breakdown.available)}")
                lines.append(f"  P&L: {TUIFormatter.format_pnl(breakdown.pnl)}")
                lines.append(f"  Accounts: {breakdown.account_count}")
                lines.append(f"  Currencies: {breakdown.currency_count}")
                lines.append(f"  Weight: {breakdown.weight:.1%}")
                lines.append("")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating gateway breakdown report: {e}")
            return "Gateway breakdown report unavailable"
    
    def get_risk_summary_report(self, portfolio: PortfolioSummary) -> str:
        """
        Get formatted risk summary report.
        
        Args:
            portfolio: Portfolio summary data
            
        Returns:
            Formatted risk summary report
        """
        try:
            lines = []
            lines.append("=== RISK SUMMARY ===")
            lines.append("")
            
            lines.append(f"Overall Risk Level: {portfolio.risk_level.upper()}")
            lines.append(f"Diversification Score: {portfolio.diversification_score:.1f}/100")
            lines.append("")
            
            # Risk level interpretation
            risk_descriptions = {
                "low": "Good balance management and low risk exposure",
                "medium": "Moderate risk with room for improvement",
                "high": "Elevated risk requiring attention",
                "critical": "High risk requiring immediate action",
                "unknown": "Insufficient data for risk assessment"
            }
            
            description = risk_descriptions.get(portfolio.risk_level, "Risk level unclear")
            lines.append(f"Assessment: {description}")
            lines.append("")
            
            # Diversification analysis
            if portfolio.diversification_score >= 80:
                div_status = "Excellent diversification"
            elif portfolio.diversification_score >= 60:
                div_status = "Good diversification"
            elif portfolio.diversification_score >= 40:
                div_status = "Moderate diversification"
            else:
                div_status = "Poor diversification - consider spreading risk"
            
            lines.append(f"Diversification: {div_status}")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error generating risk summary report: {e}")
            return "Risk summary report unavailable"