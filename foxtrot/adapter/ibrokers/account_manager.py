"""
Account and position management for Interactive Brokers.
"""
from copy import copy
from decimal import Decimal

from ibapi.contract import Contract

from foxtrot.util.constants import Direction, Exchange
from foxtrot.util.object import AccountData, PositionData

from .ib_mappings import ACCOUNTFIELD_IB2VT, EXCHANGE_IB2VT


class AccountManager:
    """Manages account data and position updates."""

    def __init__(self, adapter_name: str):
        """Initialize account manager."""
        self.adapter_name = adapter_name

        # Account storage
        self.accounts: dict[str, AccountData] = {}

        # Account name
        self.account: str = ""

    def set_account(self, accountsList: str, client, write_log_callback) -> None:
        """Set the trading account and request updates."""
        if not self.account:
            for account_code in accountsList.split(","):
                if account_code:
                    self.account = account_code

        write_log_callback(f"Currently used trading account: {self.account}")
        client.reqAccountUpdates(True, self.account)

    def process_account_value(self, key: str, val: str, currency: str,
                            accountName: str) -> None:
        """Process account value updates."""
        if not currency or key not in ACCOUNTFIELD_IB2VT:
            return

        accountid: str = f"{accountName}.{currency}"
        account: AccountData = self.accounts.get(accountid, None)
        if not account:
            account = AccountData(
                accountid=accountid,
                adapter_name=self.adapter_name
            )
            self.accounts[accountid] = account

        name: str = ACCOUNTFIELD_IB2VT[key]
        setattr(account, name, float(val))

    def process_portfolio_update(self, contract: Contract, position: Decimal,
                               marketPrice: float, marketValue: float,
                               averageCost: float, unrealizedPNL: float,
                               realizedPNL: float, accountName: str,
                               contract_manager, on_position_callback,
                               write_log_callback) -> None:
        """Process position updates."""
        if contract.exchange:
            exchange: Exchange = EXCHANGE_IB2VT.get(contract.exchange, None)
        elif contract.primaryExchange:
            exchange = EXCHANGE_IB2VT.get(contract.primaryExchange, None)
        else:
            exchange = Exchange.SMART   # Use smart routing by default

        if not exchange:
            msg: str = f"Unsupported exchange holding exists: {contract_manager.generate_symbol(contract)} {contract.exchange} {contract.primaryExchange}"
            write_log_callback(msg)
            return

        try:
            ib_size: int = int(contract.multiplier)
        except ValueError:
            ib_size = 1
        price = averageCost / ib_size

        pos: PositionData = PositionData(
            symbol=contract_manager.generate_symbol(contract),
            exchange=exchange,
            direction=Direction.NET,
            volume=float(position),
            price=price,
            pnl=unrealizedPNL,
            adapter_name=self.adapter_name,
        )
        on_position_callback(pos)

    def process_account_time(self, timeStamp: str, on_account_callback) -> None:
        """Process account update time and send account data."""
        for account in self.accounts.values():
            on_account_callback(copy(account))

    def get_account(self) -> str:
        """Get current trading account."""
        return self.account
