"""
Trade statistics and analysis functionality.

Handles calculation, tracking, and analysis of trade data for the monitor.
"""

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List, TYPE_CHECKING

from foxtrot.util.constants import Direction
from foxtrot.util.object import TradeData
from ...utils.formatters import TUIFormatter

if TYPE_CHECKING:
    from ..trade_monitor import TUITradeMonitor


class TradeStatistics:
    """Handles trade statistics calculation and tracking."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
        
        # Initialize statistics tracking
        self.daily_trades: Dict[date, List[TradeData]] = {}
        self.statistics: Dict[str, Any] = {
            "total_trades": 0,
            "total_volume": 0.0,
            "total_value": 0.0,
            "long_trades": 0,
            "short_trades": 0,
            "avg_price": 0.0,
            "session_pnl": 0.0,
        }
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    def process_trade_for_statistics(self, trade: TradeData) -> None:
        """
        Process a new trade for statistics tracking.
        
        Args:
            trade: Trade data to process
        """
        # Update daily trades tracking
        trade_date = trade.datetime.date()
        if trade_date not in self.daily_trades:
            self.daily_trades[trade_date] = []
        self.daily_trades[trade_date].append(trade)
        
        # Update overall statistics
        self.statistics["total_trades"] += 1
        self.statistics["total_volume"] += trade.volume
        
        trade_value = trade.price * trade.volume
        self.statistics["total_value"] += trade_value
        
        if trade.direction == Direction.LONG:
            self.statistics["long_trades"] += 1
        else:
            self.statistics["short_trades"] += 1
        
        # Calculate average price
        if self.statistics["total_volume"] > 0:
            self.statistics["avg_price"] = (
                self.statistics["total_value"] / self.statistics["total_volume"]
            )
        
        # Schedule display update
        asyncio.create_task(self.update_statistics_display())
    
    def get_daily_summary(self, target_date: date = None) -> Dict[str, Any]:
        """
        Get trade summary for a specific date.
        
        Args:
            target_date: Date to summarize (defaults to today)
            
        Returns:
            Dictionary with daily summary statistics
        """
        if target_date is None:
            target_date = date.today()
        
        trades = self.daily_trades.get(target_date, [])
        
        if not trades:
            return {
                "date": target_date,
                "trades": 0,
                "volume": 0.0,
                "value": 0.0,
                "avg_price": 0.0,
                "long_trades": 0,
                "short_trades": 0,
            }
        
        total_volume = sum(trade.volume for trade in trades)
        total_value = sum(trade.price * trade.volume for trade in trades)
        long_trades = sum(1 for trade in trades if trade.direction == Direction.LONG)
        short_trades = len(trades) - long_trades
        
        return {
            "date": target_date,
            "trades": len(trades),
            "volume": total_volume,
            "value": total_value,
            "avg_price": total_value / total_volume if total_volume > 0 else 0,
            "long_trades": long_trades,
            "short_trades": short_trades,
        }
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary for current trading session.
        
        Returns:
            Dictionary with session summary statistics
        """
        # For now, use today's trades as session
        # This could be enhanced to track actual session boundaries
        return self.get_daily_summary()
    
    def get_symbol_summary(self, symbol: str) -> Dict[str, Any]:
        """
        Get trade summary for a specific symbol.
        
        Args:
            symbol: Symbol to summarize
            
        Returns:
            Dictionary with symbol-specific statistics
        """
        symbol_trades = []
        for daily_trades in self.daily_trades.values():
            symbol_trades.extend(
                trade for trade in daily_trades if trade.symbol == symbol
            )
        
        if not symbol_trades:
            return {
                "symbol": symbol,
                "trades": 0,
                "volume": 0.0,
                "value": 0.0,
                "avg_price": 0.0,
            }
        
        total_volume = sum(trade.volume for trade in symbol_trades)
        total_value = sum(trade.price * trade.volume for trade in symbol_trades)
        
        return {
            "symbol": symbol,
            "trades": len(symbol_trades),
            "volume": total_volume,
            "value": total_value,
            "avg_price": total_value / total_volume if total_volume > 0 else 0,
        }
    
    def calculate_trade_pnl(self, trade: TradeData) -> float:
        """
        Calculate P&L for a trade (placeholder implementation).
        
        Args:
            trade: Trade data
            
        Returns:
            Calculated P&L
        """
        # This is a simplified placeholder
        # Real implementation would track positions and calculate against entry prices
        return 0.0
    
    def is_large_trade(self, trade: TradeData) -> bool:
        """
        Check if a trade exceeds the large trade threshold.
        
        Args:
            trade: Trade data to check
            
        Returns:
            True if trade is considered large
        """
        monitor = self.monitor
        trade_value = trade.price * trade.volume
        return trade_value >= monitor.large_trade_threshold
    
    async def update_statistics_display(self) -> None:
        """Update the monitor display with current statistics."""
        # This would trigger the monitor to refresh its statistics display
        # Implementation depends on the monitor's UI update mechanisms
        pass
    
    def reset_statistics(self) -> None:
        """Reset all statistics to initial state."""
        self.daily_trades.clear()
        self.statistics = {
            "total_trades": 0,
            "total_volume": 0.0,
            "total_value": 0.0,
            "long_trades": 0,
            "short_trades": 0,
            "avg_price": 0.0,
            "session_pnl": 0.0,
        }
    
    def get_formatted_summary_message(self) -> str:
        """
        Get a formatted summary message for display.
        
        Returns:
            Formatted summary string
        """
        summary = self.get_daily_summary()
        return (
            f"Today: {summary['trades']} trades, "
            f"Vol: {TUIFormatter.format_volume(summary['volume'])}, "
            f"Avg: {TUIFormatter.format_price(summary['avg_price'], 2)}"
        )