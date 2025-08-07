"""
Trade export coordinator - Simplified facade.

Coordinates export functionality through specialized export components.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .export import CSVWriter, ExportFormats

if TYPE_CHECKING:
    from ..trade_monitor import TUITradeMonitor


class TradeExport:
    """Coordinates trade data export functionality."""
    
    def __init__(self, monitor_ref):
        """Initialize with weak reference to the monitor."""
        self._monitor_ref = monitor_ref
        
        # Initialize export components
        self.csv_writer = CSVWriter(monitor_ref)
        self.export_formats = ExportFormats(monitor_ref)
    
    @property
    def monitor(self) -> "TUITradeMonitor":
        """Get the monitor instance."""
        monitor = self._monitor_ref()
        if monitor is None:
            raise RuntimeError("Monitor instance has been garbage collected")
        return monitor
    
    async def save_csv(self) -> None:
        """Save trade data to CSV with enhanced trade analysis."""
        monitor = self.monitor
        
        if not monitor.data_table:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path(f"trade_history_{timestamp}.csv")
            
            await self.csv_writer.export_to_csv(filepath)
            await monitor._add_system_message(f"Trade history exported to {filepath}")
            
        except Exception as e:
            await monitor._log_error(f"Failed to export trade history: {e}")
    
    async def export_filtered_data(self, filepath: Path = None) -> None:
        """Export only filtered trade data."""
        await self.export_formats.export_filtered_data(filepath=filepath)
    
    async def export_daily_summary(self, target_date=None) -> None:
        """Export daily summary report."""
        await self.export_formats.export_daily_summary(target_date)
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats."""
        return self.export_formats.get_supported_formats()
    
    def generate_filename(self, prefix: str = "trade_export") -> str:
        """Generate a timestamped filename."""
        return self.export_formats.generate_filename(prefix)