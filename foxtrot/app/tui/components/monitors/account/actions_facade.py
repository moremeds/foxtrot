"""
Account monitor UI actions and keyboard handlers.

Simplified facade that coordinates account monitor actions through
specialized components for filters, display, data, keyboard, and system operations.
"""

import logging
from typing import Any, Callable, Dict, Optional

from .config import AccountMonitorConfig, AccountDisplaySettings
from .filtering import AccountFilterManager

# Import specialized action components
from .actions.filter_actions import AccountFilterActions
from .actions.display_actions import AccountDisplayActions
from .actions.data_actions import AccountDataActions
from .actions.keyboard_handler import AccountKeyboardHandler
from .actions.system_actions import AccountSystemActions
from .actions.action_coordinator import AccountActionCoordinator

# Set up logging
logger = logging.getLogger(__name__)


class AccountActionHandler:
    """
    Account monitor action handler facade.
    
    Coordinates UI actions and keyboard shortcuts through specialized
    action components while maintaining backward compatibility.
    """
    
    def __init__(
        self, 
        config: AccountMonitorConfig,
        display_settings: AccountDisplaySettings,
        filter_manager: AccountFilterManager
    ):
        """Initialize action handler facade."""
        self.config = config
        self.display_settings = display_settings
        self.filter_manager = filter_manager
        
        # Initialize specialized action components
        self._init_action_components()
        
        # Setup component callbacks
        self._setup_component_callbacks()

    def _init_action_components(self) -> None:
        """Initialize specialized action components."""
        # Create individual action components
        self.filter_actions = AccountFilterActions(self.filter_manager)
        self.display_actions = AccountDisplayActions(self.display_settings)
        self.data_actions = AccountDataActions()
        self.system_actions = AccountSystemActions()
        
        # Create action coordinator that handles delegation
        self.action_coordinator = AccountActionCoordinator(
            self.filter_actions,
            self.display_actions,
            self.data_actions,
            self.system_actions
        )
        
        # Create keyboard handler and set it to use this facade as action handler
        self.keyboard_handler = AccountKeyboardHandler()
        self.keyboard_handler.set_action_handler(self.action_coordinator)

    def _setup_component_callbacks(self) -> None:
        """Setup callbacks between components."""
        # Callback functions for communication with parent component
        self._message_callback: Optional[Callable] = None
        self._update_callback: Optional[Callable] = None
        self._refresh_callback: Optional[Callable] = None

    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for system messages."""
        self._message_callback = callback
        # Propagate to all action components
        self.filter_actions.set_message_callback(callback)
        self.display_actions.set_message_callback(callback)
        self.data_actions.set_message_callback(callback)
        self.keyboard_handler.set_message_callback(callback)
        self.system_actions.set_message_callback(callback)

    def set_update_callback(self, callback: Callable) -> None:
        """Set callback for triggering updates."""
        self._update_callback = callback
        # Propagate to all action components
        self.filter_actions.set_update_callback(callback)
        self.display_actions.set_update_callback(callback)
        self.data_actions.set_update_callback(callback)
        self.system_actions.set_update_callback(callback)

    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback for refreshing display."""
        self._refresh_callback = callback
        # Propagate to all action components
        self.filter_actions.set_refresh_callback(callback)
        self.display_actions.set_refresh_callback(callback)
        self.data_actions.set_refresh_callback(callback)
        self.system_actions.set_refresh_callback(callback)

    # Delegate all action methods to the action coordinator
    def __getattr__(self, name: str):
        """
        Delegate action method calls to the action coordinator.
        
        This allows the facade to maintain backward compatibility
        while delegating all actual work to specialized components.
        """
        if name.startswith('action_'):
            if hasattr(self.action_coordinator, name):
                return getattr(self.action_coordinator, name)
        
        # If not an action method or not found, raise AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    # Keyboard Shortcuts (delegate to keyboard_handler)
    async def handle_keyboard_shortcut(self, key: str, context: Dict[str, Any] = None) -> bool:
        """Handle keyboard shortcut."""
        return await self.keyboard_handler.handle_keyboard_shortcut(key, context)

    # Utility Methods for component coordination
    def get_available_actions(self) -> Dict[str, str]:
        """Get all available actions from components."""
        return self.action_coordinator.get_available_actions()

    def get_action_history(self, limit: int = 10) -> list[str]:
        """Get recent action history from system component."""
        return self.action_coordinator.get_action_history(limit)

    def get_keyboard_shortcuts(self) -> Dict[str, str]:
        """Get keyboard shortcut mappings."""
        return self.keyboard_handler.get_keyboard_shortcuts()

    # Component Access Methods for Advanced Usage
    def get_filter_actions(self):
        """Get filter actions component."""
        return self.filter_actions

    def get_display_actions(self):
        """Get display actions component."""
        return self.display_actions

    def get_data_actions(self):
        """Get data actions component."""
        return self.data_actions

    def get_system_actions(self):
        """Get system actions component."""
        return self.system_actions

    def get_keyboard_handler(self):
        """Get keyboard handler component."""
        return self.keyboard_handler