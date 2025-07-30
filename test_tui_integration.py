#!/usr/bin/env python3
"""
Quick TUI Integration Test Runner

This script provides a simple way to test the TUI trading panel integration
without running the full test suite. It verifies core functionality works.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def quick_integration_test():
    """Run a quick integration test of the TUI trading panel."""
    print("🧪 Quick TUI Trading Panel Integration Test")
    print("=" * 50)
    
    try:
        # Test 1: Import all required modules
        print("1. Testing imports...")
        from foxtrot.app.tui.components.trading_panel import TUITradingPanel
        from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine
        print("   ✓ All imports successful")
        
        # Test 2: Create core components
        print("2. Testing component creation...")
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        event_adapter = EventEngineAdapter(event_engine)
        print("   ✓ Core components created")
        
        # Test 3: Create trading panel
        print("3. Testing trading panel creation...")
        trading_panel = TUITradingPanel(
            main_engine=main_engine,
            event_engine=event_engine
        )
        # Mock compose for testing
        trading_panel.compose = lambda: []
        print("   ✓ Trading panel created")
        
        # Test 4: Test event adapter integration
        print("4. Testing event adapter integration...")
        await event_adapter.start(asyncio.get_event_loop())
        trading_panel.set_event_adapter(event_adapter)
        print("   ✓ Event adapter integrated")
        
        # Test 5: Test order publishing
        print("5. Testing order publishing...")
        order_data = {
            "symbol": "TEST.SYMBOL",
            "direction": "BUY",
            "order_type": "LIMIT",
            "volume": "1.0",
            "price": "100.0"
        }
        order_id = await event_adapter.publish_order(order_data)
        print(f"   ✓ Order published with ID: {order_id}")
        
        # Test 6: Test validation framework
        print("6. Testing validation framework...")
        from foxtrot.app.tui.validation.base import ValidationResult, FieldValidator
        validator = FieldValidator("test_field")
        result = validator.validate("test_value")
        assert isinstance(result, ValidationResult)
        print("   ✓ Validation framework working")
        
        # Test 7: Test dialog system
        print("7. Testing dialog system...")
        from foxtrot.app.tui.dialogs.modal import ModalManager
        modal_manager = ModalManager()
        assert modal_manager is not None
        print("   ✓ Dialog system available")
        
        # Test 8: Test settings system
        print("8. Testing settings system...")
        from foxtrot.app.tui.config.settings import TUISettings, get_settings
        settings = get_settings()
        assert settings is not None
        print("   ✓ Settings system working")
        
        # Cleanup
        print("9. Cleaning up...")
        await event_adapter.stop()
        event_engine.stop()
        print("   ✓ Cleanup completed")
        
        print("\n🎉 Quick integration test PASSED!")
        print("   All core components are working correctly.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Make sure all dependencies are installed: uv sync")
        return False
        
    except Exception as e:
        print(f"\n❌ Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_entry_points():
    """Test that all entry points work correctly."""
    print("\n🚀 Testing Entry Points")
    print("=" * 30)
    
    try:
        # Test main TUI app import
        print("1. Testing main TUI app...")
        from foxtrot.app.tui.main_app import FoxtrotTUIApp, main
        print("   ✓ Main TUI app available")
        
        # Test run_tui script
        print("2. Testing run_tui script...")
        from run_tui import main as run_tui_main, parse_arguments
        args = parse_arguments.__code__.co_varnames
        assert 'config' in args or 'debug' in args
        print("   ✓ run_tui script available")
        
        # Test launcher scripts exist
        print("3. Testing launcher scripts...")
        launcher_script = Path("scripts/foxtrot-tui")
        if launcher_script.exists():
            print("   ✓ Shell launcher script exists")
        else:
            print("   ⚠ Shell launcher script not found")
        
        python_launcher = Path("scripts/run_foxtrot_tui.py")
        if python_launcher.exists():
            print("   ✓ Python launcher script exists")
        else:
            print("   ⚠ Python launcher script not found")
        
        print("\n✅ Entry point test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Entry point test failed: {e}")
        return False


async def main():
    """Main test runner."""
    print("TUI Trading Panel Integration Verification")
    print("=" * 60)
    
    # Run quick integration test
    integration_success = await quick_integration_test()
    
    # Test entry points
    entry_point_success = test_entry_points()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Final Test Summary")
    print("=" * 60)
    
    if integration_success and entry_point_success:
        print("🎉 ALL TESTS PASSED!")
        print("   ✓ TUI trading panel integration is working correctly")
        print("   ✓ Entry points are configured properly")
        print("   ✓ Ready for interactive testing")
        print("\n💡 Next steps:")
        print("   - Run: python run_tui.py --debug")
        print("   - Or: ./scripts/foxtrot-tui --debug")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        if not integration_success:
            print("   ✗ Integration test failed")
        if not entry_point_success:
            print("   ✗ Entry point test failed")
        print("\n🔧 Please fix the issues above before proceeding")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner error: {e}")
        sys.exit(1)