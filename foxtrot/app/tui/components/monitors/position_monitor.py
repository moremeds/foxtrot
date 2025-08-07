"""
Position Monitor for TUI

Portfolio position tracking component that displays holdings,
P&L calculations, and provides position management functionality.

This module now imports from the modular position_monitor package to maintain
backward compatibility while enabling better code organization.
"""

# Import all classes from the modular package to maintain backward compatibility
from .position_monitor import (
    TUIPositionMonitor,
    PositionBusinessLogic,
    PositionUIComponents,
    PositionFiltersActions,
    PositionExport,
    create_position_monitor,
)

# Re-export for backward compatibility
__all__ = [
    "TUIPositionMonitor",
    "PositionBusinessLogic", 
    "PositionUIComponents",
    "PositionFiltersActions",
    "PositionExport",
    "create_position_monitor",
]