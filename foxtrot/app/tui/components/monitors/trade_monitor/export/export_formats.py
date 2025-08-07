"""
Different export format handlers for trade data.

Supports multiple export formats beyond CSV.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .csv_writer import CSVWriter

if TYPE_CHECKING:
    from ...trade_monitor import TUITradeMonitor


class ExportFormats:
    """Coordinates different export format handlers."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
        
        # Initialize format handlers
        self.csv_writer = CSVWriter(monitor_ref)
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    async def export_filtered_data(self, format_type: str = "csv", filepath: Path = None) -> None:
        """
        Export only filtered trade data.
        
        Args:
            format_type: Export format (default: csv)
            filepath: Optional custom filepath
        """
        if format_type == "csv":
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = Path(f"filtered_trades_{timestamp}.csv")
            
            await self.csv_writer.export_to_csv(filepath)
    
    async def export_daily_summary(self, target_date=None, format_type: str = "csv") -> None:
        """
        Export daily summary report.
        
        Args:
            target_date: Date to export (defaults to today)
            format_type: Export format (default: csv)
        """
        if format_type == "csv":
            await self._export_daily_summary_csv(target_date)
    
    async def _export_daily_summary_csv(self, target_date=None) -> None:
        """Export daily summary as CSV."""
        monitor = self.monitor
        
        # Get summary data
        if hasattr(monitor, 'trade_statistics') and monitor.trade_statistics:
            summary = monitor.trade_statistics.get_daily_summary(target_date)
        else:
            summary = {"date": target_date or datetime.now().date(), "trades": 0}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = Path(f"daily_summary_{timestamp}.csv")
        
        # Write summary CSV
        import csv
        from ....utils.formatters import TUIFormatter
        
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            
            writer.writerow(["Daily Trade Summary"])
            writer.writerow(["Date", str(summary.get("date", ""))])
            writer.writerow(["Total Trades", summary.get("trades", 0)])
            
            if "volume" in summary:
                writer.writerow(["Total Volume", TUIFormatter.format_volume(summary["volume"])])
            if "value" in summary:
                writer.writerow(["Total Value", TUIFormatter.format_price(summary["value"], 2)])
            if "avg_price" in summary:
                writer.writerow(["Average Price", TUIFormatter.format_price(summary["avg_price"], 4)])
            if "long_trades" in summary:
                writer.writerow(["Long Trades", summary["long_trades"]])
            if "short_trades" in summary:
                writer.writerow(["Short Trades", summary["short_trades"]])
        
        await monitor._add_system_message(f"Daily summary exported to {filepath}")
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats."""
        return ["csv"]
    
    def generate_filename(self, prefix: str = "trade_export", extension: str = "csv") -> str:
        """
        Generate a timestamped filename.
        
        Args:
            prefix: Filename prefix
            extension: File extension
            
        Returns:
            Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.{extension}"