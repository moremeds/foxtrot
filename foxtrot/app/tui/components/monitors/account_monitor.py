"""
Account Monitor for TUI

Account information and balance tracking component that displays
account balances, margin information, and provides account management functionality.

This module now imports from the modular account_monitor package to maintain
backward compatibility while enabling better code organization.
"""

# Import all classes from the modular package to maintain backward compatibility
from .account import (
    TUIAccountMonitor,
    AccountAnalyzer,
    AccountDataFormatter,
    AccountFilterManager,
    AccountStatistics,
    AccountActionHandler,
    AccountDataExporter,
)

# Re-export for backward compatibility
__all__ = [
    "TUIAccountMonitor",
    "AccountAnalyzer", 
    "AccountDataFormatter",
    "AccountFilterManager",
    "AccountStatistics",
    "AccountActionHandler",
    "AccountDataExporter",
]