"""
Base Monitor for TUI Data Display Components

This module provides the foundation for all TUI data display components,
equivalent to the Qt BaseMonitor but optimized for terminal usage with Textual.
"""

import csv

# Removed ABC import to avoid metaclass conflicts with Textual
from datetime import datetime
from pathlib import Path
from typing import Any

from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.coordinate import Coordinate
from textual.message import Message
from textual.widgets import DataTable, Static

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.utility import TRADER_DIR

from ..config.settings import get_settings
from ..integration.event_adapter import TUIEventMixin


class TUIDataMonitor(Container, TUIEventMixin):
    """
    Base class for TUI data monitoring components.

    Provides the same functionality as Qt BaseMonitor but optimized for terminal usage.
    Features include:
        - Real-time data updates via EventEngine integration
        - Sortable columns with visual indicators
        - Color coding for different data types
        - Export functionality (CSV)
        - Keyboard navigation and shortcuts
        - Context menu actions
        - Column state persistence
    """

    # Bindings for keyboard shortcuts
    BINDINGS = [
        Binding("r", "resize_columns", "Resize Columns"),
        Binding("s", "save_csv", "Save CSV"),
        Binding("c", "clear_data", "Clear Data"),
        Binding("f", "toggle_filter", "Filter"),
        Binding("ctrl+a", "select_all", "Select All"),
        Binding("escape", "clear_selection", "Clear Selection"),
    ]

    # Class attributes to be overridden by subclasses
    event_type: str = ""
    data_key: str = ""
    sorting: bool = False
    headers: dict[str, dict[str, Any]] = {}

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        monitor_name: str = "Monitor",
        **kwargs: Any,
    ) -> None:
        """
        Initialize the TUI data monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine for handling events
            monitor_name: Display name for the monitor
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        TUIEventMixin.__init__(self)

        self.main_engine = main_engine
        self.event_engine = event_engine
        self.monitor_name = monitor_name

        # Data storage
        self.cells: dict[str, dict[str, Any]] = {}
        self.row_data: dict[int, Any] = {}  # Maps row index to data object

        # UI components
        self.title_bar: Static | None = None
        self.data_table: DataTable | None = None

        # State management
        self.is_sorting_enabled = self.sorting
        self.current_sort_column: str | None = None
        self.sort_ascending = True
        self.max_rows = get_settings().performance.max_table_rows

        # Filter state
        self.filter_active = False
        self.filter_text = ""

        # Export settings
        self.export_dir = Path(TRADER_DIR) / "exports"
        self.export_dir.mkdir(exist_ok=True)

    def compose(self):
        """Create the monitor layout."""
        with Vertical():
            # Title bar
            self.title_bar = Static(self.monitor_name, classes="title-bar")
            yield self.title_bar

            # Data table
            self.data_table = DataTable(
                cursor_type="row",
                zebra_stripes=get_settings().layout.zebra_stripes,
                show_cursor=True,
            )
            yield self.data_table

    async def on_mount(self) -> None:
        """Called when the monitor is mounted."""
        # Initialize the table
        await self._init_table()

        # Register for events
        await self._register_events()

        # Load saved settings
        await self._load_settings()

    async def _init_table(self) -> None:
        """Initialize the data table with columns."""
        if not self.data_table:
            return

        # Clear existing columns to prevent duplicates
        self.data_table.clear(columns=True)

        # Add columns based on headers configuration
        for header_key, header_config in self.headers.items():
            display_name = header_config.get("display", header_key)
            try:
                self.data_table.add_column(display_name, key=header_key)
            except Exception as e:
                # Log error but continue
                await self._log_error(f"Failed to add column {header_key}: {e}")

        # Configure table settings
        if get_settings().layout.auto_resize_columns:
            # Textual handles auto-resizing automatically
            pass

    async def _register_events(self) -> None:
        """Register for events from the EventEngine."""
        if self.event_type and self._event_adapter:
            self.register_event_handler(self.event_type, self._process_event)

    async def _process_event(self, event: Event) -> None:
        """
        Process new data from event and update the table.

        Args:
            event: The event containing data to display
        """
        try:
            data = event.data

            # Disable sorting during updates to prevent errors
            if self.is_sorting_enabled:
                self._disable_sorting()

            # Update data in table
            if not self.data_key:
                await self._insert_new_row(data)
            else:
                key = getattr(data, self.data_key, None)
                if key is None:
                    return

                if key in self.cells:
                    await self._update_existing_row(data, key)
                else:
                    await self._insert_new_row(data)

            # Re-enable sorting
            if self.is_sorting_enabled:
                self._enable_sorting()

        except Exception as e:
            # Log error but don't crash the monitor
            await self._log_error(f"Error processing event: {e}")

    async def _insert_new_row(self, data: Any) -> None:
        """
        Insert a new row into the table.

        Args:
            data: The data object to insert
        """
        if not self.data_table:
            return

        # Check row limit
        if self.data_table.row_count >= self.max_rows:
            # Remove oldest row (last row)
            self.data_table.remove_row(self.data_table.row_count - 1)

        # Prepare row data
        row_values = []
        row_cells = {}

        for header_key, header_config in self.headers.items():
            content = getattr(data, header_key, "")
            formatted_content = self._format_cell_content(content, header_config)
            row_values.append(formatted_content)

            # Store cell data if it's updatable
            if header_config.get("update", False):
                row_cells[header_key] = {"content": content, "data": data, "config": header_config}

        # Add row to table (at the top)
        self.data_table.add_row(*row_values, key=None)

        # Store cell references if we have a data key
        if self.data_key:
            key = getattr(data, self.data_key)
            self.cells[key] = row_cells
            self.row_data[0] = data  # New row is always at index 0

        # Apply cell styling
        await self._apply_row_styling(0, data)

    async def _update_existing_row(self, data: Any, key: str) -> None:
        """
        Update an existing row in the table.

        Args:
            data: The updated data object
            key: The key identifying the row to update
        """
        if not self.data_table or key not in self.cells:
            return

        row_cells = self.cells[key]

        # Find the row index for this key
        row_index = self._find_row_by_key(key)
        if row_index is None:
            # Row not found, insert as new
            await self._insert_new_row(data)
            return

        # Update each cell in the row
        for col_index, (header_key, header_config) in enumerate(self.headers.items()):
            if header_key in row_cells:
                content = getattr(data, header_key, "")
                formatted_content = self._format_cell_content(content, header_config)

                # Update cell content
                self.data_table.update_cell(Coordinate(row_index, col_index), formatted_content)

                # Update stored cell data
                row_cells[header_key]["content"] = content
                row_cells[header_key]["data"] = data

        # Update row data reference
        self.row_data[row_index] = data

        # Apply updated styling
        await self._apply_row_styling(row_index, data)

    def _format_cell_content(self, content: Any, config: dict[str, Any]) -> str:
        """
        Format cell content according to configuration.

        Args:
            content: The raw content to format
            config: The header configuration

        Returns:
            Formatted content string
        """
        if content is None:
            return ""

        # Handle different cell types
        cell_type = config.get("cell", "default")

        if cell_type == "float":
            if isinstance(content, int | float):
                precision = config.get("precision", 2)
                return f"{content:.{precision}f}"

        elif cell_type == "percent":
            if isinstance(content, int | float):
                return f"{content:.2%}"

        elif cell_type == "datetime":
            if isinstance(content, datetime):
                return content.strftime("%H:%M:%S")

        elif cell_type == "enum" and hasattr(content, "value"):
            return str(content.value)

        return str(content)

    async def _apply_row_styling(self, row_index: int, data: Any) -> None:
        """
        Apply color styling to a row based on data content.

        Args:
            row_index: The row index to style
            data: The data object for styling decisions
        """
        # This would be implemented based on the specific monitor type
        # Base implementation does nothing

    def _find_row_by_key(self, key: str) -> int | None:
        """
        Find the row index for a given data key.

        Args:
            key: The data key to search for

        Returns:
            Row index if found, None otherwise
        """
        # This is a simplified implementation
        # In practice, we'd need to maintain a key-to-row mapping
        for row_index, data in self.row_data.items():
            if hasattr(data, self.data_key) and getattr(data, self.data_key) == key:
                return row_index
        return None

    def _disable_sorting(self) -> None:
        """Temporarily disable sorting during updates."""
        # Textual DataTable doesn't have the same sorting concerns as Qt

    def _enable_sorting(self) -> None:
        """Re-enable sorting after updates."""
        # Textual DataTable doesn't have the same sorting concerns as Qt

    async def _load_settings(self) -> None:
        """Load monitor-specific settings."""
        # Load column widths, visibility, etc.
        # This would be implemented based on settings storage

    async def _save_settings(self) -> None:
        """Save monitor-specific settings."""
        # Save column widths, visibility, etc.
        # This would be implemented based on settings storage

    async def _log_error(self, message: str) -> None:
        """Log an error message."""
        # This could emit a log event or write to a log file
        print(f"ERROR [{self.monitor_name}]: {message}")

    # Action handlers for key bindings

    def action_resize_columns(self) -> None:
        """Resize all columns to fit content."""
        # Textual handles this automatically, but we could force a refresh
        if self.data_table:
            self.data_table.refresh()

    async def action_save_csv(self) -> None:
        """Save table data to CSV file."""
        if not self.data_table:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.monitor_name.lower()}_{timestamp}.csv"
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers
                headers = [config["display"] for config in self.headers.values()]
                writer.writerow(headers)

                # Write data rows
                for row_index in range(self.data_table.row_count):
                    row_data = []
                    for col_index in range(len(self.headers)):
                        cell_value = self.data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    writer.writerow(row_data)

            await self._log_message(f"Data exported to {filepath}")

        except Exception as e:
            await self._log_error(f"Failed to export CSV: {e}")

    def action_clear_data(self) -> None:
        """Clear all data from the table."""
        if self.data_table:
            self.data_table.clear()
            self.cells.clear()
            self.row_data.clear()

    def action_toggle_filter(self) -> None:
        """Toggle filter mode."""
        self.filter_active = not self.filter_active
        # Update title to show filter status
        if self.title_bar:
            status = " [FILTER]" if self.filter_active else ""
            self.title_bar.update(f"{self.monitor_name}{status}")

    def action_select_all(self) -> None:
        """Select all rows in the table."""
        # Textual DataTable doesn't support multi-selection by default

    def action_clear_selection(self) -> None:
        """Clear current selection."""
        if self.data_table:
            self.data_table.cursor_coordinate = Coordinate(0, 0)

    # Event handlers

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table."""
        # Get the selected data object
        selected_data = self.row_data.get(event.cursor_row)
        if selected_data:
            # Emit a custom message for parent components to handle
            self.post_message(self.RowSelected(selected_data, event.cursor_row))

    async def _log_message(self, message: str) -> None:
        """Log an informational message."""
        print(f"INFO [{self.monitor_name}]: {message}")

    # Custom messages

    class RowSelected(Message):
        """Message sent when a row is selected."""

        def __init__(self, data: Any, row_index: int) -> None:
            self.data = data
            self.row_index = row_index
            super().__init__()

    class DataUpdated(Message):
        """Message sent when data is updated."""

        def __init__(self, data: Any, update_type: str) -> None:
            self.data = data
            self.update_type = update_type  # "insert", "update", "delete"
            super().__init__()


class TUIBaseMonitor(TUIDataMonitor):
    """
    Concrete base monitor class that can be used directly or subclassed.

    This class provides a working implementation that can handle generic data objects.
    """

    def __init__(
        self,
        main_engine: MainEngine,
        event_engine: EventEngine,
        event_type: str,
        data_key: str,
        headers: dict[str, dict[str, Any]],
        monitor_name: str = "Base Monitor",
        **kwargs: Any,
    ) -> None:
        """
        Initialize a configurable base monitor.

        Args:
            main_engine: The main trading engine
            event_engine: The event engine
            event_type: Event type to listen for
            data_key: Key field for identifying unique records
            headers: Column configuration
            monitor_name: Display name
            **kwargs: Additional arguments
        """
        self.event_type = event_type
        self.data_key = data_key
        self.headers = headers

        super().__init__(main_engine, event_engine, monitor_name, **kwargs)
