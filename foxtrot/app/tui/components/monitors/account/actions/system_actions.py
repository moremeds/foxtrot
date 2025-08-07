"""
Account monitor system actions.

Handles system-level actions like refresh, reset, export, and utility operations
for the account monitor interface.
"""

from typing import Any, Callable, Dict, Optional


class AccountSystemActions:
    """Handles system-level actions for account monitor."""
    
    def __init__(self):
        """Initialize system actions handler."""
        # Callback functions
        self._message_callback: Optional[Callable] = None
        self._update_callback: Optional[Callable] = None
        self._refresh_callback: Optional[Callable] = None
        
        # Action tracking
        self._action_history: list[str] = []
    
    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for system messages."""
        self._message_callback = callback
    
    def set_update_callback(self, callback: Callable) -> None:
        """Set callback for triggering updates."""
        self._update_callback = callback
    
    def set_refresh_callback(self, callback: Callable) -> None:
        """Set callback for refreshing display."""
        self._refresh_callback = callback
    
    async def _add_system_message(self, message: str) -> None:
        """Add system message if callback is set."""
        if self._message_callback:
            await self._message_callback(message)
    
    async def _trigger_update(self) -> None:
        """Trigger update if callback is set."""
        if self._update_callback:
            await self._update_callback()
    
    async def _trigger_refresh(self) -> None:
        """Trigger refresh if callback is set."""
        if self._refresh_callback:
            await self._refresh_callback()
    
    def _track_action(self, action_name: str) -> None:
        """Track action for history."""
        self._action_history.append(action_name)
        if len(self._action_history) > 50:
            self._action_history.pop(0)
    
    # System Actions
    async def action_refresh_data(self) -> None:
        """Refresh all account data."""
        try:
            await self._add_system_message("Refreshing account data...")
            await self._trigger_refresh()
            self._track_action("refresh_data")
            
        except Exception as e:
            await self._add_system_message(f"Error refreshing data: {e}")
    
    async def action_reset_view(self, clear_filters_callback=None, reset_display_callback=None) -> None:
        """Reset view to default state."""
        try:
            # Clear filters if callback provided
            if clear_filters_callback:
                await clear_filters_callback()
            
            # Reset display settings if callback provided
            if reset_display_callback:
                await reset_display_callback()
            
            await self._add_system_message("View reset to defaults")
            self._track_action("reset_view")
            
        except Exception as e:
            await self._add_system_message(f"Error resetting view: {e}")
    
    async def action_export_summary(self) -> None:
        """Export account summary data."""
        try:
            await self._add_system_message("Export functionality will be implemented")
            self._track_action("export_summary")
            
        except Exception as e:
            await self._add_system_message(f"Error exporting summary: {e}")
    
    async def action_backup_settings(self) -> None:
        """Backup current settings."""
        try:
            await self._add_system_message("Settings backup functionality will be implemented")
            self._track_action("backup_settings")
            
        except Exception as e:
            await self._add_system_message(f"Error backing up settings: {e}")
    
    async def action_restore_settings(self) -> None:
        """Restore settings from backup."""
        try:
            await self._add_system_message("Settings restore functionality will be implemented")
            self._track_action("restore_settings")
            
        except Exception as e:
            await self._add_system_message(f"Error restoring settings: {e}")
    
    async def action_clear_history(self) -> None:
        """Clear action history."""
        try:
            self._action_history.clear()
            await self._add_system_message("Action history cleared")
            self._track_action("clear_history")
            
        except Exception as e:
            await self._add_system_message(f"Error clearing history: {e}")
    
    async def action_show_statistics(self, stats_data: Dict[str, Any] = None) -> None:
        """Display system statistics."""
        try:
            if not stats_data:
                stats_data = self._get_default_statistics()
            
            stats_summary = self._format_statistics(stats_data)
            await self._add_system_message(f"Statistics: {stats_summary}")
            self._track_action("show_statistics")
            
        except Exception as e:
            await self._add_system_message(f"Error showing statistics: {e}")
    
    # Utility Methods
    def _get_default_statistics(self) -> Dict[str, Any]:
        """Get default system statistics."""
        return {
            "actions_performed": len(self._action_history),
            "system_status": "active",
            "memory_usage": "normal"
        }
    
    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """Format statistics for display."""
        try:
            actions = stats.get("actions_performed", 0)
            status = stats.get("system_status", "unknown")
            memory = stats.get("memory_usage", "unknown")
            
            return f"{actions} actions, {status} status, {memory} memory"
        except Exception:
            return "Statistics unavailable"
    
    def get_action_history(self, limit: int = 10) -> list[str]:
        """Get recent action history."""
        return self._action_history[-limit:]
    
    def get_available_system_actions(self) -> Dict[str, str]:
        """Get list of available system actions."""
        return {
            "refresh_data": "Refresh account data",
            "reset_view": "Reset view to defaults",
            "export_summary": "Export account summary",
            "backup_settings": "Backup current settings",
            "restore_settings": "Restore settings from backup", 
            "clear_history": "Clear action history",
            "show_statistics": "Display system statistics"
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "active_callbacks": {
                "message": self._message_callback is not None,
                "update": self._update_callback is not None,
                "refresh": self._refresh_callback is not None
            },
            "action_history_count": len(self._action_history),
            "last_action": self._action_history[-1] if self._action_history else None
        }