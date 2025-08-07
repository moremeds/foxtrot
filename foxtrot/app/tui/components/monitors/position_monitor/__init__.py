"""
Position monitor modular package.

This package provides a modular position monitoring system with separation
of concerns between business logic, UI components, filters/actions, export 
functionality, and controller orchestration.

Public API:
    - TUIPositionMonitor: Main position monitor class
    - PositionBusinessLogic: Core business logic and portfolio analytics
    - PositionUIComponents: Visual formatting and presentation
    - PositionFiltersActions: Filter operations and user actions
    - PositionExport: CSV export and portfolio reporting functionality
    - create_position_monitor: Convenience factory function
"""

from .position_controller import TUIPositionMonitor, create_position_monitor
from .position_business_logic import PositionBusinessLogic
from .position_ui_components import PositionUIComponents
from .position_filters_actions import PositionFiltersActions
from .position_export import PositionExport

__all__ = [
    "TUIPositionMonitor",
    "PositionBusinessLogic", 
    "PositionUIComponents",
    "PositionFiltersActions",
    "PositionExport",
    "create_position_monitor",
]

# Version and module metadata
__version__ = "1.0.0"
__author__ = "Foxtrot Trading Platform"
__description__ = "Modular position monitoring and portfolio analysis components"