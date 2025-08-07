"""
Historical data tracking component.

Manages historical account data storage, retrieval, and trend analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from collections import defaultdict

from foxtrot.util.object import AccountData
from .data_structures import HistoricalEntry

# Set up logging
logger = logging.getLogger(__name__)


class HistoricalTracker:
    """Manages historical account data and trend analysis."""
    
    def __init__(self, max_entries_per_account: int = 1000):
        """
        Initialize historical tracker.
        
        Args:
            max_entries_per_account: Maximum historical entries to keep per account
        """
        self.max_entries_per_account = max_entries_per_account
        
        # Historical data storage
        self.account_history: Dict[str, List[HistoricalEntry]] = defaultdict(list)
        self.portfolio_history: List[Dict[str, Any]] = []
        
        # Tracking statistics
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(hours=1)  # Cleanup old data hourly
    
    def add_account_history_entry(self, account_data: AccountData) -> None:
        """
        Add historical entry for an account.
        
        Args:
            account_data: Account data to add to history
        """
        try:
            entry = HistoricalEntry(
                timestamp=datetime.now(),
                balance=account_data.balance,
                available=account_data.available,
                frozen=account_data.frozen,
                pnl=account_data.net_pnl,
                margin=getattr(account_data, 'margin', 0)
            )
            
            account_id = account_data.vt_accountid
            self.account_history[account_id].append(entry)
            
            # Maintain size limit
            if len(self.account_history[account_id]) > self.max_entries_per_account:
                self.account_history[account_id].pop(0)
            
            # Periodic cleanup of old data
            self._periodic_cleanup()
            
        except Exception as e:
            logger.error(f"Error adding account history entry for {account_data.vt_accountid}: {e}")
    
    def add_portfolio_history_entry(self, portfolio_summary: Dict[str, Any]) -> None:
        """
        Add historical entry for portfolio-level data.
        
        Args:
            portfolio_summary: Portfolio summary data to add to history
        """
        try:
            entry = {
                "timestamp": datetime.now(),
                "total_balance": portfolio_summary.get("total_balance", 0.0),
                "total_equity": portfolio_summary.get("total_equity", 0.0),
                "total_pnl": portfolio_summary.get("total_pnl", 0.0),
                "account_count": portfolio_summary.get("total_accounts", 0),
                "risk_level": portfolio_summary.get("risk_level", "unknown")
            }
            
            self.portfolio_history.append(entry)
            
            # Maintain size limit for portfolio history
            if len(self.portfolio_history) > self.max_entries_per_account:
                self.portfolio_history.pop(0)
                
        except Exception as e:
            logger.error(f"Error adding portfolio history entry: {e}")
    
    def get_balance_history(self, account_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get balance history for a specific account.
        
        Args:
            account_id: Account identifier
            hours: Number of hours of history to return
            
        Returns:
            List of historical balance data points
        """
        try:
            if account_id not in self.account_history:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            history_data = []
            for entry in self.account_history[account_id]:
                if entry.timestamp >= cutoff_time:
                    history_data.append({
                        "timestamp": entry.timestamp,
                        "balance": entry.balance,
                        "available": entry.available,
                        "frozen": entry.frozen,
                        "pnl": entry.pnl,
                        "margin": entry.margin
                    })
            
            return history_data
            
        except Exception as e:
            logger.error(f"Error getting balance history for {account_id}: {e}")
            return []
    
    def get_portfolio_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get portfolio history for the specified time period.
        
        Args:
            hours: Number of hours of history to return
            
        Returns:
            List of historical portfolio data points
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            return [
                entry for entry in self.portfolio_history
                if entry.get("timestamp", datetime.min) >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error getting portfolio history: {e}")
            return []
    
    def calculate_balance_change(self, account_id: str, hours: int = 24) -> Dict[str, float]:
        """
        Calculate balance change over the specified period.
        
        Args:
            account_id: Account identifier
            hours: Period in hours to calculate change
            
        Returns:
            Dictionary with change statistics
        """
        try:
            history = self.get_balance_history(account_id, hours)
            
            if len(history) < 2:
                return {
                    "change_amount": 0.0,
                    "change_percent": 0.0,
                    "period_hours": hours,
                    "data_points": len(history)
                }
            
            # Get first and last entries
            first_entry = history[0]
            last_entry = history[-1]
            
            # Calculate changes
            balance_change = last_entry["balance"] - first_entry["balance"]
            pnl_change = last_entry["pnl"] - first_entry["pnl"]
            
            # Calculate percentage change
            if first_entry["balance"] > 0:
                percent_change = (balance_change / first_entry["balance"]) * 100
            else:
                percent_change = 0.0
            
            return {
                "change_amount": balance_change,
                "change_percent": percent_change,
                "pnl_change": pnl_change,
                "period_hours": hours,
                "data_points": len(history),
                "start_balance": first_entry["balance"],
                "end_balance": last_entry["balance"]
            }
            
        except Exception as e:
            logger.error(f"Error calculating balance change for {account_id}: {e}")
            return {
                "change_amount": 0.0,
                "change_percent": 0.0,
                "period_hours": hours,
                "data_points": 0
            }
    
    def get_trend_analysis(self, account_id: str, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze trends for an account over the specified period.
        
        Args:
            account_id: Account identifier
            hours: Period in hours to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        try:
            history = self.get_balance_history(account_id, hours)
            
            if len(history) < 3:
                return {
                    "trend": "insufficient_data",
                    "volatility": 0.0,
                    "average_balance": 0.0,
                    "data_points": len(history)
                }
            
            # Calculate basic statistics
            balances = [entry["balance"] for entry in history]
            pnls = [entry["pnl"] for entry in history]
            
            avg_balance = sum(balances) / len(balances)
            min_balance = min(balances)
            max_balance = max(balances)
            
            # Calculate volatility (coefficient of variation)
            if avg_balance > 0:
                balance_std = (sum((b - avg_balance) ** 2 for b in balances) / len(balances)) ** 0.5
                volatility = balance_std / avg_balance
            else:
                volatility = 0.0
            
            # Determine trend direction
            first_half_avg = sum(balances[:len(balances)//2]) / (len(balances)//2)
            second_half_avg = sum(balances[len(balances)//2:]) / (len(balances) - len(balances)//2)
            
            if second_half_avg > first_half_avg * 1.02:  # 2% threshold
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.98:
                trend = "decreasing"
            else:
                trend = "stable"
            
            return {
                "trend": trend,
                "volatility": volatility,
                "average_balance": avg_balance,
                "min_balance": min_balance,
                "max_balance": max_balance,
                "balance_range": max_balance - min_balance,
                "first_half_avg": first_half_avg,
                "second_half_avg": second_half_avg,
                "data_points": len(history)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends for {account_id}: {e}")
            return {
                "trend": "error",
                "volatility": 0.0,
                "average_balance": 0.0,
                "data_points": 0
            }
    
    def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup of old historical data."""
        try:
            now = datetime.now()
            
            # Only cleanup once per hour
            if now - self._last_cleanup < self._cleanup_interval:
                return
            
            self._last_cleanup = now
            cutoff_time = now - timedelta(days=30)  # Keep 30 days of data
            
            # Cleanup account history
            for account_id in list(self.account_history.keys()):
                self.account_history[account_id] = [
                    entry for entry in self.account_history[account_id]
                    if entry.timestamp >= cutoff_time
                ]
                
                # Remove accounts with no recent data
                if not self.account_history[account_id]:
                    del self.account_history[account_id]
            
            # Cleanup portfolio history
            self.portfolio_history = [
                entry for entry in self.portfolio_history
                if entry.get("timestamp", datetime.min) >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about historical data storage."""
        try:
            return {
                "accounts_tracked": len(self.account_history),
                "total_account_entries": sum(len(entries) for entries in self.account_history.values()),
                "portfolio_entries": len(self.portfolio_history),
                "last_cleanup": self._last_cleanup,
                "max_entries_per_account": self.max_entries_per_account
            }
        except Exception as e:
            logger.error(f"Error getting historical tracker statistics: {e}")
            return {}