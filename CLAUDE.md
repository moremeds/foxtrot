# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. I use both English and Chinese in this project development, but all comments, logs, codes are in English. You should understand the Chinese

## Project Overview

Foxtrot is an event-driven trading platform framework built with Python. It follows a modular architecture with adapters for different brokers, a core event engine, and server components for data management.

## Architecture

### Core Components

1. **Event Engine** (`foxtrot/core/engine.py`)
   - Central event-driven system using `EventEngine` class
   - Handles event distribution, timer events, and handler registration
   - Thread-safe with queue-based event processing

2. **Main Engine** (`foxtrot/server/engine.py`)
   - `MainEngine` class acts as the platform core
   - Manages adapters, engines, and apps
   - Coordinates OMS (Order Management System), logging, and email functionality

3. **Base Adapter** (`foxtrot/adapter/base_adapter.py`)
   - Abstract class for broker/exchange connections
   - Implements standard interface for orders, trades, positions, accounts
   - Thread-safe design with event callbacks

4. **Data Objects** (`foxtrot/util/object.py`)
   - Dataclasses for trading objects: TickData, OrderData, TradeData, etc.
   - Exchange-agnostic with standardized fields
   - Uses `vt_symbol` format: "{symbol}.{exchange}"

### Module Structure

- `foxtrot/adapter/`: Broker/exchange adapters (e.g., Interactive Brokers)
- `foxtrot/app/`: Application modules with engine and widget components
- `foxtrot/core/`: Core event system
- `foxtrot/server/`: Main engine, OMS, database, datafeed
- `foxtrot/util/`: Constants, converters, logging, settings, utilities

## Key Patterns

### Event Flow
1. Adapters receive market/account updates
2. Updates converted to standardized data objects
3. Events pushed through EventEngine
4. Engines and apps subscribe to relevant events
5. OMS maintains state for orders, positions, accounts

### VT Symbol Convention
All symbols use format: `{symbol}.{exchange}` (e.g., "SPY.SMART", "EUR.IDEALPRO")

### Thread Safety
- All adapter methods must be thread-safe
- Event engine uses thread-safe queues
- No mutable shared state between objects

## Development Commands

### Install Dependencies
```bash
poetry install  # Install all dependencies in virtual environment
poetry shell   # Activate the virtual environment
```

### Run Tests
```bash
poetry run pytest  # Run all tests
poetry run pytest -v --cov=foxtrot  # Run with coverage
```

### Code Quality
```bash
poetry run black foxtrot/  # Format code
poetry run ruff check foxtrot/  # Lint code
poetry run mypy foxtrot/  # Type check
```

### Key Dependencies
- `ibapi` - Interactive Brokers API
- `tzlocal` - Timezone handling
- Development: `pytest`, `black`, `ruff`, `mypy`

## Working with the Code

### Adding New Adapters
1. Inherit from `BaseAdapter`
2. Implement abstract methods: connect, close, subscribe, send_order, etc.
3. Convert broker-specific data to standard VT objects
4. Push events through callbacks (on_tick, on_order, etc.)

### Adding New Engines
1. Inherit from `BaseEngine`
2. Register event handlers in __init__
3. Add to MainEngine.init_engines()
4. Access via main_engine.get_engine()

### Event Types
Standard events defined in `util/event_type.py`:
- EVENT_TICK, EVENT_ORDER, EVENT_TRADE
- EVENT_POSITION, EVENT_ACCOUNT, EVENT_CONTRACT
- EVENT_LOG, EVENT_QUOTE

### Settings
Global settings in `util/settings.py`, loaded from `vt_setting.json`:
- Database configuration
- Email settings for notifications  
- Logging levels
- Datafeed credentials

## Important Notes

- All imports should use `foxtrot` as the root package (e.g., `from foxtrot.core.engine import EventEngine`)
- Settings file `vt_setting.json` must exist in working directory
- Uses timezone-aware datetime objects
- Follows dataclass patterns for all data structures
- Email engine runs in separate thread for notifications

# 🛑 MANDATORY PRE-CODING CHECKLIST 🛑
**BEFORE ANY CODING ACTION, I MUST ANSWER THESE QUESTIONS:**

## IMPORTS检查 (EVERY TIME)
- 所有imports都在文件顶部？**必须回答：是**
- 没有在函数/方法内部import？**必须回答：是**

## KISS检查 (EVERY TIME)
- 这行代码100%必要吗？**必须回答：是**
- 有没有全局实例/变量？**必须回答：没有，或者有充分理由**
- 模块能独立导入吗？**必须回答：是，无副作用**

## TDD检查 (EVERY TIME)
- 我要写几个测试？**必须回答：一个**
- 用数据库吗？**必须回答：不，用mock**
- TDD步骤？**必须回答：RED/GREEN/REFACTOR之一**
- 具体行为？**必须一句话描述**

## 违规警告
如果我开始编码而没有先做这个检查，用户应该立刻说"停！检查CLAUDE.md"

⚠️ **这个检查是MANDATORY的，不是可选的**

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
