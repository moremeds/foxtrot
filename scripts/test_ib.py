#!/usr/bin/env python3
"""
Interactive Brokers Connection Test Script

This script tests the connection to Interactive Brokers TWS/Gateway and displays account information.
"""
import argparse
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from foxtrot.tools.config import load_config, ConfigError, create_example_config
from foxtrot.tools.enhanced_tester import run_test_with_retries
from foxtrot.tools.utils import setup_logging, create_summary_report


def main():
    """Main entry point for the IB connection tester."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.create_config:
        create_example_config(args.create_config)
        print(f"Example configuration created: {args.create_config}")
        return 0
    
    try:
        # Load configuration
        config_overrides = {}
        if args.host:
            config_overrides['host'] = args.host
        if args.port:
            config_overrides['port'] = args.port
        if args.client_id:
            config_overrides['client_id'] = args.client_id
        if args.account:
            config_overrides['account'] = args.account
        if args.timeout:
            config_overrides['connection_timeout'] = args.timeout
        if args.verbose:
            config_overrides['verbose'] = True
        if args.json:
            config_overrides['json_output'] = True
        if args.log_level:
            config_overrides['log_level'] = args.log_level
        
        config = load_config(args.config, **config_overrides)
        
        # Setup logging
        setup_logging(config.log_level, config.log_file, config.verbose)
        
        # Run the test
        success, tester = run_test_with_retries(config)
        
        # Generate and display results
        if tester:
            report = create_summary_report(
                config=config,
                connection_successful=success,
                account_data=tester.account_data,
                position_data=tester.position_data,
                error_message=tester.last_error,
                json_output=config.json_output
            )
            print(report)
        
        return 0 if success else 1
        
    except ConfigError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nTest interrupted by user", file=sys.stderr)
        return 3
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 4


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Test Interactive Brokers connection and display account information",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic test with default settings
  python test_ib.py
  
  # Test with custom host and port
  python test_ib.py --host 192.168.1.100 --port 7496
  
  # Test with specific configuration file
  python test_ib.py --config my_ib_config.json
  
  # Create example configuration file
  python test_ib.py --create-config example_config.json
  
  # Verbose output with JSON format
  python test_ib.py --verbose --json
  
Environment Variables:
  FOXTROT_IB_HOST            - TWS/Gateway host address
  FOXTROT_IB_PORT            - TWS/Gateway port number
  FOXTROT_IB_CLIENT_ID       - Client ID for connection
  FOXTROT_IB_ACCOUNT         - Trading account number
  FOXTROT_IB_CONNECTION_TIMEOUT - Connection timeout in seconds
  FOXTROT_IB_LOG_LEVEL       - Logging level (DEBUG, INFO, WARNING, ERROR)
  FOXTROT_IB_VERBOSE         - Enable verbose output (true/false)
  FOXTROT_IB_JSON_OUTPUT     - Enable JSON output (true/false)
        """
    )
    
    # Configuration options
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file (JSON format)'
    )
    
    parser.add_argument(
        '--create-config',
        metavar='FILE',
        help='Create example configuration file and exit'
    )
    
    # Connection settings
    parser.add_argument(
        '--host',
        help='TWS/Gateway host address (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        help='TWS/Gateway port number (default: 7497)'
    )
    
    parser.add_argument(
        '--client-id',
        type=int,
        help='Client ID for connection (default: 1)'
    )
    
    parser.add_argument(
        '--account', '-a',
        help='Trading account number (auto-detected if not specified)'
    )
    
    parser.add_argument(
        '--timeout', '-t',
        type=int,
        help='Connection timeout in seconds (default: 30)'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set logging level (default: INFO)'
    )
    
    return parser


if __name__ == '__main__':
    sys.exit(main())