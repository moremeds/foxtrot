"""
Account monitor statistics tracking and calculation logic.

This module handles account statistics collection, aggregation,
and real-time calculation of portfolio metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque

from foxtrot.util.object import AccountData
from .config import AccountMonitorConfig

# Set up logging
logger = logging.getLogger(__name__)


class AccountStatistics:
    """
    Tracks and calculates account statistics and portfolio metrics.
    
    Features:
    - Real-time statistics calculation
    - Historical tracking with configurable retention
    - Multi-currency aggregation
    - Performance metrics calculation
    - Risk-adjusted returns
    - Portfolio composition analysis
    """
    
    def __init__(self, config: AccountMonitorConfig):
        """
        Initialize statistics tracker.
        
        Args:
            config: Account monitor configuration
        """
        self.config = config
        
        # Current statistics
        self.statistics: Dict[str, Any] = self._init_statistics()
        
        # Historical data storage
        self.history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.last_snapshot_time = datetime.now()
        self.snapshot_interval = timedelta(minutes=5)  # Snapshot every 5 minutes
        
        # Account tracking
        self.account_data: Dict[str, AccountData] = {}
        self.account_count_by_currency: Dict[str, int] = defaultdict(int)
        self.account_count_by_gateway: Dict[str, int] = defaultdict(int)
        
        # Performance tracking
        self.performance_metrics: Dict[str, Any] = {}
        self.daily_snapshots: List[Dict[str, Any]] = []
    
    def _init_statistics(self) -> Dict[str, Any]:
        """Initialize statistics dictionary with default values."""
        stats = {}
        for field, config in self.config.STATISTICS_FIELDS.items():
            stats[field] = config.get("default", 0)
        return stats
    
    async def update_account(self, account_data: AccountData) -> None:
        """
        Update statistics with new account data.
        
        Args:
            account_data: New or updated account data
        """
        try:
            account_id = account_data.vt_accountid
            old_data = self.account_data.get(account_id)
            
            # Store the new data
            self.account_data[account_id] = account_data
            
            # Update currency and gateway counts
            self._update_counts(account_data, old_data)
            
            # Recalculate all statistics
            await self._recalculate_statistics()
            
            # Take snapshot if enough time has passed
            await self._maybe_take_snapshot()
            
            # Update performance metrics
            await self._update_performance_metrics()
            
        except Exception as e:
            logger.error(f"Error updating account statistics: {e}")
    
    def _update_counts(self, new_data: AccountData, old_data: Optional[AccountData]) -> None:
        """Update currency and gateway counts."""
        # Remove old data counts
        if old_data:
            self.account_count_by_currency[old_data.currency] -= 1
            self.account_count_by_gateway[old_data.gateway_name] -= 1
            
            # Clean up zero counts
            if self.account_count_by_currency[old_data.currency] <= 0:
                del self.account_count_by_currency[old_data.currency]
            if self.account_count_by_gateway[old_data.gateway_name] <= 0:
                del self.account_count_by_gateway[old_data.gateway_name]
        
        # Add new data counts
        self.account_count_by_currency[new_data.currency] += 1
        self.account_count_by_gateway[new_data.gateway_name] += 1
    
    async def _recalculate_statistics(self) -> None:
        """Recalculate all portfolio statistics from current account data."""
        try:
            # Reset statistics
            stats = self._init_statistics()
            
            # Aggregate across all accounts
            for account_data in self.account_data.values():
                stats["total_accounts"] += 1
                stats["total_balance"] += account_data.balance
                stats["total_available"] += account_data.available
                stats["total_frozen"] += account_data.frozen
                stats["total_pnl"] += account_data.net_pnl
                
                # Optional fields with safe access
                commission = getattr(account_data, "commission", 0)
                margin = getattr(account_data, "margin", 0)
                
                stats["total_commission"] += commission
                stats["total_margin"] += margin
            
            # Calculate derived metrics
            stats["total_equity"] = stats["total_balance"] + stats["total_pnl"]
            
            if stats["total_balance"] > 0:
                stats["equity_ratio"] = stats["total_equity"] / stats["total_balance"]
            else:
                stats["equity_ratio"] = 1.0
            
            # Store updated statistics
            self.statistics = stats
            
        except Exception as e:
            logger.error(f"Error recalculating statistics: {e}")
    
    async def _maybe_take_snapshot(self) -> None:
        """Take a historical snapshot if enough time has passed."""
        now = datetime.now()
        if now - self.last_snapshot_time >= self.snapshot_interval:
            await self._take_snapshot()
            self.last_snapshot_time = now
    
    async def _take_snapshot(self) -> None:
        """Take a snapshot of current statistics for historical tracking."""
        try:
            snapshot = {
                "timestamp": datetime.now(),
                "statistics": self.statistics.copy(),
                "account_count": len(self.account_data),
                "currencies": len(self.account_count_by_currency),
                "gateways": len(self.account_count_by_gateway)
            }
            
            # Store in history
            self.history["portfolio"].append(snapshot)
            
            # Also store daily snapshot for performance calculations
            if self._should_take_daily_snapshot():
                self.daily_snapshots.append(snapshot.copy())
                # Keep only last 30 days
                if len(self.daily_snapshots) > 30:
                    self.daily_snapshots.pop(0)
                    
        except Exception as e:
            logger.error(f"Error taking snapshot: {e}")
    
    def _should_take_daily_snapshot(self) -> bool:
        """Check if we should take a daily snapshot."""
        if not self.daily_snapshots:
            return True
        
        last_snapshot_time = self.daily_snapshots[-1]["timestamp"]
        return (datetime.now() - last_snapshot_time).days >= 1
    
    async def _update_performance_metrics(self) -> None:
        """Update performance metrics based on historical data."""
        try:
            if len(self.daily_snapshots) < 2:
                return  # Need at least 2 snapshots for performance calculation
            
            current = self.statistics
            previous = self.daily_snapshots[-2]["statistics"]
            
            # Calculate daily returns
            if previous["total_equity"] > 0:
                daily_return = (
                    (current["total_equity"] - previous["total_equity"]) / 
                    previous["total_equity"]
                )
                self.performance_metrics["daily_return"] = daily_return
                self.performance_metrics["daily_return_pct"] = daily_return * 100
            
            # Calculate volatility if we have enough data
            if len(self.daily_snapshots) >= 7:
                await self._calculate_volatility()
            
            # Calculate max drawdown
            await self._calculate_max_drawdown()
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    async def _calculate_volatility(self) -> None:
        """Calculate portfolio volatility based on daily returns."""
        try:
            # Get daily returns for the last 30 days
            returns = []
            for i in range(1, min(len(self.daily_snapshots), 31)):
                current_equity = self.daily_snapshots[-i]["statistics"]["total_equity"]
                previous_equity = self.daily_snapshots[-i-1]["statistics"]["total_equity"]
                
                if previous_equity > 0:
                    daily_return = (current_equity - previous_equity) / previous_equity
                    returns.append(daily_return)
            
            if len(returns) < 2:
                return
            
            # Calculate standard deviation of returns
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
            volatility = variance ** 0.5
            
            # Annualized volatility (assuming 252 trading days)
            annualized_volatility = volatility * (252 ** 0.5)
            
            self.performance_metrics["volatility"] = volatility
            self.performance_metrics["annualized_volatility"] = annualized_volatility
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
    
    async def _calculate_max_drawdown(self) -> None:
        """Calculate maximum drawdown from peak equity."""
        try:
            if len(self.daily_snapshots) < 2:
                return
            
            peak_equity = 0
            max_drawdown = 0
            
            for snapshot in self.daily_snapshots:
                equity = snapshot["statistics"]["total_equity"]
                
                # Update peak
                if equity > peak_equity:
                    peak_equity = equity
                
                # Calculate current drawdown
                if peak_equity > 0:
                    current_drawdown = (peak_equity - equity) / peak_equity
                    max_drawdown = max(max_drawdown, current_drawdown)
            
            self.performance_metrics["max_drawdown"] = max_drawdown
            self.performance_metrics["max_drawdown_pct"] = max_drawdown * 100
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current portfolio statistics."""
        return self.statistics.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()
    
    def get_currency_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get balance breakdown by currency.
        
        Returns:
            Dictionary with currency-specific balances and statistics
        """
        currency_data = {}
        
        for account_data in self.account_data.values():
            currency = account_data.currency
            if currency not in currency_data:
                currency_data[currency] = {
                    "balance": 0.0,
                    "available": 0.0,
                    "frozen": 0.0,
                    "pnl": 0.0,
                    "account_count": 0
                }
            
            currency_data[currency]["balance"] += account_data.balance
            currency_data[currency]["available"] += account_data.available
            currency_data[currency]["frozen"] += account_data.frozen
            currency_data[currency]["pnl"] += account_data.net_pnl
            currency_data[currency]["account_count"] += 1
        
        return currency_data
    
    def get_gateway_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """
        Get balance breakdown by gateway.
        
        Returns:
            Dictionary with gateway-specific statistics
        """
        gateway_data = {}
        
        for account_data in self.account_data.values():
            gateway = account_data.gateway_name
            if gateway not in gateway_data:
                gateway_data[gateway] = {
                    "balance": 0.0,
                    "available": 0.0,
                    "pnl": 0.0,
                    "account_count": 0,
                    "currencies": set()
                }
            
            gateway_data[gateway]["balance"] += account_data.balance
            gateway_data[gateway]["available"] += account_data.available
            gateway_data[gateway]["pnl"] += account_data.net_pnl
            gateway_data[gateway]["account_count"] += 1
            gateway_data[gateway]["currencies"].add(account_data.currency)
        
        # Convert currency sets to counts for serialization
        for gateway_info in gateway_data.values():
            gateway_info["currency_count"] = len(gateway_info["currencies"])
            del gateway_info["currencies"]
        
        return gateway_data
    
    def get_account_history(self, account_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get balance history for a specific account.
        
        Args:
            account_id: Account identifier
            hours: Number of hours of history to return
            
        Returns:
            List of historical account data points
        """
        if account_id not in self.account_data:
            return []
        
        # This would typically be stored separately for each account
        # For now, return portfolio-level history as a placeholder
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history_data = []
        for snapshot in self.history["portfolio"]:
            if snapshot["timestamp"] >= cutoff_time:
                # Would extract account-specific data in real implementation
                history_data.append({
                    "timestamp": snapshot["timestamp"],
                    "balance": snapshot["statistics"]["total_balance"],
                    "available": snapshot["statistics"]["total_available"],
                    "pnl": snapshot["statistics"]["total_pnl"]
                })
        
        return history_data
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive account summary with all metrics.
        
        Returns:
            Dictionary containing statistics, performance, and breakdown data
        """
        summary = {
            "statistics": self.get_statistics(),
            "performance": self.get_performance_metrics(),
            "currency_breakdown": self.get_currency_breakdown(),
            "gateway_breakdown": self.get_gateway_breakdown(),
            "account_counts": {
                "total": len(self.account_data),
                "by_currency": dict(self.account_count_by_currency),
                "by_gateway": dict(self.account_count_by_gateway)
            },
            "last_updated": datetime.now()
        }
        
        return summary
    
    def reset_statistics(self) -> None:
        """Reset all statistics and historical data."""
        self.statistics = self._init_statistics()
        self.account_data.clear()
        self.account_count_by_currency.clear()
        self.account_count_by_gateway.clear()
        self.performance_metrics.clear()
        self.history.clear()
        self.daily_snapshots.clear()
        self.last_snapshot_time = datetime.now()