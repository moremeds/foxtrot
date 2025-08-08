# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. While I use both English and Chinese in project development, all code, comments, logs, and documentation must be in English. Claude should understand Chinese instructions but respond and code in English.

## Development Commands

### Run Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/adapter/binance/test_api_client.py

# Run with coverage
uv run pytest -v --cov=foxtrot --cov-report=term-missing

# Run tests matching pattern
uv run pytest -k "test_connect"
```

### Code Quality
```bash
# Format code
uv run black foxtrot/

# Lint
uv run ruff check foxtrot/

# Type checking
uv run mypy foxtrot/

# All quality checks in sequence
uv run black foxtrot/ && uv run ruff check foxtrot/ && uv run mypy foxtrot/
```

### Run TUI Application
```bash
./scripts/foxtrot-tui
```

### Task Management
```bash
# View next task
task-master next

# Show task details
task-master show <id>

# Mark task complete
task-master set-status --id=<id> --status=done

# Update subtask with progress
task-master update-subtask --id=<id> --prompt="implementation notes"
```

## Architecture Overview

### Event-Driven Core
The platform centers around an **EventEngine** that manages all communication between components:
- **EventEngine** (`foxtrot/core/event_engine.py`): Thread-safe event distribution with queue-based processing
- **MainEngine** (`foxtrot/server/engine.py`): Orchestrates adapters, engines, and applications
- **Event Flow**: Adapters → Standardized Events → EventEngine → Subscribers (Engines/Apps)

### Adapter Pattern
Each broker adapter follows a consistent architecture:
```
adapter/
├── {broker}.py          # Main facade implementing BaseAdapter
├── api_client.py        # Connection management and manager factory
├── account_manager.py   # Account operations
├── order_manager.py     # Order lifecycle
├── market_data.py       # Real-time data
└── {broker}_mappings.py # Data format conversions
```

### Data Object Standardization
- All trading objects use dataclasses (`foxtrot/util/object.py`)
- Symbol format: `{symbol}.{exchange}` (e.g., "SPY.SMART", "BTCUSDT.BINANCE")
- Events defined in `util/event_type.py`: EVENT_TICK, EVENT_ORDER, EVENT_TRADE, etc.

### Dependency Injection
- Interfaces defined in `foxtrot/core/interfaces.py` (IAdapter, IEngine, IEventEngine)
- Factory functions in `foxtrot/core/common.py` to avoid circular dependencies
- Adapters depend on interfaces, not concrete implementations

## Critical Development Rules

### File Organization 硬性指标
- **Maximum 200 lines** per Python file
- **Maximum 8 files** per directory
- When limits exceeded, refactor into subdirectories with focused modules

### Code Quality Standards 坏味道 BAD TASTE to AVOID

除了硬性指标以外，还需要时刻关注优雅的架构设计，避免出现以下可能侵蚀我们代码质量的「坏味道」：

1. **僵化 (Rigidity)**: 系统难以变更，任何微小的改动都会引发一连串的连锁修改
2. **冗余 (Redundancy)**: 同样的代码逻辑在多处重复出现，导致维护困难且容易产生不一致
3. **循环依赖 (Circular Dependencies)**: 两个或多个模块互相纠缠，形成无法解耦的"死结"
4. **脆弱性 (Fragility)**: 对代码一处的修改，导致了系统中其他看似无关部分功能的意外损坏
5. **晦涩性 (Obscurity)**: 代码意图不明，结构混乱，导致阅读者难以理解其功能和设计
6. **数据泥团 (Data Clumps)**: 多个数据项总是一起出现在不同方法的参数中，暗示着它们应该被组合成一个独立的对象
7. **不必要的复杂性 (Needless Complexity)**: 用"杀牛刀"去解决"杀鸡"的问题，过度设计使系统变得臃肿且难以理解

【非常重要！！】无论何时，一旦你识别出那些可能侵蚀我们代码质量的「坏味道」，都应当立即询问用户是否需要优化，并给出合理的优化建议

### Testing Requirements
- **Never connect to real brokers** in tests - always use mocks
- **One behavior per test** - keep tests focused
- **Use fixtures** from `tests/fixtures/` for test data
- **Target 80% coverage** minimum for new code

### Import Rules
- All imports at file top (no imports inside functions)
- Use absolute imports: `from foxtrot.core.event_engine import EventEngine`
- Check for circular dependencies when adding new imports

## Current Development Focus

### Critical Issues (Sprint 1)
1. **WebSocket Test Failures**: 5 tests failing with real connections instead of mocks
2. **TUI Async Integration**: Need to implement proper async/await with textual
3. **Test Coverage**: Currently 53%, target 80%

### Active Tasks
Check Task Master for current priorities:
```bash
task-master next  # See next task
task-master list --status=pending  # View all pending work
```

## Project Configuration

### Settings
- Configuration file: `vt_setting.json` (must exist in working directory)
- Environment variables in `.env` for API keys
- Task Master config: `.taskmaster/config.json`

### Dependencies
- **Package Manager**: uv (preferred) or poetry
- **Python Version**: 3.11+
- **Key Libraries**: ccxt, ibapi, textual, PySide6
- **Testing**: pytest, pytest-mock, pytest-asyncio

## Task Master Integration

Task Master manages development workflow. Key files:
- `.taskmaster/tasks/tasks.json` - Task database
- `.taskmaster/docs/prd.txt` - Requirements document
- `docs/ROADMAP.md` - Consolidated development roadmap

For detailed Task Master commands, see `.taskmaster/CLAUDE.md`