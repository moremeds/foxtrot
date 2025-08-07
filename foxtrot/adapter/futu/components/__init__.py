"""
Futu API Client modular components package.

This package provides focused, specialized components for managing Futu OpenD
operations through a clean, modular architecture with single responsibilities.

Components organized by functional domain:
    - connection/: Connection orchestration and validation
    - health/: Health monitoring and reconnection management
    - context/: SDK context lifecycle management
    - status/: Status reporting and diagnostics
    - management/: High-level manager coordination

Public API:
    All components are available for direct import and use, supporting
    both the main FutuApiClient and independent usage for testing.
"""

# Connection management components
from .connection import (
    FutuConnectionOrchestrator,
    FutuConnectionValidator
)

# Health monitoring components  
from .health import (
    FutuHealthMonitor,
    HealthChecker,
    ReconnectionManager,
    MonitorConfig
)

# Context management components
from .context import (
    FutuContextManager,
    FutuContextInitializer,
    FutuContextUtilities
)

# Status reporting components
from .status import (
    FutuStatusProvider,
    StatusDiagnostics
)

# Management coordination components
from .management import (
    FutuManagerCoordinator,
    FutuCallbackHandlerManager
)

# Public API exports for backward compatibility and direct usage
__all__ = [
    # Connection management
    "FutuConnectionOrchestrator",
    "FutuConnectionValidator",
    
    # Health monitoring
    "FutuHealthMonitor", 
    "HealthChecker",
    "ReconnectionManager",
    "MonitorConfig",
    
    # Context management
    "FutuContextManager",
    "FutuContextInitializer", 
    "FutuContextUtilities",
    
    # Status reporting
    "FutuStatusProvider",
    "StatusDiagnostics",
    
    # Management coordination
    "FutuManagerCoordinator",
    "FutuCallbackHandlerManager",
]

# Version and module metadata
__version__ = "1.1.0"
__author__ = "Foxtrot Trading Platform"
__description__ = "Modular Futu API client components organized by functional domain"