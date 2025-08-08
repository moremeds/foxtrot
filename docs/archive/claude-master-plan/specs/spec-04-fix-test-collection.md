# Specification: Fix Test Collection

**Spec ID**: spec-04  
**Phase**: 2 - Test Infrastructure Repair  
**Priority**: P0 - Critical  
**Effort**: 4 hours

## Problem Statement

Tests exist but pytest cannot collect them:
```bash
$ pytest tests/unit/
collected 0 items
```

This makes development dangerous as changes cannot be verified.

## Solution Approach

### Step 1: Diagnose Collection Issues
```bash
# Verbose collection to see problems
pytest tests/unit/ --collect-only -vv

# Check for import errors
python -c "import tests.unit.core.test_event_engine_unit"
```

### Step 2: Fix Import Paths
Common issues:
- Missing __init__.py files
- Incorrect import statements
- Circular dependencies in test files

### Step 3: Create Proper Test Structure
```python
# Correct test file structure
import pytest
from unittest.mock import Mock, patch

# Fix imports to use absolute paths
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.event_type import Event

class TestEventEngine:
    """Test event engine functionality"""
    
    def test_engine_starts(self):
        """Test that engine can be created and started"""
        engine = EventEngine()
        assert engine is not None
        
    def test_engine_stops(self):
        """Test that engine stops cleanly"""
        engine = EventEngine()
        engine.start()
        engine.stop()
        assert not engine.active
```

## Implementation Details

### Common Problems to Fix

1. **Missing Test Markers**
```python
# Before (not collected):
def check_something():
    assert True

# After (collected):
def test_something():  # Must start with 'test_'
    assert True
```

2. **Import Errors**
```python
# Before (fails):
from ...core import EventEngine  # Relative import issues

# After (works):
from foxtrot.core.event_engine import EventEngine
```

3. **Missing Fixtures**
```python
# Create conftest.py with shared fixtures
# tests/conftest.py
import pytest
from foxtrot.core.event_engine import EventEngine

@pytest.fixture
def event_engine():
    engine = EventEngine()
    yield engine
    engine.stop()
```

## Success Criteria

### Measurable Outcomes
- ✅ `pytest tests/` collects >0 tests
- ✅ At least 10 tests can run
- ✅ No import errors during collection
- ✅ Clear test output

### Verification Method
```bash
# Should show collected tests
pytest tests/ --collect-only | grep "test session starts"
pytest tests/ --collect-only | grep "collected"

# Should run without errors
pytest tests/unit/core/ -v

# Should show test names
pytest tests/ --collect-only -q
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Hidden dependencies | High | Medium | Mock all external dependencies |
| Broken fixtures | Medium | Medium | Start with simple tests |
| Import cycles | Low | High | Use absolute imports |

## Estimated Timeline

- Hour 1: Diagnose collection issues
- Hour 2: Fix import problems
- Hour 3: Create basic conftest.py
- Hour 4: Verify all tests collect

## Dependencies

- Requires spec-01 and spec-02 complete (clean file structure)

## Notes

- Don't write new tests yet, just fix collection
- Focus on making existing tests discoverable
- Simple fixes only - no test refactoring