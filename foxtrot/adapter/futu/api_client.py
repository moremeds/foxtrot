"""
Futu API Client - Central coordinator for all Futu OpenD operations.

This module provides a central coordinator that manages all manager interactions
and the Futu SDK context lifecycle through modular components. It serves as the
primary interface for all Futu OpenAPI operations through the OpenD gateway.
"""

import weakref
from typing import TYPE_CHECKING, Any

from foxtrot.core.event_engine import EventEngine

from .components.management.manager_coordinator import FutuManagerCoordinator
from .components.connection.connection_orchestrator import FutuConnectionOrchestrator
from .components.management.callback_handler_manager import FutuCallbackHandlerManager
from .components.status.status_provider import FutuStatusProvider

if TYPE_CHECKING:
    from .account_manager import FutuAccountManager
    from .contract_manager_facade import FutuContractManager
    from .historical_data import FutuHistoricalData
    from .market_data import FutuMarketData
    from .order_manager import FutuOrderManager


class FutuApiClient:
    """
    Central coordinator for all Futu adapter operations.

    This class coordinates specialized modular components to manage the Futu SDK
    contexts, managers, callbacks, and connection lifecycle. It serves as the
    primary interface while delegating responsibilities to focused modules.

    Architecture:
    - Modular component composition for focused responsibilities
    - Connection orchestrator for lifecycle management
    - Manager coordinator for specialized managers
    - Callback handler manager for real-time data
    - Status provider for health monitoring and diagnostics
    """

    def __init__(self, event_engine: EventEngine, adapter_name: str):
        """Initialize the API client with modular components."""
        self.event_engine = event_engine
        self.adapter_name = adapter_name

        # Connection state (managed by components but accessible for compatibility)
        self.connected = False
        self.last_settings: dict[str, Any] = {}

        # SDK contexts (managed by context manager but accessible for compatibility)
        self.quote_ctx = None
        self.trade_ctx_hk = None
        self.trade_ctx_us = None

        # Callback handlers (managed by callback manager but accessible for compatibility)
        self.quote_handler = None
        self.trade_handler = None

        # Manager instances (managed by manager coordinator but accessible for compatibility)
        self.account_manager = None
        self.order_manager = None
        self.market_data = None
        self.historical_data = None
        self.contract_manager = None

        # Market access flags (set by connection orchestrator)
        self.hk_access = False
        self.us_access = False
        self.cn_access = False
        self.paper_trading = True

        # Initialize modular components with weak reference to avoid circular references
        self._api_client_ref = weakref.ref(self)
        self.manager_coordinator = FutuManagerCoordinator(self._api_client_ref)
        self.connection_orchestrator = FutuConnectionOrchestrator(self._api_client_ref)
        self.callback_manager = FutuCallbackHandlerManager(self._api_client_ref)
        
        # Status provider requires references to other components
        self.status_provider = FutuStatusProvider(
            self._api_client_ref,
            self.connection_orchestrator,
            self.connection_orchestrator.health_monitor,
            self.manager_coordinator,
            self.callback_manager
        )

    def initialize_managers(self) -> None:
        """Initialize all manager instances via manager coordinator."""
        self.manager_coordinator.initialize_managers()

    def connect(self, settings: dict[str, Any]) -> bool:
        """
        Connect to Futu OpenD gateway using provided settings.

        Args:
            settings: Dictionary containing OpenD configuration

        Returns:
            True if connection successful, False otherwise
        """
        # Delegate to connection orchestrator for complete connection workflow
        success = self.connection_orchestrator.connect(settings)
        
        if success:
            # Set up callback handlers after successful connection
            self.callback_manager.setup_callback_handlers()
            
            # Initialize managers after connection and callbacks
            self.manager_coordinator.initialize_managers()
            
            self._log_info("Futu OpenD connected and authenticated")
        else:
            self._log_error("Connection failed")
            
        return success

    def setup_callback_handlers(self) -> None:
        """Register SDK callback handlers for real-time data via callback manager."""
        self.callback_manager.setup_callback_handlers()

    def close(self) -> None:
        """Close all OpenD connections and cleanup resources via orchestrator."""
        try:
            # Clean up all components in reverse order
            self.manager_coordinator.cleanup_managers()
            self.callback_manager.cleanup_handlers()
            self.connection_orchestrator.disconnect()
            
            self._log_info("All Futu contexts closed")

        except Exception as e:
            self._log_error(f"Error closing connections: {e}")

    def get_connection_health(self) -> dict[str, Any]:
        """
        Get detailed connection health information via status provider.

        Returns:
            Dictionary with health status and metrics
        """
        return self.status_provider.get_connection_health()

    def get_trade_context(self, market: str):
        """
        Get appropriate trade context for market via status provider.

        Args:
            market: Market identifier (HK, US, CN)

        Returns:
            Trade context for the market, or None if not available
        """
        return self.status_provider.get_trade_context_for_market(market)

    def get_opend_status(self) -> dict[str, Any]:
        """
        Get OpenD gateway status information via status provider.

        Returns:
            Dictionary with connection status details
        """
        return self.status_provider.get_opend_status()

    def _log_info(self, msg: str) -> None:
        """Log info message through adapter."""
        if hasattr(self, 'adapter') and self.adapter:
            self.adapter.write_log(msg)

    def _log_error(self, msg: str) -> None:
        """Log error message through adapter."""
        if hasattr(self, 'adapter') and self.adapter:
            self.adapter.write_log(f"ERROR: {msg}")

    def set_adapter(self, adapter) -> None:
        """Set adapter reference for logging."""
        self.adapter = adapter
