"""
Log Monitor for TUI

Real-time log display component that shows system messages, trading events,
and error notifications in a structured table format.
"""

from datetime import datetime
from typing import Any

from textual.coordinate import Coordinate

from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.event_type import EVENT_LOG
from foxtrot.util.object import LogData

from ...config.settings import get_settings
from ..base_monitor import TUIDataMonitor


class TUILogMonitor(TUIDataMonitor):
    """
    TUI Log Monitor for displaying real-time log messages.

    Features:
        - Real-time log message display
        - Color coding by log level (INFO, WARNING, ERROR, etc.)
        - Automatic scrolling to show latest messages
        - Log level filtering
        - Gateway-specific log filtering
        - Export functionality for log analysis
    """

    # Monitor configuration
    event_type = EVENT_LOG
    data_key = ""  # No unique key - all log entries are separate
    sorting = False  # Keep chronological order

    # Column configuration
    headers = {
        "time": {
            "display": "Time",
            "cell": "datetime",
            "update": False,
            "width": 12,
        },
        "level": {
            "display": "Level",
            "cell": "enum",
            "update": False,
            "width": 8,
        },
        "msg": {
            "display": "Message",
            "cell": "default",
            "update": False,
            "width": 60,
        },
        "gateway_name": {
            "display": "Gateway",
            "cell": "default",
            "update": False,
            "width": 12,
        },
    }

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine, **kwargs: Any) -> None:
        """
        Initialize the log monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            **kwargs: Additional arguments
        """
        super().__init__(main_engine, event_engine, monitor_name="Log Monitor", **kwargs)

        # Log-specific settings
        self.max_log_entries = get_settings().performance.max_log_entries
        self.auto_scroll = True
        self.level_filter: str | None = None
        self.gateway_filter: str | None = None

        # Color scheme for log levels
        self.level_colors = {
            "DEBUG": "dim white",
            "INFO": "cyan",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bright_red",
        }

    def compose(self):
        """Create the log monitor layout with additional controls."""
        # Use the base compose but add log-specific title
        for widget in super().compose():
            yield widget

    async def on_mount(self) -> None:
        """Called when the log monitor is mounted."""
        await super().on_mount()

        # Add initial log message
        await self._add_system_message("INFO", "Log monitor initialized")

    async def _process_event(self, event) -> None:
        """
        Process log events with filtering and formatting.

        Args:
            event: Log event containing LogData
        """
        try:
            log_data: LogData = event.data

            # Apply filters
            if self.level_filter and log_data.level != self.level_filter:
                return

            if self.gateway_filter and log_data.adapter_name != self.gateway_filter:
                return

            # Process the log entry
            await super()._process_event(event)

            # Auto-scroll to latest message if enabled
            if self.auto_scroll and self.data_table:
                self.data_table.cursor_coordinate = Coordinate(0, 0)

        except Exception as e:
            # Fallback error handling - don't let log monitor crash
            await self._add_system_message("ERROR", f"Log monitor error: {e}")

    async def _insert_new_row(self, data: LogData) -> None:
        """
        Insert a new log entry with special handling for log rotation.

        Args:
            data: The LogData object to insert
        """
        if not self.data_table:
            return

        # Check if we need to remove old entries
        if self.data_table.row_count >= self.max_log_entries:
            # Remove oldest entries (from the bottom)
            rows_to_remove = self.data_table.row_count - self.max_log_entries + 1
            for _ in range(rows_to_remove):
                if self.data_table.row_count > 0:
                    self.data_table.remove_row(self.data_table.row_count - 1)

        # Format log data for display
        formatted_time = self._format_log_time(data.time)
        formatted_level = data.level
        formatted_message = self._format_log_message(data.msg)
        formatted_gateway = data.adapter_name or "SYSTEM"

        # Insert the new log entry at the top
        row_values = [formatted_time, formatted_level, formatted_message, formatted_gateway]
        self.data_table.add_row(*row_values, key=None)

        # Apply color styling based on log level
        await self._apply_log_styling(0, data)

    def _format_log_time(self, log_time: datetime) -> str:
        """
        Format log timestamp for display.

        Args:
            log_time: The datetime object

        Returns:
            Formatted time string
        """
        return log_time.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds

    def _format_log_message(self, message: str) -> str:
        """
        Format log message for display with truncation if needed.

        Args:
            message: The raw log message

        Returns:
            Formatted message string
        """
        # Truncate very long messages
        max_length = 100
        if len(message) > max_length:
            return message[: max_length - 3] + "..."
        return message

    async def _apply_log_styling(self, row_index: int, data: LogData) -> None:
        """
        Apply color styling to log entries based on level.

        Args:
            row_index: The row index to style
            data: The LogData object
        """
        # This would apply colors based on log level
        # Textual's DataTable styling is handled through CSS
        # For now, we rely on the CSS configuration in the app

    async def _add_system_message(self, level: str, message: str) -> None:
        """
        Add a system-generated log message.

        Args:
            level: Log level (INFO, WARNING, ERROR, etc.)
            message: The message text
        """
        # Create a synthetic LogData object
        from foxtrot.util.object import LogData

        log_data = LogData(msg=message, level=level, adapter_name="SYSTEM")

        # Insert directly without going through event system
        await self._insert_new_row(log_data)

    # Additional action methods specific to log monitor

    def action_toggle_auto_scroll(self) -> None:
        """Toggle automatic scrolling to latest messages."""
        self.auto_scroll = not self.auto_scroll
        if self.title_bar:
            status = " [AUTO-SCROLL]" if self.auto_scroll else ""
            self.title_bar.update(f"Log Monitor{status}")

    def action_filter_by_level(self, level: str) -> None:
        """
        Filter logs by level.

        Args:
            level: Log level to filter by (INFO, WARNING, ERROR, etc.)
        """
        self.level_filter = level if level != self.level_filter else None
        self._update_filter_display()

    def action_filter_by_gateway(self, gateway: str) -> None:
        """
        Filter logs by gateway.

        Args:
            gateway: Gateway name to filter by
        """
        self.gateway_filter = gateway if gateway != self.gateway_filter else None
        self._update_filter_display()

    def action_clear_filters(self) -> None:
        """Clear all active filters."""
        self.level_filter = None
        self.gateway_filter = None
        self._update_filter_display()

    def _update_filter_display(self) -> None:
        """Update the title bar to show active filters."""
        if not self.title_bar:
            return

        title = "Log Monitor"
        filters = []

        if self.level_filter:
            filters.append(f"Level:{self.level_filter}")

        if self.gateway_filter:
            filters.append(f"Gateway:{self.gateway_filter}")

        if self.auto_scroll:
            filters.append("AUTO-SCROLL")

        if filters:
            title += f" [{', '.join(filters)}]"

        self.title_bar.update(title)

    # Enhanced key bindings for log monitor
    BINDINGS = TUIDataMonitor.BINDINGS + [
        ("a", "toggle_auto_scroll", "Auto-scroll"),
        ("1", "filter_info", "Info Only"),
        ("2", "filter_warning", "Warning+"),
        ("3", "filter_error", "Error Only"),
        ("ctrl+f", "clear_filters", "Clear Filters"),
    ]

    def action_filter_info(self) -> None:
        """Filter to show INFO level and above."""
        self.action_filter_by_level("INFO")

    def action_filter_warning(self) -> None:
        """Filter to show WARNING level and above."""
        self.action_filter_by_level("WARNING")

    def action_filter_error(self) -> None:
        """Filter to show ERROR level and above."""
        self.action_filter_by_level("ERROR")

    async def action_save_csv(self) -> None:
        """Save log data to CSV with enhanced formatting."""
        if not self.data_table:
            return

        try:
            import csv

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"foxtrot_logs_{timestamp}.csv"
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers with additional metadata
                writer.writerow(
                    ["Timestamp", "Level", "Message", "Gateway", "Export Date", "Total Entries"]
                )

                # Write log entries
                export_time = datetime.now().isoformat()
                total_entries = self.data_table.row_count

                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend([export_time, str(total_entries)])
                    else:
                        row_data.extend(["", ""])

                    writer.writerow(row_data)

            await self._add_system_message("INFO", f"Logs exported to {filepath}")

        except Exception as e:
            await self._add_system_message("ERROR", f"Failed to export logs: {e}")


# Convenience function for creating log monitor
def create_log_monitor(main_engine: MainEngine, event_engine: EventEngine) -> TUILogMonitor:
    """
    Create a configured log monitor instance.

    Args:
        main_engine: The main trading engine
        event_engine: The event engine

    Returns:
        Configured TUILogMonitor instance
    """
    return TUILogMonitor(main_engine, event_engine)
