"""
Unit tests for FutuAccountManager.

This module tests account and position queries across multiple markets.
"""

from datetime import datetime
import unittest
from unittest.mock import MagicMock
import pytest

import pandas as pd

from foxtrot.adapter.futu.account_manager import FutuAccountManager
from foxtrot.adapter.futu.api_client import FutuApiClient
from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import AccountData, PositionData

from .mock_futu_sdk import RET_ERROR, RET_OK, TrdEnv, TrdMarket


class TestFutuAccountManager(unittest.TestCase):
    """Test cases for FutuAccountManager."""

    def setUp(self) -> None:
        """Set up test environment."""

        # Create mock API client
        self.api_client = MagicMock(spec=FutuApiClient)
        self.api_client.adapter_name = "FUTU"
        self.api_client.paper_trading = True
        self.api_client.hk_access = True
        self.api_client.us_access = True
        self.api_client.cn_access = False

        # Create MagicMock trade contexts instead of using MockFutuTestCase ones
        self.mock_hk_trade_ctx = MagicMock()
        self.mock_us_trade_ctx = MagicMock()

        self.api_client.trade_ctx_hk = self.mock_hk_trade_ctx
        self.api_client.trade_ctx_us = self.mock_us_trade_ctx
        self.mock_hk_trade_ctx.accinfo_query = MagicMock()
        self.mock_us_trade_ctx.accinfo_query = MagicMock()
        self.mock_hk_trade_ctx.position_list_query = MagicMock()
        self.mock_us_trade_ctx.position_list_query = MagicMock()

        # Mock adapter for callbacks
        self.mock_adapter = MagicMock()
        self.api_client.adapter = self.mock_adapter

        # Mock get_trade_context method
        def mock_get_trade_context(market: str):
            if market == "HK":
                return self.mock_hk_trade_ctx
            if market == "US":
                return self.mock_us_trade_ctx
            return None

        self.api_client.get_trade_context = mock_get_trade_context

        # Mock _log_error and _log_info methods
        self.api_client._log_error = MagicMock()
        self.api_client._log_info = MagicMock()

        # Create account manager
        self.account_manager = FutuAccountManager(self.api_client)

    def tearDown(self) -> None:
        """Clean up test environment."""

    @pytest.mark.timeout(10)
    def test_initialization(self) -> None:
        """Test account manager initialization."""
        self.assertEqual(self.account_manager.api_client, self.api_client)

    @pytest.mark.timeout(10)
    def test_query_account_all_markets(self) -> None:
        """Test account query for all accessible markets."""
        # Mock account data responses
        hk_account_data = {
            "acc_id": "HK123456",
            "total_assets": 1000000.0,
            "frozen_cash": 50000.0,
            "avl_withdrawal_cash": 950000.0,
            "total_fee": 100.0,
            "margin_call_req": 0.0,
        }

        us_account_data = {
            "acc_id": "US123456",
            "total_assets": 500000.0,
            "frozen_cash": 25000.0,
            "avl_withdrawal_cash": 475000.0,
            "total_fee": 50.0,
            "margin_call_req": 0.0,
        }

        # Mock trade context responses
        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([hk_account_data]))
        self.mock_us_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([us_account_data]))

        # Query accounts
        self.account_manager.query_account()

        # Verify both markets were queried
        self.mock_hk_trade_ctx.accinfo_query.assert_called_once_with(
            trd_env=TrdEnv.SIMULATE,
            trd_market=TrdMarket.HK
        )
        self.mock_us_trade_ctx.accinfo_query.assert_called_once_with(
            trd_env=TrdEnv.SIMULATE,
            trd_market=TrdMarket.US
        )

        # Verify adapter callbacks were called twice (HK + US)
        self.assertEqual(self.mock_adapter.on_account.call_count, 2)

    @pytest.mark.timeout(10)
    def test_query_account_single_market(self) -> None:
        """Test account query for single market."""
        # Disable US access
        self.api_client.us_access = False

        # Mock HK account data
        hk_account_data = {
            "acc_id": "HK123456",
            "total_assets": 1000000.0,
            "frozen_cash": 50000.0,
            "avl_withdrawal_cash": 950000.0,
            "total_fee": 100.0,
            "margin_call_req": 0.0,
        }

        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([hk_account_data]))

        # Query accounts
        self.account_manager.query_account()

        # Verify only HK was queried
        self.mock_hk_trade_ctx.accinfo_query.assert_called_once()
        self.mock_us_trade_ctx.accinfo_query.assert_not_called()

        # Verify single callback
        self.assertEqual(self.mock_adapter.on_account.call_count, 1)

    @pytest.mark.timeout(10)
    def test_account_data_processing(self) -> None:
        """Test account data processing and conversion."""
        account_data = {
            "acc_id": "HK123456",
            "total_assets": 1000000.0,
            "frozen_cash": 50000.0,
            "avl_withdrawal_cash": 950000.0,
            "total_fee": 100.0,
            "margin_call_req": 5000.0,
        }

        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([account_data]))

        # Query account
        self.account_manager.query_account()

        # Verify callback was called with correct AccountData
        self.mock_adapter.on_account.assert_called_once()
        call_args = self.mock_adapter.on_account.call_args[0][0]

        self.assertIsInstance(call_args, AccountData)
        self.assertEqual(call_args.accountid, "FUTU.HK.HK123456")
        self.assertEqual(call_args.balance, 1000000.0)
        self.assertEqual(call_args.frozen, 50000.0)
        self.assertEqual(call_args.available, 950000.0)  # Calculated as balance - frozen
        self.assertEqual(call_args.adapter_name, "FUTU")

    @pytest.mark.timeout(10)
    def test_account_query_error_handling(self) -> None:
        """Test account query error handling."""
        # Mock SDK error
        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_ERROR, "Connection failed")

        # Query account
        self.account_manager.query_account()

        # Verify error was logged
        self.api_client._log_error.assert_called()

        # Verify no callback was made due to error
        self.mock_adapter.on_account.assert_not_called()

    @pytest.mark.timeout(10)
    def test_query_position_all_markets(self) -> None:
        """Test position query for all accessible markets."""
        # Mock position data
        hk_positions = [
            {
                "code": "HK.00700",
                "qty": 1000,
                "frozen_qty": 0,
                "cost_price": 450.0,
                "unrealized_pl": 5000.0,
                "yesterday_qty": 1000,
            }
        ]

        us_positions = [
            {
                "code": "US.AAPL",
                "qty": 100,
                "frozen_qty": 0,
                "cost_price": 150.0,
                "unrealized_pl": 500.0,
                "yesterday_qty": 100,
            }
        ]

        # Mock trade context responses
        self.mock_hk_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame(hk_positions))
        self.mock_us_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame(us_positions))

        # Query positions
        self.account_manager.query_position()

        # Verify both markets were queried
        self.mock_hk_trade_ctx.position_list_query.assert_called_once_with(
            trd_env=TrdEnv.SIMULATE,
            trd_market=TrdMarket.HK
        )
        self.mock_us_trade_ctx.position_list_query.assert_called_once_with(
            trd_env=TrdEnv.SIMULATE,
            trd_market=TrdMarket.US
        )

        # Verify adapter callbacks were called twice (HK + US)
        self.assertEqual(self.mock_adapter.on_position.call_count, 2)

    @pytest.mark.timeout(10)
    def test_position_data_processing(self) -> None:
        """Test position data processing and conversion."""
        position_data = {
            "code": "HK.00700",
            "qty": 1000,
            "frozen_qty": 100,
            "cost_price": 450.0,
            "unrealized_pl": 5000.0,
            "yesterday_qty": 900,
        }

        self.mock_hk_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame([position_data]))

        # Query positions
        self.account_manager.query_position()

        # Verify callback was called with correct PositionData
        self.mock_adapter.on_position.assert_called_once()
        call_args = self.mock_adapter.on_position.call_args[0][0]

        self.assertIsInstance(call_args, PositionData)
        self.assertEqual(call_args.symbol, "0700")
        self.assertEqual(call_args.exchange, Exchange.SEHK)
        self.assertEqual(call_args.direction, Direction.LONG)
        self.assertEqual(call_args.volume, 1000.0)
        self.assertEqual(call_args.frozen, 100.0)
        self.assertEqual(call_args.price, 450.0)
        self.assertEqual(call_args.pnl, 5000.0)
        self.assertEqual(call_args.yd_volume, 900.0)
        self.assertEqual(call_args.adapter_name, "FUTU")

    @pytest.mark.timeout(10)
    def test_short_position_processing(self) -> None:
        """Test short position data processing."""
        position_data = {
            "code": "US.AAPL",
            "qty": -100,  # Short position
            "frozen_qty": 0,
            "cost_price": 150.0,
            "unrealized_pl": -500.0,
            "yesterday_qty": -100,
        }

        self.mock_us_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame([position_data]))

        # Query positions
        self.account_manager.query_position()

        # Verify short position handling
        self.mock_adapter.on_position.assert_called_once()
        call_args = self.mock_adapter.on_position.call_args[0][0]
        self.assertEqual(call_args.direction, Direction.SHORT)
        self.assertEqual(call_args.volume, 100.0)  # Absolute value

    @pytest.mark.timeout(10)
    def test_zero_position_filtering(self) -> None:
        """Test that zero positions are filtered out."""
        position_data = {
            "code": "HK.00700",
            "qty": 0,  # Zero position
            "frozen_qty": 0,
            "cost_price": 450.0,
            "unrealized_pl": 0.0,
            "yesterday_qty": 0,
        }

        self.mock_hk_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame([position_data]))

        # Query positions
        self.account_manager.query_position()

        # Verify no callback was made for zero position
        self.mock_adapter.on_position.assert_not_called()

    @pytest.mark.timeout(10)
    def test_position_query_error_handling(self) -> None:
        """Test position query error handling."""
        # Mock SDK error
        self.mock_hk_trade_ctx.position_list_query.return_value = (RET_ERROR, "Connection failed")

        # Query positions
        self.account_manager.query_position()

        # Verify error was logged
        self.api_client._log_error.assert_called()

        # Verify no callback was made due to error
        self.mock_adapter.on_position.assert_not_called()

    @pytest.mark.timeout(10)
    def test_no_trade_context_handling(self) -> None:
        """Test handling when trade context is not available."""
        # Mock get_trade_context to return None
        self.api_client.get_trade_context = MagicMock(return_value=None)

        # Query account and position
        self.account_manager.query_account()
        self.account_manager.query_position()

        # Verify error was logged twice (account + position)
        self.assertEqual(self.api_client._log_error.call_count, 4)

        # Verify no callbacks were made
        self.mock_adapter.on_account.assert_not_called()
        self.mock_adapter.on_position.assert_not_called()

    @pytest.mark.timeout(10)
    def test_real_trading_environment(self) -> None:
        """Test queries in real trading environment."""
        # Set real trading mode
        self.api_client.paper_trading = False

        account_data = {"acc_id": "HK123456", "total_assets": 1000000.0}
        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([account_data]))

        # Query account
        self.account_manager.query_account()

        # Verify real trading environment was used
        self.mock_hk_trade_ctx.accinfo_query.assert_called_once_with(
            trd_env=TrdEnv.REAL,
            trd_market=TrdMarket.HK
        )

    @pytest.mark.timeout(10)
    def test_multiple_positions_processing(self) -> None:
        """Test processing multiple positions in one response."""
        positions_data = [
            {
                "code": "HK.00700",
                "qty": 1000,
                "frozen_qty": 0,
                "cost_price": 450.0,
                "unrealized_pl": 5000.0,
                "yesterday_qty": 1000,
            },
            {
                "code": "HK.00005",
                "qty": 500,
                "frozen_qty": 0,
                "cost_price": 65.0,
                "unrealized_pl": -1000.0,
                "yesterday_qty": 500,
            }
        ]

        self.mock_hk_trade_ctx.position_list_query.return_value = (RET_OK, pd.DataFrame(positions_data))

        # Query positions
        self.account_manager.query_position()

        # Verify both positions were processed
        self.assertEqual(self.mock_adapter.on_position.call_count, 2)

    @pytest.mark.timeout(10)
    def test_exception_handling_in_processing(self) -> None:
        """Test exception handling in data processing methods."""
        # Mock adapter to raise exception
        self.mock_adapter.on_account.side_effect = Exception("Callback error")

        account_data = {"acc_id": "HK123456", "total_assets": 1000000.0}
        self.mock_hk_trade_ctx.accinfo_query.return_value = (RET_OK, pd.DataFrame([account_data]))

        # Query account (should not crash)
        self.account_manager.query_account()

        # Verify error was logged
        self.api_client._log_error.assert_called()


if __name__ == '__main__':
    unittest.main()
