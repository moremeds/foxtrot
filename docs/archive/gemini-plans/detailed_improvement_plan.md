# Detailed Improvement Plan for Foxtrot

## 1. Introduction

This document provides a detailed, step-by-step plan to improve the `foxtrot` trading platform. The plan is inspired by the robust practices observed in the `nautilus_trader` project but adapted to fit `foxtrot`'s Python-native, lightweight philosophy.

The goal is to enhance reliability, expand features, and improve the developer experience without introducing the complexity of a hybrid Rust/Python codebase.

---

## 2. Architectural Enhancements for Reliability

### 2.1. Introduce State Persistence for `OmsEngine`

-   **Inspiration:** `nautilus_trader`'s optional Redis-backed state persistence for fault tolerance.
-   **Goal:** Ensure that the state of orders, trades, and positions can survive an application restart.
-   **Adoption Strategy:** Implement a simple, file-based persistence layer using Python's built-in `sqlite3` library.

#### **Step-by-Step Implementation:**

1.  **Create a Persistence Interface:**
    *   Create a new file: `foxtrot/server/persistence.py`.
    *   Define an abstract base class `Persistence` with `save(data)` and `load()` methods.

2.  **Implement `SqlitePersistence`:**
    *   In `foxtrot/server/persistence.py`, create a `SqlitePersistence` class that inherits from `Persistence`.
    *   **`__init__(self, db_path)`:** Takes the path to the SQLite database file.
    *   **`connect(self)`:** Establishes a connection and creates a table (e.g., `oms_state`) if it doesn't exist. The table should have two columns: `key` (TEXT, PRIMARY KEY) and `value` (TEXT).
    *   **`save(self, key, data)`:** Serializes the `data` (e.g., a dictionary of orders) into a JSON string and saves it to the database using an `INSERT OR REPLACE` statement.
    *   **`load(self, key)`:** Loads the JSON string from the database and deserializes it back into a Python object.

3.  **Integrate Persistence into `OmsEngine`:**
    *   Modify `OmsEngine.__init__`:
        ```python
        # In foxtrot/server/engines/oms_engine.py
        class OmsEngine(BaseEngine):
            def __init__(self, main_engine, event_engine):
                super().__init__(main_engine, event_engine, "oms")
                self.persistence = SqlitePersistence("foxtrot_state.db")
                self.persistence.connect()
                self.load_state()
                # ... rest of init
        ```
    *   Implement `load_state()` and `save_state()` methods in `OmsEngine`:
        ```python
        def load_state(self):
            self.orders = self.persistence.load("orders") or {}
            self.trades = self.persistence.load("trades") or {}
            self.positions = self.persistence.load("positions") or {}
            # Re-populate active_orders from the loaded orders
            self.active_orders = {
                oid: order for oid, order in self.orders.items() if order.is_active()
            }

        def save_state(self):
            self.persistence.save("orders", self.orders)
            self.persistence.save("trades", self.trades)
            self.persistence.save("positions", self.positions)
        ```
    *   Update `OmsEngine`'s `process_*_event` methods to call `self.save_state()` after updating the state. To avoid excessive I/O, this could be throttled (e.g., save only once every few seconds).

4.  **Ensure Graceful Shutdown:**
    *   In `MainEngine.close()`, ensure it calls a `close` method on the `OmsEngine` which in turn calls `save_state()` one last time.

### 2.2. Decompose `OmsEngine` into Granular Managers

-   **Inspiration:** `nautilus_trader`'s highly modular design with many small, focused components.
-   **Goal:** Improve modularity, adhere to the 200-line file limit, and make components easier to test.

#### **Step-by-Step Implementation:**

1.  **Create `oms` Directory:**
    *   Create a new directory: `foxtrot/server/oms/`.

2.  **Create Manager Classes:**
    *   **`foxtrot/server/oms/order_manager.py`:**
        *   Create an `OrderManager` class.
        *   Move `orders` and `active_orders` dictionaries from `OmsEngine` to `OrderManager`.
        *   Move `process_order_event`, `get_order`, `get_all_orders`, and `get_all_active_orders` methods to `OrderManager`.
    *   **`foxtrot/server/oms/position_manager.py`:**
        *   Create a `PositionManager` class.
        *   Move `positions` dictionary and `process_position_event`, `get_position`, `get_all_positions` methods to `PositionManager`.
    *   **`foxtrot/server/oms/trade_manager.py`:**
        *   Create a `TradeManager` class.
        *   Move `trades` dictionary and `process_trade_event`, `get_trade`, `get_all_trades` methods to `TradeManager`.

3.  **Refactor `OmsEngine` as a Facade:**
    *   The `OmsEngine` class will now coordinate the managers.
    *   Its `__init__` method will instantiate the managers.
    *   It will still register for events, but instead of processing them directly, it will delegate the event to the appropriate manager.
        ```python
        # In foxtrot/server/engines/oms_engine.py
        class OmsEngine(BaseEngine):
            def __init__(self, main_engine, event_engine):
                # ...
                self.order_manager = OrderManager(self)
                self.position_manager = PositionManager(self)
                self.trade_manager = TradeManager(self)
                # ...

            def process_order_event(self, event: Event):
                self.order_manager.process_order_event(event)
                self.save_state() # Still handles persistence coordination

            # Getter methods will now delegate
            def get_order(self, vt_orderid: str):
                return self.order_manager.get_order(vt_orderid)
        ```

---

## 3. Advanced Trading Features

### 3.1. Implement a Dedicated Backtesting Engine

-   **Inspiration:** `nautilus_trader`'s core, high-performance backtesting engine.
-   **Goal:** Provide a robust, event-driven backtesting capability that is decoupled from live trading.

#### **Step-by-Step Implementation:**

1.  **Create `BacktestEngine` Class:**
    *   Create a new file: `foxtrot/server/backtester.py`.
    *   Define the `BacktestEngine` class.

2.  **Implement `BacktestEngine` Methods:**
    *   **`__init__(self, main_engine, event_engine)`:** Standard engine setup.
    *   **`set_strategy(self, strategy_class, strategy_setting)`:** Store the strategy to be tested.
    *   **`load_data(self, data_path, start_date, end_date)`:** Load historical data (e.g., from a CSV file) into a pandas DataFrame.
    *   **`run_backtest(self)`:** This is the core method. It will:
        *   Iterate through the loaded historical data row by row.
        *   For each row, create the appropriate `Event` object (`EVENT_TICK` or `EVENT_BAR`).
        *   Crucially, it will **not** use `time.sleep`. Instead, it will publish events as fast as possible, simulating the passage of time.
        *   It will also need to publish its own `EVENT_TIMER` events at the correct intervals based on the data's timestamps.
    *   **`calculate_statistics(self)`:** After the backtest is complete, calculate performance metrics (Sharpe ratio, max drawdown, etc.).

3.  **Create a Backtesting Script:**
    *   Create an example script in `examples/run_backtest.py` that shows how to:
        1.  Instantiate `MainEngine` and `EventEngine`.
        2.  Get the `BacktestEngine`.
        3.  Set a strategy and load data.
        4.  Run the backtest and print the results.

---

## 4. Developer Experience and Automation

### 4.1. Create a `Makefile`

-   **Inspiration:** `nautilus_trader`'s `Makefile` for automating common tasks.
-   **Goal:** Standardize development workflows and make the project easier to contribute to.

#### **Step-by-Step Implementation:**

1.  **Create `Makefile`:**
    *   Create a file named `Makefile` in the project root.
    *   Add the following content:
        ```makefile
        # Makefile for foxtrot development

        .PHONY: help install test lint clean

        help:
        	@echo "Available commands:"
        	@echo "  install       - Install dependencies using uv"
        	@echo "  test          - Run pytest"
        	@echo "  lint          - Run ruff and black"
        	@echo "  clean         - Remove temporary files"

        install:
        	@echo "Installing dependencies..."
        	uv sync

        test:
        	@echo "Running tests..."
        	uv run pytest

        lint:
        	@echo "Running linter..."
        	uv run ruff check foxtrot/
        	@echo "Running formatter..."
        	uv run black foxtrot/

        clean:
        	@echo "Cleaning up..."
        	find . -type f -name "*.pyc" -delete
        	find . -type d -name "__pycache__" -delete
        	rm -rf .pytest_cache
        	rm -f .coverage
        ```

### 4.2. Enhance Project Documentation

-   **Inspiration:** `nautilus_trader`'s comprehensive, user-facing documentation.
-   **Goal:** Improve project onboarding, maintainability, and user adoption.
-   **Adoption Strategy:** Use **MkDocs** with the Material theme.

#### **Step-by-Step Implementation:**

1.  **Add Dependencies:**
    *   Add `mkdocs` and `mkdocs-material` to the `[tool.uv.dev-dependencies]` section of `pyproject.toml`.

2.  **Scaffold Documentation:**
    *   Run `uv sync` to install the new dependencies.
    *   Run `uv run mkdocs new .` in the project root. This will create a `docs/` directory and an `mkdocs.yml` file.

3.  **Configure `mkdocs.yml`:**
    ```yaml
    site_name: Foxtrot Trading Platform
    theme:
      name: material
    nav:
      - 'Home': 'index.md'
      - 'Architecture': 'architecture.md'
      - 'Guides':
        - 'Creating an Adapter': 'guides/creating_an_adapter.md'
        - 'Writing a Strategy': 'guides/writing_a_strategy.md'
    ```

4.  **Create Initial Documentation Files:**
    *   **`docs/index.md`:** A high-level overview of the project.
    *   **`docs/architecture.md`:** A detailed explanation of the `EventEngine`, `MainEngine`, Adapters, and the event flow.
    *   **`docs/guides/creating_an_adapter.md`:** A step-by-step guide for developers on how to implement a new `BaseAdapter`.

5.  **Add a `docs` command to the `Makefile`:**
    ```makefile
    docs:
    	@echo "Building documentation..."
    	uv run mkdocs build
    ```
