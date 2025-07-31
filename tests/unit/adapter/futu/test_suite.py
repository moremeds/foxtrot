"""
Test suite for Futu adapter unit tests.

This module provides a comprehensive test suite runner for all Futu adapter components.
"""

import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

# Import all test modules
from .test_api_client import TestFutuApiClient
from .test_futu_adapter import TestFutuAdapter
from .test_futu_mappings import TestFutuMappings
from .test_order_manager import TestFutuOrderManager


def create_test_suite() -> unittest.TestSuite:
    """Create a comprehensive test suite for Futu adapter."""
    suite = unittest.TestSuite()

    # Add adapter facade tests
    suite.addTest(unittest.makeSuite(TestFutuAdapter))

    # Add API client tests
    suite.addTest(unittest.makeSuite(TestFutuApiClient))

    # Add order manager tests
    suite.addTest(unittest.makeSuite(TestFutuOrderManager))

    # Add mappings tests
    suite.addTest(unittest.makeSuite(TestFutuMappings))

    return suite


def run_all_tests(verbosity: int = 2) -> unittest.TestResult:
    """Run all Futu adapter tests."""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


if __name__ == '__main__':
    print("Running Futu Adapter Test Suite")
    print("=" * 50)

    # Run the complete test suite
    result = run_all_tests()

    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
