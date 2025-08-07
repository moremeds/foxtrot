"""
Order Management System (OMS) engine for trading platform.
"""

from foxtrot.core.event_engine import Event, EventEngine
from foxtrot.server.engine_manager import BaseEngine
from foxtrot.server.oms_data_store import OmsDataStore
from foxtrot.util.converter import OffsetConverter
from foxtrot.util.event_type import (
    EVENT_ACCOUNT,
    EVENT_CONTRACT,
    EVENT_ORDER,
    EVENT_POSITION,
    EVENT_QUOTE,
    EVENT_TICK,
    EVENT_TRADE,
)
from foxtrot.util.object import (
    AccountData,
    ContractData,
    OrderData,
    OrderRequest,
    PositionData,
    QuoteData,
    TickData,
    TradeData,
)


class OmsEngine(BaseEngine):
    """
    Provides order management system function.
    """

    def __init__(self, main_engine, event_engine: EventEngine) -> None:
        """"""
        super().__init__(main_engine, event_engine, "oms")

        self.data_store: OmsDataStore = OmsDataStore()
        self.offset_converters: dict[str, OffsetConverter] = {}

        # Expose data store collections for backward compatibility
        self.ticks = self.data_store.ticks
        self.orders = self.data_store.orders
        self.trades = self.data_store.trades
        self.positions = self.data_store.positions
        self.accounts = self.data_store.accounts
        self.contracts = self.data_store.contracts
        self.quotes = self.data_store.quotes
        self.active_orders = self.data_store.active_orders
        self.active_quotes = self.data_store.active_quotes

        self.register_event()

    def register_event(self) -> None:
        """"""
        self.event_engine.register(EVENT_TICK, self.process_tick_event)
        self.event_engine.register(EVENT_ORDER, self.process_order_event)
        self.event_engine.register(EVENT_TRADE, self.process_trade_event)
        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        self.event_engine.register(EVENT_ACCOUNT, self.process_account_event)
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        self.event_engine.register(EVENT_QUOTE, self.process_quote_event)

    def process_tick_event(self, event: Event) -> None:
        """"""
        tick: TickData = event.data
        self.data_store.ticks[tick.vt_symbol] = tick

    def process_order_event(self, event: Event) -> None:
        """"""
        order: OrderData = event.data
        self.data_store.orders[order.vt_orderid] = order

        # If order is active, then update data in dict.
        if order.is_active():
            self.data_store.active_orders[order.vt_orderid] = order
        # Otherwise, pop inactive order from in dict
        elif order.vt_orderid in self.data_store.active_orders:
            self.data_store.active_orders.pop(order.vt_orderid)

        # Update to offset converter
        converter: OffsetConverter | None = self.offset_converters.get(order.adapter_name, None)
        if converter:
            converter.update_order(order)

    def process_trade_event(self, event: Event) -> None:
        """"""
        trade: TradeData = event.data
        self.data_store.trades[trade.vt_tradeid] = trade

        # Update to offset converter
        converter: OffsetConverter | None = self.offset_converters.get(trade.adapter_name, None)
        if converter:
            converter.update_trade(trade)

    def process_position_event(self, event: Event) -> None:
        """"""
        position: PositionData = event.data
        self.data_store.positions[position.vt_positionid] = position

        # Update to offset converter
        converter: OffsetConverter | None = self.offset_converters.get(position.adapter_name, None)
        if converter:
            converter.update_position(position)

    def process_account_event(self, event: Event) -> None:
        """"""
        account: AccountData = event.data
        self.data_store.accounts[account.vt_accountid] = account

    def process_contract_event(self, event: Event) -> None:
        """"""
        contract: ContractData = event.data
        self.data_store.contracts[contract.vt_symbol] = contract

        # Initialize offset converter for each gateway
        if contract.adapter_name not in self.offset_converters:
            self.offset_converters[contract.adapter_name] = OffsetConverter(self)

    def process_quote_event(self, event: Event) -> None:
        """"""
        quote: QuoteData = event.data
        self.data_store.quotes[quote.vt_quoteid] = quote

        # If quote is active, then update data in dict.
        if quote.is_active():
            self.data_store.active_quotes[quote.vt_quoteid] = quote
        # Otherwise, pop inactive quote from in dict
        elif quote.vt_quoteid in self.data_store.active_quotes:
            self.data_store.active_quotes.pop(quote.vt_quoteid)

    # Delegate to data store for backward compatibility
    def get_tick(self, vt_symbol: str) -> TickData | None:
        """Get latest market tick data by vt_symbol."""
        return self.data_store.get_tick(vt_symbol)

    def get_order(self, vt_orderid: str) -> OrderData | None:
        """Get latest order data by vt_orderid."""
        return self.data_store.get_order(vt_orderid)

    def get_trade(self, vt_tradeid: str) -> TradeData | None:
        """Get trade data by vt_tradeid."""
        return self.data_store.get_trade(vt_tradeid)

    def get_position(self, vt_positionid: str) -> PositionData | None:
        """Get latest position data by vt_positionid."""
        return self.data_store.get_position(vt_positionid)

    def get_account(self, vt_accountid: str) -> AccountData | None:
        """Get latest account data by vt_accountid."""
        return self.data_store.get_account(vt_accountid)

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """Get contract data by vt_symbol."""
        return self.data_store.get_contract(vt_symbol)

    def get_quote(self, vt_quoteid: str) -> QuoteData | None:
        """Get latest quote data by vt_orderid."""
        return self.data_store.get_quote(vt_quoteid)

    def get_all_ticks(self) -> list[TickData]:
        """Get all tick data."""
        return self.data_store.get_all_ticks()

    def get_all_orders(self) -> list[OrderData]:
        """Get all order data."""
        return self.data_store.get_all_orders()

    def get_all_trades(self) -> list[TradeData]:
        """Get all trade data."""
        return self.data_store.get_all_trades()

    def get_all_positions(self) -> list[PositionData]:
        """Get all position data."""
        return self.data_store.get_all_positions()

    def get_all_accounts(self) -> list[AccountData]:
        """Get all account data."""
        return self.data_store.get_all_accounts()

    def get_all_contracts(self) -> list[ContractData]:
        """Get all contract data."""
        return self.data_store.get_all_contracts()

    def get_all_quotes(self) -> list[QuoteData]:
        """Get all quote data."""
        return self.data_store.get_all_quotes()

    def get_all_active_orders(self) -> list[OrderData]:
        """Get all active orders."""
        return self.data_store.get_all_active_orders()

    def get_all_active_quotes(self) -> list[QuoteData]:
        """Get all active quotes."""
        return self.data_store.get_all_active_quotes()

    def update_order_request(self, req: OrderRequest, vt_orderid: str, adapter_name: str) -> None:
        """Update order request to offset converter."""
        converter: OffsetConverter | None = self.offset_converters.get(adapter_name, None)
        if converter:
            converter.update_order_request(req, vt_orderid)

    def convert_order_request(
        self, req: OrderRequest, adapter_name: str, lock: bool, net: bool = False
    ) -> list[OrderRequest]:
        """Convert original order request according to given mode."""
        converter: OffsetConverter | None = self.offset_converters.get(adapter_name, None)
        if not converter:
            return [req]

        reqs: list[OrderRequest] = converter.convert_order_request(req, lock, net)
        return reqs

    def get_converter(self, adapter_name: str) -> OffsetConverter | None:
        """Get offset converter object of specific adapter."""
        return self.offset_converters.get(adapter_name, None)