"""
Futu account manager for account and position queries.

This module handles account balance and position queries across multiple markets.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import AccountData, PositionData
import futu as ft

from .futu_mappings import convert_futu_to_vt_symbol, get_futu_trd_market

if TYPE_CHECKING:
    from .api_client import FutuApiClient


class FutuAccountManager:
    """
    Account and position management for Futu OpenD gateway.

    Handles account balance queries and position tracking across
    multiple markets (HK, US, CN) with multi-currency support.
    """

    def __init__(self, api_client: "FutuApiClient"):
        """Initialize the account manager."""
        self.api_client = api_client

    def query_account(self) -> None:
        """Query account information via SDK for all accessible markets."""
        try:
            # Query account info for each accessible market
            markets = []
            if self.api_client.hk_access:
                markets.append("HK")
            if self.api_client.us_access:
                markets.append("US")
            if self.api_client.cn_access:
                markets.append("CN")

            for market in markets:
                self._query_market_account(market)

        except Exception as e:
            self.api_client._log_error(f"Account query error: {e}")

    def _query_market_account(self, market: str) -> None:
        """
        Query account information for specific market.

        Args:
            market: Market identifier (HK, US, CN)
        """
        try:
            # Get appropriate trade context
            trade_ctx = self.api_client.get_trade_context(market)
            if not trade_ctx:
                self.api_client._log_error(f"No trade context for account query: {market}")
                return

            # Query account info
            trd_env = ft.TrdEnv.SIMULATE if self.api_client.paper_trading else ft.TrdEnv.REAL
            trd_market = get_futu_trd_market(market)

            ret, data = trade_ctx.accinfo_query(
                trd_env=trd_env,
                trd_market=trd_market
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Account query failed for {market}: {data}")
                return

            # Process account data
            if isinstance(data, list):
                for acc_data in data:
                    self._process_account_data(market, acc_data)
            else:
                self._process_account_data(market, data)

        except Exception as e:
            self.api_client._log_error(f"Market account query error for {market}: {e}")

    def _process_account_data(self, market: str, acc_data: dict) -> None:
        """
        Process and fire account data event.

        Args:
            market: Market identifier
            acc_data: Account data from SDK
        """
        try:
            account = AccountData(
                accountid=f"FUTU.{market}.{acc_data.get('acc_id', '')}",
                balance=float(acc_data.get("total_assets", 0)),
                frozen=float(acc_data.get("frozen_cash", 0)),
                available=float(acc_data.get("avl_withdrawal_cash", 0)),
                commission=float(acc_data.get("total_fee", 0)),
                margin=float(acc_data.get("margin_call_req", 0)),
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )

            # Fire account event
            self.api_client.adapter.on_account(account)

        except Exception as e:
            self.api_client._log_error(f"Account data processing error: {e}")

    def query_position(self) -> None:
        """Query position information via SDK for all accessible markets."""
        try:
            # Query positions for each accessible market
            markets = []
            if self.api_client.hk_access:
                markets.append("HK")
            if self.api_client.us_access:
                markets.append("US")
            if self.api_client.cn_access:
                markets.append("CN")

            for market in markets:
                self._query_market_position(market)

        except Exception as e:
            self.api_client._log_error(f"Position query error: {e}")

    def _query_market_position(self, market: str) -> None:
        """
        Query position information for specific market.

        Args:
            market: Market identifier (HK, US, CN)
        """
        try:
            # Get appropriate trade context
            trade_ctx = self.api_client.get_trade_context(market)
            if not trade_ctx:
                self.api_client._log_error(f"No trade context for position query: {market}")
                return

            # Query positions
            trd_env = ft.TrdEnv.SIMULATE if self.api_client.paper_trading else ft.TrdEnv.REAL
            trd_market = get_futu_trd_market(market)

            ret, data = trade_ctx.position_list_query(
                trd_env=trd_env,
                trd_market=trd_market
            )

            if ret != ft.RET_OK:
                self.api_client._log_error(f"Position query failed for {market}: {data}")
                return

            # Process position data
            if isinstance(data, list):
                for pos_data in data:
                    self._process_position_data(market, pos_data)
            else:
                self._process_position_data(market, data)

        except Exception as e:
            self.api_client._log_error(f"Market position query error for {market}: {e}")

    def _process_position_data(self, market: str, pos_data: dict) -> None:
        """
        Process and fire position data event.

        Args:
            market: Market identifier
            pos_data: Position data from SDK
        """
        try:
            # Convert to VT symbol
            code = pos_data.get("code", "")
            if not code:
                return

            vt_symbol = convert_futu_to_vt_symbol(market, code)
            symbol, exchange_str = vt_symbol.split(".")

            # Determine position direction
            qty = float(pos_data.get("qty", 0))
            if qty == 0:
                return  # Skip zero positions

            direction = Direction.LONG if qty > 0 else Direction.SHORT

            position = PositionData(
                symbol=symbol,
                exchange=Exchange(exchange_str),
                direction=direction,
                volume=abs(qty),
                frozen=float(pos_data.get("frozen_qty", 0)),
                price=float(pos_data.get("cost_price", 0)),
                pnl=float(pos_data.get("unrealized_pl", 0)),
                yd_volume=float(pos_data.get("yesterday_qty", 0)),
                datetime=datetime.now(),
                adapter_name=self.api_client.adapter_name,
            )

            # Fire position event
            self.api_client.adapter.on_position(position)

        except Exception as e:
            self.api_client._log_error(f"Position data processing error: {e}")
