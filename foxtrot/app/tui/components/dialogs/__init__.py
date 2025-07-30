"""
Dialog System for Foxtrot TUI

This package provides a comprehensive dialog system for user interactions,
confirmations, and data entry in the TUI interface.
"""

from .base import BaseDialog, DialogResult, DialogType
from .confirmation import OrderConfirmationDialog, CancelConfirmationDialog
from .modal import ModalManager

__all__ = [
    "BaseDialog",
    "DialogResult", 
    "DialogType",
    "OrderConfirmationDialog",
    "CancelConfirmationDialog",
    "ModalManager",
]