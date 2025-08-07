"""
Account monitor modular package.

This package provides a modular account monitoring system with the following components:
- Configuration and display settings management
- Data formatting and filtering
- Statistics tracking and analysis  
- Risk management and warning system
- UI actions and keyboard handling
- Data export functionality
- Main controller orchestration

The package maintains backward compatibility by exporting the main TUIAccountMonitor
class which provides the same interface as the original monolithic implementation.
"""

# Main controller class for backward compatibility
from .account_controller import TUIAccountMonitor

# Core configuration and data classes
from .config import AccountMonitorConfig, AccountDisplaySettings
from .messages import (
    AccountMonitorMessage, 
    AccountFilterChanged, 
    AccountWarning, 
    AccountRiskAlert,
    AccountExportCompleted
)

# Analysis and summary classes
from .analysis_facade import AccountSummary, PortfolioSummary, AccountAnalyzer

# Component classes (available for advanced usage)
from .formatting import AccountDataFormatter
from .filtering import AccountFilterManager, AccountFilter
from .statistics import AccountStatistics
from .risk_manager import AccountRiskManager, RiskLevel, RiskCategory, RiskThreshold
from .actions_facade import AccountActionHandler
from .export_facade import AccountDataExporter

# Version info
__version__ = "2.0.0"
__author__ = "Foxtrot Trading Platform"

# Backward compatibility alias
AccountMonitor = TUIAccountMonitor

# Factory function for backward compatibility
def create_account_monitor(main_engine, event_engine):
    """
    Create a configured account monitor instance using modular architecture.
    
    This factory function maintains backward compatibility with the original
    create_account_monitor interface while using the new modular implementation.
    
    Args:
        main_engine: The main trading engine (for future use)
        event_engine: The event engine
        
    Returns:
        Configured TUIAccountMonitor instance
    """
    return TUIAccountMonitor(event_engine)

__all__ = [
    # Main classes
    "TUIAccountMonitor",
    "AccountMonitor",  # Backward compatibility alias
    "create_account_monitor",  # Factory function for backward compatibility
    
    # Configuration
    "AccountMonitorConfig", 
    "AccountDisplaySettings",
    
    # Data classes
    "AccountMonitorMessage",
    "AccountFilterChanged", 
    "AccountWarning", 
    "AccountRiskAlert",
    "AccountExportCompleted",
    "AccountSummary", 
    "PortfolioSummary",
    
    # Component classes
    "AccountAnalyzer",
    "AccountDataFormatter",
    "AccountFilterManager", 
    "AccountFilter",
    "AccountStatistics",
    "AccountRiskManager",
    "AccountActionHandler", 
    "AccountDataExporter",
    
    # Enums
    "RiskLevel", 
    "RiskCategory",
    "RiskThreshold",
    
    # Package metadata
    "__version__",
    "__author__"
]