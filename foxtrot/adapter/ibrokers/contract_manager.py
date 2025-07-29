"""
Contract management and utility functions for Interactive Brokers.
"""
import shelve
from copy import copy
from datetime import datetime

from ibapi.contract import Contract, ContractDetails

from foxtrot.util.constants import Exchange, Product
from foxtrot.util.object import ContractData
from foxtrot.util.utility import get_file_path

from .ib_mappings import EXCHANGE_IB2VT, EXCHANGE_VT2IB, JOIN_SYMBOL, OPTION_IB2VT, PRODUCT_IB2VT


class ContractManager:
    """Manages contract data and IB contract utilities."""

    def __init__(self, adapter_name: str):
        """Initialize contract manager."""
        self.adapter_name = adapter_name

        # Contract storage
        self.contracts: dict[str, ContractData] = {}
        self.ib_contracts: dict[str, Contract] = {}

        # Data persistence
        self.data_filename = "ib_contract_data.db"
        self.data_filepath = str(get_file_path(self.data_filename))

        # Request tracking
        self.reqid_symbol_map: dict[int, str] = {}
        self.reqid_underlying_map: dict[int, Contract] = {}

    def process_contract_details(self, reqId: int, contractDetails: ContractDetails,
                               on_contract_callback, write_log_callback) -> None:
        """Process contract details from IB."""
        # Extract contract information
        ib_contract: Contract = contractDetails.contract

        # Handle the case where the contract multiplier is 0
        if not ib_contract.multiplier:
            ib_contract.multiplier = 1

        # For string-style symbols, get them from the cache
        if reqId in self.reqid_symbol_map:
            symbol: str = self.reqid_symbol_map[reqId]
        # Otherwise, use numeric-style symbols by default
        else:
            symbol = str(ib_contract.conId)

        # Filter out unsupported types
        product: Product = PRODUCT_IB2VT.get(ib_contract.secType, None)
        if not product:
            return

        # Generate the contract
        contract: ContractData = ContractData(
            symbol=symbol,
            exchange=EXCHANGE_IB2VT[ib_contract.exchange],
            name=contractDetails.longName,
            product=PRODUCT_IB2VT[ib_contract.secType],
            size=float(ib_contract.multiplier),
            pricetick=contractDetails.minTick,
            min_volume=contractDetails.minSize,
            net_position=True,
            history_data=True,
            stop_supported=True,
            adapter_name=self.adapter_name,
        )

        if contract.product == Product.OPTION:
            underlying_symbol: str = str(contractDetails.underConId)

            contract.option_portfolio = underlying_symbol + "_O"
            contract.option_type = OPTION_IB2VT.get(ib_contract.right, None)
            contract.option_strike = ib_contract.strike
            contract.option_index = str(ib_contract.strike)
            contract.option_expiry = datetime.strptime(ib_contract.lastTradeDateOrContractMonth, "%Y%m%d")
            contract.option_underlying = underlying_symbol + "_" + ib_contract.lastTradeDateOrContractMonth

        if contract.vt_symbol not in self.contracts:
            on_contract_callback(contract)

            self.contracts[contract.vt_symbol] = contract
            self.ib_contracts[contract.vt_symbol] = ib_contract

    def process_contract_details_end(self, reqId: int, write_log_callback) -> None:
        """Process end of contract details."""
        # Only process option queries
        underlying: Contract = self.reqid_underlying_map.get(reqId, None)
        if not underlying:
            return

        # Output log information
        symbol: str = self.generate_symbol(underlying)
        exchange: Exchange = EXCHANGE_IB2VT.get(underlying.exchange, Exchange.SMART)
        vt_symbol: str = f"{symbol}.{exchange.value}"

        write_log_callback(f"{vt_symbol} option chain query successful")

        # Save option contracts to a file
        self.save_contract_data()

    def load_contract_data(self, on_contract_callback, write_log_callback) -> None:
        """Load local contract data."""
        f = shelve.open(self.data_filepath)
        self.contracts = f.get("contracts", {})
        self.ib_contracts = f.get("ib_contracts", {})
        f.close()

        for contract in self.contracts.values():
            on_contract_callback(contract)

        write_log_callback("Successfully loaded local cached contract information")

    def save_contract_data(self) -> None:
        """Save contract data to a local file."""
        # Before saving, ensure that all contract data interface names are set to IB to avoid issues with other modules
        contracts: dict[str, ContractData] = {}
        for vt_symbol, contract in self.contracts.items():
            c: ContractData = copy(contract)
            c.adapter_name = "IB"
            contracts[vt_symbol] = c

        f = shelve.open(self.data_filepath)
        f["contracts"] = contracts
        f["ib_contracts"] = self.ib_contracts
        f.close()

    def generate_symbol(self, ib_contract: Contract) -> str:
        """Generate a contract symbol."""
        # Generate a string-style symbol
        fields: list = [ib_contract.symbol]

        if ib_contract.secType in ["FUT", "OPT", "FOP"]:
            fields.append(ib_contract.lastTradeDateOrContractMonth)

        if ib_contract.secType in ["OPT", "FOP"]:
            fields.append(ib_contract.right)
            fields.append(str(ib_contract.strike))
            fields.append(str(ib_contract.multiplier))

        fields.append(ib_contract.currency)
        fields.append(ib_contract.secType)

        symbol: str = JOIN_SYMBOL.join(fields)
        exchange: Exchange = EXCHANGE_IB2VT.get(ib_contract.exchange, Exchange.SMART)
        vt_symbol: str = f"{symbol}.{exchange.value}"

        # If the string-style symbol is not found in the contract information, use the numeric symbol
        if vt_symbol not in self.contracts:
            symbol = str(ib_contract.conId)

        return symbol

    def get_contract(self, vt_symbol: str) -> ContractData | None:
        """Get contract data by vt_symbol."""
        return self.contracts.get(vt_symbol)

    def get_ib_contract(self, vt_symbol: str) -> Contract | None:
        """Get IB contract by vt_symbol."""
        return self.ib_contracts.get(vt_symbol)


def generate_ib_contract(symbol: str, exchange: Exchange) -> Contract | None:
    """Generate an IB contract from symbol and exchange."""
    # String-style symbol
    if "-" in symbol:
        try:
            fields: list[str] = symbol.split(JOIN_SYMBOL)

            ib_contract: Contract = Contract()
            ib_contract.exchange = EXCHANGE_VT2IB[exchange]
            ib_contract.secType = fields[-1]
            ib_contract.currency = fields[-2]
            ib_contract.symbol = fields[0]

            if ib_contract.secType in ["FUT", "OPT", "FOP"]:
                ib_contract.lastTradeDateOrContractMonth = fields[1]

            if ib_contract.secType == "FUT":
                if len(fields) == 5:
                    ib_contract.multiplier = int(fields[2])

            if ib_contract.secType in ["OPT", "FOP"]:
                ib_contract.right = fields[2]
                ib_contract.strike = float(fields[3])
                ib_contract.multiplier = int(fields[4])
        except IndexError:
            ib_contract = None
    # Numeric-style symbol (ConId)
    else:
        if symbol.isdigit():
            ib_contract = Contract()
            ib_contract.exchange = EXCHANGE_VT2IB[exchange]
            ib_contract.conId = symbol
        else:
            ib_contract = None

    return ib_contract
