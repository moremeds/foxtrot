"""
Account monitor keyboard shortcut handler.

Handles keyboard shortcut mappings and key processing for account actions.
"""

from typing import Any, Callable, Dict, Optional


class AccountKeyboardHandler:
    """Handles keyboard shortcuts for account monitor actions."""
    
    def __init__(self):
        """Initialize keyboard handler."""
        # Callback functions
        self._message_callback: Optional[Callable] = None
        self._action_handler: Optional[object] = None
        
        # Keyboard shortcut mappings
        self._keyboard_shortcuts = self._setup_keyboard_shortcuts()
    
    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for system messages."""
        self._message_callback = callback
    
    def set_action_handler(self, handler: object) -> None:
        """Set the action handler that contains the actual action methods."""
        self._action_handler = handler
    
    def _setup_keyboard_shortcuts(self) -> Dict[str, str]:
        """Setup keyboard shortcut mappings."""
        return {
            "f": "action_clear_filters",
            "u": "action_filter_usd", 
            "z": "action_filter_zero",
            "m": "action_filter_margin",
            "p": "action_toggle_percentage",
            "w": "action_toggle_margin_warnings",
            "a": "action_toggle_auto_scroll",
            "g": "action_toggle_currency_grouping",
            "r": "action_refresh_data",
            "escape": "action_reset_view",
            "c": "action_toggle_compact_view",
            "d": "action_toggle_detailed_view",
            "o": "action_toggle_color_coding",
            "s": "action_cycle_sort_order",
            "h": "action_filter_high_risk",
            "plus": "action_filter_profitable",
            "minus": "action_filter_losing",
            "e": "action_export_summary"
        }
    
    async def handle_keyboard_shortcut(
        self, 
        key: str, 
        context: Dict[str, Any] = None
    ) -> bool:
        """
        Handle keyboard shortcut.
        
        Args:
            key: Key pressed
            context: Optional context information
            
        Returns:
            True if shortcut was handled
        """
        try:
            action_name = self._keyboard_shortcuts.get(key.lower())
            if not action_name:
                return False
            
            if not self._action_handler:
                return False
            
            # Get the action method from the action handler
            action_method = getattr(self._action_handler, action_name, None)
            if not action_method:
                return False
            
            # Execute the action
            await action_method()
            return True
            
        except Exception as e:
            if self._message_callback:
                await self._message_callback(f"Keyboard shortcut error: {e}")
            return False
    
    def get_keyboard_shortcuts(self) -> Dict[str, str]:
        """Get keyboard shortcut mappings."""
        return self._keyboard_shortcuts.copy()
    
    def get_shortcut_help(self) -> Dict[str, str]:
        """Get keyboard shortcut help information."""
        return {
            "f": "Clear all filters",
            "u": "Filter USD currency", 
            "z": "Toggle zero balance",
            "m": "Filter margin accounts",
            "p": "Toggle percentage display",
            "w": "Toggle margin warnings",
            "a": "Toggle auto-scroll",
            "g": "Toggle currency grouping",
            "r": "Refresh data",
            "escape": "Reset view",
            "c": "Toggle compact view",
            "d": "Toggle detailed view",
            "o": "Toggle color coding",
            "s": "Cycle sort order",
            "h": "Filter high risk",
            "+": "Filter profitable",
            "-": "Filter losing",
            "e": "Export summary"
        }
    
    def add_custom_shortcut(self, key: str, action_name: str) -> None:
        """Add a custom keyboard shortcut."""
        self._keyboard_shortcuts[key.lower()] = action_name
    
    def remove_shortcut(self, key: str) -> None:
        """Remove a keyboard shortcut."""
        self._keyboard_shortcuts.pop(key.lower(), None)
    
    def has_shortcut(self, key: str) -> bool:
        """Check if a key has a shortcut assigned."""
        return key.lower() in self._keyboard_shortcuts