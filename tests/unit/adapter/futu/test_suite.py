"""
Test suite for Futu adapter unit tests.

This module provides a comprehensive test suite runner for all Futu adapter components.
Use this module to run all Futu adapter tests via pytest.
"""

import subprocess
import sys
from pathlib import Path


def run_futu_adapter_tests(verbose: bool = True, coverage: bool = True) -> int:
    """
    Run all Futu adapter tests using pytest.
    
    Args:
        verbose: Whether to run in verbose mode
        coverage: Whether to include coverage reporting
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Get the directory containing this test suite
    test_dir = Path(__file__).parent
    
    # Build pytest command
    cmd = ["pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=foxtrot.adapter.futu", "--cov-report=term-missing"])
    
    # Add the test directory to run all futu adapter tests
    cmd.append(str(test_dir))
    
    # Add timeout for individual tests
    cmd.extend(["--timeout=30"])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        # Run pytest
        result = subprocess.run(cmd, cwd=test_dir.parent.parent.parent.parent)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def main():
    """Main entry point for the test suite."""
    print("Futu Adapter Test Suite")
    print("=" * 60)
    print("Running all Futu adapter tests via pytest...")
    print()
    
    exit_code = run_futu_adapter_tests()
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
