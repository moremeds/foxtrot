"""
Account monitor data formatting and display logic.

This module handles all data formatting, cell content preparation,
and styling logic for the account monitor display.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from foxtrot.util.object import AccountData
from foxtrot.app.tui.utils.formatters import TUIFormatter
from foxtrot.app.tui.utils.colors import get_color_manager

from .config import AccountMonitorConfig

# Set up logging
logger = logging.getLogger(__name__)


class AccountDataFormatter:
    """
    Handles data formatting for account monitor display.
    
    Features:
    - Currency formatting with precision control
    - P&L formatting with color indicators
    - Percentage formatting with sign indication
    - DateTime formatting with multiple formats
    - Automatic truncation for long text
    - Type-safe formatting with validation
    """
    
    def __init__(self, config: Optional[AccountMonitorConfig] = None, display_settings: Optional[Any] = None):
        """Initialize formatter with color manager and optional config."""
        self.color_manager = get_color_manager()
        self.config = config or AccountMonitorConfig()
        self.display_settings = display_settings
    
    def format_cell_content(self, content: Any, config: Dict[str, Any]) -> str:
        """
        Format cell content with account-specific formatting.
        
        Args:
            content: The raw content to format
            config: The header configuration from AccountMonitorConfig
            
        Returns:
            Formatted content string
            
        Note:
            Returns "-" for None values and handles type conversion safely.
        """
        if content is None:
            return "-"
        
        try:
            cell_type = config.get("cell", "default")
            precision = config.get("precision", 2)
            width = config.get("width", 20)
            
            return self._format_by_cell_type(content, cell_type, precision, width)
            
        except Exception as e:
            logger.error(f"Error formatting cell content: {e}")
            return str(content)[:config.get("width", 20)]
    
    def _format_by_cell_type(self, content: Any, cell_type: str, precision: int, width: int) -> str:
        """
        Format content based on cell type.
        
        Args:
            content: Content to format
            cell_type: Type of formatting to apply
            precision: Decimal precision for numeric values
            width: Maximum width for text content
            
        Returns:
            Formatted string
        """
        if cell_type == "currency":
            return self._format_currency(content, precision)
        
        elif cell_type == "pnl":
            return self._format_pnl(content)
        
        elif cell_type == "percentage":
            return self._format_percentage(content)
        
        elif cell_type == "datetime":
            return self._format_datetime(content)
        
        else:  # default formatting
            return self._format_default(content, width)
    
    def _format_currency(self, content: Any, precision: int) -> str:
        """Format currency values with proper precision."""
        try:
            if isinstance(content, (int, float)):
                return TUIFormatter.format_currency(content, precision=precision)
            else:
                # Try to convert to float
                value = float(content)
                return TUIFormatter.format_currency(value, precision=precision)
        except (ValueError, TypeError):
            return str(content)
    
    def _format_pnl(self, content: Any) -> str:
        """Format P&L with sign indication and color coding."""
        try:
            if isinstance(content, (int, float)):
                return TUIFormatter.format_pnl(content, show_percentage=False)
            else:
                # Try to convert to float
                value = float(content)
                return TUIFormatter.format_pnl(value, show_percentage=False)
        except (ValueError, TypeError):
            return str(content)
    
    def _format_percentage(self, content: Any) -> str:
        """Format percentage values with sign indication."""
        try:
            if isinstance(content, (int, float)):
                if content != 0:
                    return TUIFormatter.format_percentage(content, show_sign=True)
                return "-"
            else:
                # Try to convert to float
                value = float(content)
                if value != 0:
                    return TUIFormatter.format_percentage(value, show_sign=True)
                return "-"
        except (ValueError, TypeError):
            return str(content)
    
    def _format_datetime(self, content: Any) -> str:
        """Format datetime values."""
        try:
            if isinstance(content, datetime):
                return TUIFormatter.format_datetime(content, "time")
            elif isinstance(content, str):
                # Try to parse datetime string
                dt = datetime.fromisoformat(content.replace('Z', '+00:00'))
                return TUIFormatter.format_datetime(dt, "time")
            else:
                return str(content)
        except (ValueError, TypeError):
            return str(content)
    
    def _format_default(self, content: Any, width: int) -> str:
        """Format default content with truncation."""
        content_str = str(content)
        if len(content_str) > width:
            return TUIFormatter.truncate_text(content_str, width)
        return content_str


class AccountRowStyler:
    """
    Handles row-level styling for account data based on values and conditions.
    
    Features:
    - Balance-based color coding
    - P&L-based styling (green/red)
    - Margin warning highlights
    - Risk-level styling
    - Currency-specific formatting
    """
    
    def __init__(self, config: AccountMonitorConfig):
        """
        Initialize styler with configuration.
        
        Args:
            config: Account monitor configuration instance
        """
        self.config = config
        self.color_manager = get_color_manager()
    
    async def apply_row_styling(
        self, 
        row_index: int, 
        account_data: AccountData,
        data_table: Any,
        display_settings: Any
    ) -> None:
        """
        Apply color styling to account data based on balance and P&L.
        
        Args:
            row_index: The row index to style
            account_data: The AccountData object
            data_table: The data table widget (if available)
            display_settings: Display settings for conditional styling
        """
        if not data_table:
            return
        
        try:
            # Apply balance-based styling
            await self._apply_balance_styling(row_index, account_data, data_table, display_settings)
            
            # Apply P&L-based styling  
            await self._apply_pnl_styling(row_index, account_data, data_table)
            
            # Apply margin-based warnings if enabled
            if display_settings.highlight_margin_warnings:
                await self._apply_margin_styling(row_index, account_data, data_table)
            
            # Apply currency-specific styling
            await self._apply_currency_styling(row_index, account_data, data_table)
            
        except Exception as e:
            logger.error(f"Error applying row styling for row {row_index}: {e}")
    
    async def _apply_balance_styling(
        self, 
        row_index: int, 
        account_data: AccountData, 
        data_table: Any,
        display_settings: Any
    ) -> None:
        """Apply styling based on account balance levels."""
        try:
            # Low balance warning
            if account_data.available < self.config.BALANCE_WARNING_THRESHOLD:
                # Apply warning style to available balance column
                # This would integrate with Textual's styling system
                pass
            
            # Zero balance handling
            if account_data.balance == 0 and account_data.available == 0:
                if not display_settings.show_zero_balances:
                    # Apply dimmed/hidden style
                    pass
                    
        except Exception as e:
            logger.error(f"Error applying balance styling: {e}")
    
    async def _apply_pnl_styling(self, row_index: int, account_data: AccountData, data_table: Any) -> None:
        """Apply styling based on P&L values."""
        try:
            # Get P&L color from color manager
            pnl_color = self.color_manager.get_pnl_color(account_data.net_pnl)
            
            # Apply color to P&L column
            # This would integrate with Textual's styling system
            # For now, we just calculate the appropriate color
            
        except Exception as e:
            logger.error(f"Error applying P&L styling: {e}")
    
    async def _apply_margin_styling(self, row_index: int, account_data: AccountData, data_table: Any) -> None:
        """Apply styling based on margin usage levels."""
        try:
            if hasattr(account_data, "margin") and account_data.margin > 0:
                margin_ratio = account_data.margin / max(account_data.balance, 1)
                
                if margin_ratio > self.config.MARGIN_WARNING_THRESHOLD:
                    # Apply high margin warning style
                    # This would integrate with Textual's styling system
                    pass
                    
        except Exception as e:
            logger.error(f"Error applying margin styling: {e}")
    
    async def _apply_currency_styling(self, row_index: int, account_data: AccountData, data_table: Any) -> None:
        """Apply styling based on currency type."""
        try:
            # Different styling for different currencies
            currency = getattr(account_data, 'currency', 'USD')
            
            # Apply currency-specific styling
            # This could include different colors or indicators for different currencies
            
        except Exception as e:
            logger.error(f"Error applying currency styling: {e}")


class AccountDisplayFormatter:
    """
    Handles display formatting for account summary and statistics.
    
    Features:
    - Title bar formatting with statistics
    - Filter display formatting
    - Summary statistics formatting
    - Multi-currency display handling
    """
    
    def __init__(self, config: AccountMonitorConfig):
        """
        Initialize display formatter.
        
        Args:
            config: Account monitor configuration
        """
        self.config = config
        self.formatter = AccountDataFormatter()
    
    def format_title_bar(
        self, 
        statistics: Dict[str, Any], 
        display_settings: Any
    ) -> str:
        """
        Format title bar with current statistics and filters.
        
        Args:
            statistics: Current account statistics
            display_settings: Display settings including filters
            
        Returns:
            Formatted title string
        """
        try:
            # Base title with key statistics
            title = (
                f"Account Monitor - "
                f"Balance: {TUIFormatter.format_currency(statistics.get('total_balance', 0))} | "
                f"Available: {TUIFormatter.format_currency(statistics.get('total_available', 0))}"
            )
            
            # Add P&L if significant
            total_pnl = statistics.get('total_pnl', 0)
            if abs(total_pnl) > 0.01:
                title += f" | P&L: {TUIFormatter.format_pnl(total_pnl)}"
            
            # Add filter information if active
            filter_summary = display_settings.get_filter_summary()
            if filter_summary != "None":
                title += f" [{filter_summary}]"
            
            return title
            
        except Exception as e:
            logger.error(f"Error formatting title bar: {e}")
            return "Account Monitor"
    
    def format_statistics_summary(self, statistics: Dict[str, Any]) -> Dict[str, str]:
        """
        Format statistics for display.
        
        Args:
            statistics: Raw statistics dictionary
            
        Returns:
            Dictionary with formatted statistics strings
        """
        formatted = {}
        
        try:
            for field, value in statistics.items():
                if field in self.config.STATISTICS_FIELDS:
                    field_config = self.config.STATISTICS_FIELDS[field]
                    format_type = field_config.get("format", "default")
                    
                    if format_type == "currency":
                        formatted[field] = TUIFormatter.format_currency(value)
                    elif format_type == "pnl":
                        formatted[field] = TUIFormatter.format_pnl(value)
                    elif format_type == "percentage":
                        formatted[field] = TUIFormatter.format_percentage(value)
                    elif format_type == "int":
                        formatted[field] = str(int(value))
                    else:
                        formatted[field] = str(value)
                else:
                    formatted[field] = str(value)
                    
        except Exception as e:
            logger.error(f"Error formatting statistics: {e}")
            formatted[field] = str(value)
        
        return formatted
    
    def format_risk_metrics(self, risk_metrics: Dict[str, Any]) -> Dict[str, str]:
        """
        Format risk metrics for display.
        
        Args:
            risk_metrics: Raw risk metrics dictionary
            
        Returns:
            Dictionary with formatted risk metrics strings
        """
        formatted = {}
        
        try:
            for field, value in risk_metrics.items():
                if field in self.config.RISK_FIELDS:
                    field_config = self.config.RISK_FIELDS[field]
                    format_type = field_config.get("format", "default")
                    
                    if format_type == "currency":
                        formatted[field] = TUIFormatter.format_currency(value)
                    elif format_type == "percentage":
                        formatted[field] = TUIFormatter.format_percentage(value)
                    elif format_type == "decimal_2":
                        formatted[field] = f"{value:.2f}"
                    else:
                        formatted[field] = str(value)
                else:
                    formatted[field] = str(value)
                    
        except Exception as e:
            logger.error(f"Error formatting risk metrics: {e}")
            formatted[field] = str(value)
        
        return formatted
    
    def format_currency_breakdown(self, currency_data: Dict[str, Dict[str, float]]) -> str:
        """
        Format currency breakdown for display.
        
        Args:
            currency_data: Currency breakdown data
            
        Returns:
            Formatted currency breakdown string
        """
        try:
            if not currency_data:
                return "No currency data available"
            
            # Show top 3 currencies by balance
            sorted_currencies = sorted(
                currency_data.items(),
                key=lambda x: x[1]["balance"],
                reverse=True
            )[:3]
            
            currency_info = []
            for currency, data in sorted_currencies:
                balance = data["balance"]
                currency_info.append(f"{currency}:{TUIFormatter.format_currency(balance)}")
            
            return f"Currencies: {', '.join(currency_info)}"
            
        except Exception as e:
            logger.error(f"Error formatting currency breakdown: {e}")
            return "Currency breakdown unavailable"