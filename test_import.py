#!/usr/bin/env python3
"""Simple import test for BinanceAdapter."""

import sys
sys.path.insert(0, '/home/ubuntu/projects/foxtrot')

try:
    from foxtrot.adapter.binance import BinanceAdapter
    from foxtrot.core.engine import EventEngine
    from foxtrot.util.constants import Exchange
    print("✅ All imports successful")
    
    # Test basic instantiation
    from unittest.mock import Mock
    mock_engine = Mock()
    adapter = BinanceAdapter(mock_engine, "test")
    print(f"✅ Adapter instantiated: {adapter.default_name}")
    print(f"✅ Exchanges: {adapter.exchanges}")
    print(f"✅ Default settings: {list(adapter.default_setting.keys())}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")