"""
Base Dialog Infrastructure

This module provides the foundational classes and types for the TUI dialog system,
including modal dialog base class, result handling, and event management.
"""

import asyncio
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Callable

from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.message import Message
from textual.widgets import Button, Static, Label
from textual.screen import ModalScreen
from textual.widget import Widget


class DialogType(Enum):
    """Types of dialogs available in the system."""
    
    CONFIRMATION = "confirmation"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    INPUT = "input"
    CUSTOM = "custom"


@dataclass
class DialogResult:
    """Result object returned by dialog interactions."""
    
    confirmed: bool = False
    cancelled: bool = False
    data: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
    
    @property
    def success(self) -> bool:
        """True if dialog was confirmed without error."""
        return self.confirmed and not self.error
    
    @property
    def failed(self) -> bool:
        """True if dialog was cancelled or had error."""
        return self.cancelled or bool(self.error)


class BaseDialog(ModalScreen):
    """
    Base class for all TUI dialogs.
    
    Provides common functionality including:
    - Modal behavior with backdrop
    - Standard button layouts
    - Result handling
    - Keyboard shortcuts
    - Event management
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm", "Confirm", priority=True),
        Binding("ctrl+c", "cancel", "Cancel"),
    ]
    
    DEFAULT_CSS = """
    BaseDialog {
        align: center middle;
    }
    
    .dialog-container {
        background: $surface;
        border: thick $primary;
        width: 60%;
        height: auto;
        max-width: 80;
        min-height: 15;
        padding: 1;
    }
    
    .dialog-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .dialog-content {
        padding: 1;
        margin-bottom: 1;
    }
    
    .dialog-buttons {
        align: center middle;
        height: 3;
    }
    
    .confirm-button {
        margin-right: 2;
    }
    
    .cancel-button {
        margin-left: 2;
    }
    """
    
    def __init__(
        self,
        title: str,
        dialog_type: DialogType = DialogType.CUSTOM,
        show_cancel: bool = True,
        confirm_text: str = "OK",
        cancel_text: str = "Cancel",
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.title = title
        self.dialog_type = dialog_type
        self.show_cancel = show_cancel
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        
        # Result handling
        self.result = DialogResult()
        self.result_future: Optional[asyncio.Future] = None
        
        # UI components
        self.title_widget: Optional[Static] = None
        self.content_container: Optional[Container] = None
        self.confirm_button: Optional[Button] = None
        self.cancel_button: Optional[Button] = None
    
    def compose(self):
        """Create the dialog layout."""
        with Container(classes="dialog-container"):
            # Title
            self.title_widget = Static(self.title, classes="dialog-title")
            yield self.title_widget
            
            # Content area - subclasses override this
            with Vertical(classes="dialog-content") as content_container:
                self.content_container = content_container
                yield from self.compose_content()
            
            # Buttons
            with Horizontal(classes="dialog-buttons"):
                self.confirm_button = Button(
                    self.confirm_text, 
                    variant="primary", 
                    classes="confirm-button"
                )
                yield self.confirm_button
                
                if self.show_cancel:
                    self.cancel_button = Button(
                        self.cancel_text, 
                        variant="default", 
                        classes="cancel-button"
                    )
                    yield self.cancel_button
    
    @abstractmethod
    def compose_content(self) -> list[Widget]:
        """
        Compose the dialog content area.
        
        Subclasses must implement this to define their specific content.
        
        Returns:
            List of widgets to include in the content area
        """
        pass
    
    async def on_mount(self):
        """Initialize dialog after mounting."""
        await self.setup_dialog()
    
    async def setup_dialog(self):
        """Setup dialog-specific initialization."""
        # Focus the confirm button by default
        if self.confirm_button:
            self.confirm_button.focus()
    
    async def on_button_pressed(self, event: Button.Pressed):
        """Handle button press events."""
        if event.button == self.confirm_button:
            await self.action_confirm()
        elif event.button == self.cancel_button:
            await self.action_cancel()
    
    async def action_confirm(self):
        """Handle confirm action."""
        try:
            # Validate dialog content
            validation_result = await self.validate_input()
            if not validation_result.success:
                await self.show_validation_error(validation_result.error)
                return
            
            # Collect dialog data
            self.result.data = await self.collect_data()
            self.result.confirmed = True
            self.result.cancelled = False
            
            # Close dialog with result
            await self.close_with_result(self.result)
            
        except Exception as e:
            self.result.error = str(e)
            await self.close_with_result(self.result)
    
    async def action_cancel(self):
        """Handle cancel action."""
        self.result.confirmed = False
        self.result.cancelled = True
        await self.close_with_result(self.result)
    
    async def validate_input(self) -> DialogResult:
        """
        Validate dialog input before confirming.
        
        Returns:
            DialogResult with validation status
        """
        # Default implementation - no validation
        return DialogResult(confirmed=True)
    
    async def collect_data(self) -> Dict[str, Any]:
        """
        Collect data from dialog inputs.
        
        Returns:
            Dictionary containing dialog data
        """
        # Default implementation - no data
        return {}
    
    async def show_validation_error(self, error: str):
        """
        Show validation error to user.
        
        Args:
            error: Error message to display
        """
        # Simple implementation - could be enhanced with error widget
        if self.title_widget:
            original_title = self.title_widget.renderable
            self.title_widget.update(f"Error: {error}")
            
            # Restore original title after delay
            await asyncio.sleep(2)
            self.title_widget.update(original_title)
    
    async def close_with_result(self, result: DialogResult):
        """
        Close dialog and return result.
        
        Args:
            result: Result to return
        """
        if self.result_future and not self.result_future.done():
            self.result_future.set_result(result)
        
        self.dismiss(result)
    
    async def wait_for_result(self) -> DialogResult:
        """
        Wait for dialog result.
        
        Returns:
            Dialog result when dialog is closed
        """
        if not self.result_future:
            self.result_future = asyncio.Future()
        
        return await self.result_future


class SimpleConfirmationDialog(BaseDialog):
    """
    Simple confirmation dialog with message and Yes/No buttons.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Yes",
        cancel_text: str = "No",
        **kwargs
    ):
        super().__init__(
            title=title,
            dialog_type=DialogType.CONFIRMATION,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            **kwargs
        )
        self.message = message
        self.message_widget: Optional[Static] = None
    
    def compose_content(self) -> list[Widget]:
        """Compose confirmation dialog content."""
        self.message_widget = Static(self.message, classes="dialog-message")
        return [self.message_widget]


class InfoDialog(BaseDialog):
    """
    Information dialog with message and OK button.
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        **kwargs
    ):
        super().__init__(
            title=title,
            dialog_type=DialogType.INFO,
            show_cancel=False,
            confirm_text="OK",
            **kwargs
        )
        self.message = message
        self.message_widget: Optional[Static] = None
    
    def compose_content(self) -> list[Widget]:
        """Compose info dialog content."""
        self.message_widget = Static(self.message, classes="dialog-message")
        return [self.message_widget]


class WarningDialog(BaseDialog):
    """
    Warning dialog with message and OK/Cancel buttons.
    """
    
    DEFAULT_CSS = BaseDialog.DEFAULT_CSS + """
    WarningDialog .dialog-title {
        color: $warning;
    }
    
    WarningDialog .dialog-container {
        border: thick $warning;
    }
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        **kwargs
    ):
        super().__init__(
            title=title,
            dialog_type=DialogType.WARNING,
            confirm_text="OK",
            cancel_text="Cancel",
            **kwargs
        )
        self.message = message
        self.message_widget: Optional[Static] = None
    
    def compose_content(self) -> list[Widget]:
        """Compose warning dialog content."""
        self.message_widget = Static(self.message, classes="dialog-message")
        return [self.message_widget]


class ErrorDialog(BaseDialog):
    """
    Error dialog with message and OK button.
    """
    
    DEFAULT_CSS = BaseDialog.DEFAULT_CSS + """
    ErrorDialog .dialog-title {
        color: $error;
    }
    
    ErrorDialog .dialog-container {
        border: thick $error;
    }
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        **kwargs
    ):
        super().__init__(
            title=title,
            dialog_type=DialogType.ERROR,
            show_cancel=False,
            confirm_text="OK",
            **kwargs
        )
        self.message = message
        self.message_widget: Optional[Static] = None
    
    def compose_content(self) -> list[Widget]:
        """Compose error dialog content."""
        self.message_widget = Static(self.message, classes="dialog-message")
        return [self.message_widget]