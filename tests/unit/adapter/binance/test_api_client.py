"""
Unit tests for BinanceApiClient.

Tests the central coordinator to ensure it properly manages
CCXT exchange instances and coordinates manager interactions.
"""

from unittest.mock import Mock, patch
import pytest

from foxtrot.adapter.binance.api_client import BinanceApiClient
from foxtrot.core.event_engine import EventEngine


class TestBinanceApiClient:
    """Test cases for BinanceApiClient coordinator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.event_engine = Mock(spec=EventEngine)
        self.api_client = BinanceApiClient(self.event_engine, "TEST_BINANCE")

    def teardown_method(self):
        """Clean up test fixtures to prevent memory leaks."""
        # Close API client if it has resources
        if hasattr(self.api_client, "close"):
            try:
                self.api_client.close()
            except Exception:
                pass  # Ignore cleanup exceptions

        # Clear references to prevent memory leaks
        self.api_client = None
        self.event_engine = None

    @pytest.mark.timeout(10)
    def test_initialization(self):
        """Test API client initialization."""
        assert self.api_client.event_engine == self.event_engine
        assert self.api_client.adapter_name == "TEST_BINANCE"
        assert self.api_client.exchange is None
        assert self.api_client.connected is False

        # Managers should be None initially
        assert self.api_client.account_manager is None
        assert self.api_client.order_manager is None
        assert self.api_client.market_data is None
        assert self.api_client.historical_data is None
        assert self.api_client.contract_manager is None

    @patch("foxtrot.adapter.binance.api_client.BinanceApiClient.initialize_managers")
    @patch("ccxt.binance")
    @pytest.mark.timeout(10)
    def test_connect_success(self, mock_ccxt_binance, mock_initialize_managers):
        """Test successful connection to Binance API."""
        # Mock CCXT exchange
        mock_exchange = Mock()
        mock_exchange.load_markets.return_value = {"BTC/USDT": {}}
        mock_ccxt_binance.return_value = mock_exchange

        settings = {"API Key": "test_key", "Secret": "test_secret", "Sandbox": True}

        result = self.api_client.connect(settings)

        assert result is True
        assert self.api_client.connected is True
        assert self.api_client.exchange == mock_exchange

        # Verify CCXT exchange configuration
        mock_ccxt_binance.assert_called_once_with(
            {
                "apiKey": "test_key",
                "secret": "test_secret",
                "enableRateLimit": True,
            }
        )

        # Verify sandbox mode was set
        mock_exchange.set_sandbox_mode.assert_called_once_with(True)

        # Verify managers were initialized
        mock_initialize_managers.assert_called_once()
        mock_exchange.load_markets.assert_called_once()

    @pytest.mark.timeout(10)
    def test_connect_missing_credentials(self):
        """Test connection failure with missing credentials."""
        settings = {"API Key": "", "Secret": "test_secret", "Sandbox": True}

        result = self.api_client.connect(settings)

        assert result is False
        assert self.api_client.connected is False
        assert self.api_client.exchange is None

    @patch("ccxt.binance")
    @pytest.mark.timeout(10)
    def test_connect_ccxt_exception(self, mock_ccxt_binance):
        """Test connection failure due to CCXT exception."""
        mock_ccxt_binance.side_effect = Exception("Connection failed")

        settings = {"API Key": "test_key", "Secret": "test_secret", "Sandbox": True}

        result = self.api_client.connect(settings)

        assert result is False
        assert self.api_client.connected is False

    @patch("ccxt.binance")
    @pytest.mark.timeout(10)
    def test_connect_load_markets_failure(self, mock_ccxt_binance):
        """Test connection failure when load_markets returns empty."""
        mock_exchange = Mock()
        mock_exchange.load_markets.return_value = {}  # Empty markets
        mock_ccxt_binance.return_value = mock_exchange

        settings = {"API Key": "test_key", "Secret": "test_secret", "Sandbox": True}

        result = self.api_client.connect(settings)

        assert result is False
        assert self.api_client.connected is False

    @patch("foxtrot.adapter.binance.account_manager.BinanceAccountManager")
    @patch("foxtrot.adapter.binance.order_manager.BinanceOrderManager")
    @patch("foxtrot.adapter.binance.market_data.BinanceMarketData")
    @patch("foxtrot.adapter.binance.historical_data.BinanceHistoricalData")
    @patch("foxtrot.adapter.binance.contract_manager.BinanceContractManager")
    @pytest.mark.timeout(10)
    def test_initialize_managers(
        self,
        mock_contract_mgr_class,
        mock_historical_class,
        mock_market_data_class,
        mock_order_mgr_class,
        mock_account_mgr_class,
    ):
        """Test manager initialization."""
        # Create mock instances
        mock_account_mgr = Mock()
        mock_order_mgr = Mock()
        mock_market_data = Mock()
        mock_historical_data = Mock()
        mock_contract_mgr = Mock()

        # Configure mock classes to return mock instances
        mock_account_mgr_class.return_value = mock_account_mgr
        mock_order_mgr_class.return_value = mock_order_mgr
        mock_market_data_class.return_value = mock_market_data
        mock_historical_class.return_value = mock_historical_data
        mock_contract_mgr_class.return_value = mock_contract_mgr

        self.api_client.initialize_managers()

        # Verify all managers were created and assigned
        assert self.api_client.account_manager == mock_account_mgr
        assert self.api_client.order_manager == mock_order_mgr
        assert self.api_client.market_data == mock_market_data
        assert self.api_client.historical_data == mock_historical_data
        assert self.api_client.contract_manager == mock_contract_mgr

        # Verify managers were initialized with correct parameters
        mock_account_mgr_class.assert_called_once_with(self.api_client)
        mock_order_mgr_class.assert_called_once_with(self.api_client)
        mock_market_data_class.assert_called_once_with(self.api_client)
        mock_historical_class.assert_called_once_with(self.api_client)
        mock_contract_mgr_class.assert_called_once_with(self.api_client)

    @pytest.mark.timeout(10)
    def test_close_with_market_data(self):
        """Test close method with market data manager."""
        # Mock market data manager
        mock_market_data = Mock()
        self.api_client.market_data = mock_market_data

        # Mock exchange with close method
        mock_exchange = Mock()
        mock_exchange.close = Mock()
        self.api_client.exchange = mock_exchange
        self.api_client.connected = True

        self.api_client.close()

        # Verify market data was closed
        mock_market_data.close.assert_called_once()

        # Verify exchange was closed
        mock_exchange.close.assert_called_once()

        # Verify connection state was reset
        assert self.api_client.connected is False

    @pytest.mark.timeout(10)
    def test_close_without_managers(self):
        """Test close method without managers."""
        # Mock exchange without close method
        mock_exchange = Mock()
        del mock_exchange.close  # Remove close method
        self.api_client.exchange = mock_exchange
        self.api_client.connected = True

        # Should not raise exception
        self.api_client.close()
        assert self.api_client.connected is False

    @pytest.mark.timeout(10)
    def test_close_with_exception(self):
        """Test close method handles exceptions gracefully."""
        mock_market_data = Mock()
        mock_market_data.close.side_effect = Exception("Close failed")
        self.api_client.market_data = mock_market_data
        self.api_client.connected = True

        # Should not raise exception
        self.api_client.close()
        assert self.api_client.connected is False

    @pytest.mark.timeout(10)
    def test_log_info(self):
        """Test info logging method."""
        with patch("builtins.print") as mock_print:
            self.api_client._log_info("Test message")
            mock_print.assert_called_once_with("[TEST_BINANCE] INFO: Test message")

    @pytest.mark.timeout(10)
    def test_log_error(self):
        """Test error logging method."""
        with patch("builtins.print") as mock_print:
            self.api_client._log_error("Test error")
            mock_print.assert_called_once_with("[TEST_BINANCE] ERROR: Test error")
