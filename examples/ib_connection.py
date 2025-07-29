#!/usr/bin/env python3
"""
Example: Testing Interactive Brokers connectivity.

This example demonstrates how to use the IB testing utilities to check
connectivity to Interactive Brokers TWS or Gateway.
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from foxtrot.testing.ibrokers import IBConnectionTester, IBConfig


def main():
    """Test Interactive Brokers connection."""
    # Configure connection
    config = IBConfig(
        host="127.0.0.1",
        port=7497,  # TWS paper trading (use 4001 for Gateway)
        client_id=1
    )
    
    # Create tester
    tester = IBConnectionTester(config)
    
    print("Testing Interactive Brokers connection...")
    print(f"Connecting to {config.host}:{config.port}")
    
    # Run connection test
    success = tester.run_test()
    
    if success:
        print("✅ Connected to Interactive Brokers")
        
        # Display account summary
        if tester.account_data:
            print("\nAccount Summary:")
            for account_id, account in tester.account_data.items():
                print(f"  Account: {account_id}")
                print(f"  Balance: ${account.balance:,.2f}")
                print(f"  Available: ${account.available:,.2f}")
        
        # Display positions
        if tester.position_data:
            print(f"\nPositions ({len(tester.position_data)}):")
            for symbol, position in tester.position_data.items():
                print(f"  {symbol}: {position.volume} @ ${position.price:.2f}")
        else:
            print("\nNo open positions")
            
    else:
        print("❌ Connection failed")
        if tester.last_error:
            print(f"Error: {tester.last_error}")


if __name__ == "__main__":
    main()