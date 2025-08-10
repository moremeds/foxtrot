## Foxtrot Test Failures Classification and Analysis

Date: 2025-08-08
Scope: Unit tests across util, adapter (Binance, Futu), server, TUI components, core, and UI.

### Executive Summary
- Multiple failures stem from API drift after refactors (logger API, TUI account monitor, DI container, server logging messages).
- Environment-dependent UI imports (EGL) and optional TA-lib handling also contribute to failures.
- Adapter-layer (Binance/Futu) tests are impacted by logger API changes and lifecycle/setting mismatches.

---

### 1) Logger API migration not applied everywhere
- Symptoms:
  - `TypeError: get_component_logger() missing 1 required positional argument: 'foxtrot_logger'`
  - `TypeError: get_adapter_logger() missing 1 required positional argument: 'foxtrot_logger'`
- Affected tests (examples):
  - `tests/unit/util/test_websocket_utils.py::TestAsyncThreadBridge::test_emit_event_without_engine`
  - Many in `tests/unit/adapter/binance/test_websocket_manager.py` (initialization, connect, disconnect, add/remove subscription, etc.)
- Likely root cause:
  - Logger helpers now require an injected `FoxtrotLogger` instance, but some modules still use the legacy convenience signature.
- Impact:
  - Prevents initialization paths in websocket managers/market data, causing cascaded failures in adapter tests.

### 2) Binance adapter default settings and websocket lifecycle
- Symptoms:
  - Default settings mismatch: `test_default_settings` asserts fail comparing expected dict vs actual (e.g., websocket flags, public-market-only flag, etc.).
  - Websocket components not initialized (`None`), subscribe returns `False`, `.is_alive` on `NoneType` errors, and `watch_symbol_async` logger TypeError (linked to §1).
- Affected tests:
  - `tests/unit/adapter/binance/test_binance_adapter.py::TestBinanceAdapter::test_default_settings`
  - Multiple in `tests/unit/adapter/binance/test_market_data_websocket.py` (subscribe_success, components_initialization, close_market_data, watch_symbol_async, multiple_subscriptions)
- Likely root causes:
  - Divergence between the test contract for `BinanceAdapter.default_setting` and the current implementation (new keys/values introduced).
  - Websocket manager/market data not instantiating due to earlier logger errors or feature-flag gating; unsubscribe/lifecycle behaviors expected by tests not present or guarded.

### 3) Futu adapter API client expectations
- Symptoms:
  - `OpenD` status not true; connection returns `None`; trade context selection false.
- Affected tests:
  - `tests/unit/adapter/futu/test_api_client.py` (3 failures)
- Likely root cause:
  - Incomplete integration or changed behavior in API client relative to mocks/fixtures used by tests; environment flags not aligned with test assumptions.

### 4) TUI Account monitor: config/model/filters API drift
- Symptoms:
  - Missing methods on config/display settings: `update_from_dict`, `validate`, `get_field_config` (tests expect alias of `get_column_config`), setter-like APIs (`set_currency_filter`, `set_gateway_filter`, `set_min_balance_filter`) absent.
  - Filter classes signature/attributes mismatches (`AccountFilter() takes no arguments`, missing `name`, constructor kwargs not accepted).
  - Data model signature mismatches: `AccountData.__init__()` unexpected kwarg `vt_accountid`.
  - Formatting expectations not met (currency `$-` vs `0.00`, datetime contains "2023" vs only time).
  - Risk threshold expectations differ (`'low' in ['medium','high']`).
- Affected tests: Many across
  - `tests/unit/app/tui/components/monitors/account/test_account_controller.py`
  - `tests/unit/app/tui/components/monitors/account/test_config.py`
  - `tests/unit/app/tui/components/monitors/account/test_filtering.py`
  - `tests/unit/app/tui/components/monitors/account/test_formatting.py`
  - `tests/unit/app/tui/components/monitors/account/test_statistics.py`
- Likely root causes:
  - Refactor reduced or renamed the API surface; tests still target richer legacy interfaces and data shapes.

### 5) Trading panel integration: missing private methods and form manager APIs
- Symptoms:
  - `TUITradingPanel` missing methods: `_validate_form`, `_confirm_order`, `_update_market_data`, `_get_account_balance`, `_handle_order_error`, `_cancel_all_orders`, `_submit_order`.
  - `TradingFormManager` missing: `set_inputs`, `update_price_requirement`, etc.
- Affected tests:
  - `tests/unit/app/tui/components/test_trading_components.py`
  - `tests/unit/app/tui/test_trading_panel_integration.py`
- Likely root cause:
  - Incomplete implementation/stubbing of integration-facing methods expected by tests.

### 6) UI widget imports and system dependencies
- Symptoms:
  - `ImportError: libEGL.so.1` missing for tests importing UI modules.
  - `module 'foxtrot.app' has no attribute 'ui'` (package path difference `app/ui` vs `app/tui`).
- Affected tests:
  - `tests/unit/app/ui/test_widget_split.py` (multiple cases)
- Likely root causes:
  - Headless CI environment missing system EGL libs.
  - Repo moved from `ui` to `tui` (or structure changed), tests not updated accordingly.

### 7) Core DI container API gaps
- Symptoms:
  - Missing `create`, `get_singleton`, and override lifecycle methods in `DIContainer`.
- Affected tests:
  - `tests/unit/core/test_di_container.py` (numerous cases)
- Likely root cause:
  - The DI container is skeletal or renamed; tests expect full feature set for factory/singleton/override patterns.

### 8) Utility functions: path/JSON and TA-lib monkeypatching
- Symptoms (Path/JSON):
  - `TEMP_DIR.joinpath` mock expectations not met for `get_file_path`, `get_folder_path`, `save_json`, `load_json`.
  - `load_json` returns `{}` even when file exists; on nonexistent file it doesn’t call `save_json`.
- Symptoms (Technical Indicators):
  - Patching `foxtrot.util.utility.talib` fails because `talib` attribute isn’t present on module.
- Affected tests:
  - `tests/unit/util/test_utility.py` (PathUtilities, JSONUtilities, TechnicalIndicators)
- Likely root causes:
  - Utility functions reimplemented to not rely on `TEMP_DIR` and helper functions in the same way; tests are anchored to previous behavior.
  - TA-lib is optional and imported differently; tests rely on a monkey-patchable module attribute that isn’t exposed.

### 9) Server manager logging message contracts
- Symptoms:
  - Assertion mismatch on log messages and kwargs: expected exact text (e.g., "Adapter NONEXISTENT not found.") and `source="MAIN"`; actual logs differ (e.g., "Adapter not found: NONEXISTENT") and missing kwarg.
- Affected tests:
  - `tests/unit/server/test_adapter_manager.py`
  - `tests/unit/server/test_engine_manager.py`
- Likely root cause:
  - Message strings evolved and logging wrapper no longer forwards `source` kwarg as tests expect.

### 10) OMS Engine contract schema
- Symptoms:
  - `TypeError: ContractData.__init__() missing 1 required positional argument: 'product'`.
- Affected tests:
  - `tests/unit/server/test_oms_engine.py::test_process_contract_event`
- Likely root cause:
  - `ContractData` constructor now requires `product`; test fixture not updated.

### 11) Event engine performance expectation
- Symptoms:
  - `AssertionError: Memory should increase with queue size`.
- Affected tests:
  - `tests/unit/core/test_event_engine_performance.py`
- Likely root cause:
  - Assumption in test not holding due to memory pooling/GC behavior or different benchmark approach; not a functional error but an assertion heuristic.

---

## Cross-Cutting Themes
- **API drift vs. tests**: Substantial refactors changed names, signatures, and behaviors. Tests target previous contracts.
- **Logger injection**: New requirement to inject `FoxtrotLogger` broadly; modules/tests still using legacy calls fail early.
- **Environment deps**: EGL and TA-lib require test-friendly shims to run in headless environments without optional libs.

## Recommendations (for planning; no fixes applied)
- Provide backward-compatible logger shims (optional param with a default singleton) to unblock wide areas.
- Decide on canonical `BinanceAdapter.default_setting` and update either code or tests to match; ensure websocket components are created under test conditions.
- Reintroduce thin compatibility wrappers for TUI Account monitor config/display/filter APIs used by tests, or update tests to new API surface.
- Expose `talib` attribute on `foxtrot.util.utility` as `None` by default to permit test patching when TA-lib is absent.
- Skip or shim EGL-dependent tests in headless CI; align module paths from `ui` to `tui` where applicable.
- Flesh out `DIContainer` with `create`/`get_singleton`/override methods or update tests to the intended minimal API.
- Normalize server log message strings and kwarg `source` contract (or update tests consistently).
- Update OMS test fixtures to include `product` if schema change is intended.

## Notable Failing Buckets (from latest run excerpt)
- Binance adapter: defaults, websocket init/subscribe/lifecycle
- Futu adapter: connection/OpenD/trade context
- TUI account monitor: config, filtering, formatting, statistics
- Trading panel: missing integration methods
- UI widgets: EGL import and module path
- Core DI container: missing methods
- Util: TEMP_DIR path/json contracts; TA-lib monkeypatching
- Server: logging assertion mismatches
- OMS: contract `product` field required

No code changes were made as part of this analysis. This document is for classification and root-cause hypotheses only.
