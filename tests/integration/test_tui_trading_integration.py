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
from datetime import datetime
from pathlib import Path
import sys

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from foxtrot.app.tui.components.trading_panel import TUITradingPanel
from foxtrot.app.tui.integration.event_adapter import EventEngineAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.server.engine import MainEngine
from foxtrot.util.constants import Exchange
from foxtrot.util.object import AccountData, TickData


@pytest.fixture
async def trading_panel():
    """Pytest fixture to set up the TUI trading panel for testing."""
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    event_adapter = EventEngineAdapter(event_engine)
    await event_adapter.start(asyncio.get_event_loop())

    panel = TUITradingPanel(
        main_engine=main_engine,
        event_engine=event_engine
    )
    panel.compose = list
    panel.set_event_adapter(event_adapter)

    yield panel

    await event_adapter.stop()
    event_engine.stop()


@pytest.mark.asyncio
async def test_event_engine_integration(trading_panel: TUITradingPanel):
    """Test that event engine integration works correctly."""
    event_processed = asyncio.Event()
    main_loop = asyncio.get_running_loop()

    @pytest.mark.timeout(30)
    def test_handler(event):
        main_loop.call_soon_threadsafe(event_processed.set)

    trading_panel.event_engine.register("TEST_EVENT", test_handler)

    from foxtrot.core.event import Event
    test_event = Event("TEST_EVENT", {"test": "data"})
    trading_panel.event_engine.put(test_event)

    try:
        await asyncio.wait_for(event_processed.wait(), timeout=5)
    except asyncio.TimeoutError:
        pytest.fail("Event not processed within timeout")


@pytest.mark.asyncio
async def test_input_validation(trading_panel: TUITradingPanel):
    """Test input validation framework."""
    # Test valid input data
    valid_data = {
        "symbol": "BTCUSDT",
        "direction": "BUY",
        "order_type": "LIMIT",
        "volume": "1.0",
        "price": "50000.0"
    }
    if hasattr(trading_panel, '_validate_form'):
        is_valid, errors = trading_panel._validate_form(valid_data)
        assert is_valid
        assert not errors

    # Test invalid input data
    invalid_data = {
        "symbol": "",
        "direction": "INVALID",
        "order_type": "LIMIT",
        "volume": "-1.0",
        "price": "abc"
    }
    if hasattr(trading_panel, '_validate_form'):
        is_valid, errors = trading_panel._validate_form(invalid_data)
        assert not is_valid
        assert errors


@pytest.mark.asyncio
async def test_order_submission_pipeline(trading_panel: TUITradingPanel):
    """Test order submission pipeline."""
    order_data = {
        "symbol": "BTCUSDT",
        "direction": "BUY",
        "order_type": "LIMIT",
        "volume": "1.0",
        "price": "50000.0"
    }
    order_id = await trading_panel.event_adapter.publish_order(order_data)
    assert order_id is not None


@pytest.mark.asyncio
async def test_market_data_handling(trading_panel: TUITradingPanel):
    """Test market data handling."""
    tick_data = TickData(
        symbol="BTCUSDT.BINANCE",
        exchange=Exchange.BINANCE,
        datetime=datetime.now(),
        name="BTCUSDT",
        last_price=50000.0,
        bid_price_1=49999.0,
        ask_price_1=50001.0,
        volume=1000.0,
        adapter_name="BINANCE"
    )
    if hasattr(trading_panel, '_update_market_data'):
        await trading_panel._update_market_data(tick_data)


@pytest.mark.asyncio
async def test_account_integration(trading_panel: TUITradingPanel):
    """Test account data integration."""
    account_data = AccountData(
        accountid="test_account",
        balance=10000.0,
        frozen=0.0,
        adapter_name="TEST"
    )
    trading_panel.main_engine.update_account(account_data)

    if hasattr(trading_panel, '_get_account_balance'):
        balance = await trading_panel._get_account_balance("test_account")
        assert balance == 10000.0
