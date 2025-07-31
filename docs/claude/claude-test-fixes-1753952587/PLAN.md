# Comprehensive Test Suite Fix Plan

**Date**: 2025-07-31  
**Project**: Foxtrot Trading Platform  
**Scope**: Complete test suite failure resolution and reliability improvements  

## Executive Summary

This plan addresses critical test suite failures affecting 18 test files with missing `import pytest` statements, plus deeper architectural issues with threading, resource management, and test isolation. The plan is structured in 5 phases progressing from immediate blockers to long-term reliability improvements.

**Total Estimated Time**: 8-12 days  
**Critical Path**: Phase 1 (imports) → Phase 2 (execution) → Phase 3 (reliability)  
**Success Metric**: All tests pass consistently with <2% flaky test rate  

---

## Phase 1: CRITICAL IMMEDIATE FIXES
**Priority**: CRITICAL  
**Time Estimate**: 2-3 hours  
**Risk Level**: Low  
**Blocks**: All test execution  

### 1.1 Fix Missing Pytest Imports

**Problem**: 18 files use `@pytest.mark.timeout()` decorators without importing pytest, causing collection failures.

**Files Requiring `import pytest`**:
```
tests/integration/test_futu_mainengine_integration.py
tests/unit/adapter/binance/test_account_manager.py
tests/unit/adapter/binance/test_api_client.py
tests/unit/adapter/binance/test_binance_adapter.py
tests/unit/adapter/binance/test_binance_mappings.py
tests/unit/adapter/binance/test_order_manager.py
tests/unit/adapter/futu/test_account_manager.py
tests/unit/adapter/futu/test_api_client.py
tests/unit/adapter/futu/test_futu_adapter.py
tests/unit/adapter/futu/test_futu_mappings.py
tests/unit/adapter/futu/test_historical_data.py
tests/unit/adapter/futu/test_market_data.py
tests/unit/adapter/futu/test_order_manager.py
tests/unit/adapter/futu/test_suite.py
test_futu_phase2.py
test_tui_integration.py
test_tui_simple.py
docs/claude/claude-tests-1753950690/add_timeouts.py
```

**Implementation**:
```python
# Add to top of each file after existing imports:
import pytest
```

**Specific Changes**:
1. **For each file above**:
   - Locate the import section (typically lines 1-10)
   - Add `import pytest` after other standard library imports
   - Ensure proper import order (standard → third-party → local)

### 1.2 Import Validation Script

**Create**: `scripts/validate_test_imports.py`
```python
#!/usr/bin/env python3
"""Validate all test file imports work correctly."""

import sys
from pathlib import Path
import importlib.util

def validate_test_file_imports():
    """Check all test files can be imported without errors."""
    test_files = [
        # List all test files here
    ]
    
    failed_imports = []
    for test_file in test_files:
        try:
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"✅ {test_file}")
        except Exception as e:
            failed_imports.append((test_file, str(e)))
            print(f"❌ {test_file}: {e}")
    
    return len(failed_imports) == 0

if __name__ == "__main__":
    success = validate_test_file_imports()
    sys.exit(0 if success else 1)
```

### 1.3 Basic Collection Test

**Verification Commands**:
```bash
# Test collection works without errors
pytest --collect-only

# Test specific categories
pytest --collect-only tests/unit/
pytest --collect-only tests/integration/
pytest --collect-only tests/e2e/

# Run validation script
python scripts/validate_test_imports.py
```

**Success Criteria**:
- ✅ All 18 files can be imported without NameError
- ✅ pytest --collect-only runs without collection errors
- ✅ No syntax errors in any test file
- ✅ All timeout decorators work correctly

---

## Phase 2: HIGH PRIORITY TEST EXECUTION FIXES
**Priority**: HIGH  
**Time Estimate**: 1-2 days  
**Risk Level**: Medium  
**Dependencies**: Phase 1 complete  

### 2.1 EventEngine Threading Fixes

**Problem**: EventEngine threads may hang, causing timeouts and resource leaks.

**File**: `foxtrot/core/event_engine.py`

**Current Issues**:
- stop() method has 5-second timeout with warnings
- Complex idempotent start/stop logic
- Thread join failures cause resource leaks

**Enhancements**:
```python
def stop(self, timeout: float = 10.0, progress_callback=None) -> bool:
    """Enhanced stop with progress monitoring and guaranteed cleanup."""
    if not self._active:
        return True
    
    self._active = False
    shutdown_success = True
    
    # Stop timer thread
    if self._timer and self._timer.is_alive():
        self._timer.join(timeout=timeout/2)
        if self._timer.is_alive():
            if progress_callback:
                progress_callback("Warning: timer thread still active")
            shutdown_success = False
    
    # Stop main thread
    if self._thread and self._thread.is_alive():
        self._thread.join(timeout=timeout/2)
        if self._thread.is_alive():
            if progress_callback:
                progress_callback("Warning: main thread still active")
            shutdown_success = False
    
    # Force cleanup if threads still active
    if not shutdown_success:
        self._force_cleanup()
    
    return shutdown_success

def _force_cleanup(self):
    """Force cleanup of resources when threads don't terminate gracefully."""
    # Clear queues
    try:
        while not self._queue.empty():
            self._queue.get_nowait()
    except:
        pass
    
    # Clear handlers
    self.clear_handlers()
    
    # Log warning
    self.write_log("Warning: Forced EventEngine cleanup due to thread termination failure")
```

### 2.2 Standard Test Fixtures

**Create**: `tests/fixtures/event_fixtures.py`
```python
import pytest
import threading
from foxtrot.core.event_engine import EventEngine

@pytest.fixture
def event_engine():
    """Provide EventEngine with guaranteed cleanup."""
    initial_threads = threading.active_count()
    engine = EventEngine(0.1)  # Fast timer for testing
    engine.start()
    
    yield engine
    
    # Guaranteed cleanup
    if engine._active:
        success = engine.stop(timeout=5.0)
        assert success, "EventEngine failed to stop gracefully"
    
    # Validate no thread leak
    final_threads = threading.active_count()
    assert final_threads <= initial_threads, f"Thread leak: {final_threads - initial_threads}"

@pytest.fixture
def isolated_environment():
    """Provide isolated test environment with resource tracking."""
    import tempfile
    import os
    
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Track initial resource state
        initial_threads = threading.active_count()
        
        yield temp_dir
        
        # Validate resource cleanup
        final_threads = threading.active_count()
        assert final_threads <= initial_threads, "Resource leak detected"
        
        os.chdir(original_cwd)
```

### 2.3 Mixed Framework Conversion

**Problem**: Files mixing `unittest.TestCase` with pytest decorators cause conflicts.

**Files to Convert**:
- `tests/unit/adapter/futu/test_suite.py`
- Any file with `class Test*(unittest.TestCase)` + `@pytest.mark.*`

**Conversion Pattern**:
```python
# BEFORE (Mixed - problematic)
class TestFutuApiClient(unittest.TestCase, MockFutuTestCase):
    @pytest.mark.timeout(10)
    def setUp(self):
        # unittest setup
        pass
    
    def test_connection(self):
        # test code
        pass

# AFTER (Pure pytest)
class TestFutuApiClient:
    @pytest.fixture(autouse=True)
    def setup(self, mock_futu_environment):
        # pytest setup using fixtures
        self.client = mock_futu_environment
        yield
        # automatic cleanup

    @pytest.mark.timeout(10)
    def test_connection(self, mock_futu_environment):
        # test code with injected dependencies
        pass
```

### 2.4 Resource Cleanup Validation

**Implementation**: Add to all test files
```python
@pytest.fixture(autouse=True)
def validate_resource_cleanup():
    """Automatically validate resource cleanup after each test."""
    import threading
    import gc
    
    # Initial state
    initial_threads = threading.active_count()
    gc.collect()  # Baseline garbage collection
    
    yield
    
    # Post-test validation
    gc.collect()  # Force cleanup
    final_threads = threading.active_count()
    
    if final_threads > initial_threads:
        active_threads = [t.name for t in threading.enumerate() if t.is_alive()]
        pytest.fail(f"Thread leak detected: {final_threads - initial_threads}. "
                   f"Active threads: {active_threads}")
```

**Success Criteria**:
- ✅ All EventEngine tests run without hanging
- ✅ No mixed framework patterns remain
- ✅ Resource cleanup validation passes for all tests
- ✅ Thread leaks eliminated (active_count stable)

---

## Phase 3: MEDIUM PRIORITY TEST RELIABILITY
**Priority**: MEDIUM  
**Time Estimate**: 2-3 days  
**Risk Level**: Medium  
**Dependencies**: Phase 2 complete  

### 3.1 Fix Cascading Import Dependencies

**Problem**: `test_suite.py` files create cascade failures when single imports fail.

**File**: `tests/unit/adapter/futu/test_suite.py`

**Current Pattern (Problematic)**:
```python
# Causes cascade failure if any import fails
from .test_api_client import TestFutuApiClient
from .test_futu_adapter import TestFutuAdapter
from .test_futu_mappings import TestFutuMappings
# ... more imports
```

**Solution**: Remove test_suite.py cascade pattern
1. Delete `test_suite.py` files that only aggregate imports
2. Make each test file independently discoverable
3. Use pytest's automatic discovery instead

**Alternative**: If test_suite.py must be kept:
```python
# Safe import pattern with error isolation
import importlib
import pytest

def safe_import_test_class(module_name, class_name):
    """Safely import test class with error isolation."""
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
    except ImportError as e:
        pytest.skip(f"Skipping {class_name}: {e}")
        return None

# Only import what's actually available
TestFutuApiClient = safe_import_test_class('.test_api_client', 'TestFutuApiClient')
TestFutuAdapter = safe_import_test_class('.test_futu_adapter', 'TestFutuAdapter')
```

### 3.2 Async/Sync Integration Standardization

**Problem**: Complex async/sync bridge patterns in TUI tests cause race conditions.

**File**: `tests/unit/app/tui/test_trading_panel_integration.py`

**Create**: `tests/fixtures/async_fixtures.py`
```python
import asyncio
import pytest
from foxtrot.core.event_engine import EventEngine

class AsyncSyncBridge:
    """Standard bridge for async/sync coordination in tests."""
    
    def __init__(self, event_engine, loop=None):
        self.event_engine = event_engine
        self.loop = loop or asyncio.get_event_loop()
        self._handlers = {}
    
    async def call_threadsafe(self, func, *args, timeout=5.0):
        """Call sync function from async context with timeout."""
        future = self.loop.run_in_executor(None, func, *args)
        return await asyncio.wait_for(future, timeout=timeout)
    
    def register_handler(self, event_type, handler):
        """Register async handler for sync events."""
        def bridge_handler(event):
            # Bridge from sync thread to async context
            asyncio.run_coroutine_threadsafe(handler(event), self.loop)
        
        self._handlers[event_type] = bridge_handler
        self.event_engine.register(event_type, bridge_handler)
    
    async def wait_for_event(self, event_type, timeout=5.0):
        """Wait for specific event with timeout."""
        event_received = asyncio.Event()
        received_event = None
        
        def handler(event):
            nonlocal received_event
            received_event = event
            event_received.set()
        
        self.register_handler(event_type, handler)
        
        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            return received_event
        finally:
            # Cleanup handler
            if event_type in self._handlers:
                del self._handlers[event_type]

@pytest.fixture
async def async_event_bridge(event_engine):
    """Provide standardized async/sync bridge."""
    bridge = AsyncSyncBridge(event_engine)
    yield bridge
    # Automatic cleanup handled by event_engine fixture
```

### 3.3 Test Independence Validation

**Create**: `scripts/test_independence_check.py`
```python
#!/usr/bin/env python3
"""Validate each test file can run independently."""

import subprocess
import sys
from pathlib import Path

def test_file_independence():
    """Test each file runs independently."""
    test_files = list(Path("tests").rglob("test_*.py"))
    failed_files = []
    
    for test_file in test_files:
        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                failed_files.append((test_file, result.stderr))
                print(f"❌ {test_file}: Independence test failed")
            else:
                print(f"✅ {test_file}: Independence test passed")
        except subprocess.TimeoutExpired:
            failed_files.append((test_file, "Timeout"))
            print(f"⏰ {test_file}: Timeout")
    
    return len(failed_files) == 0, failed_files

if __name__ == "__main__":
    success, failures = test_file_independence()
    if not success:
        print(f"\nFailed files: {len(failures)}")
        for file, error in failures:
            print(f"  {file}: {error}")
    sys.exit(0 if success else 1)
```

**Success Criteria**:
- ✅ No cascading import failures
- ✅ Each test file runs independently
- ✅ Async/sync integration stable and predictable
- ✅ Race conditions eliminated in TUI tests

---

## Phase 4: ENHANCEMENT QUALITY IMPROVEMENTS
**Priority**: ENHANCEMENT  
**Time Estimate**: 1-2 days  
**Risk Level**: Low  
**Dependencies**: Phase 3 complete  

### 4.1 Framework Standardization

**Action**: Convert all remaining unittest patterns to pure pytest

**Files to Standardize**:
- Any remaining `unittest.TestCase` classes
- setUp/tearDown methods → pytest fixtures
- `self.assert*` → `assert` statements
- `self.assertEqual` → `assert a == b`

**Pattern Conversion**:
```python
# BEFORE (unittest)
class TestExample(unittest.TestCase):
    def setUp(self):
        self.client = Client()
    
    def tearDown(self):
        self.client.close()
    
    def test_connection(self):
        self.assertTrue(self.client.connect())
        self.assertEqual(self.client.status, "connected")

# AFTER (pytest)
class TestExample:
    @pytest.fixture
    def client(self):
        client = Client()
        yield client
        client.close()
    
    def test_connection(self, client):
        assert client.connect()
        assert client.status == "connected"
```

### 4.2 Reusable Test Utilities

**Create**: `tests/utils/test_helpers.py`
```python
"""Reusable test utilities and helpers."""

import time
import threading
from contextlib import contextmanager
from foxtrot.core.event_engine import EventEngine

class TestEventCollector:
    """Collect events during tests for assertion."""
    
    def __init__(self, event_engine):
        self.event_engine = event_engine
        self.collected_events = []
        self._handlers = {}
    
    def collect(self, event_type):
        """Start collecting events of specific type."""
        def handler(event):
            self.collected_events.append(event)
        
        self._handlers[event_type] = handler
        self.event_engine.register(event_type, handler)
    
    def stop_collecting(self, event_type):
        """Stop collecting specific event type."""
        if event_type in self._handlers:
            handler = self._handlers.pop(event_type)
            self.event_engine.unregister(event_type, handler)
    
    def clear(self):
        """Clear collected events."""
        self.collected_events.clear()
    
    def wait_for_events(self, count, timeout=5.0):
        """Wait for specific number of events."""
        start_time = time.time()
        while len(self.collected_events) < count:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Expected {count} events, got {len(self.collected_events)}")
            time.sleep(0.1)

@contextmanager
def temporary_handlers(event_engine, handlers):
    """Temporarily register event handlers."""
    for event_type, handler in handlers.items():
        event_engine.register(event_type, handler)
    
    try:
        yield
    finally:
        for event_type, handler in handlers.items():
            event_engine.unregister(event_type, handler)

def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
    """Wait for condition to become true."""
    start_time = time.time()
    while not condition_func():
        if time.time() - start_time > timeout:
            raise TimeoutError("Condition not met within timeout")
        time.sleep(interval)
```

### 4.3 Automated Quality Gates

**Create**: `.github/workflows/test-quality.yml` (if using GitHub)
```yaml
name: Test Quality Gates

on: [push, pull_request]

jobs:
  test-quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Validate test imports
      run: python scripts/validate_test_imports.py
    
    - name: Test independence check
      run: python scripts/test_independence_check.py
    
    - name: Run test suite with coverage
      run: |
        pytest --cov=foxtrot --cov-report=xml --cov-fail-under=80
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
```

**Create**: `scripts/pre_commit_test_validation.py`
```python
#!/usr/bin/env python3
"""Pre-commit validation for test quality."""

import subprocess
import sys

def run_validation():
    """Run all test validations."""
    checks = [
        ("Import validation", ["python", "scripts/validate_test_imports.py"]),
        ("Collection test", ["pytest", "--collect-only"]),
        ("Quick smoke test", ["pytest", "tests/unit/util/", "-v", "--tb=short"]),
    ]
    
    failed_checks = []
    for name, command in checks:
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {name}: PASSED")
            else:
                print(f"❌ {name}: FAILED")
                print(result.stderr)
                failed_checks.append(name)
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            failed_checks.append(name)
    
    return len(failed_checks) == 0

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
```

**Success Criteria**:
- ✅ All tests use pytest exclusively
- ✅ Reusable test utilities available
- ✅ Automated quality gates in place
- ✅ Pre-commit validation working

---

## Phase 5: MONITORING CONTINUOUS IMPROVEMENT
**Priority**: MONITORING  
**Time Estimate**: Ongoing  
**Risk Level**: Low  
**Dependencies**: All previous phases  

### 5.1 Test Execution Monitoring

**Create**: `scripts/test_health_monitor.py`
```python
#!/usr/bin/env python3
"""Monitor test suite health and performance."""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path

class TestHealthMonitor:
    def __init__(self, results_file="test_health_results.json"):
        self.results_file = Path(results_file)
        self.load_history()
    
    def load_history(self):
        """Load historical test results."""
        if self.results_file.exists():
            with open(self.results_file) as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def run_health_check(self):
        """Run comprehensive test health check."""
        start_time = time.time()
        
        # Run full test suite with timing
        result = subprocess.run(
            ["pytest", "-v", "--tb=short", "--durations=10"],
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        # Parse results
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "returncode": result.returncode,
            "passed": result.stdout.count(" PASSED"),
            "failed": result.stdout.count(" FAILED"),
            "errors": result.stdout.count(" ERROR"),
            "skipped": result.stdout.count(" SKIPPED"),
        }
        
        # Analyze trends
        if len(self.history) > 0:
            last_run = self.history[-1]
            health_data["duration_change"] = duration - last_run["duration"]
            health_data["failure_change"] = health_data["failed"] - last_run["failed"]
        
        self.history.append(health_data)
        
        # Save results
        with open(self.results_file, "w") as f:
            json.dump(self.history, f, indent=2)
        
        return health_data
    
    def report_trends(self):
        """Generate trend report."""
        if len(self.history) < 2:
            return "Insufficient data for trend analysis"
        
        recent = self.history[-5:]  # Last 5 runs
        avg_duration = sum(r["duration"] for r in recent) / len(recent)
        avg_failures = sum(r["failed"] for r in recent) / len(recent)
        
        report = f"""
Test Health Trends (Last {len(recent)} runs):
- Average Duration: {avg_duration:.2f}s
- Average Failures: {avg_failures:.1f}
- Success Rate: {(1 - avg_failures/max(1, sum(r["passed"] + r["failed"] for r in recent)/len(recent)))*100:.1f}%
"""
        return report

if __name__ == "__main__":
    monitor = TestHealthMonitor()
    health = monitor.run_health_check()
    
    print(f"Test Health Check Results:")
    print(f"Duration: {health['duration']:.2f}s")
    print(f"Passed: {health['passed']}")
    print(f"Failed: {health['failed']}")
    print(f"Errors: {health['errors']}")
    print(f"Skipped: {health['skipped']}")
    
    print(monitor.report_trends())
```

### 5.2 Regression Prevention

**Create**: `scripts/regression_detector.py`
```python
#!/usr/bin/env python3
"""Detect performance and reliability regressions."""

import json
import sys
from pathlib import Path

class RegressionDetector:
    def __init__(self, threshold_duration=1.5, threshold_failures=0.1):
        self.threshold_duration = threshold_duration  # 50% duration increase
        self.threshold_failures = threshold_failures  # 10% failure rate increase
    
    def check_regressions(self, health_file="test_health_results.json"):
        """Check for regressions in latest test run."""
        if not Path(health_file).exists():
            return False, "No health history available"
        
        with open(health_file) as f:
            history = json.load(f)
        
        if len(history) < 2:
            return False, "Insufficient history for regression detection"
        
        current = history[-1]
        baseline = history[-2]
        
        regressions = []
        
        # Duration regression
        if "duration_change" in current and current["duration_change"] > 0:
            duration_increase = current["duration_change"] / baseline["duration"]
            if duration_increase > self.threshold_duration:
                regressions.append(f"Duration regression: {duration_increase:.1%} increase")
        
        # Failure rate regression
        if current["failed"] > baseline["failed"]:
            total_current = current["passed"] + current["failed"]
            total_baseline = baseline["passed"] + baseline["failed"]
            
            if total_current > 0 and total_baseline > 0:
                current_rate = current["failed"] / total_current
                baseline_rate = baseline["failed"] / total_baseline
                
                if current_rate > baseline_rate + self.threshold_failures:
                    regressions.append(f"Failure rate regression: {current_rate:.1%} vs {baseline_rate:.1%}")
        
        return len(regressions) == 0, regressions
    
if __name__ == "__main__":
    detector = RegressionDetector()
    no_regression, issues = detector.check_regressions()
    
    if no_regression:
        print("✅ No regressions detected")
        sys.exit(0)
    else:
        print("❌ Regressions detected:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
```

### 5.3 Continuous Quality Dashboard

**Create**: `scripts/generate_quality_report.py`
```python
#!/usr/bin/env python3
"""Generate comprehensive test quality report."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def generate_quality_report():
    """Generate comprehensive quality report."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "sections": {}
    }
    
    # Test coverage
    coverage_result = subprocess.run(
        ["pytest", "--cov=foxtrot", "--cov-report=json"],
        capture_output=True
    )
    
    if coverage_result.returncode == 0 and Path("coverage.json").exists():
        with open("coverage.json") as f:
            coverage_data = json.load(f)
        report["sections"]["coverage"] = {
            "total_coverage": coverage_data["totals"]["percent_covered"],
            "missing_lines": coverage_data["totals"]["missing_lines"],
            "files_low_coverage": [
                f for f, data in coverage_data["files"].items() 
                if data["summary"]["percent_covered"] < 80
            ]
        }
    
    # Test counts by category
    test_files = {
        "unit": list(Path("tests/unit").rglob("test_*.py")),
        "integration": list(Path("tests/integration").rglob("test_*.py")),
        "e2e": list(Path("tests/e2e").rglob("test_*.py"))
    }
    
    report["sections"]["test_counts"] = {
        category: len(files) for category, files in test_files.items()
    }
    
    # Performance metrics
    if Path("test_health_results.json").exists():
        with open("test_health_results.json") as f:
            health_history = json.load(f)
        
        if health_history:
            latest = health_history[-1]
            report["sections"]["performance"] = {
                "last_run_duration": latest["duration"],
                "last_run_results": {
                    "passed": latest["passed"],
                    "failed": latest["failed"],
                    "errors": latest["errors"]
                }
            }
    
    # Generate HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Quality Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .metric {{ padding: 10px; margin: 10px; border: 1px solid #ddd; }}
            .good {{ background-color: #d4edda; }}
            .warning {{ background-color: #fff3cd; }}
            .error {{ background-color: #f8d7da; }}
        </style>
    </head>
    <body>
        <h1>Test Quality Report</h1>
        <p>Generated: {report['generated_at']}</p>
        
        <h2>Coverage</h2>
        <div class="metric {'good' if report.get('sections', {}).get('coverage', {}).get('total_coverage', 0) >= 80 else 'warning'}">
            Total Coverage: {report.get('sections', {}).get('coverage', {}).get('total_coverage', 'N/A')}%
        </div>
        
        <h2>Test Counts</h2>
        {chr(10).join(f'<div class="metric">{{cat.title()}}: {{count}} files</div>' 
                      for cat, count in report.get('sections', {}).get('test_counts', {}).items())}
        
        <h2>Performance</h2>
        <div class="metric">
            Last Run Duration: {report.get('sections', {}).get('performance', {}).get('last_run_duration', 'N/A')}s
        </div>
    </body>
    </html>
    """
    
    with open("test_quality_report.html", "w") as f:
        f.write(html_report)
    
    return report

if __name__ == "__main__":
    report = generate_quality_report()
    print("✅ Quality report generated: test_quality_report.html")
    print(json.dumps(report, indent=2))
```

---

## Verification Strategy

### Phase 1 Verification
```bash
# Test collection works
pytest --collect-only
echo "Exit code: $?"

# Import validation
python scripts/validate_test_imports.py

# Basic smoke test
pytest tests/unit/util/test_constants.py -v
```

### Phase 2 Verification
```bash
# EventEngine tests without hanging
timeout 60 pytest tests/unit/core/test_event_engine_unit.py -v

# Resource cleanup validation
pytest tests/unit/adapter/binance/ -v --resource-check

# Mixed framework elimination check
grep -r "unittest.TestCase" tests/ | grep "@pytest"
```

### Phase 3 Verification
```bash
# Independent test execution
pytest tests/unit/adapter/futu/test_api_client.py -v

# Async/sync integration stability
pytest tests/unit/app/tui/ -v --count=5

# Import cascade elimination
python scripts/test_independence_check.py
```

### Phase 4 Verification
```bash
# Framework standardization
grep -r "unittest.TestCase" tests/ | wc -l  # Should be 0

# Quality gates working
python scripts/pre_commit_test_validation.py

# Coverage requirements
pytest --cov=foxtrot --cov-fail-under=80
```

### Phase 5 Verification
```bash
# Health monitoring
python scripts/test_health_monitor.py

# Regression detection
python scripts/regression_detector.py

# Quality reporting
python scripts/generate_quality_report.py
```

---

## Risk Assessment & Mitigation

### High Risk Items

**EventEngine Threading Changes**
- **Risk**: May introduce new race conditions
- **Mitigation**: Extensive testing with thread safety validation
- **Rollback Plan**: Revert to original EventEngine, fix imports only

**Framework Conversion**
- **Risk**: May break existing test logic
- **Mitigation**: Convert incrementally, validate each conversion
- **Rollback Plan**: Keep unittest patterns for complex cases

### Medium Risk Items

**Test Independence Changes**
- **Risk**: May reveal hidden dependencies
- **Mitigation**: Fix dependencies systematically, not all at once
- **Recovery**: Add skip markers for problematic tests temporarily

**Async/Sync Integration**
- **Risk**: Complex timing issues
- **Mitigation**: Use proven patterns, extensive timeout testing
- **Recovery**: Simplify integration, use synchronous alternatives

### Low Risk Items

**Import Fixes** - Straightforward, low risk
**Monitoring Setup** - Non-invasive, can be added incrementally
**Quality Gates** - Can be implemented without affecting existing tests

---

## Success Metrics

### Immediate Success (Phase 1)
- ✅ Zero test collection errors
- ✅ All pytest imports working
- ✅ Basic test execution possible

### Short-term Success (Phases 2-3)
- ✅ <5% flaky test rate
- ✅ All tests complete within timeout periods
- ✅ No resource leaks detected
- ✅ Each test file runs independently

### Long-term Success (Phases 4-5)
- ✅ >80% code coverage maintained
- ✅ <2% test failure rate in CI
- ✅ Test suite duration <10 minutes
- ✅ Zero framework mixing patterns
- ✅ Automated quality gates passing

---

## Implementation Timeline

### Week 1
- **Day 1**: Phase 1 (Import fixes) - 3 hours
- **Day 2-3**: Phase 2 (EventEngine fixes, resource cleanup) - 2 days
- **Day 4-5**: Phase 3 (Test reliability, independence) - 2 days

### Week 2
- **Day 1-2**: Phase 4 (Quality improvements, standardization) - 2 days
- **Day 3**: Phase 5 (Monitoring setup) - 1 day
- **Day 4-5**: Testing, validation, documentation - 2 days

### Ongoing
- **Weekly**: Health monitoring and regression detection
- **Monthly**: Quality report review and improvement planning
- **Quarterly**: Test architecture review and optimization

---

## Conclusion

This comprehensive plan addresses both immediate blocking issues and long-term test reliability concerns. The phased approach ensures that critical issues are resolved first while building a foundation for maintainable, reliable testing going forward.

**Key Benefits**:
- ✅ Immediate restoration of test functionality
- ✅ Elimination of threading and resource management issues  
- ✅ Improved test isolation and independence
- ✅ Standardized, maintainable test patterns
- ✅ Automated quality assurance and monitoring

**Expected Outcomes**:
- Complete test suite functionality restored
- <2% flaky test rate achieved
- Automated quality gates preventing future regressions
- Comprehensive monitoring and health tracking
- Foundation for continued test reliability improvements

---

**Plan Created**: 2025-07-31  
**Total Estimated Effort**: 8-12 days  
**Implementation Priority**: CRITICAL → HIGH → MEDIUM → ENHANCEMENT → MONITORING  
**Next Action**: Begin Phase 1 import fixes immediately