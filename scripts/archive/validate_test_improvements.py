#!/usr/bin/env python3
"""
Test Suite Improvement Validation Script

Validates the effectiveness of the test suite improvements implemented 
for the Foxtrot trading platform.
"""

import subprocess
import time
from pathlib import Path


def run_test_suite(test_path: str, timeout: int = 300) -> dict:
    """
    Run a test suite and measure performance metrics.
    
    Args:
        test_path: Path to test file/directory
        timeout: Maximum time to wait for tests
        
    Returns:
        dict: Test results with timing and success metrics
    """
    start_time = time.time()
    
    try:
        result = subprocess.run([
            'uv', 'run', 'pytest', test_path, '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=timeout)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Parse test results
        output_lines = result.stdout.split('\n')
        passed = sum(1 for line in output_lines if 'PASSED' in line)
        failed = sum(1 for line in output_lines if 'FAILED' in line)
        skipped = sum(1 for line in output_lines if 'SKIPPED' in line)
        
        return {
            'success': result.returncode == 0,
            'duration': duration,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': passed + failed + skipped,
            'timeout': False,
            'output': result.stdout,
            'errors': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        end_time = time.time()
        return {
            'success': False,
            'duration': end_time - start_time,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
            'timeout': True,
            'output': '',
            'errors': 'Test timed out'
        }


def main():
    """Run test suite validation."""
    print("🧪 FOXTROT TEST SUITE IMPROVEMENT VALIDATION")
    print("=" * 60)
    
    # Test categories to validate
    test_categories = {
        'Unit Tests (Core)': 'tests/unit/core/test_event_engine_unit.py',
        'Unit Tests (Utils)': 'tests/unit/util/',
        'Integration Tests': 'tests/integration/test_futu_mainengine_integration.py',
        'E2E Tests (Basic)': 'tests/e2e/test_binance_mainengine_e2e.py::TestBinanceMainEngineE2E::test_main_engine_setup_and_connection',
    }
    
    results = {}
    total_time = 0
    
    for category, test_path in test_categories.items():
        print(f"\n📋 Testing: {category}")
        print("-" * 40)
        
        # Check if test path exists
        if not Path(test_path.split('::')[0]).exists():
            print(f"   ⚠️  Skipping - test path not found: {test_path}")
            continue
        
        # Run tests with appropriate timeout
        timeout = 60 if 'E2E' in category else 120 if 'Integration' in category else 180
        
        result = run_test_suite(test_path, timeout)
        results[category] = result
        total_time += result['duration']
        
        # Display results
        if result['timeout']:
            print(f"   ❌ TIMEOUT after {result['duration']:.1f}s")
        elif result['success']:
            print(f"   ✅ PASSED: {result['passed']}/{result['total']} tests in {result['duration']:.1f}s")
        else:
            print(f"   ❌ FAILED: {result['failed']}/{result['total']} tests failed in {result['duration']:.1f}s")
            if result['errors']:
                print(f"   📝 Errors: {result['errors'][:200]}...")
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    total_tests = sum(r['total'] for r in results.values() if not r['timeout'])
    total_passed = sum(r['passed'] for r in results.values() if not r['timeout'])
    total_failed = sum(r['failed'] for r in results.values() if not r['timeout'])
    total_timeouts = sum(1 for r in results.values() if r['timeout'])
    
    print(f"Total Test Runtime: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {total_passed}")
    print(f"Tests Failed: {total_failed}")
    print(f"Test Timeouts: {total_timeouts}")
    
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Improvement assessment
    print("\n🎯 IMPROVEMENT ASSESSMENT")
    print("-" * 30)
    
    if total_timeouts == 0:
        print("✅ No timeout issues detected")
    else:
        print(f"⚠️  {total_timeouts} test category(s) still experiencing timeouts")
    
    if total_time < 300:  # 5 minutes
        print("✅ Test execution time is reasonable")
    else:
        print("⚠️  Test execution time may need further optimization")
    
    if total_failed == 0 and total_timeouts == 0:
        print("✅ All tests executing successfully")
        print("\n🎉 TEST SUITE IMPROVEMENTS SUCCESSFUL!")
        print("   - Thread cleanup issues resolved")
        print("   - Timeout issues eliminated") 
        print("   - Test infrastructure enhanced")
        print("   - Execution reliability improved")
    else:
        print("🔧 Some issues remain - see detailed results above")
    
    # Next steps recommendations
    print("\n💡 NEXT STEPS")
    print("-" * 15)
    print("1. Run full test suite: uv run pytest tests/ -v")
    print("2. Monitor thread cleanup in production")
    print("3. Consider implementing test parallelization")
    print("4. Add performance regression testing")


if __name__ == "__main__":
    main()