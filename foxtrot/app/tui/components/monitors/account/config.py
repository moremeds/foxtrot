"""
Account monitor configuration and constants.

This module provides configuration data, column headers, display settings,
and constants for the account monitoring system.
"""

from typing import Dict, Any

from foxtrot.util.event_type import EVENT_ACCOUNT


class AccountMonitorConfig:
    """Configuration class for account monitor settings."""
    
    # Monitor configuration
    EVENT_TYPE = EVENT_ACCOUNT
    DATA_KEY = "vt_accountid"
    MONITOR_NAME = "Account Monitor"
    
    # Display settings
    SORTING_ENABLED = True
    AUTO_SCROLL_DEFAULT = True
    SHOW_ZERO_BALANCES_DEFAULT = False
    GROUP_BY_CURRENCY_DEFAULT = True
    SHOW_PERCENTAGE_CHANGES_DEFAULT = True
    HIGHLIGHT_MARGIN_WARNINGS_DEFAULT = True
    
    # Risk management thresholds
    MARGIN_WARNING_THRESHOLD = 0.8      # 80% margin usage warning
    BALANCE_WARNING_THRESHOLD = 1000.0  # Warn below $1000
    PNL_WARNING_THRESHOLD = -500.0      # Warn on daily losses > $500
    
    # History settings
    MAX_ACCOUNT_HISTORY = 100           # Maximum number of historical entries per account
    DEFAULT_HISTORY_HOURS = 24          # Default history timeframe in hours
    
    # Column configuration with enhanced metadata
    HEADERS: Dict[str, Dict[str, Any]] = {
        "accountid": {
            "display": "Account ID",
            "cell": "default",
            "update": False,
            "width": 15,
            "precision": 0,
            "sortable": True,
            "filterable": True,
            "description": "Unique account identifier",
        },
        "balance": {
            "display": "Balance",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": True,
            "description": "Total account balance",
            "color_coded": True,
        },
        "frozen": {
            "display": "Frozen",
            "cell": "currency", 
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": False,
            "description": "Frozen/locked balance",
            "color_coded": True,
        },
        "available": {
            "display": "Available",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": True,
            "description": "Available balance for trading",
            "color_coded": True,
        },
        "currency": {
            "display": "Currency",
            "cell": "default",
            "update": False,
            "width": 8,
            "precision": 0,
            "sortable": True,
            "filterable": True,
            "description": "Account currency",
        },
        "pre_balance": {
            "display": "Pre Balance", 
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": False,
            "description": "Previous day's closing balance",
        },
        "net_pnl": {
            "display": "Net P&L",
            "cell": "pnl",
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": False,
            "description": "Net profit and loss",
            "color_coded": True,
        },
        "commission": {
            "display": "Commission",
            "cell": "currency",
            "update": True,
            "width": 10,
            "precision": 2,
            "sortable": True,
            "filterable": False,
            "description": "Trading commissions paid",
        },
        "margin": {
            "display": "Margin",
            "cell": "currency",
            "update": True,
            "width": 12,
            "precision": 2,
            "sortable": True,
            "filterable": False,
            "description": "Margin requirement",
            "color_coded": True,
        },
        "datetime": {
            "display": "Updated",
            "cell": "datetime",
            "update": True,
            "width": 12,
            "precision": 0,
            "sortable": True,
            "filterable": False,
            "description": "Last update timestamp",
        },
        "gateway_name": {
            "display": "Gateway",
            "cell": "default",
            "update": False,
            "width": 10,
            "precision": 0,
            "sortable": True,
            "filterable": True,
            "description": "Trading gateway/broker",
        },
    }
    
    # Key bindings configuration
    KEY_BINDINGS = [
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
    
    # Statistics field definitions
    STATISTICS_FIELDS = {
        "total_accounts": {
            "display": "Total Accounts",
            "format": "int",
            "default": 0
        },
        "total_balance": {
            "display": "Total Balance",
            "format": "currency", 
            "default": 0.0,
            "color_coded": True
        },
        "total_available": {
            "display": "Total Available",
            "format": "currency",
            "default": 0.0,
            "color_coded": True
        },
        "total_frozen": {
            "display": "Total Frozen", 
            "format": "currency",
            "default": 0.0
        },
        "total_pnl": {
            "display": "Total P&L",
            "format": "pnl",
            "default": 0.0,
            "color_coded": True
        },
        "total_commission": {
            "display": "Total Commission",
            "format": "currency",
            "default": 0.0
        },
        "total_margin": {
            "display": "Total Margin",
            "format": "currency",
            "default": 0.0,
            "color_coded": True
        }
    }
    
    # Risk metrics field definitions
    RISK_FIELDS = {
        "margin_ratio": {
            "display": "Margin Ratio",
            "format": "percentage",
            "default": 0.0,
            "warning_threshold": MARGIN_WARNING_THRESHOLD,
            "color_coded": True
        },
        "buying_power": {
            "display": "Buying Power",
            "format": "currency",
            "default": 0.0,
            "color_coded": True
        },
        "leverage_used": {
            "display": "Leverage Used",
            "format": "decimal_2",
            "default": 0.0,
            "color_coded": True
        },
        "risk_utilization": {
            "display": "Risk Utilization", 
            "format": "percentage",
            "default": 0.0,
            "warning_threshold": 0.75,  # 75% risk utilization warning
            "color_coded": True
        }
    }

    @classmethod
    def get_sortable_columns(cls) -> list[str]:
        """Get list of sortable column names."""
        return [
            name for name, config in cls.HEADERS.items()
            if config.get("sortable", False)
        ]
    
    @classmethod
    def get_filterable_columns(cls) -> list[str]:
        """Get list of filterable column names."""
        return [
            name for name, config in cls.HEADERS.items()
            if config.get("filterable", False)
        ]
    
    @classmethod
    def get_color_coded_columns(cls) -> list[str]:
        """Get list of color-coded column names."""
        return [
            name for name, config in cls.HEADERS.items()
            if config.get("color_coded", False)
        ]
    
    @classmethod
    def get_column_config(cls, column_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific column.
        
        Args:
            column_name: Name of the column
            
        Returns:
            Column configuration dictionary
            
        Raises:
            KeyError: If column name not found
        """
        if column_name not in cls.HEADERS:
            raise KeyError(f"Unknown column: {column_name}")
        return cls.HEADERS[column_name].copy()
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration consistency.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Validate headers have required fields
            required_header_fields = ["display", "cell", "update", "width", "precision"]
            for name, config in cls.HEADERS.items():
                for field in required_header_fields:
                    if field not in config:
                        raise ValueError(f"Header '{name}' missing required field '{field}'")
            
            # Validate thresholds are reasonable
            if not (0 < cls.MARGIN_WARNING_THRESHOLD < 1):
                raise ValueError("Margin warning threshold must be between 0 and 1")
            
            if cls.BALANCE_WARNING_THRESHOLD < 0:
                raise ValueError("Balance warning threshold must be non-negative")
                
            if cls.PNL_WARNING_THRESHOLD > 0:
                raise ValueError("PnL warning threshold should be negative (loss threshold)")
            
            return True
            
        except (ValueError, KeyError) as e:
            # In production, this would use proper logging
            print(f"Configuration validation error: {e}")
            return False


class AccountDisplaySettings:
    """Account monitor display settings container."""
    
    def __init__(self):
        """Initialize with default settings."""
        self.show_zero_balances = AccountMonitorConfig.SHOW_ZERO_BALANCES_DEFAULT
        self.group_by_currency = AccountMonitorConfig.GROUP_BY_CURRENCY_DEFAULT
        self.show_percentage_changes = AccountMonitorConfig.SHOW_PERCENTAGE_CHANGES_DEFAULT
        self.highlight_margin_warnings = AccountMonitorConfig.HIGHLIGHT_MARGIN_WARNINGS_DEFAULT
        self.auto_scroll_to_updates = AccountMonitorConfig.AUTO_SCROLL_DEFAULT
        
        # Filter settings
        self.currency_filter: str | None = None
        self.gateway_filter: str | None = None
        self.min_balance_filter: float | None = None
    
    def reset_filters(self) -> None:
        """Reset all filters to default state."""
        self.currency_filter = None
        self.gateway_filter = None
        self.min_balance_filter = None
    
    def has_active_filters(self) -> bool:
        """Check if any filters are currently active."""
        return any([
            self.currency_filter is not None,
            self.gateway_filter is not None,
            self.min_balance_filter is not None,
            not self.show_zero_balances  # This acts as a filter
        ])
    
    def get_filter_summary(self) -> str:
        """Get a summary string of active filters."""
        filters = []
        if self.currency_filter:
            filters.append(f"Currency:{self.currency_filter}")
        if self.gateway_filter:
            filters.append(f"Gateway:{self.gateway_filter}")
        if self.min_balance_filter is not None:
            filters.append(f"MinBalance:{self.min_balance_filter}")
        if not self.show_zero_balances:
            filters.append("NON-ZERO")
        
        return ", ".join(filters) if filters else "None"


# Initialize and validate configuration on module load
if not AccountMonitorConfig.validate_config():
    raise ImportError("Account monitor configuration validation failed")