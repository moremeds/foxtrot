"""
Unit tests for BinanceAccountManager.

Tests account information queries, position tracking,
and account state caching functionality.
"""

from unittest.mock import Mock
import pytest

from foxtrot.adapter.binance.account_manager import BinanceAccountManager
from foxtrot.util.constants import Exchange
from foxtrot.util.object import AccountData


class TestBinanceAccountManager:
    """Test cases for BinanceAccountManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_api_client = Mock()
        self.mock_api_client.adapter_name = "TEST_BINANCE"
        self.account_manager = BinanceAccountManager(self.mock_api_client)

    @pytest.mark.timeout(10)
    def test_initialization(self):
        """Test account manager initialization."""
        assert self.account_manager.api_client == self.mock_api_client
        assert self.account_manager._account_cache is None

    @pytest.mark.timeout(10)
    def test_query_account_success(self):
        """Test successful account query."""
        # Mock exchange with balance data
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            "USDT": {"total": 1000.0, "used": 100.0, "free": 900.0},
            "BTC": {"total": 0.5, "used": 0.1, "free": 0.4},
        }
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_account()

        # Verify account data
        assert result is not None
        assert isinstance(result, AccountData)
        assert result.accountid == "TEST_BINANCE"
        assert result.balance == 1000.0
        assert result.frozen == 100.0
        assert result.adapter_name == "TEST_BINANCE"

        # Verify data was cached
        assert self.account_manager._account_cache is not None

    @pytest.mark.timeout(10)
    def test_query_account_no_exchange(self):
        """Test account query when exchange is not connected."""
        self.mock_api_client.exchange = None

        result = self.account_manager.query_account()

        assert result is None
        assert self.account_manager._account_cache is None

    @pytest.mark.timeout(10)
    def test_query_account_empty_response(self):
        """Test account query with empty response."""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = None
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_account()

        assert result is None

    @pytest.mark.timeout(10)
    def test_query_account_exception(self):
        """Test account query handles exceptions."""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.side_effect = Exception("API error")
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_account()

        assert result is None
        self.mock_api_client._log_error.assert_called_with("Failed to query account: API error")

    @pytest.mark.timeout(10)
    def test_query_position_success(self):
        """Test successful position query."""
        # Mock exchange with balance data
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            "USDT": {"total": 1000.0, "used": 100.0, "free": 900.0},
            "BTC": {"total": 0.5, "used": 0.1, "free": 0.4},
            "ETH": {"total": 0.0, "used": 0.0, "free": 0.0},  # Zero balance, should be filtered
        }
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_position()

        # Verify positions (should only include non-zero balances)
        assert len(result) == 2

        # Check USDT position
        usdt_position = next((p for p in result if p.symbol.startswith("USDT")), None)
        assert usdt_position is not None
        assert usdt_position.volume == 1000.0
        assert usdt_position.frozen == 100.0
        assert usdt_position.exchange == Exchange.BINANCE

        # Check BTC position
        btc_position = next((p for p in result if p.symbol.startswith("BTC")), None)
        assert btc_position is not None
        assert btc_position.volume == 0.5
        assert btc_position.frozen == 0.1

    @pytest.mark.timeout(10)
    def test_query_position_no_exchange(self):
        """Test position query when exchange is not connected."""
        self.mock_api_client.exchange = None

        result = self.account_manager.query_position()

        assert result == []

    @pytest.mark.timeout(10)
    def test_query_position_empty_response(self):
        """Test position query with empty response."""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = None
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_position()

        assert result == []

    @pytest.mark.timeout(10)
    def test_query_position_exception(self):
        """Test position query handles exceptions."""
        mock_exchange = Mock()
        mock_exchange.fetch_balance.side_effect = Exception("API error")
        self.mock_api_client.exchange = mock_exchange

        result = self.account_manager.query_position()

        assert result == []
        self.mock_api_client._log_error.assert_called_with("Failed to query positions: API error")

    @pytest.mark.timeout(10)
    def test_get_cached_account(self):
        """Test getting cached account data."""
        # Initially no cache
        assert self.account_manager.get_cached_account() is None

        # Query account to populate cache
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            "USDT": {"total": 1000.0, "used": 100.0, "free": 900.0}
        }
        self.mock_api_client.exchange = mock_exchange

        self.account_manager.query_account()

        # Now cache should be available
        cached_data = self.account_manager.get_cached_account()
        assert cached_data is not None
        assert "USDT" in cached_data

    @pytest.mark.timeout(10)
    def test_clear_cache(self):
        """Test clearing cached account data."""
        # Populate cache first
        mock_exchange = Mock()
        mock_exchange.fetch_balance.return_value = {
            "USDT": {"total": 1000.0, "used": 100.0, "free": 900.0}
        }
        self.mock_api_client.exchange = mock_exchange

        self.account_manager.query_account()
        assert self.account_manager._account_cache is not None

        # Clear cache
        self.account_manager.clear_cache()
        assert self.account_manager._account_cache is None
