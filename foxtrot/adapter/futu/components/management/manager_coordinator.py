"""
Futu manager coordinator for specialized manager lifecycle management.

This module coordinates the initialization, management, and cleanup of all
specialized Futu managers (account, order, market data, historical data, contracts).
"""

import weakref
from typing import Dict, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ...account_manager import FutuAccountManager
    from ...contract_manager import FutuContractManager
    from ...historical_data import FutuHistoricalData
    from ...market_data import FutuMarketData
    from ...order_manager import FutuOrderManager
    from ...api_client import FutuApiClient
    
    ManagerType = Union[FutuAccountManager, FutuOrderManager, FutuMarketData, FutuHistoricalData, FutuContractManager]


class FutuManagerCoordinator:
    """
    Coordinator for specialized Futu manager lifecycle operations.
    
    This class handles the initialization, management, and cleanup
    of all specialized managers used by the Futu adapter.
    """

    def __init__(self, api_client_ref: 'weakref.ref[FutuApiClient]') -> None:
        """
        Initialize manager coordinator.
        
        Args:
            api_client_ref: Weak reference to FutuApiClient instance
        """
        self._api_client_ref = api_client_ref
        
        # Manager instances (initialized by initialize_managers)
        self._managers: Dict[str, 'ManagerType'] = {}
        self._initialized: bool = False

    def initialize_managers(self) -> bool:
        """
        Initialize all specialized manager instances.
        
        Returns:
            True if initialization successful, False otherwise
        """
        api_client = self._api_client_ref()
        if not api_client:
            return False

        if self._initialized:
            self._log_info("Managers already initialized")
            return True

        try:
            # Import here to avoid circular imports
            from ..account_manager import FutuAccountManager
            from ..contract_manager import FutuContractManager
            from ..historical_data import FutuHistoricalData
            from ..market_data import FutuMarketData
            from ..order_manager import FutuOrderManager

            # Initialize all managers with the API client
            self._managers["account"] = FutuAccountManager(api_client)
            self._managers["order"] = FutuOrderManager(api_client)
            self._managers["market_data"] = FutuMarketData(api_client)
            self._managers["historical"] = FutuHistoricalData(api_client)
            self._managers["contract"] = FutuContractManager(api_client)

            # Set manager references in API client for backward compatibility
            api_client.account_manager = self._managers["account"]
            api_client.order_manager = self._managers["order"]
            api_client.market_data = self._managers["market_data"] 
            api_client.historical_data = self._managers["historical"]
            api_client.contract_manager = self._managers["contract"]

            self._initialized = True
            self._log_info("All Futu managers initialized successfully")
            return True

        except (ImportError, AttributeError) as e:
            self._log_error(f"Failed to initialize managers: {e}")
            return False
        except Exception as e:
            self._log_error(f"Unexpected error during manager initialization: {e}")
            return False

    def get_manager(self, manager_type: str) -> Optional['ManagerType']:
        """
        Get a specific manager instance.
        
        Args:
            manager_type: Type of manager ('account', 'order', 'market_data', 'historical', 'contract')
            
        Returns:
            Manager instance or None if not found
        """
        return self._managers.get(manager_type)

    def get_all_managers(self) -> Dict[str, 'ManagerType']:
        """
        Get all manager instances.
        
        Returns:
            Dictionary of manager type to manager instance
        """
        return self._managers.copy()

    def is_initialized(self) -> bool:
        """
        Check if managers have been initialized.
        
        Returns:
            True if managers are initialized, False otherwise
        """
        return self._initialized

    def cleanup_managers(self) -> None:
        """
        Clean up all manager instances and clear references.
        """
        api_client = self._api_client_ref()
        
        try:
            # Clear manager references in API client
            if api_client:
                api_client.account_manager = None
                api_client.order_manager = None
                api_client.market_data = None
                api_client.historical_data = None
                api_client.contract_manager = None

            # Clear local manager references
            self._managers.clear()
            self._initialized = False
            
            self._log_info("All Futu managers cleaned up")

        except Exception as e:
            self._log_error(f"Unexpected error during manager cleanup: {e}")

    def get_manager_status(self) -> Dict[str, Union[bool, Optional[str], int, Dict[str, Dict[str, Union[bool, Optional[str]]]]]]:
        """
        Get status information for all managers.
        
        Returns:
            Dictionary with manager status information
        """
        api_client = self._api_client_ref()
        
        status = {
            "coordinator_alive": api_client is not None,
            "initialized": self._initialized,
            "manager_count": len(self._managers),
            "managers": {}
        }

        for manager_type, manager in self._managers.items():
            status["managers"][manager_type] = {
                "initialized": manager is not None,
                "type": type(manager).__name__ if manager else None
            }

        return status

    def reinitialize_managers(self) -> bool:
        """
        Reinitialize all managers (cleanup and initialize).
        
        Returns:
            True if reinitialization successful, False otherwise
        """
        self._log_info("Reinitializing all managers")
        self.cleanup_managers()
        return self.initialize_managers()

    def _log_info(self, msg: str) -> None:
        """Log info message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_info'):
            api_client._log_info(f"ManagerCoordinator: {msg}")

    def _log_error(self, msg: str) -> None:
        """Log error message through API client."""
        api_client = self._api_client_ref()
        if api_client and hasattr(api_client, '_log_error'):
            api_client._log_error(f"ManagerCoordinator: {msg}")