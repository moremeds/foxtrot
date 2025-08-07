"""
Futu context manager for SDK context lifecycle management.

This module provides a unified interface for managing Futu SDK contexts
by coordinating initialization, utilities, and cleanup operations.
"""

import weakref
from typing import Any, Dict

from .context_initializer import FutuContextInitializer
from .context_utilities import FutuContextUtilities


class FutuContextManager:
    """Main coordinator for Futu SDK context lifecycle operations."""

    def __init__(self, api_client_ref: weakref.ref):
        """Initialize context manager with modular components."""
        self._api_client_ref = api_client_ref
        self.initializer = FutuContextInitializer(api_client_ref)
        self.utilities = FutuContextUtilities(api_client_ref)

    def initialize_contexts(self, host: str, port: int, settings: Dict[str, Any]) -> bool:
        """Initialize all OpenD contexts with proper error handling."""
        return self.initializer.initialize_all_contexts(host, port, settings)

    def setup_callback_handlers(self) -> None:
        """Register SDK callback handlers for real-time data."""
        self.utilities.setup_callback_handlers()

    def cleanup_contexts(self) -> None:
        """Close all OpenD contexts and cleanup resources."""
        self.utilities.cleanup_contexts()

    def get_context_status(self) -> Dict[str, Any]:
        """Get status of all SDK contexts."""
        return self.utilities.get_context_status()

    def get_trade_context(self, market: str):
        """Get appropriate trade context for market."""
        return self.utilities.get_trade_context(market)

    def test_contexts(self) -> Dict[str, Any]:
        """Test all initialized contexts for connectivity."""
        return self.utilities.test_contexts()