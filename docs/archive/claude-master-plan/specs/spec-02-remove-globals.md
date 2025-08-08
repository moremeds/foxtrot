# Specification: Remove Global Instances

**Spec ID**: spec-02  
**Phase**: 1 - Code Health Emergency  
**Priority**: P0 - Critical  
**Effort**: 4 hours

## Problem Statement

Global instances and import-time side effects violate CLAUDE.md principles:
- Global variables make testing impossible
- Import side effects cause unpredictable behavior
- Singleton patterns without proper initialization

Examples found:
- Global event engine instances
- Logger instances created at import
- Database connections initialized globally

## Solution Approach

### Step 1: Identify All Global Instances
```bash
# Search for global instances
grep -r "^[a-z_]*\s*=\s*[A-Z]" --include="*.py" foxtrot/
```

### Step 2: Convert to Factory Pattern
```python
# Before (BAD):
# foxtrot/util/logger.py
logger = Logger("global_logger")  # Created at import!

# After (GOOD):
# foxtrot/util/logger.py
_logger = None

def get_logger():
    global _logger
    if _logger is None:
        _logger = Logger("foxtrot")
    return _logger
```

### Step 3: Dependency Injection
```python
# Before (BAD):
class SomeEngine:
    def __init__(self):
        self.logger = logger  # Uses global!

# After (GOOD):
class SomeEngine:
    def __init__(self, logger=None):
        self.logger = logger or get_logger()
```

## Implementation Details

### Known Globals to Fix

1. **Event Engine**
   - Location: Various adapter files
   - Solution: Pass through constructor
   - Impact: High - affects all adapters

2. **Logger Instances**
   - Location: Throughout codebase
   - Solution: Use get_logger() factory
   - Impact: Medium - affects logging

3. **Database Connections**
   - Location: Server modules
   - Solution: Connection manager class
   - Impact: High - affects persistence

## Success Criteria

### Measurable Outcomes
- ✅ No global instances in module scope
- ✅ All imports have no side effects
- ✅ Tests can mock all dependencies
- ✅ Clean import without initialization

### Verification Method
```python
# Test clean import
python -c "import foxtrot"
# Should not create any instances

# Test mockability
def test_with_mock():
    mock_logger = Mock()
    engine = SomeEngine(logger=mock_logger)
    assert engine.logger is mock_logger
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking initialization | Medium | High | Test each change thoroughly |
| Performance impact | Low | Low | Lazy initialization pattern |
| Test breakage | High | Medium | Update tests to use factories |

## Estimated Timeline

- Hour 1: Identify all global instances
- Hour 2: Convert loggers to factory pattern
- Hour 3: Fix event engine initialization
- Hour 4: Testing and verification

## Dependencies

- Should be done after spec-01 (file splitting) for cleaner structure

## Notes

- Keep changes minimal - only remove globals
- Don't redesign architecture
- Maintain backward compatibility where possible