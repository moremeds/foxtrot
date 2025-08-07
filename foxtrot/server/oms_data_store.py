"""
Data storage functionality for Order Management System.
"""

from foxtrot.util.object import (
    AccountData,
    ContractData,
    OrderData,
    PositionData,
    QuoteData,
    TickData,
    TradeData,
)


class OmsDataStore:
    """
    Stores and manages trading data for OMS.
    """

    def __init__(self) -> None:
        """Initialize data store."""
        self.ticks: dict[str, TickData] = {}
        self.orders: dict[str, OrderData] = {}
        self.trades: dict[str, TradeData] = {}
        self.positions: dict[str, PositionData] = {}
        self.accounts: dict[str, AccountData] = {}
        self.contracts: dict[str, ContractData] = {}
        self.quotes: dict[str, QuoteData] = {}

        self.active_orders: dict[str, OrderData] = {}
        self.active_quotes: dict[str, QuoteData] = {}

    # Get single item methods
    def get_tick(self, vt_symbol: str) -> TickData | None:
        """Get latest market tick data by vt_symbol."""
        return self.ticks.get(vt_symbol, None)

    def get_order(self, vt_orderid: str) -> OrderData | None:
        """Get latest order data by vt_orderid."""
        return self.orders.get(vt_orderid, None)

    def get_trade(self, vt_tradeid: str) -> TradeData | None:
        """Get trade data by vt_tradeid."""
        return self.trades.get(vt_tradeid, None)

    def get_position(self, vt_positionid: str) -> PositionData | None:
        """Get latest position data by vt_positionid."""
        return self.positions.get(vt_positionid, None)

    def get_account(self, vt_accountid: str) -> AccountData | None:
        """Get latest account data by vt_accountid."""
        return self.accounts.get(vt_accountid, None)

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """Get contract data by vt_symbol."""
        return self.contracts.get(vt_symbol, None)

    def get_quote(self, vt_quoteid: str) -> QuoteData | None:
        """Get latest quote data by vt_orderid."""
        return self.quotes.get(vt_quoteid, None)

    # Get all items methods
    def get_all_ticks(self) -> list[TickData]:
        """Get all tick data."""
        return list(self.ticks.values())

    def get_all_orders(self) -> list[OrderData]:
        """Get all order data."""
        return list(self.orders.values())

    def get_all_trades(self) -> list[TradeData]:
        """Get all trade data."""
        return list(self.trades.values())

    def get_all_positions(self) -> list[PositionData]:
        """Get all position data."""
        return list(self.positions.values())

    def get_all_accounts(self) -> list[AccountData]:
        """Get all account data."""
        return list(self.accounts.values())

    def get_all_contracts(self) -> list[ContractData]:
        """Get all contract data."""
        return list(self.contracts.values())

    def get_all_quotes(self) -> list[QuoteData]:
        """Get all quote data."""
        return list(self.quotes.values())

    def get_all_active_orders(self) -> list[OrderData]:
        """Get all active orders."""
        return list(self.active_orders.values())

    def get_all_active_quotes(self) -> list[QuoteData]:
        """Get all active quotes."""
        return list(self.active_quotes.values())