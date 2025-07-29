#!/usr/bin/env python3
"""
Simple example of testing IB connection programmatically.
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from foxtrot.testing.ibrokers.config import load_config
from foxtrot.testing.ibrokers.enhanced import run_test_with_retries
from foxtrot.testing.ibrokers.utils import setup_logging, create_summary_report


def main():
    """Simple example of IB connection testing."""
    
    # Load configuration with some overrides
    config = load_config(
        host="127.0.0.1",
        port=4001,
        client_id=1,
        log_level="INFO",
        verbose=True
    )
    
    # Setup logging
    setup_logging(config.log_level, verbose=config.verbose)
    
    print("Testing Interactive Brokers connection...")
    print(f"Connecting to {config.host}:{config.port}")
    
    # Run the test
    success, tester = run_test_with_retries(config)
    
    if success and tester:
        print("\n✅ Connection test PASSED!")
        
        # Display results
        report = create_summary_report(
            config=config,
            connection_successful=success,
            account_data=tester.account_data,
            position_data=tester.position_data,
            json_output=False
        )
        print(report)
        
    else:
        print("\n❌ Connection test FAILED!")
        if tester and tester.last_error:
            print(f"Error: {tester.last_error}")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())