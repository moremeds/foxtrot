"""
Trade monitor header configuration and management.

Provides column headers and configuration for trade display.
"""

from typing import Any, Dict


class TradeHeaders:
    """Manages trade monitor column headers and configuration."""
    
    @staticmethod
    def get_headers_config() -> Dict[str, Dict[str, Any]]:
        """
        Get the headers configuration for trade display.
        
        Returns:
            Dictionary with header configuration
        """
        return {
            "tradeid": {
                "display": "Trade ID",
                "cell": "default",
                "update": False,
                "width": 12,
                "precision": 0,
            },
            "orderid": {
                "display": "Order ID",
                "cell": "default",
                "update": False,
                "width": 12,
                "precision": 0,
            },
            "symbol": {
                "display": "Symbol",
                "cell": "default",
                "update": False,
                "width": 12,
                "precision": 0,
            },
            "exchange": {
                "display": "Exchange",
                "cell": "enum",
                "update": False,
                "width": 8,
                "precision": 0,
            },
            "direction": {
                "display": "Direction",
                "cell": "direction",
                "update": False,
                "width": 8,
                "precision": 0,
            },
            "offset": {
                "display": "Offset",
                "cell": "enum",
                "update": False,
                "width": 6,
                "precision": 0,
            },
            "price": {
                "display": "Price",
                "cell": "float",
                "update": False,
                "width": 10,
                "precision": 4,
            },
            "volume": {
                "display": "Volume",
                "cell": "volume",
                "update": False,
                "width": 10,
                "precision": 0,
            },
            "datetime": {
                "display": "Time",
                "cell": "datetime",
                "update": False,
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
    
    @staticmethod
    def get_column_names() -> list[str]:
        """Get list of column names in display order."""
        return list(TradeHeaders.get_headers_config().keys())
    
    @staticmethod
    def get_display_names() -> list[str]:
        """Get list of display names for headers."""
        config = TradeHeaders.get_headers_config()
        return [config[col]["display"] for col in config.keys()]
    
    @staticmethod
    def get_column_config(column: str) -> Dict[str, Any]:
        """
        Get configuration for a specific column.
        
        Args:
            column: Column name
            
        Returns:
            Column configuration dictionary
        """
        config = TradeHeaders.get_headers_config()
        return config.get(column, {})
    
    @staticmethod 
    def get_total_width() -> int:
        """
        Calculate total width of all columns.
        
        Returns:
            Total width in characters
        """
        config = TradeHeaders.get_headers_config()
        return sum(col_config.get("width", 10) for col_config in config.values())