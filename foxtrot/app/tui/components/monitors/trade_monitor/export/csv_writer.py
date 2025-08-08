"""
CSV export functionality for trade data.

Handles CSV file writing and formatting for trade exports.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, List, TYPE_CHECKING

from foxtrot.util.object import TradeData
from foxtrot.app.tui.utils.formatters import TUIFormatter

if TYPE_CHECKING:
    from ...trade_monitor import TUITradeMonitor


class CSVWriter:
    """Handles CSV export functionality for trade data."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    async def export_to_csv(self, filepath: Path) -> None:
        """
        Export trade data to CSV file.
        
        Args:
            filepath: Path to save the CSV file
        """
        monitor = self.monitor
        
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            
            # Write headers
            await self._write_headers(writer)
            
            # Write trade data
            await self._write_trade_data(writer)
            
            # Write summary section
            await self._write_summary_section(writer)
    
    async def _write_headers(self, writer: csv.writer) -> None:
        """Write CSV headers including analysis columns."""
        monitor = self.monitor
        
        # Basic headers
        headers = list(monitor.headers.keys())
        
        # Enhanced analysis headers
        analysis_headers = [
            "trade_value", 
            "daily_volume", 
            "session_position", 
            "pnl_estimate", 
            "notes"
        ]
        
        writer.writerow(headers + analysis_headers)
    
    async def _write_trade_data(self, writer: csv.writer) -> None:
        """Write trade data rows with analysis."""
        monitor = self.monitor
        
        for row_data in monitor.data_table.data:
            # Basic trade data
            trade_row = [str(cell) for cell in row_data]
            
            # Add analysis data
            analysis_data = await self._generate_analysis_data(row_data)
            trade_row.extend(analysis_data)
            
            writer.writerow(trade_row)
    
    async def _generate_analysis_data(self, row_data: List[Any]) -> List[str]:
        """
        Generate analysis data for a trade row.
        
        Args:
            row_data: Raw trade row data
            
        Returns:
            List of analysis values
        """
        if len(row_data) < 7:  # Insufficient data
            return ["", "", "", "", ""]
        
        try:
            price = float(row_data[6])  # Assuming price is at index 6
            volume = float(row_data[7])  # Assuming volume is at index 7
            trade_value = price * volume
            
            return [
                TUIFormatter.format_price(trade_value, 2),
                self._get_daily_volume_info(row_data),
                self._get_session_position_info(row_data),
                self._estimate_pnl(row_data),
                self._generate_trade_notes(row_data)
            ]
        except (ValueError, IndexError):
            return ["", "", "", "", ""]
    
    def _get_daily_volume_info(self, row_data: List[Any]) -> str:
        """Get daily volume information placeholder."""
        # Placeholder - would implement actual daily volume tracking
        return "N/A"
    
    def _get_session_position_info(self, row_data: List[Any]) -> str:
        """Get session position information placeholder."""
        # Placeholder - would implement actual position tracking
        return "N/A"
    
    def _estimate_pnl(self, row_data: List[Any]) -> str:
        """Estimate P&L placeholder."""
        # Placeholder - would implement actual P&L calculation
        return "0.00"
    
    def _generate_trade_notes(self, row_data: List[Any]) -> str:
        """Generate notes for the trade."""
        notes = []
        
        try:
            if len(row_data) >= 8:
                price = float(row_data[6])
                volume = float(row_data[7])
                trade_value = price * volume
                
                monitor = self.monitor
                if trade_value >= monitor.large_trade_threshold:
                    notes.append("LARGE_TRADE")
        except (ValueError, IndexError):
            pass
        
        return "; ".join(notes) if notes else ""
    
    async def _write_summary_section(self, writer: csv.writer) -> None:
        """Write summary statistics section to CSV."""
        monitor = self.monitor
        
        # Empty row separator
        writer.writerow([])
        
        # Summary section header
        writer.writerow(["TRADE SUMMARY"])
        writer.writerow(["Metric", "Value"])
        
        # Get statistics
        if hasattr(monitor, 'trade_statistics') and monitor.trade_statistics:
            stats = monitor.trade_statistics.statistics
            
            summary_data = [
                ("Total Trades", stats["total_trades"]),
                ("Total Volume", TUIFormatter.format_volume(stats["total_volume"])),
                ("Total Value", TUIFormatter.format_price(stats["total_value"], 2)),
                ("Average Price", TUIFormatter.format_price(stats["avg_price"], 4)),
                ("Long Trades", stats["long_trades"]),
                ("Short Trades", stats["short_trades"]),
            ]
            
            for metric, value in summary_data:
                writer.writerow([metric, value])
        
        # Export metadata
        writer.writerow([])
        writer.writerow(["EXPORT METADATA"])
        writer.writerow(["Export Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["Monitor Version", "1.0.0"])