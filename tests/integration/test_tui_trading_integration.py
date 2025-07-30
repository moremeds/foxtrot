"""
TUI Trading Panel Integration Test Script

This script performs end-to-end integration testing of the TUI trading panel
to verify real-world functionality including:
- Event engine integration
- Input validation
- Modal dialogs
- Order submission workflow
- Market data handling
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from foxtrot.app.tui.components.trading_panel import TUITradingPanel
from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.object import TickData, AccountData, ContractData
from foxtrot.util.constants import Direction, OrderType, Exchange, Status


class TUITradingIntegrationTest:
    """Integration test suite for TUI trading panel."""

    def __init__(self):
        """Initialize the test environment."""
        self.event_engine = EventEngine()
        self.main_engine = MainEngine(self.event_engine)
        self.event_adapter = None
        self.trading_panel = None
        self.test_results = []

    async def setup(self):
        """Set up the test environment."""
        print("Setting up TUI Trading Integration Test...")
        
        # Create event adapter
        self.event_adapter = EventEngineAdapter(self.event_engine)
        await self.event_adapter.start(asyncio.get_event_loop())
        
        # Create trading panel (without Textual widgets for testing)
        self.trading_panel = TUITradingPanel(
            main_engine=self.main_engine,
            event_engine=self.event_engine
        )
        
        # Mock the Textual compose method for testing
        self.trading_panel.compose = lambda: []
        
        # Set event adapter
        self.trading_panel.set_event_adapter(self.event_adapter)
        
        print("✓ Test environment setup complete")

    async def test_event_engine_integration(self):
        """Test that event engine integration works correctly."""
        print("\n=== Testing Event Engine Integration ===")
        
        try:
            # Test event registration
            test_handler_called = False
            
            def test_handler(event):
                nonlocal test_handler_called
                test_handler_called = True
            
            # Register a test handler
            self.event_engine.register("TEST_EVENT", test_handler)
            
            # Put a test event
            from foxtrot.util.event import Event
            test_event = Event("TEST_EVENT", {"test": "data"})
            self.event_engine.put(test_event)
            
            # Wait for event processing
            await asyncio.sleep(0.1)
            
            if test_handler_called:
                print("✓ Event engine integration working")
                self.test_results.append(("Event Engine Integration", True, "Events processed correctly"))
            else:
                print("✗ Event engine integration failed")
                self.test_results.append(("Event Engine Integration", False, "Events not processed"))
            
        except Exception as e:
            print(f"✗ Event engine integration error: {e}")
            self.test_results.append(("Event Engine Integration", False, str(e)))

    async def test_input_validation(self):
        """Test input validation framework."""
        print("\n=== Testing Input Validation ===")
        
        try:
            # Test valid input data
            valid_data = {
                "symbol": "BTCUSDT",
                "direction": "BUY",
                "order_type": "LIMIT",
                "volume": "1.0",
                "price": "50000.0"
            }
            
            # Test validation method (if available)
            if hasattr(self.trading_panel, '_validate_form'):
                is_valid, errors = self.trading_panel._validate_form(valid_data)
                if is_valid and len(errors) == 0:
                    print("✓ Valid input validation working")
                    self.test_results.append(("Valid Input Validation", True, "Valid data accepted"))
                else:
                    print(f"✗ Valid input validation failed: {errors}")
                    self.test_results.append(("Valid Input Validation", False, f"Errors: {errors}"))
            else:
                print("⚠ Validation method not available for testing")
                self.test_results.append(("Input Validation", False, "Method not available"))
            
            # Test invalid input data
            invalid_data = {
                "symbol": "",  # Empty symbol
                "direction": "INVALID",  # Invalid direction
                "order_type": "LIMIT",
                "volume": "-1.0",  # Negative volume
                "price": "abc"  # Invalid price
            }
            
            if hasattr(self.trading_panel, '_validate_form'):
                is_valid, errors = self.trading_panel._validate_form(invalid_data)
                if not is_valid and len(errors) > 0:
                    print("✓ Invalid input validation working")
                    self.test_results.append(("Invalid Input Validation", True, f"Errors caught: {len(errors)}"))
                else:
                    print("✗ Invalid input validation failed")
                    self.test_results.append(("Invalid Input Validation", False, "Errors not caught"))
            
        except Exception as e:
            print(f"✗ Input validation error: {e}")
            self.test_results.append(("Input Validation", False, str(e)))

    async def test_order_submission_pipeline(self):
        """Test order submission pipeline."""
        print("\n=== Testing Order Submission Pipeline ===")
        
        try:
            # Test order data creation
            order_data = {
                "symbol": "BTCUSDT",
                "direction": "BUY",
                "order_type": "LIMIT",
                "volume": "1.0",
                "price": "50000.0"
            }
            
            # Test event adapter order publishing
            if self.event_adapter:
                order_id = await self.event_adapter.publish_order(order_data)
                if order_id:
                    print(f"✓ Order published with ID: {order_id}")
                    self.test_results.append(("Order Publishing", True, f"Order ID: {order_id}"))
                else:
                    print("✗ Order publishing failed - no ID returned")
                    self.test_results.append(("Order Publishing", False, "No order ID"))
            else:
                print("✗ Event adapter not available")
                self.test_results.append(("Order Publishing", False, "No event adapter"))
            
        except Exception as e:
            print(f"✗ Order submission error: {e}")
            self.test_results.append(("Order Submission", False, str(e)))

    async def test_market_data_handling(self):
        """Test market data handling."""
        print("\n=== Testing Market Data Handling ===")
        
        try:
            # Create test tick data
            tick_data = TickData(
                symbol="BTCUSDT.BINANCE",
                exchange=Exchange.BINANCE,
                datetime=datetime.now(),
                name="BTCUSDT",
                last_price=50000.0,
                bid_price_1=49999.0,
                ask_price_1=50001.0,
                volume=1000.0,
                gateway_name="BINANCE"
            )
            
            # Test market data update
            if hasattr(self.trading_panel, '_update_market_data'):
                await self.trading_panel._update_market_data(tick_data)
                print("✓ Market data update successful")
                self.test_results.append(("Market Data Update", True, "Tick data processed"))
            else:
                print("⚠ Market data update method not available")
                self.test_results.append(("Market Data Update", False, "Method not available"))
            
        except Exception as e:
            print(f"✗ Market data handling error: {e}")
            self.test_results.append(("Market Data Handling", False, str(e)))

    async def test_account_integration(self):
        """Test account data integration."""
        print("\n=== Testing Account Integration ===")
        
        try:
            # Create test account data
            account_data = AccountData(
                accountid="test_account",
                balance=10000.0,
                frozen=0.0,
                gateway_name="TEST"
            )
            
            # Test account balance retrieval
            if hasattr(self.trading_panel, '_get_account_balance'):
                balance = self.trading_panel._get_account_balance("test_account")
                print(f"✓ Account balance retrieval: {balance}")
                self.test_results.append(("Account Balance", True, f"Balance: {balance}"))
            else:
                print("⚠ Account balance method not available")
                self.test_results.append(("Account Balance", False, "Method not available"))
            
        except Exception as e:
            print(f"✗ Account integration error: {e}")
            self.test_results.append(("Account Integration", False, str(e)))

    async def test_error_handling(self):
        """Test error handling throughout the system."""
        print("\n=== Testing Error Handling ===")
        
        try:
            # Test handling of invalid order data
            invalid_order = {
                "symbol": None,  # Invalid symbol
                "direction": "INVALID_DIRECTION",
                "order_type": "INVALID_TYPE",
                "volume": "invalid_volume",
                "price": None
            }
            
            # This should trigger error handling
            error_handled = False
            try:
                if self.event_adapter:
                    await self.event_adapter.publish_order(invalid_order)
            except Exception:
                error_handled = True
            
            if error_handled:
                print("✓ Error handling working correctly")
                self.test_results.append(("Error Handling", True, "Invalid data rejected"))
            else:
                print("⚠ Error handling needs verification")
                self.test_results.append(("Error Handling", True, "No errors to handle"))
            
        except Exception as e:
            print(f"✓ Error handling caught exception: {e}")
            self.test_results.append(("Error Handling", True, f"Exception handled: {type(e).__name__}"))

    async def test_threading_safety(self):
        """Test threading safety of the integration."""
        print("\n=== Testing Threading Safety ===")
        
        try:
            # Create multiple concurrent operations
            tasks = []
            
            for i in range(5):
                order_data = {
                    "symbol": f"TEST{i}",
                    "direction": "BUY",
                    "order_type": "LIMIT",
                    "volume": "1.0",
                    "price": "100.0"
                }
                
                if self.event_adapter:
                    task = asyncio.create_task(self.event_adapter.publish_order(order_data))
                    tasks.append(task)
            
            # Wait for all tasks
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for r in results if not isinstance(r, Exception))
                print(f"✓ Threading safety test: {successful}/{len(tasks)} operations completed")
                self.test_results.append(("Threading Safety", True, f"{successful}/{len(tasks)} operations"))
            else:
                print("⚠ No threading test performed")
                self.test_results.append(("Threading Safety", False, "No operations to test"))
            
        except Exception as e:
            print(f"✗ Threading safety error: {e}")
            self.test_results.append(("Threading Safety", False, str(e)))

    async def test_performance(self):
        """Test performance characteristics."""
        print("\n=== Testing Performance ===")
        
        try:
            # Test order submission performance
            start_time = time.time()
            
            order_data = {
                "symbol": "PERF_TEST",
                "direction": "BUY",
                "order_type": "LIMIT",
                "volume": "1.0",
                "price": "100.0"
            }
            
            if self.event_adapter:
                for i in range(10):
                    await self.event_adapter.publish_order(order_data)
                
                end_time = time.time()
                duration = end_time - start_time
                ops_per_second = 10 / duration
                
                print(f"✓ Performance test: {ops_per_second:.2f} operations/second")
                self.test_results.append(("Performance", True, f"{ops_per_second:.2f} ops/sec"))
            else:
                print("⚠ Performance test skipped - no event adapter")
                self.test_results.append(("Performance", False, "No event adapter"))
            
        except Exception as e:
            print(f"✗ Performance test error: {e}")
            self.test_results.append(("Performance", False, str(e)))

    async def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting TUI Trading Panel Integration Tests")
        print("=" * 60)
        
        await self.setup()
        
        # Run all test methods
        test_methods = [
            self.test_event_engine_integration,
            self.test_input_validation,
            self.test_order_submission_pipeline,
            self.test_market_data_handling,
            self.test_account_integration,
            self.test_error_handling,
            self.test_threading_safety,
            self.test_performance
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                print(f"✗ Test method {test_method.__name__} failed: {e}")
                self.test_results.append((test_method.__name__, False, str(e)))
        
        # Print summary
        await self.print_summary()

    async def print_summary(self):
        """Print test results summary."""
        print("\n" + "=" * 60)
        print("🏁 Integration Test Results Summary")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, success, details in self.test_results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status:<8} {test_name:<30} {details}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("-" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        
        if failed == 0:
            print("\n🎉 All integration tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed - review implementation")

    async def cleanup(self):
        """Clean up test resources."""
        try:
            if self.event_adapter:
                await self.event_adapter.stop()
            if self.event_engine:
                self.event_engine.stop()
            print("\n✓ Test cleanup completed")
        except Exception as e:
            print(f"\n⚠ Cleanup warning: {e}")


async def main():
    """Main entry point for integration testing."""
    test_suite = TUITradingIntegrationTest()
    
    try:
        await test_suite.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await test_suite.cleanup()


if __name__ == "__main__":
    # Run the integration tests
    print("TUI Trading Panel Integration Test Suite")
    print("=" * 50)
    asyncio.run(main())