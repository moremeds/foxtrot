#!/usr/bin/env python3
"""Simple test runner for Binance adapter tests."""

import sys
import os

# Add project root to path
sys.path.insert(0, '/home/ubuntu/projects/foxtrot')

# Run the tests manually
if __name__ == "__main__":
    try:
        from tests.unit.adapter.binance.test_binance_adapter import TestBinanceAdapter
        import unittest
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestBinanceAdapter)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print(f"\n{'='*50}")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, failure in result.failures:
                print(f"  {test}: {failure}")
                
        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"  {test}: {error}")
        
        if result.wasSuccessful():
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed!")
            
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()