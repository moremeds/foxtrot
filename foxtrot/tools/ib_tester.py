"""
Interactive Brokers connection tester.

Provides comprehensive testing of IB adapter connectivity and account information retrieval.
"""
import logging
import threading
import time
from typing import Dict, Optional

from foxtrot.adapter.ibrokers import IBAdapter
from foxtrot.core.engine import EventEngine
from foxtrot.core.event import EVENT_ACCOUNT, EVENT_POSITION, EVENT_LOG, Event
from foxtrot.util.object import AccountData, PositionData

from .config import IBConfig
from .utils import format_connection_status, format_error_message, get_troubleshooting_tips, validate_tws_connection


class IBConnectionTester:
    """Test Interactive Brokers adapter connectivity and retrieve account information."""
    
    def __init__(self, config: IBConfig):
        """Initialize the connection tester.
        
        Args:
            config: IB configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.event_engine: Optional[EventEngine] = None
        self.adapter: Optional[IBAdapter] = None
        
        # Test state
        self.connection_status = "disconnected"
        self.account_data: Dict[str, AccountData] = {}
        self.position_data: Dict[str, PositionData] = {}
        self.last_error: Optional[str] = None
        
        # Synchronization
        self.connection_event = threading.Event()
        self.data_collection_event = threading.Event()
        self.test_completed = threading.Event()
        
        # Test results
        self.connection_successful = False
        self.data_collection_successful = False
        self.test_start_time: Optional[float] = None
        self.connection_time: Optional[float] = None
        
    def run_test(self) -> bool:
        """Run the complete IB connection test.
        
        Returns:
            True if test completed successfully, False otherwise
        """
        self.logger.info("Starting Interactive Brokers connection test")
        self.test_start_time = time.time()
        
        try:
            # Pre-flight checks
            if not self._pre_flight_check():
                return False
            
            # Initialize components
            if not self._initialize_components():
                return False
            
            # Test connection
            if not self._test_connection():
                return False
            
            # Collect account data
            if not self._collect_account_data():
                self.logger.warning("Account data collection failed, but connection was successful")
                # Don't return False here - connection test passed
            
            self.logger.info("Connection test completed successfully")
            return True
            
        except Exception as e:
            self.last_error = format_error_message(e, "test execution")
            self.logger.error(self.last_error)
            return False
        
        finally:
            self._cleanup()
    
    def _pre_flight_check(self) -> bool:
        """Perform pre-flight checks before attempting connection.
        
        Returns:
            True if all checks pass, False otherwise
        """
        self.logger.info(format_connection_status("checking", "Validating TWS/Gateway connectivity"))
        
        # Check if TWS/Gateway is running
        if not validate_tws_connection(self.config.host, self.config.port):
            error_msg = f"Cannot connect to TWS/Gateway at {self.config.host}:{self.config.port}"
            self.last_error = error_msg
            self.logger.error(error_msg)
            self.logger.info(get_troubleshooting_tips("connection"))
            return False
        
        self.logger.info(format_connection_status("validated", "TWS/Gateway is reachable"))
        return True
    
    def _initialize_components(self) -> bool:
        """Initialize event engine and adapter.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            self.logger.info(format_connection_status("initializing", "Setting up event engine and adapter"))
            
            # Create event engine
            self.event_engine = EventEngine()
            
            # Create adapter
            self.adapter = IBAdapter(self.event_engine, "IB_TESTER")
            
            # Register event handlers
            self._register_event_handlers()
            
            # Start event engine
            self.event_engine.start()
            
            self.logger.info(format_connection_status("initialized", "Components ready"))
            return True
            
        except Exception as e:
            self.last_error = format_error_message(e, "component initialization")
            self.logger.error(self.last_error)
            return False
    
    def _register_event_handlers(self) -> None:
        """Register event handlers for adapter events."""
        if not self.event_engine:
            return
        
        # Register handlers
        self.event_engine.register(EVENT_ACCOUNT, self._on_account_event)
        self.event_engine.register(EVENT_POSITION, self._on_position_event)
        self.event_engine.register(EVENT_LOG, self._on_log_event)
    
    def _test_connection(self) -> bool:
        """Test adapter connection to IB.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.adapter:
            self.last_error = "Adapter not initialized"
            self.logger.error(self.last_error)
            return False
        
        try:
            self.logger.info(format_connection_status("connecting", f"Attempting connection to {self.config.host}:{self.config.port}"))
            
            # Prepare connection settings
            connection_settings = {
                "TWS Address": self.config.host,
                "TWS Port": self.config.port,
                "Client ID": self.config.client_id,
                "Trading Account": self.config.account
            }
            
            # Attempt connection
            self.adapter.connect(connection_settings)
            
            # Wait for connection confirmation
            connection_timeout = self.config.connection_timeout
            self.logger.info(f"Waiting for connection confirmation (timeout: {connection_timeout}s)")
            
            if self.connection_event.wait(timeout=connection_timeout):
                self.connection_time = time.time() - self.test_start_time
                self.connection_successful = True
                self.logger.info(format_connection_status("connected", f"Connection established in {self.connection_time:.1f}s"))
                return True
            else:
                self.last_error = f"Connection timeout after {connection_timeout} seconds"
                self.logger.error(self.last_error)
                self.logger.info(get_troubleshooting_tips("timeout"))
                return False
                
        except Exception as e:
            self.last_error = format_error_message(e, "connection")
            self.logger.error(self.last_error)
            self.logger.info(get_troubleshooting_tips("connection"))
            return False
    
    def _collect_account_data(self) -> bool:
        """Collect account and position data.
        
        Returns:
            True if data collection successful, False otherwise
        """
        try:
            self.logger.info(format_connection_status("collecting", "Gathering account and position data"))
            
            # Wait for account data
            data_timeout = self.config.data_timeout
            self.logger.info(f"Waiting for account data (timeout: {data_timeout}s)")
            
            if self.data_collection_event.wait(timeout=data_timeout):
                self.data_collection_successful = True
                self.logger.info(format_connection_status("collected", f"Received data for {len(self.account_data)} accounts, {len(self.position_data)} positions"))
                return True
            else:
                self.last_error = f"Data collection timeout after {data_timeout} seconds"
                self.logger.warning(self.last_error)
                self.logger.info(get_troubleshooting_tips("data"))
                return False
                
        except Exception as e:
            self.last_error = format_error_message(e, "data collection")
            self.logger.error(self.last_error)
            return False
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.logger.info("Cleaning up resources")
            
            # Close adapter
            if self.adapter:
                self.adapter.close()
            
            # Stop event engine
            if self.event_engine:
                self.event_engine.stop()
            
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def _on_account_event(self, event: Event) -> None:
        """Handle account data events.
        
        Args:
            event: Account event
        """
        if not isinstance(event.data, AccountData):
            return
        
        account_data: AccountData = event.data
        self.account_data[account_data.accountid] = account_data
        
        self.logger.debug(f"Received account data for {account_data.accountid}")
        
        # Signal data collection if we have at least one account
        if not self.data_collection_event.is_set() and self.account_data:
            self.data_collection_event.set()
    
    def _on_position_event(self, event: Event) -> None:
        """Handle position data events.
        
        Args:
            event: Position event
        """
        if not isinstance(event.data, PositionData):
            return
        
        position_data: PositionData = event.data
        self.position_data[position_data.vt_symbol] = position_data
        
        self.logger.debug(f"Received position data for {position_data.vt_symbol}")
    
    def _on_log_event(self, event: Event) -> None:
        """Handle log events from the adapter.
        
        Args:
            event: Log event
        """
        if hasattr(event.data, 'msg'):
            log_msg = event.data.msg
            
            # Check for connection confirmation
            if "connected successfully" in log_msg.lower():
                self.connection_status = "connected"
                if not self.connection_event.is_set():
                    self.connection_event.set()
            
            # Check for connection loss
            elif "connection lost" in log_msg.lower():
                self.connection_status = "disconnected"
            
            # Log adapter messages at debug level to reduce noise
            self.logger.debug(f"Adapter: {log_msg}")
    
    @property
    def test_duration(self) -> Optional[float]:
        """Get total test duration in seconds."""
        if self.test_start_time:
            return time.time() - self.test_start_time
        return None
    
    @property
    def summary(self) -> Dict[str, any]:
        """Get test summary data."""
        return {
            "connection_successful": self.connection_successful,
            "data_collection_successful": self.data_collection_successful,
            "accounts_found": len(self.account_data),
            "positions_found": len(self.position_data),
            "connection_time": self.connection_time,
            "test_duration": self.test_duration,
            "last_error": self.last_error
        }