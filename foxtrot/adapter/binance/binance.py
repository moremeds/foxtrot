"""
Binance adapter facade - Clean interface implementing BaseAdapter.

This module provides a streamlined facade that delegates all operations
to the BinanceApiClient and its specialized managers.
"""

from typing import Dict, List, Any

from foxtrot.adapter.base_adapter import BaseAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.object import (
    AccountData,
    BarData,
    CancelRequest,
    ContractData,
    HistoryRequest,
    OrderData,
    OrderRequest,
    PositionData,
    SubscribeRequest,
    TickData,
    TradeData,
)

from .api_client import BinanceApiClient


class BinanceAdapter(BaseAdapter):
    """
    Binance trading adapter facade.
    
    This adapter provides a clean BaseAdapter interface while delegating
    all operations to the modular BinanceApiClient system.
    """

    default_name: str = "BINANCE"

    default_setting: Dict[str, Any] = {
        "API Key": "",
        "Secret": "",
        "Sandbox": False,
        "Proxy Host": "",
        "Proxy Port": 0,
    }

    exchanges: List[Exchange] = [Exchange.BINANCE]

    def __init__(self, event_engine: EventEngine, adapter_name: str) -> None:
        """Initialize the Binance adapter."""
        super().__init__(event_engine=event_engine, adapter_name=adapter_name)
        
        # Create the API client that coordinates all operations
        self.api_client = BinanceApiClient(event_engine, adapter_name)

    def connect(self, setting: Dict[str, Any]) -> bool:
        """
        Connect to Binance API.
        
        Args:
            setting: Dictionary containing connection settings
            
        Returns:
            True if connection successful, False otherwise
        """
        success = self.api_client.connect(setting)
        if success:
            # Load and publish contracts to MainEngine OMS
            self._load_all_contracts()
            
            # Query initial account and position data
            self.query_account()
            self.query_position()
            
        return success

    def close(self) -> None:
        """Close connection and cleanup resources."""
        self.api_client.close()

    def subscribe(self, req: SubscribeRequest) -> bool:
        """
        Subscribe to market data.
        
        Args:
            req: Subscription request
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self.api_client.market_data:
            return False
        return self.api_client.market_data.subscribe(req)

    def send_order(self, req: OrderRequest) -> str:
        """
        Send an order.
        
        Args:
            req: Order request
            
        Returns:
            Local order ID if successful, empty string otherwise
        """
        if not self.api_client.order_manager:
            return ""
        return self.api_client.order_manager.send_order(req)

    def cancel_order(self, req: CancelRequest) -> bool:
        """
        Cancel an order.
        
        Args:
            req: Cancel request
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.api_client.order_manager:
            return False
        return self.api_client.order_manager.cancel_order(req)

    def query_account(self) -> None:
        """Query account information."""
        if not self.api_client.account_manager:
            return
        
        account_data = self.api_client.account_manager.query_account()
        if account_data:
            self.on_account(account_data)

    def query_position(self) -> None:
        """Query position information."""
        if not self.api_client.account_manager:
            return
            
        positions = self.api_client.account_manager.query_position()
        for position in positions:
            self.on_position(position)

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        """
        Query historical data.
        
        Args:
            req: History request
            
        Returns:
            List of historical bar data
        """
        if not self.api_client.historical_data:
            return []
        return self.api_client.historical_data.query_history(req)

    def query_contract(self, symbol: str) -> ContractData:
        """
        Query contract information.
        
        Args:
            symbol: Symbol to query
            
        Returns:
            Contract data if found, None otherwise
        """
        if not self.api_client.contract_manager:
            return None
        return self.api_client.contract_manager.query_contract(symbol)

    def get_available_contracts(self) -> List[ContractData]:
        """
        Get all available contracts.
        
        Returns:
            List of available contracts
        """
        if not self.api_client.contract_manager:
            return []
        return self.api_client.contract_manager.get_available_contracts()

    @property
    def connected(self) -> bool:
        """Check if adapter is connected."""
        return self.api_client.connected
    
    def _load_all_contracts(self) -> None:
        """Load all available contracts and publish them to MainEngine OMS."""
        if not self.api_client.contract_manager:
            return
            
        try:
            # Force load markets if not already loaded
            if not self.api_client.contract_manager._markets_loaded:
                self.api_client.contract_manager._load_markets()
            
            # Publish all contracts to MainEngine OMS via events
            for contract in self.api_client.contract_manager._contracts.values():
                # Create a copy to ensure immutability as required by BaseAdapter
                contract_copy = ContractData(
                    symbol=contract.symbol,
                    exchange=contract.exchange,
                    name=contract.name,
                    product=contract.product,
                    size=contract.size,
                    pricetick=contract.pricetick,
                    min_volume=contract.min_volume,
                    stop_supported=contract.stop_supported,
                    net_position=contract.net_position,
                    history_data=contract.history_data,
                    adapter_name=contract.adapter_name
                )
                self.on_contract(contract_copy)
                
            self.write_log(f"Loaded {len(self.api_client.contract_manager._contracts)} contracts")
            
        except Exception as e:
            self.write_log(f"Failed to load contracts: {str(e)}")