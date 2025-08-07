"""
Position monitor export functionality for portfolio analysis and reporting.

This module handles CSV export operations, file management,
and export formatting for position and portfolio data.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from textual.coordinate import Coordinate

from .position_business_logic import PositionBusinessLogic
from .position_ui_components import PositionUIComponents


class PositionExport:
    """
    Export functionality for position monitor data.
    
    This class handles CSV export operations, file management,
    and export formatting with comprehensive portfolio metadata inclusion.
    """

    def __init__(
        self,
        business_logic: PositionBusinessLogic,
        ui_components: PositionUIComponents,
    ):
        self.business_logic = business_logic
        self.ui_components = ui_components

        # Export configuration
        self.export_dir = Path("exports")
        self.default_filename_prefix = "portfolio_positions"
        
        # Callback for system messages (set by controller)
        self._add_system_message_callback: Optional[Callable] = None
        self._log_error_callback: Optional[Callable] = None

    def set_callbacks(
        self,
        add_system_message_callback: Callable,
        log_error_callback: Callable,
    ) -> None:
        """
        Set callbacks for system messages and error logging.

        Args:
            add_system_message_callback: Callback to add system messages
            log_error_callback: Callback to log errors
        """
        self._add_system_message_callback = add_system_message_callback
        self._log_error_callback = log_error_callback

    def ensure_export_directory(self) -> None:
        """Ensure export directory exists."""
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate_filename(self, prefix: Optional[str] = None) -> str:
        """
        Generate timestamped filename for export.

        Args:
            prefix: Optional filename prefix

        Returns:
            Generated filename
        """
        prefix = prefix or self.default_filename_prefix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.csv"

    async def save_csv(
        self,
        data_table,
        headers: Dict[str, Dict[str, Any]],
        symbol_filter: Optional[str] = None,
    ) -> None:
        """
        Save position data to CSV with portfolio analysis.

        Args:
            data_table: The data table widget with position data
            headers: Column headers configuration
            symbol_filter: Active symbol filter
        """
        if not data_table:
            if self._add_system_message_callback:
                await self._add_system_message_callback("No data table available for export")
            return

        try:
            self.ensure_export_directory()
            
            filename = self.generate_filename()
            filepath = self.export_dir / filename

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Write headers with portfolio analysis context
                export_headers = self.ui_components.get_export_headers(headers)
                writer.writerow(export_headers)

                # Get export metadata
                metadata = self.ui_components.format_export_metadata(symbol_filter)
                summary = self.business_logic.get_portfolio_summary()

                # Write position data with calculated values
                for row_index in range(data_table.row_count):
                    row_data = []
                    
                    # Extract cell data from the table
                    for col_index in range(len(headers)):
                        cell_value = data_table.get_cell(Coordinate(row_index, col_index))
                        row_data.append(str(cell_value) if cell_value else "")

                    # Calculate additional fields
                    position_value = "N/A"  # Would be calculated from price * volume
                    risk_level = metadata["risk_level"]

                    # Add metadata to first row only
                    if row_index == 0:
                        row_data.extend([
                            position_value,
                            risk_level,
                            metadata["export_time"],
                            metadata["filter_info"],
                            metadata["total_positions"],
                            metadata["portfolio_pnl"],
                            metadata["win_rate"],
                        ])
                    else:
                        # Empty cells for subsequent rows
                        row_data.extend(["", "", "", "", "", "", ""])

                    writer.writerow(row_data)

                # Write summary footer
                self._write_export_footer(writer, summary)

            if self._add_system_message_callback:
                await self._add_system_message_callback(f"Portfolio positions exported to {filepath}")

        except Exception as e:
            error_msg = f"Failed to export portfolio positions: {e}"
            if self._log_error_callback:
                await self._log_error_callback(error_msg)
            if self._add_system_message_callback:
                await self._add_system_message_callback(f"Export failed: {str(e)}")

    def _write_export_footer(self, writer: csv.writer, summary: Dict[str, Any]) -> None:
        """
        Write export footer with portfolio summary information.

        Args:
            writer: CSV writer object
            summary: Portfolio summary data
        """
        # Empty row separator
        writer.writerow([])
        
        # Portfolio summary section
        writer.writerow(["PORTFOLIO SUMMARY"])
        writer.writerow(["Active Positions", str(summary["active_positions"])])
        writer.writerow(["Long Positions", str(summary["long_positions"])])
        writer.writerow(["Short Positions", str(summary["short_positions"])])
        writer.writerow(["Total P&L", f"{summary['total_pnl']:.2f}"])
        writer.writerow(["Total Value", f"{summary['total_value']:.2f}"])
        writer.writerow(["Win Rate", f"{summary['win_rate']:.1f}%"])
        writer.writerow(["Average P&L", f"{summary['avg_pnl']:.2f}"])
        
        # Portfolio metrics section
        writer.writerow([])
        writer.writerow(["PORTFOLIO METRICS"])
        writer.writerow(["Net Exposure", f"{summary['net_exposure']:.2f}"])
        writer.writerow(["Gross Exposure", f"{summary['gross_exposure']:.2f}"])
        writer.writerow(["Largest Position", f"{summary['largest_position']:.2f}"])
        writer.writerow(["Largest P&L", f"{summary['largest_pnl']:.2f}"])

        # Export metadata
        writer.writerow([])
        writer.writerow(["EXPORT INFO"])
        writer.writerow(["Export Date", datetime.now().isoformat()])
        writer.writerow(["Generated By", "Foxtrot Position Monitor"])

    def export_portfolio_analysis(
        self,
        row_data: Dict[str, Any],
        filename_prefix: str = "portfolio_analysis",
    ) -> Optional[Path]:
        """
        Export detailed portfolio analysis report.

        Args:
            row_data: All position data for analysis
            filename_prefix: Filename prefix for export

        Returns:
            Path to exported file or None if failed
        """
        try:
            self.ensure_export_directory()
            
            filename = self.generate_filename(filename_prefix)
            filepath = self.export_dir / filename

            summary = self.business_logic.get_portfolio_summary()

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Portfolio analysis headers
                writer.writerow([
                    "Symbol", "Direction", "Volume", "Avg Price", "Position Value",
                    "P&L", "P&L %", "Risk Level", "Exposure %"
                ])

                total_portfolio_value = summary["total_value"]

                # Write position analysis data
                for position_id, position_data in row_data.items():
                    if hasattr(position_data, "symbol"):
                        position_value = self.business_logic.calculate_position_value(position_data)
                        risk_level = self.business_logic.get_risk_level(position_data)
                        exposure_pct = (position_value / max(total_portfolio_value, 1)) * 100
                        pnl_pct = (position_data.pnl / max(position_value, 1)) * 100
                        
                        writer.writerow([
                            position_data.symbol,
                            position_data.direction.value if hasattr(position_data.direction, 'value') else str(position_data.direction),
                            position_data.volume,
                            f"{position_data.price:.4f}",
                            f"{position_value:.2f}",
                            f"{position_data.pnl:.2f}",
                            f"{pnl_pct:.2f}%",
                            risk_level,
                            f"{exposure_pct:.1f}%"
                        ])

                # Portfolio summary
                writer.writerow([])
                writer.writerow(["PORTFOLIO SUMMARY"])
                writer.writerow(["Total Positions", str(summary["active_positions"])])
                writer.writerow(["Portfolio Value", f"{summary['total_value']:.2f}"])
                writer.writerow(["Portfolio P&L", f"{summary['total_pnl']:.2f}"])
                writer.writerow(["Win Rate", f"{summary['win_rate']:.1f}%"])
                writer.writerow(["Net Exposure", f"{summary['net_exposure']:.2f}"])
                writer.writerow(["Gross Exposure", f"{summary['gross_exposure']:.2f}"])

            return filepath

        except Exception as e:
            if self._log_error_callback:
                import asyncio
                asyncio.create_task(self._log_error_callback(f"Failed to export portfolio analysis: {e}"))
            return None

    def export_symbol_analysis(
        self,
        symbol: str,
        row_data: Dict[str, Any],
        filename_prefix: str = "symbol_analysis",
    ) -> Optional[Path]:
        """
        Export analysis for a specific symbol.

        Args:
            symbol: Symbol to analyze
            row_data: All position data
            filename_prefix: Filename prefix for export

        Returns:
            Path to exported file or None if failed
        """
        try:
            self.ensure_export_directory()
            
            filename = self.generate_filename(f"{filename_prefix}_{symbol}")
            filepath = self.export_dir / filename

            exposure = self.business_logic.get_symbol_exposure(symbol, row_data)

            if exposure["positions"] == 0:
                return None

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Symbol analysis header
                writer.writerow(["SYMBOL ANALYSIS:", symbol])
                writer.writerow([])
                
                # Summary metrics
                writer.writerow(["Total Positions", str(exposure["positions"])])
                writer.writerow(["Net Volume", f"{exposure['net_volume']:.0f}"])
                writer.writerow(["Total Value", f"{exposure['total_value']:.2f}"])
                writer.writerow(["Total P&L", f"{exposure['total_pnl']:.2f}"])
                writer.writerow(["Average Price", f"{exposure['avg_price']:.4f}"])

                writer.writerow([])
                writer.writerow(["Export Date", datetime.now().isoformat()])

            return filepath

        except Exception as e:
            if self._log_error_callback:
                import asyncio
                asyncio.create_task(self._log_error_callback(f"Failed to export symbol analysis: {e}"))
            return None

    def get_export_summary(self) -> Dict[str, Any]:
        """
        Get export operation summary.

        Returns:
            Dictionary with export statistics and options
        """
        return {
            "export_directory": str(self.export_dir),
            "default_prefix": self.default_filename_prefix,
            "supported_formats": ["CSV"],
            "includes_portfolio_analysis": True,
            "includes_symbol_analysis": True,
            "includes_risk_metrics": True,
            "includes_exposure_analysis": True,
        }