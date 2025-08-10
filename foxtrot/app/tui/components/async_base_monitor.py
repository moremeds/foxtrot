"""
Async Base Monitor for TUI Data Display Components

Enhanced version of base_monitor with proper async patterns and non-blocking operations.
"""

import asyncio
from typing import Any, Optional, Dict, List
from datetime import datetime

from textual.widgets import DataTable
from textual.coordinate import Coordinate
from textual import work

from ..async_bridge import AsyncBridge, AsyncEventHandler
from .base_monitor import TUIDataMonitor


class AsyncTUIDataMonitor(TUIDataMonitor):
    """
    Enhanced base monitor with async patterns for non-blocking operations.
    
    Key improvements:
    - Non-blocking data updates using background tasks
    - Throttled high-frequency updates
    - Batch processing for efficiency
    - Proper async initialization
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the async monitor."""
        super().__init__(*args, **kwargs)
        
        # Async components
        self.async_bridge = AsyncBridge()
        self._update_queue: asyncio.Queue = asyncio.Queue()
        self._batch_processor_task: Optional[asyncio.Task] = None
        self._update_throttle: Dict[str, float] = {}
        self._throttle_interval = 0.1  # 100ms throttle for updates
        
        # Performance metrics
        self._update_count = 0
        self._last_update_time = datetime.now()
    
    async def on_mount(self) -> None:
        """Enhanced mount with async initialization."""
        await super().on_mount()
        
        # Start batch processor for efficient updates
        self._batch_processor_task = self.async_bridge.create_background_task(
            self._process_update_batch(),
            name=f"{self.monitor_name}_batch_processor"
        )
    
    @AsyncEventHandler.async_handler(timeout=2.0)
    async def process_event(self, event: Any) -> None:
        """
        Process events asynchronously without blocking UI.
        
        Args:
            event: The event to process
        """
        # Queue the event for batch processing
        await self._update_queue.put(event)
    
    async def _process_update_batch(self) -> None:
        """
        Process updates in batches for efficiency.
        
        Batches multiple updates together to reduce UI refresh overhead.
        """
        batch: List[Any] = []
        batch_timeout = 0.05  # 50ms batch window
        
        while True:
            try:
                # Collect updates for batch processing
                deadline = asyncio.get_event_loop().time() + batch_timeout
                
                while asyncio.get_event_loop().time() < deadline:
                    try:
                        remaining = deadline - asyncio.get_event_loop().time()
                        if remaining > 0:
                            event = await asyncio.wait_for(
                                self._update_queue.get(),
                                timeout=remaining
                            )
                            batch.append(event)
                    except asyncio.TimeoutError:
                        break
                
                # Process batch if we have updates
                if batch:
                    await self._apply_batch_updates(batch)
                    batch.clear()
                
                # Small delay to prevent tight loop
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(0.1)
    
    async def _apply_batch_updates(self, batch: List[Any]) -> None:
        """
        Apply a batch of updates efficiently.
        
        Args:
            batch: List of events to process
        """
        # Group updates by key for deduplication
        updates_by_key: Dict[str, Any] = {}
        
        for event in batch:
            if hasattr(event, 'data'):
                data = event.data
                if self.data_key and hasattr(data, self.data_key):
                    key = getattr(data, self.data_key)
                    # Keep only the latest update for each key
                    updates_by_key[key] = data
                else:
                    # No key, process immediately
                    await self._process_single_update(data)
        
        # Apply deduplicated updates
        for key, data in updates_by_key.items():
            if self._should_throttle(key):
                continue
            await self._process_single_update(data)
    
    def _should_throttle(self, key: str) -> bool:
        """
        Check if an update should be throttled.
        
        Args:
            key: The update key
            
        Returns:
            True if the update should be throttled
        """
        now = asyncio.get_event_loop().time()
        last_update = self._update_throttle.get(key, 0)
        
        if now - last_update < self._throttle_interval:
            return True
        
        self._update_throttle[key] = now
        return False
    
    async def _process_single_update(self, data: Any) -> None:
        """
        Process a single data update.
        
        Args:
            data: The data to process
        """
        try:
            # Determine if this is new or existing data
            if self.data_key and hasattr(data, self.data_key):
                key = getattr(data, self.data_key)
                if key in self.cells:
                    await self._update_existing_row(data, key)
                else:
                    await self._insert_new_row(data)
            else:
                await self._insert_new_row(data)
            
            # Update metrics
            self._update_count += 1
            
        except Exception as e:
            self._logger.error(f"Error processing update: {e}")
    
    @work(exclusive=True)
    async def refresh_data(self) -> None:
        """
        Refresh all data from backend asynchronously.
        
        Uses work decorator to prevent multiple simultaneous refreshes.
        """
        try:
            # Clear existing data
            if self.data_table:
                self.data_table.clear()
            self.cells.clear()
            self.row_data.clear()
            
            # Fetch fresh data from backend
            data_list = await self._fetch_backend_data()
            
            # Process all data
            for data in data_list:
                await self._process_single_update(data)
            
            self._log_refresh_complete(len(data_list))
            
        except Exception as e:
            self._logger.error(f"Failed to refresh data: {e}")
            self._show_error_state("Refresh failed")
    
    async def _fetch_backend_data(self) -> List[Any]:
        """
        Fetch data from backend. Override in subclasses.
        
        Returns:
            List of data objects
        """
        # This should be overridden by specific monitor implementations
        return []
    
    def _log_refresh_complete(self, count: int) -> None:
        """Log refresh completion with metrics."""
        elapsed = (datetime.now() - self._last_update_time).total_seconds()
        self._logger.debug(
            f"Refresh complete: {count} items, {self._update_count} updates, {elapsed:.2f}s"
        )
        self._update_count = 0
        self._last_update_time = datetime.now()
    
    def _show_error_state(self, message: str) -> None:
        """
        Show error state in the UI.
        
        Args:
            message: Error message to display
        """
        # This could update a status label or show an error overlay
        if hasattr(self, 'status_label'):
            self.status_label.update(f"❌ {message}")
    
    async def cleanup(self) -> None:
        """Clean up resources on unmount."""
        # Cancel batch processor
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
        
        # Clear throttle cache
        self._update_throttle.clear()
        
        # Call parent cleanup if exists
        if hasattr(super(), 'cleanup'):
            await super().cleanup()