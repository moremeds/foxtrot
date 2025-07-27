#!/usr/bin/env python3
"""Manual functional test for Binance adapter."""

import sys
sys.path.insert(0, '/home/ubuntu/projects/foxtrot')

from unittest.mock import Mock
from foxtrot.adapter.binance import BinanceAdapter
from foxtrot.util.constants import Exchange, Status, Direction, OrderType

def test_adapter_creation():
    """Test basic adapter instantiation."""
    print("🧪 Testing adapter creation...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test_binance")
    
    assert adapter.default_name == "BINANCE"
    assert Exchange.BINANCE in adapter.exchanges
    assert adapter.connected == False
    assert adapter.ccxt_exchange is None
    print("✅ Adapter creation test passed")

def test_mappings():
    """Test data conversion mappings."""
    print("🧪 Testing conversion mappings...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    
    # Test status mappings
    assert adapter.STATUS_CCXT2VT["open"] == Status.NOTTRADED
    assert adapter.STATUS_CCXT2VT["closed"] == Status.ALLTRADED
    assert adapter.STATUS_VT2CCXT[Status.ALLTRADED] == "closed"
    
    # Test order type mappings
    assert adapter.ORDERTYPE_VT2CCXT[OrderType.LIMIT] == "limit"
    assert adapter.ORDERTYPE_CCXT2VT["market"] == OrderType.MARKET
    
    # Test direction mappings
    assert adapter.DIRECTION_VT2CCXT[Direction.LONG] == "buy"
    assert adapter.DIRECTION_CCXT2VT["sell"] == Direction.SHORT
    
    print("✅ Mapping tests passed")

def test_symbol_conversion():
    """Test symbol format conversion."""
    print("🧪 Testing symbol conversion...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    
    # Test VT to CCXT conversion
    vt_symbol = "BTC.BINANCE"
    ccxt_symbol = adapter._convert_symbol_to_ccxt(vt_symbol)
    assert ccxt_symbol == "BTC/USDT"
    
    # Test CCXT to VT conversion
    ccxt_symbol = "ETH/USDT"
    vt_symbol = adapter._convert_symbol_from_ccxt(ccxt_symbol)
    assert vt_symbol == "ETH.BINANCE"
    
    print("✅ Symbol conversion tests passed")

def test_interval_conversion():
    """Test interval to timeframe conversion."""
    print("🧪 Testing interval conversion...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    
    assert adapter._convert_interval_to_ccxt_timeframe(1) == "1m"
    assert adapter._convert_interval_to_ccxt_timeframe(60) == "1h"
    assert adapter._convert_interval_to_ccxt_timeframe(1440) == "1d"
    assert adapter._convert_interval_to_ccxt_timeframe(999) == "1h"  # fallback
    
    print("✅ Interval conversion tests passed")

def test_data_conversion():
    """Test data object conversion."""
    print("🧪 Testing data object conversion...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    
    # Test CCXT order to OrderData conversion
    ccxt_order = {
        'id': '12345',
        'symbol': 'BTC/USDT',
        'type': 'limit',
        'side': 'buy',
        'amount': 1.0,
        'price': 50000.0,
        'filled': 0.5,
        'status': 'open',
        'timestamp': 1640995200000
    }
    
    order_data = adapter._convert_ccxt_order_to_order_data(ccxt_order)
    assert order_data.orderid == '12345'
    assert order_data.symbol == 'BTC'
    assert order_data.exchange == Exchange.BINANCE
    assert order_data.type == OrderType.LIMIT
    assert order_data.direction == Direction.LONG
    assert order_data.volume == 1.0
    assert order_data.price == 50000.0
    assert order_data.status == Status.NOTTRADED
    
    print("✅ Data conversion tests passed")

def test_error_handling():
    """Test error handling when not connected."""
    print("🧪 Testing error handling...")
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    
    # Test operations when not connected - should not raise exceptions
    adapter.query_account()  # Should just log warning
    
    mock_order_req = Mock()
    result = adapter.send_order(mock_order_req)
    assert result == ""  # Should return empty string when not connected
    
    print("✅ Error handling tests passed")

def run_all_tests():
    """Run all functional tests."""
    print("🚀 Starting Binance Adapter Functional Tests")
    print("=" * 50)
    
    try:
        test_adapter_creation()
        test_mappings()
        test_symbol_conversion()
        test_interval_conversion()
        test_data_conversion()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("🎉 ALL FUNCTIONAL TESTS PASSED!")
        print("✅ Binance adapter implementation is working correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)