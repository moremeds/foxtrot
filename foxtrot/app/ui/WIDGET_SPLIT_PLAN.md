# Widget.py Split Plan

## Current State
- File: `foxtrot/app/ui/widget.py`  
- Lines: 1290 (6x over 200-line limit)
- Classes: 21

## Target Structure

### 1. base_widget.py (~150 lines)
**Purpose**: Core widget abstractions and base classes
- `BaseMonitor` class (currently lines 229-405)
- Common constants (COLOR_LONG, COLOR_SHORT, etc.)
- Base imports needed by all widgets

### 2. cell_widget.py (~180 lines)  
**Purpose**: All table cell implementations
- `BaseCell` (lines 49-87)
- `EnumCell` (lines 88-104)
- `DirectionCell` (lines 105-125)
- `BidCell` (lines 126-137)
- `AskCell` (lines 138-149)
- `PnlCell` (lines 150-171)
- `TimeCell` (lines 172-197)
- `DateCell` (lines 198-215)
- `MsgCell` (lines 216-228)

### 3. monitor_widget.py (~180 lines)
**Purpose**: Specific monitor implementations
- `TickMonitor` (lines 406-432)
- `LogMonitor` (lines 433-448)
- `TradeMonitor` (lines 449-471)
- `OrderMonitor` (lines 472-514)
- `PositionMonitor` (lines 515-536)
- `AccountMonitor` (lines 537-554)
- `QuoteMonitor` (lines 555-597)
- `ActiveOrderMonitor` (lines 1049-1069)

### 4. trading_widget.py (~180 lines)
**Purpose**: Main trading interface
- `TradingWidget` class (lines 691-1048)
- Trading-specific helpers and methods

### 5. dialog_widget.py (~150 lines)
**Purpose**: All dialog/modal components
- `ConnectDialog` (lines 598-690)
- `AboutDialog` (lines 1170-1216)
- `GlobalDialog` (lines 1217-1290)

### 6. contract_widget.py (~100 lines)
**Purpose**: Contract management UI
- `ContractManager` (lines 1070-1169)

### 7. utils_widget.py (~50 lines)
**Purpose**: Shared utilities and helpers
- Import aggregation for convenience
- Any shared utility functions

## Implementation Steps

1. Create base structure with proper imports
2. Move classes maintaining functionality
3. Update cross-references between modules
4. Fix imports in consuming code
5. Test each module independently
6. Integration test
7. Remove original widget.py

## Dependency Management
- All modules import from `base_widget` for common base classes
- Cell classes are independent
- Monitors depend on base_widget
- Dialogs are mostly independent
- Trading widget may use cells and monitors