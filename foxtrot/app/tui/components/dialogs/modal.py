"""
Modal Manager for Dialog System

This module provides centralized management of modal dialogs,
including showing dialogs, handling results, and managing dialog lifecycle.
"""

import contextlib
from typing import Any

from textual.app import App

from .base import BaseDialog, DialogResult
from .confirmation import (
    CancelAllConfirmationDialog,
    CancelConfirmationDialog,
    OrderConfirmationDialog,
)


class ModalManager:
    """
    Centralized manager for modal dialogs in the TUI.

    Provides convenience methods for showing different types of dialogs
    and handling their results consistently across the application.
    """

    def __init__(self, app: App):
        """
        Initialize modal manager.

        Args:
            app: The Textual application instance
        """
        self.app = app
        self._active_dialogs: dict[str, BaseDialog] = {}

    async def show_dialog(self, dialog: BaseDialog) -> DialogResult:
        """
        Show a modal dialog and wait for result.

        Args:
            dialog: Dialog instance to show

        Returns:
            Dialog result when closed
        """
        try:
            # Track active dialog
            dialog_id = id(dialog)
            self._active_dialogs[str(dialog_id)] = dialog

            # Push dialog as modal screen
            self.app.push_screen(dialog)

            # Wait for result
            return await dialog.wait_for_result()


        except Exception as e:
            return DialogResult(
                confirmed=False,
                cancelled=True,
                error=str(e)
            )
        finally:
            # Clean up tracking
            self._active_dialogs.pop(str(dialog_id), None)

    async def show_confirmation(
        self,
        title: str,
        message: str,
        confirm_text: str = "Yes",
        cancel_text: str = "No"
    ) -> DialogResult:
        """
        Show a simple confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            confirm_text: Confirm button text
            cancel_text: Cancel button text

        Returns:
            Dialog result
        """
        from .base import SimpleConfirmationDialog

        dialog = SimpleConfirmationDialog(
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text
        )

        return await self.show_dialog(dialog)

    async def show_info(
        self,
        title: str,
        message: str
    ) -> DialogResult:
        """
        Show an information dialog.

        Args:
            title: Dialog title
            message: Information message

        Returns:
            Dialog result
        """
        from .base import InfoDialog

        dialog = InfoDialog(title=title, message=message)
        return await self.show_dialog(dialog)

    async def show_warning(
        self,
        title: str,
        message: str
    ) -> DialogResult:
        """
        Show a warning dialog.

        Args:
            title: Dialog title
            message: Warning message

        Returns:
            Dialog result
        """
        from .base import WarningDialog

        dialog = WarningDialog(title=title, message=message)
        return await self.show_dialog(dialog)

    async def show_error(
        self,
        title: str,
        message: str
    ) -> DialogResult:
        """
        Show an error dialog.

        Args:
            title: Dialog title
            message: Error message

        Returns:
            Dialog result
        """
        from .base import ErrorDialog

        dialog = ErrorDialog(title=title, message=message)
        return await self.show_dialog(dialog)

    async def show_order_confirmation(
        self,
        order_data: dict[str, Any],
        account_balance: float | None = None,
        market_price: float | None = None
    ) -> DialogResult:
        """
        Show order confirmation dialog.

        Args:
            order_data: Order information dictionary
            account_balance: Available account balance
            market_price: Current market price

        Returns:
            Dialog result with order confirmation data
        """
        dialog = OrderConfirmationDialog(
            order_data=order_data,
            account_balance=account_balance,
            market_price=market_price
        )

        return await self.show_dialog(dialog)

    async def show_cancel_confirmation(
        self,
        order_id: str | None = None,
        message: str = "Are you sure you want to cancel this order?"
    ) -> DialogResult:
        """
        Show order cancellation confirmation dialog.

        Args:
            order_id: ID of order to cancel
            message: Confirmation message

        Returns:
            Dialog result with cancellation confirmation
        """
        dialog = CancelConfirmationDialog(
            order_id=order_id,
            message=message
        )

        return await self.show_dialog(dialog)

    async def show_cancel_all_confirmation(
        self,
        open_orders_count: int = 0
    ) -> DialogResult:
        """
        Show cancel all orders confirmation dialog.

        Args:
            open_orders_count: Number of open orders to cancel

        Returns:
            Dialog result with cancel all confirmation
        """
        dialog = CancelAllConfirmationDialog(
            open_orders_count=open_orders_count
        )

        return await self.show_dialog(dialog)

    def close_all_dialogs(self):
        """Close all active dialogs."""
        for dialog in list(self._active_dialogs.values()):
            with contextlib.suppress(Exception):
                dialog.dismiss(DialogResult(cancelled=True))

        self._active_dialogs.clear()

    def get_active_dialog_count(self) -> int:
        """Get number of currently active dialogs."""
        return len(self._active_dialogs)

    def has_active_dialogs(self) -> bool:
        """Check if any dialogs are currently active."""
        return len(self._active_dialogs) > 0


# Global modal manager instance
_modal_manager: ModalManager | None = None


def get_modal_manager(app: App | None = None) -> ModalManager:
    """
    Get the global modal manager instance.

    Args:
        app: Textual application instance (required for first call)

    Returns:
        Modal manager instance

    Raises:
        RuntimeError: If no app provided and manager not initialized
    """
    global _modal_manager

    if _modal_manager is None:
        if app is None:
            raise RuntimeError("Modal manager not initialized and no app provided")
        _modal_manager = ModalManager(app)

    return _modal_manager


def reset_modal_manager():
    """Reset the global modal manager instance."""
    global _modal_manager
    if _modal_manager:
        _modal_manager.close_all_dialogs()
    _modal_manager = None
