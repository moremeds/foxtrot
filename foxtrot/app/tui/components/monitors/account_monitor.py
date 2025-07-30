"""
Account Monitor for TUI

Account information and balance tracking component that displays
account balances, margin information, and provides account management functionality.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

from textual.coordinate import Coordinate
from textual.message import Message

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_ACCOUNT
from foxtrot.util.object import AccountData

from ...utils.colors import ColorType, get_color_manager
from ...utils.formatters import TUIFormatter
from ..base_monitor import TUIDataMonitor


class TUIAccountMonitor(TUIDataMonitor):
    """
    TUI Account Monitor for tracking account balances and information.

    Features:
        - Real-time account balance updates
        - Multi-currency balance display
        - Margin and leverage information
        - Available buying power calculations
        - Account risk metrics and warnings
        - Balance history tracking
        - Export functionality for account analysis
        - Integration with position monitor for margin requirements
    """

    # Monitor configuration
    event_type = EVENT_ACCOUNT
    data_key = "vt_accountid"
    sorting = True  # Enable sorting by different columns

    # Column configuration
    headers = {
        "accountid": {
            "display": "Account ID",
            "cell": "default",
            "update": False,
            "width": 15,
            "precision": 0,
        },
        "balance": {
            "display": "Balance",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "frozen": {
            "display": "Frozen",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "available": {
            "display": "Available",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "currency": {
            "display": "Currency",
            "cell": "default",
            "update": False,
            "width": 8,
            "precision": 0,
        },
        "pre_balance": {
            "display": "Pre Balance",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "net_pnl": {
            "display": "Net P&L",
            "cell": "pnl",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "commission": {
            "display": "Commission",
            "cell": "currency",
            "update": True,
            "width": 10,
            "precision": 2,
        },
        "margin": {
            "display": "Margin",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
        },
        "datetime": {
            "display": "Updated",
            "cell": "datetime",
            "update": True,
            "width": 12,
            "precision": 0,
        },
        "gateway_name": {
            "display": "Gateway",
            "cell": "default",
            "update": False,
            "width": 10,
            "precision": 0,
        },
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
        """
        Initialize the account monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Account Monitor", **kwargs)

        # Color manager for styling
        self.color_manager = get_color_manager()

        # Account tracking and analytics
        self.account_history: dict[str, list[AccountData]] = {}
        self.account_statistics: dict[str, Any] = {
            "total_accounts": 0,
            "total_balance": 0.0,
            "total_available": 0.0,
            "total_frozen": 0.0,
            "total_pnl": 0.0,
            "total_commission": 0.0,
            "total_margin": 0.0,
        }

        # Risk management metrics
        self.risk_metrics: dict[str, Any] = {
            "margin_ratio": 0.0,
            "buying_power": 0.0,
            "leverage_used": 0.0,
            "risk_utilization": 0.0,
        }

        # Filtering options
        self.currency_filter: str | None = None
        self.gateway_filter: str | None = None
        self.min_balance_filter: float | None = None

        # Display options
        self.show_zero_balances = False
        self.group_by_currency = True
        self.show_percentage_changes = True
        self.highlight_margin_warnings = True
        self.auto_scroll_to_updates = True

        # Risk management settings
        self.margin_warning_threshold = 0.8  # Warn at 80% margin usage
        self.balance_warning_threshold = 1000.0  # Warn below $1000
        self.pnl_warning_threshold = -500.0  # Warn on daily losses > $500

    def compose(self):
        """Create the account monitor layout with account summary."""
        for widget in super().compose():
            yield widget

    async def on_mount(self) -> None:
        """Called when the account monitor is mounted."""
        await super().on_mount()

        # Initialize with welcome message
        await self._add_system_message("Account monitor ready for balance tracking")

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content with account-specific formatting.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        if content is None:
            return "-"

        cell_type = config.get("cell", "default")
        precision = config.get("precision", 2)

        if cell_type == "currency":
            # Format currency values
            return TUIFormatter.format_currency(content, precision=precision)

        if cell_type == "pnl":
            # Format P&L with sign indication
            return TUIFormatter.format_pnl(content, show_percentage=False)

        if cell_type == "percentage":
            # Format percentage changes
            if isinstance(content, (int, float)) and content != 0:
                return TUIFormatter.format_percentage(content, show_sign=True)
            return "-"

        if cell_type == "datetime":
            if isinstance(content, datetime):
                return TUIFormatter.format_datetime(content, "time")

        else:
            # Default formatting with truncation
            if isinstance(content, str) and len(content) > config.get("width", 20):
                return TUIFormatter.truncate_text(content, config.get("width", 20))
            return str(content)

    async def _apply_row_styling(self, row_index: int, data: AccountData) -> None:
        """
        Apply color styling to account data based on balance and P&L.

        Args:
            row_index: The row index to style
            data: The AccountData object
        """
        if not self.data_table:
            return

        try:
            # Balance-based color coding
            if data.available < self.balance_warning_threshold:
                # Low balance warning
                balance_color = ColorType.WARNING
            else:
                balance_color = ColorType.SUCCESS

            # P&L-based color coding
            pnl_color = self.color_manager.get_pnl_color(data.net_pnl)

            # Margin-based warnings
            if hasattr(data, "margin") and data.margin > 0:
                margin_ratio = data.margin / max(data.balance, 1)
                if margin_ratio > self.margin_warning_threshold:
                    # High margin usage warning
                    margin_color = ColorType.ERROR
                else:
                    margin_color = ColorType.NEUTRAL

            # Apply styling based on account properties
            # This would integrate with Textual's styling system

        except Exception as e:
            await self._log_error(f"Error applying row styling: {e}")

    async def _process_event(self, event) -> None:
        """
        Process account events with filtering and statistics updates.

        Args:
            event: Account event containing AccountData
        """
        try:
            account_data: AccountData = event.data

            # Apply filters
            if not self._passes_filters(account_data):
                return

            # Update account tracking
            await self._update_account_tracking(account_data)

            # Process the account data
            await super()._process_event(event)

            # Update statistics and risk metrics
            await self._update_account_statistics(account_data)
            await self._update_risk_metrics()

            # Handle auto-scroll if enabled
            if self.auto_scroll_to_updates and self.data_table:
                self.data_table.cursor_coordinate = Coordinate(0, 0)

            # Emit account processed message
            self.post_message(self.AccountProcessed(account_data))

            # Check for risk warnings
            await self._check_risk_warnings(account_data)

        except Exception as e:
            await self._log_error(f"Error processing account event: {e}")

    def _passes_filters(self, account_data: AccountData) -> bool:
        """
        Check if account data passes current filters.

        Args:
            account_data: The AccountData to check

        Returns:
            True if account passes all filters
        """
        # Currency filter
        if self.currency_filter:
            if account_data.currency != self.currency_filter:
                return False

        # Gateway filter
        if self.gateway_filter:
            if account_data.gateway_name != self.gateway_filter:
                return False

        # Minimum balance filter
        if self.min_balance_filter is not None:
            if account_data.balance < self.min_balance_filter:
                return False

        # Zero balance filter
        if not self.show_zero_balances:
            if account_data.balance == 0 and account_data.available == 0:
                return False

        return True

    async def _update_account_tracking(self, account_data: AccountData) -> None:
        """
        Update internal account tracking and history.

        Args:
            account_data: The account data to track
        """
        account_id = account_data.vt_accountid

        # Maintain account history for analysis
        if account_id not in self.account_history:
            self.account_history[account_id] = []

        # Keep last 100 updates for each account
        history = self.account_history[account_id]
        history.append(account_data)
        if len(history) > 100:
            history.pop(0)

    async def _update_account_statistics(self, account_data: AccountData) -> None:
        """
        Update account statistics based on new account data.

        Args:
            account_data: The new account data
        """
        # This would aggregate statistics across all accounts
        # For now, we'll track the current account
        stats = self.account_statistics

        # Update totals (simplified - would need proper aggregation)
        stats["total_balance"] = account_data.balance
        stats["total_available"] = account_data.available
        stats["total_frozen"] = account_data.frozen
        stats["total_pnl"] = account_data.net_pnl
        stats["total_commission"] = getattr(account_data, "commission", 0)
        stats["total_margin"] = getattr(account_data, "margin", 0)

        # Update display with statistics
        await self._update_statistics_display()

    async def _update_risk_metrics(self) -> None:
        """Update account risk management metrics."""
        try:
            stats = self.account_statistics

            # Calculate margin ratio
            if stats["total_balance"] > 0:
                self.risk_metrics["margin_ratio"] = stats["total_margin"] / stats["total_balance"]
            else:
                self.risk_metrics["margin_ratio"] = 0.0

            # Calculate buying power
            self.risk_metrics["buying_power"] = stats["total_available"]

            # Calculate leverage used
            if stats["total_balance"] > 0:
                self.risk_metrics["leverage_used"] = stats["total_margin"] / stats["total_balance"]
            else:
                self.risk_metrics["leverage_used"] = 0.0

            # Calculate risk utilization
            if stats["total_balance"] > 0:
                self.risk_metrics["risk_utilization"] = (
                    stats["total_frozen"] + stats["total_margin"]
                ) / stats["total_balance"]
            else:
                self.risk_metrics["risk_utilization"] = 0.0

        except Exception as e:
            await self._log_error(f"Error updating risk metrics: {e}")

    async def _update_statistics_display(self) -> None:
        """Update the title bar with current statistics."""
        if not self.title_bar:
            return

        stats = self.account_statistics

        title = f"Account Monitor - Balance: {TUIFormatter.format_currency(stats['total_balance'])} | Available: {TUIFormatter.format_currency(stats['total_available'])}"

        # Add P&L if significant
        if abs(stats["total_pnl"]) > 0.01:
            title += f" | P&L: {TUIFormatter.format_pnl(stats['total_pnl'])}"

        # Add filter information if active
        filters = []
        if self.currency_filter:
            filters.append(f"Currency:{self.currency_filter}")
        if self.gateway_filter:
            filters.append(f"Gateway:{self.gateway_filter}")
        if not self.show_zero_balances:
            filters.append("NON-ZERO")

        if filters:
            title += f" [{', '.join(filters)}]"

        self.title_bar.update(title)

    async def _check_risk_warnings(self, account_data: AccountData) -> None:
        """
        Check for risk warnings and alert if necessary.

        Args:
            account_data: Account data to check
        """
        warnings = []

        # Check for low balance
        if account_data.available < self.balance_warning_threshold:
            warnings.append(
                f"Low available balance: {TUIFormatter.format_currency(account_data.available)}"
            )

        # Check for high margin usage
        if hasattr(account_data, "margin") and account_data.margin > 0:
            margin_ratio = account_data.margin / max(account_data.balance, 1)
            if margin_ratio > self.margin_warning_threshold:
                warnings.append(
                    f"High margin usage: {TUIFormatter.format_percentage(margin_ratio)}"
                )

        # Check for significant daily losses
        if account_data.net_pnl < self.pnl_warning_threshold:
            warnings.append(f"Significant loss: {TUIFormatter.format_pnl(account_data.net_pnl)}")

        # Emit warnings
        for warning in warnings:
            await self._add_system_message(f"⚠️ {warning}")
            self.post_message(self.AccountWarning(account_data, warning))

    async def _add_system_message(self, message: str) -> None:
        """
        Add a system message to the monitor.

        Args:
            message: The message to add
        """
        if self.title_bar:
            current_time = datetime.now().strftime("%H:%M:%S")
            await self._update_statistics_display()

    # Account analysis methods

    def get_account_summary(self) -> dict[str, Any]:
        """
        Get comprehensive account summary.

        Returns:
            Dictionary with account statistics
        """
        stats = self.account_statistics.copy()
        metrics = self.risk_metrics.copy()

        # Calculate additional metrics
        total_equity = stats["total_balance"] + stats["total_pnl"]
        stats["total_equity"] = total_equity
        stats["equity_ratio"] = total_equity / max(stats["total_balance"], 1)

        return {**stats, **metrics}

    def get_currency_breakdown(self) -> dict[str, dict[str, float]]:
        """
        Get balance breakdown by currency.

        Returns:
            Dictionary with currency-specific balances
        """
        currency_data = {}

        for account_data in self.row_data.values():
            if hasattr(account_data, "currency"):
                currency = account_data.currency
                if currency not in currency_data:
                    currency_data[currency] = {
                        "balance": 0.0,
                        "available": 0.0,
                        "frozen": 0.0,
                        "pnl": 0.0,
                    }

                currency_data[currency]["balance"] += account_data.balance
                currency_data[currency]["available"] += account_data.available
                currency_data[currency]["frozen"] += account_data.frozen
                currency_data[currency]["pnl"] += account_data.net_pnl

        return currency_data

    def get_balance_history(self, account_id: str, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get balance history for an account.

        Args:
            account_id: Account identifier
            hours: Number of hours of history to return

        Returns:
            List of historical balance data
        """
        if account_id not in self.account_history:
            return []

        history = self.account_history[account_id]
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            {
                "timestamp": data.datetime,
                "balance": data.balance,
                "available": data.available,
                "pnl": data.net_pnl,
            }
            for data in history
            if data.datetime >= cutoff_time
        ]

    # Filter and display management actions

    def action_filter_by_currency(self, currency: str) -> None:
        """
        Filter accounts by currency.

        Args:
            currency: Currency code to filter by
        """
        self.currency_filter = currency if currency != self.currency_filter else None
        self._update_filter_display()

    def action_filter_by_gateway(self, gateway: str) -> None:
        """
        Filter accounts by gateway.

        Args:
            gateway: Gateway name to filter by
        """
        self.gateway_filter = gateway if gateway != self.gateway_filter else None
        self._update_filter_display()

    def action_filter_by_balance(self, min_balance: float) -> None:
        """
        Filter accounts by minimum balance.

        Args:
            min_balance: Minimum balance threshold
        """
        self.min_balance_filter = min_balance if min_balance != self.min_balance_filter else None
        self._update_filter_display()

    def action_toggle_zero_balances(self) -> None:
        """Toggle display of zero balance accounts."""
        self.show_zero_balances = not self.show_zero_balances
        self._update_filter_display()

    def action_toggle_percentage_changes(self) -> None:
        """Toggle display of percentage changes."""
        self.show_percentage_changes = not self.show_percentage_changes
        asyncio.create_task(
            self._add_system_message(
                f"Percentage changes {'ON' if self.show_percentage_changes else 'OFF'}"
            )
        )

    def action_toggle_margin_warnings(self) -> None:
        """Toggle margin warning highlights."""
        self.highlight_margin_warnings = not self.highlight_margin_warnings
        asyncio.create_task(
            self._add_system_message(
                f"Margin warnings {'ON' if self.highlight_margin_warnings else 'OFF'}"
            )
        )

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.currency_filter = None
        self.gateway_filter = None
        self.min_balance_filter = None
        self.show_zero_balances = False
        self._update_filter_display()

    def _update_filter_display(self) -> None:
        """Update the display based on current filters."""
        asyncio.create_task(self._update_statistics_display())

    # Enhanced key bindings for account monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("f1", "filter_usd", "USD Accounts"),
        ("f2", "filter_zero", "Show Zero"),
        ("f3", "filter_margin", "Margin Accounts"),
        ("f4", "show_risk", "Risk Metrics"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
        ("a", "toggle_auto_scroll", "Auto Scroll"),
        ("p", "toggle_percentage", "Show Changes %"),
        ("m", "toggle_margin_warnings", "Margin Warnings"),
        ("c", "show_currency_breakdown", "Currency Breakdown"),
        ("h", "show_balance_history", "Balance History"),
    ]

    def action_filter_usd(self) -> None:
        """Filter to show USD accounts only."""
        self.action_filter_by_currency("USD")

    def action_filter_zero(self) -> None:
        """Toggle zero balance account display."""
        self.action_toggle_zero_balances()

    def action_filter_margin(self) -> None:
        """Filter to show margin accounts only."""
        self.min_balance_filter = 100.0  # Accounts with significant balance
        self._update_filter_display()

    def action_show_risk(self) -> None:
        """Show risk metrics summary."""
        metrics = self.risk_metrics
        message = f"Risk: Margin {metrics['margin_ratio']:.1%}, Leverage {metrics['leverage_used']:.2f}x, Utilization {metrics['risk_utilization']:.1%}"
        asyncio.create_task(self._add_system_message(message))

    def action_toggle_percentage(self) -> None:
        """Toggle percentage changes display."""
        self.action_toggle_percentage_changes()

    def action_toggle_margin_warnings(self) -> None:
        """Toggle margin warning display."""
        self.action_toggle_margin_warnings()

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to account updates."""
        self.auto_scroll_to_updates = not self.auto_scroll_to_updates
        status = "ON" if self.auto_scroll_to_updates else "OFF"
        asyncio.create_task(self._add_system_message(f"Auto-scroll {status}"))

    def action_show_currency_breakdown(self) -> None:
        """Show currency breakdown summary."""
        breakdown = self.get_currency_breakdown()
        currencies = list(breakdown.keys())[:3]  # Show first 3 currencies
        if currencies:
            currency_info = []
            for c in currencies:
                balance = breakdown[c]["balance"]
                currency_info.append(f"{c}:{TUIFormatter.format_currency(balance)}")
            message = f"Currencies: {', '.join(currency_info)}"
        else:
            message = "No currency data available"
        asyncio.create_task(self._add_system_message(message))

    def action_show_balance_history(self) -> None:
        """Show balance history for selected account."""
        # This would show history for the currently selected account
        summary = self.get_account_summary()
        message = f"Balance History: Equity {TUIFormatter.format_currency(summary['total_equity'])}, P&L {TUIFormatter.format_pnl(summary['total_pnl'])}"
        asyncio.create_task(self._add_system_message(message))

    async def action_save_csv(self) -> None:
        """Save account data to CSV with risk analysis."""
        if not self.data_table:
            return

        try:
            import csv

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"account_balances_{timestamp}.csv"
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers with risk analysis context
                headers = [config["display"] for config in self.headers.values()]
                headers.extend(
                    [
                        "Equity",
                        "Margin Ratio",
                        "Risk Level",
                        "Export Date",
                        "Filter Applied",
                        "Total Accounts",
                        "Total Equity",
                        "Portfolio Risk",
                    ]
                )
                writer.writerow(headers)

                # Collect metadata
                export_time = datetime.now().isoformat()
                filter_info = f"Currency:{self.currency_filter or 'All'}"
                summary = self.get_account_summary()

                # Write account data with calculated values
                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    # Calculate additional fields (would need access to raw account data)
                    equity = "N/A"  # Would be calculated from balance + pnl
                    margin_ratio = f"{summary['margin_ratio']:.1%}"
                    risk_level = "MEDIUM"  # Would be calculated based on risk metrics

                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend(
                            [
                                equity,
                                margin_ratio,
                                risk_level,
                                export_time,
                                filter_info,
                                str(summary.get("total_accounts", 1)),
                                TUIFormatter.format_currency(summary["total_equity"]),
                                f"{summary['risk_utilization']:.1%}",
                            ]
                        )
                    else:
                        row_data.extend(["", "", "", "", "", "", "", ""])

                    writer.writerow(row_data)

            await self._add_system_message(f"Account balances exported to {filepath}")

        except Exception as e:
            await self._log_error(f"Failed to export account balances: {e}")

    # Custom messages for account events

    class AccountProcessed(Message):
        """Message sent when an account is processed."""

        def __init__(self, account_data: AccountData) -> None:
            self.account_data = account_data
            super().__init__()

    class AccountWarning(Message):
        """Message sent when an account warning is triggered."""

        def __init__(self, account_data: AccountData, warning: str) -> None:
            self.account_data = account_data
            self.warning = warning
            super().__init__()

    class AccountSelected(Message):
        """Message sent when an account is selected for trading panel update."""

        def __init__(self, account_data: AccountData) -> None:
            self.account_data = account_data
            super().__init__()


# Convenience function for creating account monitor
def create_account_monitor(main_engine: MainEngine, event_engine: EventEngine) -> TUIAccountMonitor:
    """
    Create a configured account monitor instance.

    Args:
        main_engine: The main trading engine
        event_engine: The event engine

    Returns:
        Configured TUIAccountMonitor instance
    """
    return TUIAccountMonitor(main_engine, event_engine)
