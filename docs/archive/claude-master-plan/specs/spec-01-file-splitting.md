# Specification: File Splitting

**Spec ID**: spec-01  
**Phase**: 1 - Code Health Emergency  
**Priority**: P0 - Critical  
**Effort**: 8 hours

## Problem Statement

Multiple files violate the 200-line limit from CLAUDE.md by massive margins:
- `foxtrot/app/ui/widget.py`: 1290 lines (6x over limit!)
- `foxtrot/util/utility.py`: 1051 lines (5x over limit!)
- `foxtrot/app/tui/components/trading_panel.py`: 1047 lines
- Many more files with 400-700+ lines

This makes the code unmaintainable, untestable, and violates core architectural standards.

## Solution Approach

### Step 1: Identify Logical Boundaries
For each oversized file, identify natural splitting points:
- Separate classes into individual files
- Group related functions into modules
- Extract constants and configurations

### Step 2: Create Module Structure
Transform single files into packages:
```
# Before:
foxtrot/app/ui/widget.py  # 1290 lines

# After:
foxtrot/app/ui/widgets/
    __init__.py
    base_widget.py      # 150 lines
    table_widget.py      # 180 lines
    chart_widget.py      # 190 lines
    form_widget.py       # 170 lines
    dialog_widget.py     # 160 lines
    ... (more specific widgets)
```

### Step 3: Update Imports
Maintain backward compatibility:
```python
# foxtrot/app/ui/widgets/__init__.py
from .base_widget import BaseWidget
from .table_widget import TableWidget
# ... export all public classes

# This allows existing code to still use:
# from foxtrot.app.ui.widget import TableWidget
```

## Implementation Details

### Priority Files to Split

1. **widget.py (1290 lines)**
   - Extract each widget class to separate file
   - Create base class for common functionality
   - Group related widgets in subdirectories

2. **utility.py (1051 lines)**  
   - Split into: converters.py, validators.py, formatters.py, helpers.py
   - Each focused on specific utility type
   - Maximum 150 lines per file

3. **trading_panel.py (1047 lines)**
   - Extract: order_form.py, market_display.py, validation.py
   - Separate UI from business logic
   - Create proper component hierarchy

## Success Criteria

### Measurable Outcomes
- ✅ No Python file exceeds 200 lines
- ✅ Average file size under 150 lines
- ✅ All imports continue to work
- ✅ No functionality broken

### Verification Method
```bash
# Check file sizes
find foxtrot -name "*.py" -exec wc -l {} + | awk '$1 > 200 {print}'
# Should return empty

# Run existing code
python -c "from foxtrot.app.ui.widget import TableWidget"
# Should work without errors

# Run any existing tests
pytest tests/
# Should not introduce new failures
```

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking imports | Medium | High | Use __init__.py to maintain compatibility |
| Lost functionality | Low | High | Test each split carefully |
| Merge conflicts | Medium | Medium | Coordinate with team, split one file at a time |

## Estimated Timeline

- Hour 1-2: Analyze widget.py, plan splitting
- Hour 3-4: Split widget.py into modules
- Hour 5: Split utility.py
- Hour 6: Split trading_panel.py
- Hour 7: Update imports across codebase
- Hour 8: Testing and verification

## Dependencies

- None - this is the first critical task

## Notes

- DO NOT add new abstractions during splitting
- DO NOT refactor logic, only reorganize
- DO NOT change public interfaces
- FOCUS only on reducing file sizes