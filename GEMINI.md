# GEMINI.md

This file provides guidance to Gemini when working with the Foxtrot trading platform framework. While I use both English and Chinese in project development, all code, comments, logs, and documentation must be in English. Gemini should understand Chinese instructions but respond and code in English.

## Code Architecture Standards

### Hard Requirements 硬性指标

1. **File Length Limits**
   - Dynamic languages (Python, JavaScript, TypeScript): Maximum 200 lines per file
   - Static languages (Java, Go, Rust): Maximum 250 lines per file
   - Maximum 8 files per directory - create subdirectories when exceeded

### BAD TASTE to AVOID

1.  除了硬性指标以外，还需要时刻关注优雅的架构设计，避免出现以下可能侵蚀我们代码质量的「坏味道」：
  （1）僵化 (Rigidity): 系统难以变更，任何微小的改动都会引发一连串的连锁修改。
  （2）冗余 (Redundancy): 同样的代码逻辑在多处重复出现，导致维护困难且容易产生不一致。
  （3）循环依赖 (Circular Dependency): 两个或多个模块互相纠缠，形成无法解耦的“死结”，导致难以测试与复用。
  （4）脆弱性 (Fragility): 对代码一处的修改，导致了系统中其他看似无关部分功能的意外损坏。
  （5）晦涩性 (Obscurity): 代码意图不明，结构混乱，导致阅读者难以理解其功能和设计。
  （6）数据泥团 (Data Clump): 多个数据项总是一起出现在不同方法的参数中，暗示着它们应该被组合成一个独立的对象。
  （7）不必要的复杂性 (Needless Complexity): 用“杀牛刀”去解决“杀鸡”的问题，过度设计使系统变得臃肿且难以理解。

- 【非常重要！！】无论是你自己编写代码，还是阅读或审核他人代码时，都要严格遵守上述硬性指标，以及时刻关注优雅的架构设计。
- 【非常重要！！】无论何时，一旦你识别出那些可能侵蚀我们代码质量的「坏味道」，都应当立即询问用户是否需要优化，并给出合理的优化建议

### Critical Rules
- **ALWAYS** enforce file length limits and directory organization
- **IMMEDIATELY** flag any code bad taste and propose optimizations
- **NEVER** compromise on these architectural standards

## Project Overview

Foxtrot is an event-driven trading platform framework built with Python. It follows a modular architecture with adapters for different brokers, a core event engine, and server components for data management.

## Architecture

### Core Components

1. **Event Engine** (`foxtrot/core/event_engine.py`)
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

### Adapter Architecture

Both adapters follow a consistent modular pattern with specialized managers:

#### Binance Adapter (`foxtrot/adapter/binance/`)
| File | Purpose |
|------|---------|
| `binance.py` | Main adapter facade implementing BaseAdapter interface |
| `api_client.py` | CCXT exchange coordinator and manager factory |
| `account_manager.py` | Account queries, balances, and positions |
| `order_manager.py` | Order placement, cancellation, and tracking |
| `market_data.py` | Real-time market data subscriptions |
| `historical_data.py` | Historical OHLCV data queries |
| `contract_manager.py` | Symbol/contract information |
| `binance_mappings.py` | Data format conversions between CCXT and VT |

#### Interactive Brokers Adapter (`foxtrot/adapter/ibrokers/`)
| File | Purpose |
|------|---------|
| `ibrokers.py` | Main adapter facade implementing BaseAdapter interface |
| `api_client.py` | IB API wrapper and manager coordinator |
| `account_manager.py` | Account information and portfolio management |
| `order_manager.py` | Order lifecycle management |
| `market_data.py` | Tick data and market subscriptions |
| `historical_data.py` | Historical data requests |
| `contract_manager.py` | Contract searches and definitions |
| `ib_mappings.py` | Data format conversions between IB API and VT |
| `ibrokers_legacy.py` | Legacy monolithic implementation (deprecated) |

### Module Structure

| Directory | Purpose |
|-----------|---------|
| `foxtrot/adapter/` | Broker/exchange adapters (Binance, Interactive Brokers) |
| `foxtrot/app/` | Application modules with engine and widget components |
| `foxtrot/core/` | Core event system (event_engine.py, event.py) |
| `foxtrot/server/` | Main engine, OMS, database, datafeed |
| `foxtrot/util/` | Constants, converters, logging, settings, utilities |

## Development Setup

### Install Dependencies
```bash
# Using uv (recommended - faster, better dependency resolution)
uv sync

# Or using poetry
poetry install
poetry shell
```

### Run Tests
```bash
# Using uv
uv run pytest

# Using poetry
poetry run pytest
poetry run pytest -v --cov=foxtrot  # Run with coverage
```

### Code Quality
```bash
# Using uv
uv run black foxtrot/
uv run ruff check foxtrot/
uv run mypy foxtrot/

# Using poetry
poetry run black foxtrot/
poetry run ruff check foxtrot/
poetry run mypy foxtrot/
```

### Key Dependencies
- **Runtime**: `ibapi`, `ccxt`, `tzlocal`
- **Development**: `pytest`, `black`, `ruff`, `mypy`
- **Testing**: `pytest-asyncio`, `pytest-cov`, `pytest-mock`

## Key Patterns

### Event Flow
1. Adapters receive market/account updates
2. Updates converted to standardized data objects
3. Events pushed through EventEngine
4. Engines and apps subscribe to relevant events
5. OMS maintains state for orders, positions, accounts

### VT Symbol Convention
All symbols use format: `{symbol}.{exchange}` (e.g., "SPY.SMART", "BTCUSDT.BINANCE")

### Thread Safety
- All adapter methods must be thread-safe
- Event engine uses thread-safe queues
- No mutable shared state between objects

### Adapter Pattern
- Main adapter class implements BaseAdapter interface
- Delegates to ApiClient for connection management
- ApiClient coordinates specialized managers
- Each manager handles specific functionality (orders, market data, etc.)
- Data mappings provide format conversion between broker APIs and VT objects

## Working with the Code

### Adding New Adapters
1. Create adapter directory under `foxtrot/adapter/`
2. Implement main adapter class inheriting from `BaseAdapter`
3. Create `api_client.py` for connection management
4. Add specialized managers (account, order, market_data, etc.)
5. Implement data mappings for format conversion
6. Add comprehensive test coverage

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

## Testing Strategy

### Test Organization
- Unit tests: `tests/unit/` - Test individual components in isolation
- Integration tests: `tests/integration/` - Test component interactions
- E2E tests: `tests/e2e/` - Test complete workflows

### Testing Guidelines
1. **Mock external dependencies** - Never connect to real brokers/exchanges in tests
2. **Use fixtures** - Centralize test data in `tests/fixtures/`
3. **Test one behavior per test** - Keep tests focused and simple
4. **Follow AAA pattern** - Arrange, Act, Assert
5. **Use descriptive names** - `test_<method>_<condition>_<expected_result>`

### Common Test Patterns
```python
# Mock adapter connections
@patch('foxtrot.adapter.binance.api_client.ccxt.binance')
def test_connect_success(mock_exchange):
    # Test implementation

# Use pytest fixtures
@pytest.fixture
def mock_event_engine():
    return MagicMock(spec=EventEngine)

# Test async methods
@pytest.mark.asyncio
async def test_async_operation():
    # Test async code
```

## Important Notes

- All imports should use `foxtrot` as the root package (e.g., `from foxtrot.core.event_engine import EventEngine`)
- Settings file `vt_setting.json` must exist in working directory
- Uses timezone-aware datetime objects
- Follows dataclass patterns for all data structures
- Email engine runs in separate thread for notifications
- No emojis anywhere in the project - keep all code and documentation text-only

## MANDATORY PRE-CODING CHECKLIST

**BEFORE ANY CODING ACTION, I MUST ANSWER THESE QUESTIONS:**

### 1. IMPORTS Check 导入检查
- All imports at file top? **MUST ANSWER: YES**
- No imports inside functions/methods? **MUST ANSWER: YES**

### 2. KISS Check 简洁性检查
- Is this code 100% necessary? **MUST ANSWER: YES**
- Any global instances/variables? **MUST ANSWER: NO (or justified reason)**
- Module imports independently? **MUST ANSWER: YES, no side effects**

### 3. TDD Check 测试驱动检查
- How many tests will I write? **MUST ANSWER: ONE**
- Using database? **MUST ANSWER: NO, use mocks**
- TDD stage? **MUST ANSWER: RED, GREEN, or REFACTOR**
- Specific behavior? **MUST DESCRIBE IN ONE SENTENCE**

### Violation Warning 违规警告
If I start coding without this checklist, user should immediately say: **"STOP! Check GEMINI.md"**

**This checklist is MANDATORY, not optional**

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main GEMINI.md file.**
@./.taskmaster/CLAUDE.md
