"""
Position monitor business logic for portfolio analytics and position management.

This module handles position tracking, portfolio calculations, statistics
aggregation, and risk analysis without UI dependencies.
"""

from typing import Any, Dict, List, Set
from datetime import datetime

from foxtrot.util.object import PositionData
from foxtrot.util.constants import Direction, Exchange
from ....utils.formatters import TUIFormatter


class PositionBusinessLogic:
    """
    Core business logic for position monitoring and portfolio management.
    
    This class handles all position-related calculations, portfolio analytics,
    statistics aggregation, and business rule validation with no UI dependencies.
    """

    def __init__(self):
        # Position tracking and analytics
        self.active_positions: Set[str] = set()
        self.position_statistics: Dict[str, Any] = {
            "total_positions": 0,
            "long_positions": 0,
            "short_positions": 0,
            "total_pnl": 0.0,
            "total_value": 0.0,
            "largest_position": 0.0,
            "largest_pnl": 0.0,
            "winning_positions": 0,
            "losing_positions": 0,
        }

        # Portfolio metrics
        self.portfolio_metrics: Dict[str, Any] = {
            "net_exposure": 0.0,
            "gross_exposure": 0.0,
            "leverage": 0.0,
            "beta": 0.0,
            "sharpe_ratio": 0.0,
        }

        # Risk management settings
        self.position_limit_warning = 0.8  # Warn at 80% of limit
        self.pnl_warning_threshold = -1000.0  # Warn on large losses
        self.large_position_threshold = 10000.0  # Value threshold

    def passes_filters(
        self,
        position_data: PositionData,
        symbol_filter: str | None = None,
        direction_filter: Direction | None = None,
        exchange_filter: Exchange | None = None,
        gateway_filter: str | None = None,
        min_pnl_filter: float | None = None,
        min_value_filter: float | None = None,
        show_only_active: bool = True,
    ) -> bool:
        """
        Check if position data passes current filters.

        Args:
            position_data: The PositionData to check
            symbol_filter: Symbol filter to apply
            direction_filter: Direction filter to apply
            exchange_filter: Exchange filter to apply
            gateway_filter: Gateway filter to apply
            min_pnl_filter: Minimum P&L filter to apply
            min_value_filter: Minimum value filter to apply
            show_only_active: Whether to show only active positions

        Returns:
            True if position passes all filters
        """
        # Symbol filter
        if symbol_filter:
            if symbol_filter.lower() not in position_data.symbol.lower():
                return False

        # Direction filter
        if direction_filter is not None:
            if position_data.direction != direction_filter:
                return False

        # Exchange filter
        if exchange_filter is not None:
            if position_data.exchange != exchange_filter:
                return False

        # Gateway filter
        if gateway_filter and position_data.gateway_name != gateway_filter:
            return False

        # P&L filter
        if min_pnl_filter is not None and position_data.pnl < min_pnl_filter:
            return False

        # Position value filter
        if min_value_filter is not None:
            position_value = abs(position_data.price * position_data.volume)
            if position_value < min_value_filter:
                return False

        # Active positions only filter
        return not (show_only_active and position_data.volume == 0)

    def update_position_tracking(self, position_data: PositionData) -> None:
        """
        Update internal position tracking based on position status.

        Args:
            position_data: The position data to track
        """
        position_id = position_data.vt_positionid

        # Track active vs closed positions
        if position_data.volume != 0:
            self.active_positions.add(position_id)
        else:
            self.active_positions.discard(position_id)

    def update_position_statistics(self, position_data: PositionData) -> None:
        """
        Update position statistics based on new position data.

        Args:
            position_data: The new position data
        """
        stats = self.position_statistics

        # Update position counts
        if position_data.vt_positionid not in self.active_positions and position_data.volume != 0:
            stats["total_positions"] += 1

            if position_data.direction == Direction.LONG:
                stats["long_positions"] += 1
            else:
                stats["short_positions"] += 1

        # Update P&L statistics
        stats["total_pnl"] += position_data.pnl

        # Update position value
        position_value = abs(position_data.price * position_data.volume)
        stats["total_value"] += position_value

        # Track largest position and P&L
        if position_value > stats["largest_position"]:
            stats["largest_position"] = position_value

        if abs(position_data.pnl) > abs(stats["largest_pnl"]):
            stats["largest_pnl"] = position_data.pnl

        # Update win/loss counts
        if position_data.pnl > 0:
            stats["winning_positions"] += 1
        elif position_data.pnl < 0:
            stats["losing_positions"] += 1

    def update_portfolio_metrics(self, row_data: Dict[str, PositionData]) -> None:
        """
        Update portfolio-level risk metrics.

        Args:
            row_data: Dictionary of position data by position ID
        """
        try:
            # Calculate basic portfolio metrics
            # Net exposure (long - short)
            long_value = sum(
                abs(pos.price * pos.volume)
                for pos in row_data.values()
                if hasattr(pos, "direction") and pos.direction == Direction.LONG
            )
            short_value = sum(
                abs(pos.price * pos.volume)
                for pos in row_data.values()
                if hasattr(pos, "direction") and pos.direction == Direction.SHORT
            )

            self.portfolio_metrics["net_exposure"] = long_value - short_value
            self.portfolio_metrics["gross_exposure"] = long_value + short_value

            # Calculate leverage if account value is available
            # This would integrate with account data in a full implementation

        except Exception:
            # Error in metrics calculation should not break the system
            pass

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary.

        Returns:
            Dictionary with portfolio statistics
        """
        stats = self.position_statistics.copy()
        metrics = self.portfolio_metrics.copy()

        # Calculate additional metrics
        stats["win_rate"] = stats["winning_positions"] / max(stats["total_positions"], 1) * 100
        stats["avg_pnl"] = stats["total_pnl"] / max(stats["total_positions"], 1)

        return {**stats, **metrics, "active_positions": len(self.active_positions)}

    def get_symbol_exposure(self, symbol: str, row_data: Dict[str, PositionData]) -> Dict[str, Any]:
        """
        Get exposure details for a specific symbol.

        Args:
            symbol: Symbol to analyze
            row_data: Dictionary of position data

        Returns:
            Dictionary with symbol exposure data
        """
        symbol_positions = [
            pos for pos in row_data.values() if hasattr(pos, "symbol") and pos.symbol == symbol
        ]

        if not symbol_positions:
            return {"symbol": symbol, "positions": 0}

        total_volume = sum(pos.volume for pos in symbol_positions)
        total_value = sum(abs(pos.price * pos.volume) for pos in symbol_positions)
        total_pnl = sum(pos.pnl for pos in symbol_positions)

        return {
            "symbol": symbol,
            "positions": len(symbol_positions),
            "net_volume": total_volume,
            "total_value": total_value,
            "total_pnl": total_pnl,
            "avg_price": total_value / abs(total_volume) if total_volume != 0 else 0,
        }

    def check_risk_warnings(self, position_data: PositionData) -> List[str]:
        """
        Check for risk warnings and return warning messages.

        Args:
            position_data: Position data to check

        Returns:
            List of warning messages
        """
        warnings = []

        # Check for large losses
        if position_data.pnl < self.pnl_warning_threshold:
            warnings.append(
                f"Large loss: {TUIFormatter.format_pnl(position_data.pnl)} on {position_data.symbol}"
            )

        # Check for large position size
        position_value = abs(position_data.price * position_data.volume)
        if position_value > self.large_position_threshold:
            warnings.append(
                f"Large position: {TUIFormatter.format_currency(position_value)} in {position_data.symbol}"
            )

        return warnings

    def calculate_position_value(self, position_data: PositionData) -> float:
        """
        Calculate the total value of a position.

        Args:
            position_data: Position data

        Returns:
            Position value
        """
        return abs(position_data.price * position_data.volume)

    def get_risk_level(self, position_data: PositionData) -> str:
        """
        Determine risk level for a position.

        Args:
            position_data: Position data

        Returns:
            Risk level string (LOW, MEDIUM, HIGH)
        """
        position_value = self.calculate_position_value(position_data)
        pnl_ratio = abs(position_data.pnl) / max(position_value, 1)

        if position_value > self.large_position_threshold and pnl_ratio > 0.1:
            return "HIGH"
        elif position_value > self.large_position_threshold or pnl_ratio > 0.05:
            return "MEDIUM"
        else:
            return "LOW"

    def reset_statistics(self) -> None:
        """Reset all position statistics to initial state."""
        self.active_positions.clear()
        self.position_statistics = {
            "total_positions": 0,
            "long_positions": 0,
            "short_positions": 0,
            "total_pnl": 0.0,
            "total_value": 0.0,
            "largest_position": 0.0,
            "largest_pnl": 0.0,
            "winning_positions": 0,
            "losing_positions": 0,
        }
        self.portfolio_metrics = {
            "net_exposure": 0.0,
            "gross_exposure": 0.0,
            "leverage": 0.0,
            "beta": 0.0,
            "sharpe_ratio": 0.0,
        }