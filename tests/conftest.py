"""
Global pytest configuration for Foxtrot test suite.

Provides fixtures, hooks, and configuration for improved test reliability.
"""

import os
import threading
import time
from typing import Generator

import pytest

from .fixtures.test_infrastructure import TestInfrastructure


@pytest.fixture(autouse=True)
def test_environment_cleanup():
    """
    Auto-applied fixture that ensures test environment cleanup.
    
    Runs before and after each test to ensure clean state.
    """
    # Pre-test setup
    initial_thread_count = threading.active_count()
    
    yield
    
    # Post-test cleanup
    # Give threads a moment to finish naturally
    time.sleep(0.1)
    
    # Clean up any lingering threads
    TestInfrastructure.cleanup_threads(timeout=2.0)
    
    final_thread_count = threading.active_count()
    
    # Log if we have thread leakage (for debugging)
    if final_thread_count > initial_thread_count + 1:  # Allow some tolerance
        remaining = [t.name for t in threading.enumerate() 
                    if t != threading.current_thread()]
        # Note: In production tests, this would be logged but not fail the test


@pytest.fixture
def mock_environment():
    """
    Fixture for setting up mock test environment.
    
    Provides isolated environment for testing without external dependencies.
    """
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test-specific environment variables
    test_env = {
        'FOXTROT_TEST_MODE': 'true',
        'FOXTROT_LOG_LEVEL': 'WARNING',  # Reduce log noise in tests
        'FOXTROT_DISABLE_EXTERNAL_CONNECTIONS': 'true',
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def timeout_config():
    """
    Fixture providing timeout configuration for different test types.
    """
    return TestInfrastructure.TIMEOUTS


def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", 
        "slow: marks tests as slow (may take >30 seconds)"
    )
    config.addinivalue_line(
        "markers",
        "network: marks tests that require network connectivity"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests"
    )


def pytest_runtest_setup(item):
    """
    Setup hook that runs before each test.
    
    Applies automatic timeout configuration based on test location.
    """
    # Auto-apply timeouts based on test path
    test_path = str(item.fspath)
    
    if '/e2e/' in test_path:
        # E2E tests get longer timeouts
        if not hasattr(item, 'pytestmark'):
            item.pytestmark = []
        
        # Check if timeout marker already exists
        has_timeout = any(
            mark.name == 'timeout' 
            for mark in getattr(item, 'pytestmark', [])
        )
        
        if not has_timeout:
            timeout_mark = pytest.mark.timeout(TestInfrastructure.TIMEOUTS['e2e'])
            item.pytestmark.append(timeout_mark)
    
    elif '/integration/' in test_path:
        # Integration tests get medium timeouts
        if not hasattr(item, 'pytestmark'):
            item.pytestmark = []
            
        has_timeout = any(
            mark.name == 'timeout' 
            for mark in getattr(item, 'pytestmark', [])
        )
        
        if not has_timeout:
            timeout_mark = pytest.mark.timeout(TestInfrastructure.TIMEOUTS['integration'])
            item.pytestmark.append(timeout_mark)


def pytest_runtest_teardown(item, nextitem):
    """
    Teardown hook that runs after each test.
    
    Ensures cleanup of test resources.
    """
    # Additional cleanup for specific test types
    test_path = str(item.fspath)
    
    if any(test_type in test_path for test_type in ['/e2e/', '/integration/']):
        # Give extra time for complex tests to clean up
        TestInfrastructure.cleanup_threads(timeout=3.0, aggressive=True)


@pytest.fixture
def event_engine_cleanup():
    """
    Fixture specifically for EventEngine cleanup in tests.
    
    Ensures EventEngine instances are properly stopped and cleaned up.
    """
    engines = []
    
    def register_engine(engine):
        """Register an EventEngine for cleanup."""
        engines.append(engine)
        return engine
    
    yield register_engine
    
    # Cleanup all registered engines
    for engine in engines:
        try:
            if hasattr(engine, '_active') and engine._active:
                engine.stop()
        except Exception:
            pass


@pytest.fixture
def adapter_cleanup():
    """
    Fixture for adapter cleanup in tests.
    
    Ensures adapters are properly disconnected and cleaned up.
    """
    adapters = []
    
    def register_adapter(adapter):
        """Register an adapter for cleanup."""
        adapters.append(adapter)
        return adapter
    
    yield register_adapter
    
    # Cleanup all registered adapters
    for adapter in adapters:
        try:
            if hasattr(adapter, 'connected') and adapter.connected:
                adapter.close()
            
            # Clean up WebSocket threads if present
            if hasattr(adapter, 'market_data') and adapter.market_data:
                if hasattr(adapter.market_data, '_stop_websocket'):
                    adapter.market_data._stop_websocket()
        except Exception:
            pass


# Skip tests that require external services if not configured
def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to handle conditional skipping.
    """
    # Skip network tests if in offline mode
    if os.getenv('FOXTROT_OFFLINE_MODE', 'false').lower() == 'true':
        skip_network = pytest.mark.skip(reason="Offline mode - skipping network tests")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)
    
    # Skip E2E tests if API keys not configured
    if not all([
        os.getenv('BINANCE_TESTNET_SPOT_API_KEY'),
        os.getenv('BINANCE_TESTNET_SPOT_SECRET_KEY')
    ]):
        skip_e2e = pytest.mark.skip(reason="E2E API keys not configured")
        for item in items:
            if "/e2e/" in str(item.fspath) and "binance" in str(item.fspath).lower():
                item.add_marker(skip_e2e)