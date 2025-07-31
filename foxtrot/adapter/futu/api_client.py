"""
Futu API Client - Central coordinator for all Futu OpenD operations.

This module provides a central coordinator that manages all manager interactions
and the Futu SDK context lifecycle. It serves as the primary interface
for all Futu OpenAPI operations through the OpenD gateway.
"""

import os
import threading
import time
from typing import TYPE_CHECKING, Any

from foxtrot.core.event_engine import EventEngine
import futu as ft

from .futu_callbacks import FutuQuoteHandler, FutuTradeHandler

if TYPE_CHECKING:
    from .account_manager import FutuAccountManager
    from .contract_manager import FutuContractManager
    from .historical_data import FutuHistoricalData
    from .market_data import FutuMarketData
    from .order_manager import FutuOrderManager


class FutuApiClient:
    """
    Central coordinator for all Futu adapter operations.

    This class manages the Futu SDK contexts, coordinates all manager
    interactions, and provides callback interfaces for events via OpenD gateway.

    Architecture:
    - OpenQuoteContext for market data and queries
    - Market-specific trade contexts (OpenHKTradeContext, etc.)
    - RSA key-based authentication
    - Callback-driven real-time data processing
    """

    def __init__(self, event_engine: EventEngine, adapter_name: str):
        """Initialize the API client."""
        self.event_engine = event_engine
        self.adapter_name = adapter_name

        # Futu SDK contexts (initialized on connect)
        self.quote_ctx: ft.OpenQuoteContext | None = None
        self.trade_ctx_hk: ft.OpenHKTradeContext | None = None
        self.trade_ctx_us: ft.OpenUSTradeContext | None = None

        # Callback handlers
        self.quote_handler: FutuQuoteHandler | None = None
        self.trade_handler: FutuTradeHandler | None = None

        # Manager instances (initialized later)
        self.account_manager: FutuAccountManager | None = None
        self.order_manager: FutuOrderManager | None = None
        self.market_data: FutuMarketData | None = None
        self.historical_data: FutuHistoricalData | None = None
        self.contract_manager: FutuContractManager | None = None

        # Connection state
        self.connected = False
        self.last_settings: dict[str, Any] = {}

        # Market access flags
        self.hk_access = False
        self.us_access = False
        self.cn_access = False

        # Trading environment
        self.paper_trading = True

        # Connection monitoring and health
        self._connection_lock = threading.RLock()
        self._health_monitor_thread: threading.Thread | None = None
        self._health_monitor_running = False
        self._last_heartbeat = 0.0
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_interval = 10
        self._connect_timeout = 30
        self._keep_alive_interval = 30

    def initialize_managers(self) -> None:
        """Initialize all manager instances."""
        # Import here to avoid circular imports
        from .account_manager import FutuAccountManager
        from .contract_manager import FutuContractManager
        from .historical_data import FutuHistoricalData
        from .market_data import FutuMarketData
        from .order_manager import FutuOrderManager

        self.account_manager = FutuAccountManager(self)
        self.order_manager = FutuOrderManager(self)
        self.market_data = FutuMarketData(self)
        self.historical_data = FutuHistoricalData(self)
        self.contract_manager = FutuContractManager(self)

    def connect(self, settings: dict[str, Any]) -> bool:
        """
        Connect to Futu OpenD gateway using provided settings.

        Args:
            settings: Dictionary containing OpenD configuration

        Returns:
            True if connection successful, False otherwise
        """
        with self._connection_lock:
            try:
                # Validate settings first
                if not self._validate_settings(settings):
                    return False

                # Store settings for reconnection
                self.last_settings = settings.copy()

                # Extract connection parameters with validation
                host = settings.get("Host", "127.0.0.1")
                port = settings.get("Port", 11111)
                rsa_file = settings.get("RSA Key File", "conn_key.txt")

                # Update connection settings with bounds checking
                self._max_reconnect_attempts = max(1, min(settings.get("Max Reconnect Attempts", 5), 20))
                self._reconnect_interval = max(1, min(settings.get("Reconnect Interval", 10), 300))
                self._connect_timeout = max(5, min(settings.get("Connect Timeout", 30), 300))
                self._keep_alive_interval = max(10, min(settings.get("Keep Alive Interval", 30), 3600))

                # Validate RSA key file
                if not self._validate_rsa_key(rsa_file):
                    return False

                # Configure RSA encryption
                ft.SysConfig.set_init_rsa_file(rsa_file)
                ft.SysConfig.enable_proto_encrypt(True)

                # Initialize connections with timeout handling
                if not self._initialize_connections(host, port, settings):
                    return False

                # Set up callback handlers
                self.setup_callback_handlers()

                # Initialize managers
                self.initialize_managers()

                # Start connection health monitoring
                self._start_health_monitor()

                self.connected = True
                self._reconnect_attempts = 0
                self._last_heartbeat = time.time()
                self._log_info("Futu OpenD connected and authenticated")
                return True

            except Exception as e:
                self._log_error(f"Connection failed: {e}")
                return False

    def _validate_rsa_key(self, rsa_file: str) -> bool:
        """
        Validate RSA key file exists, is readable, and has proper format.

        Args:
            rsa_file: Path to RSA key file

        Returns:
            True if valid, False otherwise

        Raises:
            None - All exceptions are caught and logged
        """
        if not rsa_file or not isinstance(rsa_file, str):
            self._log_error("RSA key file path is empty or invalid")
            return False

        if not os.path.exists(rsa_file):
            self._log_error(f"RSA key file not found: {rsa_file}")
            return False

        if not os.access(rsa_file, os.R_OK):
            self._log_error(f"RSA key file not readable: {rsa_file}")
            return False

        try:
            # Enhanced validation - check file size and format
            file_stat = os.stat(rsa_file)
            if file_stat.st_size == 0:
                self._log_error(f"RSA key file is empty: {rsa_file}")
                return False

            if file_stat.st_size > 10240:  # 10KB limit for RSA key files
                self._log_error(f"RSA key file too large (>10KB): {rsa_file}")
                return False

            with open(rsa_file, encoding='utf-8') as f:
                content = f.read().strip()

                # Validate RSA key format markers
                if not (("-----BEGIN" in content and "-----END" in content) or
                       ("-----BEGIN RSA PRIVATE KEY-----" in content and "-----END RSA PRIVATE KEY-----" in content)):
                    self._log_error(f"Invalid RSA key format in: {rsa_file}")
                    return False

                # Check for minimum key content
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                if len(lines) < 3:  # Header, content, footer minimum
                    self._log_error(f"RSA key file appears incomplete: {rsa_file}")
                    return False

        except OSError as e:
            self._log_error(f"OS error reading RSA key file {rsa_file}: {e}")
            return False
        except UnicodeDecodeError as e:
            self._log_error(f"RSA key file encoding error {rsa_file}: {e}")
            return False
        except Exception as e:
            self._log_error(f"Unexpected error reading RSA key file {rsa_file}: {e}")
            return False

        return True

    def _validate_settings(self, settings: dict[str, Any]) -> bool:
        """
        Comprehensive validation of connection settings.

        Args:
            settings: Configuration dictionary to validate

        Returns:
            True if all settings are valid, False otherwise
        """
        if not isinstance(settings, dict):
            self._log_error("Settings must be a dictionary")
            return False

        # Required settings validation
        required_keys = ["Host", "Port", "RSA Key File"]
        for key in required_keys:
            if key not in settings:
                self._log_error(f"Required setting missing: {key}")
                return False

        # Host validation
        host = settings.get("Host")
        if not isinstance(host, str) or not host.strip():
            self._log_error("Host must be a non-empty string")
            return False

        # Port validation
        port = settings.get("Port")
        if not isinstance(port, int) or not (1 <= port <= 65535):
            self._log_error("Port must be an integer between 1 and 65535")
            return False

        # Numeric settings validation with ranges
        numeric_settings = {
            "Max Reconnect Attempts": (1, 20),
            "Reconnect Interval": (1, 300),
            "Connect Timeout": (5, 300),
            "Keep Alive Interval": (10, 3600),
            "Max Subscriptions": (1, 1000),
        }

        for setting_name, (min_val, max_val) in numeric_settings.items():
            if setting_name in settings:
                value = settings[setting_name]
                if not isinstance(value, int | float) or not (min_val <= value <= max_val):
                    self._log_error(f"{setting_name} must be between {min_val} and {max_val}")
                    return False

        # Boolean settings validation
        boolean_settings = [
            "Paper Trading", "HK Market Access", "US Market Access",
            "CN Market Access", "Enable Push"
        ]

        for setting_name in boolean_settings:
            if setting_name in settings:
                value = settings[setting_name]
                if not isinstance(value, bool):
                    self._log_error(f"{setting_name} must be a boolean value")
                    return False

        # String settings validation
        string_settings = {
            "Connection ID": (0, 50),
            "Environment": ["REAL", "SIMULATE"],
            "Trading Password": (0, 100),
            "Market Data Level": ["L1", "L2"],
        }

        for setting_name, constraint in string_settings.items():
            if setting_name in settings:
                value = settings[setting_name]
                if not isinstance(value, str):
                    self._log_error(f"{setting_name} must be a string")
                    return False

                if isinstance(constraint, tuple):  # Length constraint
                    min_len, max_len = constraint
                    if not (min_len <= len(value) <= max_len):
                        self._log_error(f"{setting_name} length must be between {min_len} and {max_len}")
                        return False
                elif isinstance(constraint, list):  # Enum constraint
                    if value not in constraint:
                        self._log_error(f"{setting_name} must be one of: {constraint}")
                        return False

        # Market access validation - at least one market must be enabled
        market_access = [
            settings.get("HK Market Access", False),
            settings.get("US Market Access", False),
            settings.get("CN Market Access", False)
        ]

        if not any(market_access):
            self._log_error("At least one market access must be enabled")
            return False

        return True

    def _initialize_connections(self, host: str, port: int, settings: dict[str, Any]) -> bool:
        """
        Initialize OpenD connections with proper error handling.

        Args:
            host: OpenD gateway host
            port: OpenD gateway port
            settings: Connection settings

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize quote context with timeout
            self._log_info(f"Connecting to OpenD gateway at {host}:{port}")
            self.quote_ctx = ft.OpenQuoteContext(host=host, port=port)

            # Test quote connection with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    ret, data = self.quote_ctx.get_global_state()
                    if ret == ft.RET_OK:
                        self._log_info("Quote context connected successfully")
                        break
                    self._log_error(f"Quote context test failed (attempt {attempt + 1}/{max_retries}): {data}")
                    if attempt == max_retries - 1:  # Last attempt
                        return False
                    time.sleep(2)  # Wait before retry
                except Exception as e:
                    self._log_error(f"Quote context connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt == max_retries - 1:
                        return False
                    time.sleep(2)

            # Initialize trade contexts based on market access
            self.hk_access = settings.get("HK Market Access", True)
            self.us_access = settings.get("US Market Access", True)
            self.cn_access = settings.get("CN Market Access", False)
            self.paper_trading = settings.get("Paper Trading", True)

            # Initialize HK trade context if access enabled
            if self.hk_access:
                if not self._initialize_hk_trade_context(host, port, settings):
                    self._log_error("Failed to initialize HK trade context")
                    # Continue anyway - quote context still works

            # Initialize US trade context if access enabled
            if self.us_access:
                if not self._initialize_us_trade_context(host, port, settings):
                    self._log_error("Failed to initialize US trade context")
                    # Continue anyway - quote context still works

            return True

        except Exception as e:
            self._log_error(f"Connection initialization failed: {e}")
            return False

    def _initialize_hk_trade_context(self, host: str, port: int, settings: dict[str, Any]) -> bool:
        """Initialize HK trade context with unlock."""
        try:
            self.trade_ctx_hk = ft.OpenHKTradeContext(host=host, port=port)

            # Unlock trading if password provided
            trading_pwd = settings.get("Trading Password")
            if trading_pwd:
                ret, data = self.trade_ctx_hk.unlock_trade(trading_pwd)
                if ret != ft.RET_OK:
                    self._log_error(f"HK trading unlock failed: {data}")
                    return False
                self._log_info("HK trading unlocked successfully")
            else:
                self._log_info("HK trade context initialized (no password provided)")

            return True

        except Exception as e:
            self._log_error(f"HK trade context initialization failed: {e}")
            return False

    def _initialize_us_trade_context(self, host: str, port: int, settings: dict[str, Any]) -> bool:
        """Initialize US trade context with unlock."""
        try:
            self.trade_ctx_us = ft.OpenUSTradeContext(host=host, port=port)

            # Unlock trading if password provided
            trading_pwd = settings.get("Trading Password")
            if trading_pwd:
                ret, data = self.trade_ctx_us.unlock_trade(trading_pwd)
                if ret != ft.RET_OK:
                    self._log_error(f"US trading unlock failed: {data}")
                    return False
                self._log_info("US trading unlocked successfully")
            else:
                self._log_info("US trade context initialized (no password provided)")

            return True

        except Exception as e:
            self._log_error(f"US trade context initialization failed: {e}")
            return False

    def setup_callback_handlers(self) -> None:
        """Register SDK callback handlers for real-time data."""
        try:
            # Create callback handlers
            self.quote_handler = FutuQuoteHandler(self)
            self.trade_handler = FutuTradeHandler(self)

            # Register quote handler
            if self.quote_ctx:
                self.quote_ctx.set_handler(self.quote_handler)
                self._log_info("Quote callback handler registered")

            # Register trade handlers
            if self.trade_ctx_hk:
                self.trade_ctx_hk.set_handler(self.trade_handler)
                self._log_info("HK trade callback handler registered")

            if self.trade_ctx_us:
                self.trade_ctx_us.set_handler(self.trade_handler)
                self._log_info("US trade callback handler registered")

        except Exception as e:
            self._log_error(f"Callback handler setup failed: {e}")

    def close(self) -> None:
        """Close all OpenD connections and cleanup resources."""
        with self._connection_lock:
            try:
                # Stop health monitoring
                self._stop_health_monitor()

                # Close quote context
                if self.quote_ctx:
                    self.quote_ctx.close()
                    self.quote_ctx = None

                # Close trade contexts
                if self.trade_ctx_hk:
                    self.trade_ctx_hk.close()
                    self.trade_ctx_hk = None

                if self.trade_ctx_us:
                    self.trade_ctx_us.close()
                    self.trade_ctx_us = None

                # Clear handlers
                self.quote_handler = None
                self.trade_handler = None

                # Clear managers
                self.account_manager = None
                self.order_manager = None
                self.market_data = None
                self.historical_data = None
                self.contract_manager = None

                self.connected = False
                self._log_info("All Futu contexts closed")

            except Exception as e:
                self._log_error(f"Error closing connections: {e}")

    def _start_health_monitor(self) -> None:
        """Start connection health monitoring thread."""
        if self._health_monitor_running:
            return

        self._health_monitor_running = True
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            name="FutuHealthMonitor",
            daemon=True
        )
        self._health_monitor_thread.start()
        self._log_info("Connection health monitor started")

    def _stop_health_monitor(self) -> None:
        """Stop connection health monitoring thread."""
        self._health_monitor_running = False
        if self._health_monitor_thread and self._health_monitor_thread.is_alive():
            self._health_monitor_thread.join(timeout=5)
        self._health_monitor_thread = None

    def _health_monitor_loop(self) -> None:
        """Main health monitoring loop."""
        while self._health_monitor_running:
            try:
                # Check connection health
                if not self._check_connection_health():
                    self._log_error("Connection health check failed, attempting reconnection...")
                    self._attempt_reconnection()

                # Update heartbeat
                self._last_heartbeat = time.time()

                # Sleep until next check
                time.sleep(self._keep_alive_interval)

            except Exception as e:
                self._log_error(f"Health monitor error: {e}")
                time.sleep(5)  # Wait before retry on error

    def _check_connection_health(self) -> bool:
        """
        Check if connections are healthy.

        Returns:
            True if all connections are healthy, False otherwise
        """
        try:
            # Check quote context
            if not self.quote_ctx:
                return False

            ret, data = self.quote_ctx.get_global_state()
            if ret != ft.RET_OK:
                self._log_error(f"Quote context health check failed: {data}")
                return False

            # Optional: Check trade contexts
            if self.hk_access and self.trade_ctx_hk:
                try:
                    # Simple health check for trade context
                    ret, _ = self.trade_ctx_hk.get_acc_list()
                    if ret != ft.RET_OK:
                        self._log_error("HK trade context health check failed")
                        return False
                except Exception:
                    # Ignore trade context errors if not critical
                    pass

            if self.us_access and self.trade_ctx_us:
                try:
                    # Simple health check for trade context
                    ret, _ = self.trade_ctx_us.get_acc_list()
                    if ret != ft.RET_OK:
                        self._log_error("US trade context health check failed")
                        return False
                except Exception:
                    # Ignore trade context errors if not critical
                    pass

            return True

        except Exception as e:
            self._log_error(f"Connection health check error: {e}")
            return False

    def _attempt_reconnection(self) -> None:
        """Attempt to reconnect to OpenD gateway."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self._log_error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached, giving up")
            return

        self._reconnect_attempts += 1
        self._log_info(f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}")

        try:
            # Close existing connections
            self._cleanup_connections()

            # Wait before reconnecting
            time.sleep(self._reconnect_interval)

            # Attempt reconnection
            if self.connect(self.last_settings):
                self._log_info("Reconnection successful")

                # Restore subscriptions if market data manager exists
                if self.market_data:
                    self.market_data.restore_subscriptions()

            else:
                self._log_error(f"Reconnection attempt {self._reconnect_attempts} failed")

        except Exception as e:
            self._log_error(f"Reconnection error: {e}")

    def _cleanup_connections(self) -> None:
        """Clean up existing connections without full close."""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                self.quote_ctx = None

            if self.trade_ctx_hk:
                self.trade_ctx_hk.close()
                self.trade_ctx_hk = None

            if self.trade_ctx_us:
                self.trade_ctx_us.close()
                self.trade_ctx_us = None

        except Exception as e:
            self._log_error(f"Connection cleanup error: {e}")

    def get_connection_health(self) -> dict[str, Any]:
        """
        Get detailed connection health information.

        Returns:
            Dictionary with health status and metrics
        """
        return {
            "connected": self.connected,
            "last_heartbeat": self._last_heartbeat,
            "reconnect_attempts": self._reconnect_attempts,
            "max_reconnect_attempts": self._max_reconnect_attempts,
            "health_monitor_running": self._health_monitor_running,
            "quote_context_healthy": self.quote_ctx is not None,
            "hk_trade_context_healthy": self.trade_ctx_hk is not None if self.hk_access else None,
            "us_trade_context_healthy": self.trade_ctx_us is not None if self.us_access else None,
            "time_since_heartbeat": time.time() - self._last_heartbeat if self._last_heartbeat > 0 else None,
        }

    def get_trade_context(self, market: str):
        """
        Get appropriate trade context for market.

        Args:
            market: Market identifier (HK, US, CN)

        Returns:
            Trade context for the market, or None if not available
        """
        if market == "HK" and self.trade_ctx_hk:
            return self.trade_ctx_hk
        if market == "US" and self.trade_ctx_us:
            return self.trade_ctx_us
        # CN market would need separate context when implemented
        return None

    def get_opend_status(self) -> dict[str, Any]:
        """
        Get OpenD gateway status information.

        Returns:
            Dictionary with connection status details
        """
        status = {
            "connected": self.connected,
            "quote_context": self.quote_ctx is not None,
            "hk_trade_context": self.trade_ctx_hk is not None,
            "us_trade_context": self.trade_ctx_us is not None,
            "market_access": {
                "hk": self.hk_access,
                "us": self.us_access,
                "cn": self.cn_access,
            },
            "paper_trading": self.paper_trading,
        }

        # Get OpenD gateway info if available
        if self.quote_ctx:
            try:
                ret, data = self.quote_ctx.get_global_state()
                if ret == ft.RET_OK:
                    status["global_state"] = data
            except Exception:
                pass  # Ignore errors for status check

        return status

    def _log_info(self, msg: str) -> None:
        """Log info message through adapter."""
        if hasattr(self, 'adapter') and self.adapter:
            self.adapter.write_log(msg)

    def _log_error(self, msg: str) -> None:
        """Log error message through adapter."""
        if hasattr(self, 'adapter') and self.adapter:
            self.adapter.write_log(f"ERROR: {msg}")

    def set_adapter(self, adapter) -> None:
        """Set adapter reference for logging."""
        self.adapter = adapter
