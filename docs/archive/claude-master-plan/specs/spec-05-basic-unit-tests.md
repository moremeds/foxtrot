# Specification: Basic Unit Tests

**Spec ID**: spec-05  
**Phase**: 2 - Test Infrastructure Repair  
**Priority**: P1 - High  
**Effort**: 8 hours

## Problem Statement

No working tests for core components:
- Event Engine - heart of the system, untested
- Adapters - critical integration points, untested  
- Data Objects - core data structures, untested

This makes any refactoring dangerous.

## Solution Approach

### TDD Principle from CLAUDE.md
Write ONE test at a time following TDD:
1. RED - Write failing test
2. GREEN - Make it pass
3. REFACTOR - Clean up

### Priority Components to Test

1. **Event Engine** (Most Critical)
```python
# tests/unit/core/test_event_engine.py
class TestEventEngine:
    def test_put_and_get_event(self):
        """Test basic event flow"""
        engine = EventEngine()
        engine.start()
        
        event = Event("TEST_EVENT", {"data": "test"})
        engine.put(event)
        
        # Should process event
        time.sleep(0.1)
        engine.stop()
        # Add assertion based on behavior
        
    def test_register_handler(self):
        """Test handler registration"""
        engine = EventEngine()
        called = False
        
        def handler(event):
            nonlocal called
            called = True
            
        engine.register("TEST_EVENT", handler)
        engine.start()
        engine.put(Event("TEST_EVENT", {}))
        time.sleep(0.1)
        
        assert called
```

2. **Data Objects** (Foundation)
```python
# tests/unit/util/test_objects.py
class TestOrderData:
    def test_create_order(self):
        """Test order creation"""
        order = OrderData(
            symbol="BTCUSDT",
            exchange="BINANCE",
            direction=Direction.LONG,
            volume=0.01
        )
        assert order.symbol == "BTCUSDT"
        assert order.vt_symbol == "BTCUSDT.BINANCE"
        
    def test_order_validation(self):
        """Test order validates data"""
        with pytest.raises(ValueError):
            OrderData(
                symbol="",  # Invalid
                exchange="BINANCE",
                direction=Direction.LONG,
                volume=-1  # Invalid
            )
```

3. **Adapter Base** (Critical Interface)
```python
# tests/unit/adapter/test_base_adapter.py
class TestBaseAdapter:
    def test_adapter_lifecycle(self):
        """Test adapter can start and stop"""
        adapter = MockAdapter()
        
        adapter.connect()
        assert adapter.status == "CONNECTED"
        
        adapter.close()
        assert adapter.status == "DISCONNECTED"
        
    def test_adapter_thread_safety(self):
        """Test adapter is thread-safe"""
        adapter = MockAdapter()
        errors = []
        
        def stress_test():
            try:
                for _ in range(100):
                    adapter.submit_order(create_test_order())
            except Exception as e:
                errors.append(e)
                
        threads = [Thread(target=stress_test) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        assert len(errors) == 0
```

## Implementation Details

### Test Structure Per Component

Each component gets:
1. Basic functionality test
2. Error handling test  
3. Thread safety test (if applicable)
4. Integration point test

### Mocking Strategy
```python
# tests/mocks/mock_adapter.py
class MockAdapter(BaseAdapter):
    """Simple mock for testing"""
    
    def connect(self):
        self.status = "CONNECTED"
        
    def submit_order(self, order):
        # Simulate order submission
        return f"ORDER_{random.randint(1000, 9999)}"
```

## Success Criteria

### Measurable Outcomes
- ✅ 1+ test per major component
- ✅ Event Engine: 5+ tests
- ✅ Data Objects: 10+ tests
- ✅ Adapters: 3+ tests each
- ✅ 50% coverage on tested components

### Verification Method
```bash
# Run tests with coverage
pytest tests/unit/ --cov=foxtrot --cov-report=term-missing

# Should show:
# - EventEngine > 50% coverage
# - Data objects > 70% coverage  
# - Base adapter > 40% coverage
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Complex mocking | High | Medium | Start with simple mocks |
| Flaky tests | Medium | High | Avoid timing-dependent tests |
| Low coverage | Medium | Low | Focus on critical paths only |

## Estimated Timeline

- Hour 1-2: Event Engine tests
- Hour 3-4: Data Object tests
- Hour 5-6: Adapter base tests
- Hour 7: Mock infrastructure
- Hour 8: Coverage analysis

## Dependencies

- Requires spec-04 complete (tests must collect)

## Notes

- ONE test at a time - follow TDD strictly
- Don't aim for 100% coverage
- Test behavior, not implementation
- Keep tests simple and readable