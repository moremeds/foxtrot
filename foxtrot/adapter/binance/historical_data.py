"""
Binance Historical Data Manager - Handles historical market data queries.

This module manages historical price data queries including OHLCV data
for specified symbols and timeframes.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from foxtrot.util.object import BarData, HistoryRequest
from foxtrot.util.constants import Exchange, Interval
# datetime import removed - using datetime.now() directly

if TYPE_CHECKING:
    from .api_client import BinanceApiClient


class BinanceHistoricalData:
    """
    Manager for Binance historical data operations.
    
    Handles historical OHLCV data queries with caching and rate limiting.
    """

    def __init__(self, api_client: "BinanceApiClient"):
        """Initialize the historical data manager."""
        self.api_client = api_client
        
    def query_history(self, req: HistoryRequest) -> List[BarData]:
        """
        Query historical bar data.
        
        Args:
            req: History request object
            
        Returns:
            List of BarData objects
        """
        bars = []
        
        try:
            if not self.api_client.exchange:
                return bars
                
            # Convert symbol format
            ccxt_symbol = self._convert_symbol_to_ccxt(req.symbol)
            if not ccxt_symbol:
                self.api_client._log_error(f"Invalid symbol: {req.symbol}")
                return bars
                
            # Convert interval format
            timeframe = self._convert_interval_to_ccxt(req.interval)
            if not timeframe:
                self.api_client._log_error(f"Invalid interval: {req.interval}")
                return bars
                
            # Calculate time range
            since = None
            if req.start:
                since = int(req.start.timestamp() * 1000)  # Convert to milliseconds
                
            # Fetch OHLCV data
            ohlcv_data = self.api_client.exchange.fetch_ohlcv(
                ccxt_symbol, 
                timeframe, 
                since=since,
                limit=1000  # Binance limit
            )
            
            if not ohlcv_data:
                return bars
                
            # Convert to BarData objects
            for ohlcv in ohlcv_data:
                timestamp, open_price, high_price, low_price, close_price, volume = ohlcv
                
                # Convert timestamp to datetime
                dt = datetime.fromtimestamp(timestamp / 1000)
                
                # Filter by end time if specified
                if req.end and dt > req.end:
                    break
                    
                bar = BarData(
                    adapter_name=self.api_client.adapter_name,
                    symbol=req.symbol,
                    exchange=Exchange.BINANCE,
                    datetime=dt,
                    interval=req.interval,
                    volume=volume,
                    turnover=volume * close_price,  # Approximate turnover
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    open_interest=0  # Not available for spot trading
                )
                bars.append(bar)
                
            self.api_client._log_info(f"Retrieved {len(bars)} bars for {req.symbol}")
            
        except Exception as e:
            self.api_client._log_error(f"Failed to query history for {req.symbol}: {str(e)}")
            
        return bars
        
    def _convert_symbol_to_ccxt(self, vt_symbol: str) -> str:
        """
        Convert VT symbol format to CCXT format.
        
        Args:
            vt_symbol: Symbol in VT format (e.g., "BTCUSDT.BINANCE")
            
        Returns:
            Symbol in CCXT format (e.g., "BTC/USDT")
        """
        try:
            symbol = vt_symbol.split('.')[0]
            
            # Validate symbol format
            if len(symbol) < 4:
                return ""
                
            # Convert BTCUSDT to BTC/USDT format
            if symbol.endswith('USDT') and len(symbol) > 4:
                base = symbol[:-4]
                return f"{base}/USDT"
            elif symbol.endswith('BTC') and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/BTC"
            elif symbol.endswith('ETH') and len(symbol) > 3:
                base = symbol[:-3]
                return f"{base}/ETH"
            else:
                # Invalid symbol format
                return ""
        except Exception:
            return ""
            
    def _convert_interval_to_ccxt(self, interval: Interval) -> str:
        """
        Convert VT interval to CCXT timeframe format.
        
        Args:
            interval: VT interval enum
            
        Returns:
            CCXT timeframe string
        """
        interval_map = {
            Interval.MINUTE: "1m",
            Interval.HOUR: "1h",
            Interval.DAILY: "1d",
            Interval.WEEKLY: "1w",
        }
        return interval_map.get(interval, "1m")