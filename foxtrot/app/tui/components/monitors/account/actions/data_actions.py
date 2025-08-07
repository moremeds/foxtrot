"""
Account monitor data display actions.

Handles actions related to displaying account data summaries,
risk information, and performance analytics.
"""

from typing import Any, Callable, Dict, Optional

from foxtrot.util.object import AccountData
from foxtrot.app.tui.utils.formatters import TUIFormatter


class AccountDataActions:
    """Handles data display actions for account monitor."""
    
    def __init__(self):
        """Initialize data actions handler."""
        # Callback functions
        self._message_callback: Optional[Callable] = None
        self._update_callback: Optional[Callable] = None
        self._refresh_callback: Optional[Callable] = None
    
    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for system messages."""
        self._message_callback = callback
    
    def set_update_callback(self, callback: Callable) -> None:
        """Set callback for triggering updates."""
        self._update_callback = callback
    
    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback for refreshing display."""
        self._refresh_callback = callback
    
    async def _add_system_message(self, message: str) -> None:
        """Add system message if callback is set."""
        if self._message_callback:
            await self._message_callback(message)
    
    async def _trigger_update(self) -> None:
        """Trigger update if callback is set."""
        if self._update_callback:
            await self._update_callback()
    
    async def _trigger_refresh(self) -> None:
        """Trigger refresh if callback is set."""
        if self._refresh_callback:
            await self._refresh_callback()
    
    # Data Display Actions
    async def action_show_risk(self, risk_metrics: Dict[str, Any]) -> None:
        """
        Display risk metrics summary.
        
        Args:
            risk_metrics: Dictionary containing risk analysis data
        """
        try:
            if not risk_metrics:
                await self._add_system_message("No risk data available")
                return
            
            # Format risk summary
            risk_summary = self._format_risk_summary(risk_metrics)
            await self._add_system_message(f"Risk Summary: {risk_summary}")
            
        except Exception as e:
            await self._add_system_message(f"Error displaying risk data: {e}")
    
    async def action_show_currency_breakdown(
        self, 
        currency_data: Dict[str, Dict[str, float]]
    ) -> None:
        """
        Display currency breakdown information.
        
        Args:
            currency_data: Dictionary with currency breakdown data
        """
        try:
            if not currency_data:
                await self._add_system_message("No currency breakdown data available")
                return
            
            # Format currency breakdown
            breakdown_summary = self._format_currency_breakdown(currency_data)
            await self._add_system_message(f"Currency Breakdown: {breakdown_summary}")
            
        except Exception as e:
            await self._add_system_message(f"Error displaying currency breakdown: {e}")
    
    async def action_show_balance_history(self, summary: Dict[str, Any]) -> None:
        """
        Display balance history summary.
        
        Args:
            summary: Dictionary containing balance history data
        """
        try:
            if not summary:
                await self._add_system_message("No balance history available")
                return
            
            # Format balance history summary
            history_summary = self._format_balance_history(summary)
            await self._add_system_message(f"Balance History: {history_summary}")
            
        except Exception as e:
            await self._add_system_message(f"Error displaying balance history: {e}")
    
    async def action_show_performance_summary(
        self, 
        performance_data: Dict[str, Any]
    ) -> None:
        """
        Display performance summary.
        
        Args:
            performance_data: Dictionary containing performance metrics
        """
        try:
            if not performance_data:
                await self._add_system_message("No performance data available")
                return
            
            # Format performance summary
            perf_summary = self._format_performance_summary(performance_data)
            await self._add_system_message(f"Performance: {perf_summary}")
            
        except Exception as e:
            await self._add_system_message(f"Error displaying performance data: {e}")
    
    async def action_select_account(self, account_data: AccountData) -> None:
        """
        Handle account selection action.
        
        Args:
            account_data: Selected account data
        """
        try:
            if not account_data:
                await self._add_system_message("No account selected")
                return
            
            # Format account selection summary
            account_summary = self._format_account_summary(account_data)
            await self._add_system_message(f"Selected: {account_summary}")
            await self._trigger_update()
            
        except Exception as e:
            await self._add_system_message(f"Error selecting account: {e}")
    
    async def action_analyze_risk_trends(
        self, 
        risk_history: list[Dict[str, Any]]
    ) -> None:
        """
        Analyze and display risk trends.
        
        Args:
            risk_history: List of historical risk data points
        """
        try:
            if not risk_history or len(risk_history) < 2:
                await self._add_system_message("Insufficient risk history for trend analysis")
                return
            
            # Analyze trends
            trend_analysis = self._analyze_risk_trends(risk_history)
            await self._add_system_message(f"Risk Trends: {trend_analysis}")
            
        except Exception as e:
            await self._add_system_message(f"Error analyzing risk trends: {e}")
    
    # Formatting Helper Methods
    def _format_risk_summary(self, risk_metrics: Dict[str, Any]) -> str:
        """Format risk metrics into readable summary."""
        try:
            risk_level = risk_metrics.get("overall_risk", "UNKNOWN")
            margin_ratio = risk_metrics.get("portfolio_margin_ratio", 0.0)
            volatility = risk_metrics.get("portfolio_volatility", 0.0)
            
            return (
                f"{risk_level} risk, "
                f"{margin_ratio:.1%} margin, "
                f"{volatility:.1%} volatility"
            )
        except Exception:
            return "Risk data unavailable"
    
    def _format_currency_breakdown(
        self, 
        currency_data: Dict[str, Dict[str, float]]
    ) -> str:
        """Format currency breakdown into readable summary."""
        try:
            currencies = []
            for currency, data in currency_data.items():
                balance = data.get("total_balance", 0.0)
                if balance > 0:
                    currencies.append(f"{currency}: {TUIFormatter.format_currency(balance)}")
            
            return " | ".join(currencies[:3])  # Show top 3 currencies
        except Exception:
            return "Currency data unavailable"
    
    def _format_balance_history(self, summary: Dict[str, Any]) -> str:
        """Format balance history into readable summary."""
        try:
            current_balance = summary.get("current_balance", 0.0)
            change_24h = summary.get("change_24h", 0.0)
            change_percent = summary.get("change_percent_24h", 0.0)
            
            change_str = f"{change_percent:+.1%}" if change_percent else "0.0%"
            return (
                f"{TUIFormatter.format_currency(current_balance)} "
                f"({change_str} 24h)"
            )
        except Exception:
            return "History unavailable"
    
    def _format_performance_summary(self, performance_data: Dict[str, Any]) -> str:
        """Format performance data into readable summary."""
        try:
            total_pnl = performance_data.get("total_pnl", 0.0)
            pnl_percent = performance_data.get("pnl_percent", 0.0)
            win_rate = performance_data.get("win_rate", 0.0)
            
            pnl_str = TUIFormatter.format_currency(total_pnl)
            return (
                f"{pnl_str} ({pnl_percent:+.1%}), "
                f"{win_rate:.1%} win rate"
            )
        except Exception:
            return "Performance data unavailable"
    
    def _format_account_summary(self, account_data: AccountData) -> str:
        """Format account data into readable summary."""
        try:
            return (
                f"{account_data.accountid} "
                f"({account_data.currency}) "
                f"{TUIFormatter.format_currency(account_data.balance)}"
            )
        except Exception:
            return "Account data unavailable"
    
    def _analyze_risk_trends(self, risk_history: list[Dict[str, Any]]) -> str:
        """Analyze risk trend from historical data."""
        try:
            if len(risk_history) < 2:
                return "Insufficient data"
            
            # Get latest and previous risk levels
            latest = risk_history[-1]
            previous = risk_history[-2]
            
            latest_risk = latest.get("overall_risk_score", 50)
            previous_risk = previous.get("overall_risk_score", 50)
            
            change = latest_risk - previous_risk
            
            if abs(change) < 5:
                trend = "Stable"
            elif change > 0:
                trend = f"Increasing (+{change:.1f})"
            else:
                trend = f"Decreasing ({change:.1f})"
            
            return f"{trend} risk trend"
            
        except Exception:
            return "Trend analysis unavailable"
    
    # Utility Methods
    def get_available_data_actions(self) -> Dict[str, str]:
        """Get list of available data actions."""
        return {
            "show_risk": "Display risk metrics summary",
            "show_currency_breakdown": "Show currency distribution",
            "show_balance_history": "Display balance history",
            "show_performance_summary": "Show performance metrics",
            "select_account": "Select account for details",
            "analyze_risk_trends": "Analyze risk trend patterns"
        }