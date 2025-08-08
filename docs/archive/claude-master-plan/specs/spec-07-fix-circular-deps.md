# Specification: Fix Circular Dependencies

**Spec ID**: spec-07  
**Phase**: 3 - Architecture Cleanup  
**Priority**: P1 - High  
**Effort**: 6 hours

## Problem Statement

Circular dependencies make the code:
- Hard to test (can't mock dependencies)
- Hard to understand (unclear relationships)
- Prone to import errors
- Violates clean architecture principles

Common patterns found:
- Engine imports Adapter, Adapter imports Engine
- Utils import Models, Models import Utils
- UI imports Core, Core imports UI

## Solution Approach

### Step 1: Detect All Circular Dependencies
```bash
# Use tool to find cycles
pip install pydeps
pydeps foxtrot --max-bacon=2 --pylib-all > dependencies.svg

# Or manually check
python -c "import foxtrot" 2>&1 | grep "circular import"
```

### Step 2: Break Cycles with Interfaces
```python
# Before (CIRCULAR):
# engine.py
from foxtrot.adapter import BaseAdapter
class Engine:
    def __init__(self, adapter: BaseAdapter):
        self.adapter = adapter

# adapter.py  
from foxtrot.engine import Engine
class BaseAdapter:
    def __init__(self, engine: Engine):
        self.engine = engine

# After (FIXED):
# interfaces.py
from abc import ABC, abstractmethod
class IEngine(ABC):
    @abstractmethod
    def process_event(self, event): pass

class IAdapter(ABC):
    @abstractmethod
    def submit_order(self, order): pass

# engine.py
from foxtrot.interfaces import IAdapter
class Engine(IEngine):
    def __init__(self, adapter: IAdapter):
        self.adapter = adapter

# adapter.py
from foxtrot.interfaces import IEngine  
class BaseAdapter(IAdapter):
    def __init__(self, engine: IEngine):
        self.engine = engine
```

### Step 3: Dependency Inversion
```python
# Before (tight coupling):
class OrderManager:
    def __init__(self):
        from foxtrot.database import Database
        self.db = Database()  # Creates dependency

# After (dependency injection):
class OrderManager:
    def __init__(self, db=None):
        self.db = db  # Injected dependency
```

## Implementation Details

### Known Circular Dependencies

1. **Engine ↔ Adapter**
   - Location: server/engine.py ↔ adapter/base_adapter.py
   - Solution: Use event system for communication
   - Impact: High

2. **Utils ↔ Objects**
   - Location: util/utility.py ↔ util/object.py
   - Solution: Move shared code to util/common.py
   - Impact: Medium

3. **UI ↔ Core**
   - Location: app/ui/ ↔ core/
   - Solution: UI should only import from core, never reverse
   - Impact: Medium

### Breaking Strategies

1. **Event-Based Decoupling**
```python
# Instead of direct calls
adapter.engine.process_order(order)

# Use events
event_engine.put(Event(EVENT_ORDER, order))
```

2. **Extract Common Code**
```python
# Move shared utilities to separate module
# util/common.py - no dependencies
# util/converters.py - imports from common
# util/validators.py - imports from common
```

3. **Lazy Imports** (Last Resort)
```python
def process_order(order):
    # Import only when needed
    from foxtrot.engine import Engine
    engine = Engine()
    engine.process(order)
```

## Success Criteria

### Measurable Outcomes
- ✅ No circular import errors
- ✅ Clean dependency graph
- ✅ All imports at top of file
- ✅ Tests can mock any dependency

### Verification Method
```python
# Test for circular imports
import sys
import foxtrot
# Should not raise ImportError

# Generate dependency graph
# Should show tree structure, no cycles

# Test mockability
from unittest.mock import Mock
mock_engine = Mock(spec=IEngine)
adapter = BaseAdapter(mock_engine)
# Should work without real engine
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | Medium | High | Use interfaces to maintain compatibility |
| Performance impact | Low | Low | Events are async anyway |
| Complex refactoring | High | Medium | Fix one cycle at a time |

## Estimated Timeline

- Hour 1: Map all dependencies
- Hour 2: Create interface definitions
- Hour 3-4: Break Engine ↔ Adapter cycle
- Hour 5: Break Utils cycles
- Hour 6: Testing and verification

## Dependencies

- Complete after spec-01 (file splitting)
- Complete after spec-02 (remove globals)

## Notes

- Don't over-abstract with too many interfaces
- Keep changes minimal and focused
- Test after breaking each cycle
- Document new relationships