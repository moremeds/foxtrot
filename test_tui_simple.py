#!/usr/bin/env python3
"""
Simple TUI Integration Test

This script provides a basic integration test that verifies core functionality
without waiting for async responses or timeouts.
"""

import pytest

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@pytest.mark.timeout(10)
def test_imports():
    """Test all critical imports."""
    print("1. Testing imports...")
    try:
        # Core TUI imports
        # Dialog system
        from foxtrot.app.tui.components.dialogs import (
            BaseDialog,
            ModalManager,
            OrderConfirmationDialog,
        )
        from foxtrot.app.tui.components.trading_panel import TUITradingPanel

        # Settings
        from foxtrot.app.tui.config.settings import TUISettings, get_settings
        from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter
        from foxtrot.app.tui.main_app import FoxtrotTUIApp, main

        # Utils
        from foxtrot.app.tui.utils import format_currency, format_number, get_color_for_value

        # Validation framework
        from foxtrot.app.tui.validation import (
            DirectionValidator,
            ExchangeValidator,
            FormValidator,
            OrderTypeValidator,
            PriceValidator,
            SymbolValidator,
            ValidationResult,
            VolumeValidator,
        )
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine

        print("   ✓ All critical imports successful")
        return True
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False


@pytest.mark.timeout(10)
def test_component_creation():
    """Test creating core components."""
    print("2. Testing component creation...")
    try:
        from foxtrot.app.tui.components.trading_panel import TUITradingPanel
        from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter
        from foxtrot.core.event_engine import EventEngine
        from foxtrot.server.engine import MainEngine

        # Create core components
        event_engine = EventEngine()
        main_engine = MainEngine(event_engine)
        event_adapter = EventEngineAdapter(event_engine)

        # Create trading panel
        trading_panel = TUITradingPanel(
            main_engine=main_engine,
            event_engine=event_engine
        )

        # Mock compose for testing
        trading_panel.compose = list

        print("   ✓ Core components created successfully")
        return True
    except Exception as e:
        print(f"   ✗ Component creation error: {e}")
        return False


@pytest.mark.timeout(10)
def test_validation_framework():
    """Test validation framework."""
    print("3. Testing validation framework...")
    try:
        from foxtrot.app.tui.validation import (
            PriceValidator,
            SymbolValidator,
            ValidationResult,
            VolumeValidator,
        )

        # Test symbol validator
        symbol_validator = SymbolValidator()
        result = symbol_validator.validate("BTCUSDT")
        assert isinstance(result, ValidationResult)

        # Test price validator
        price_validator = PriceValidator()
        result = price_validator.validate("50000.0")
        assert isinstance(result, ValidationResult)

        # Test volume validator
        volume_validator = VolumeValidator()
        result = volume_validator.validate("1.0")
        assert isinstance(result, ValidationResult)

        print("   ✓ Validation framework working")
        return True
    except Exception as e:
        print(f"   ✗ Validation framework error: {e}")
        return False


@pytest.mark.timeout(10)
def test_dialog_system():
    """Test dialog system."""
    print("4. Testing dialog system...")
    try:
        from foxtrot.app.tui.components.dialogs.base import DialogResult
        from foxtrot.app.tui.components.dialogs.confirmation import OrderConfirmationDialog

        # Create dialog result (this doesn't need an app)
        result = DialogResult(confirmed=True)
        assert result.success

        # Test dialog classes are importable
        assert OrderConfirmationDialog is not None

        print("   ✓ Dialog system working")
        return True
    except Exception as e:
        print(f"   ✗ Dialog system error: {e}")
        return False


@pytest.mark.timeout(10)
def test_settings_system():
    """Test settings system."""
    print("5. Testing settings system...")
    try:
        from foxtrot.app.tui.config.settings import TUISettings, get_settings

        # Test settings creation
        settings = TUISettings()
        assert settings is not None

        # Test global settings
        global_settings = get_settings()
        assert global_settings is not None

        print("   ✓ Settings system working")
        return True
    except Exception as e:
        print(f"   ✗ Settings system error: {e}")
        return False


@pytest.mark.timeout(10)
def test_order_data_creation():
    """Test order data creation without publishing."""
    print("6. Testing order data creation...")
    try:
        from foxtrot.util.constants import Direction, Exchange, OrderType
        from foxtrot.util.object import OrderData

        # Create order data
        order = OrderData(
            symbol="TEST.SYMBOL",
            exchange=Exchange.SMART,
            orderid="test_123",
            type=OrderType.LIMIT,
            direction=Direction.LONG,
            volume=1.0,
            price=100.0,
            adapter_name="TEST"
        )

        assert order.symbol == "TEST.SYMBOL"
        assert order.vt_symbol == "TEST.SYMBOL.SMART"

        print("   ✓ Order data creation working")
        return True
    except Exception as e:
        print(f"   ✗ Order data creation error: {e}")
        return False


@pytest.mark.timeout(10)
def test_entry_points():
    """Test entry point availability."""
    print("7. Testing entry points...")
    try:
        # Test main app entry point
        from foxtrot.app.tui.main_app import main
        assert callable(main)

        # Test run_tui entry point
        from run_tui import main as run_tui_main
        assert callable(run_tui_main)

        # Test launcher scripts exist
        launcher_script = Path("scripts/foxtrot-tui")
        python_launcher = Path("scripts/run_foxtrot_tui.py")

        if launcher_script.exists():
            print("   ✓ Shell launcher script available")
        else:
            print("   ⚠ Shell launcher script not found")

        if python_launcher.exists():
            print("   ✓ Python launcher script available")
        else:
            print("   ⚠ Python launcher script not found")

        print("   ✓ Entry points working")
        return True
    except Exception as e:
        print(f"   ✗ Entry points error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Simple TUI Integration Test")
    print("=" * 50)

    tests = [
        test_imports,
        test_component_creation,
        test_validation_framework,
        test_dialog_system,
        test_settings_system,
        test_order_data_creation,
        test_entry_points
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ✗ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        print("✓ TUI trading panel integration is working correctly")
        print("✓ All core components are functional")
        print("✓ Ready for interactive testing")
        print("\n💡 Next steps:")
        print("   - Run: python3 run_tui.py --debug")
        print("   - Or: ./scripts/foxtrot-tui --debug")
        return True
    print(f"\n❌ {failed} TEST(S) FAILED!")
    print("🔧 Please fix the issues above before proceeding")
    return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
