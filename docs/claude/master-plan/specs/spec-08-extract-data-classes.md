# Specification: Extract Data Classes

**Spec ID**: spec-08  
**Phase**: 3 - Architecture Cleanup  
**Priority**: P1 - High  
**Effort**: 4 hours

## Problem Statement

Data clumps (multiple parameters always passed together) indicate missing abstractions:
- Order submission methods with 8+ parameters
- Market data handlers with 6+ related fields
- Configuration passed as individual values

This violates clean code principles and makes methods hard to use and test.

## Solution Approach

### Identify Data Clumps
```python
# Before (BAD - Data Clump):
def submit_order(symbol, exchange, direction, volume, price, 
                 order_type, time_in_force, reference):
    # 8 parameters always passed together
    pass

# After (GOOD - Data Class):
@dataclass
class OrderRequest:
    symbol: str
    exchange: str
    direction: Direction
    volume: float
    price: Optional[float]
    order_type: OrderType
    time_in_force: TimeInForce
    reference: Optional[str]

def submit_order(request: OrderRequest):
    # Single parameter, clear interface
    pass
```

## Success Criteria

- ✅ No method with >4 parameters
- ✅ Related data grouped into classes
- ✅ Type hints on all data classes
- ✅ Validation in data class __post_init__

## Verification Method

```bash
# Find methods with too many parameters
grep -r "def.*(.*):" --include="*.py" | grep -E ",.*,.*,.*," 
# Should return minimal results
```