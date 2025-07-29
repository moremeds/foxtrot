
### Plan: Refactor Binance Adapter

**Objective:** Refactor the `binance` adapter to mirror the structure and functionality of the `ibrokers` adapter, using the `ccxt` library to support both spot and futures trading.

**Analysis Summary:** The `ibrokers` adapter has a well-defined, modular structure. The `binance` adapter is currently a single file. The `ccxt` library is already a project dependency, and the `.env.example` file is correctly set up for Binance API keys.

**Step-by-Step Plan:**

1.  **Create New Files:** Create the following new files in the `foxtrot/adapter/binance/` directory to mirror the `ibrokers` structure:
    *   `account_manager.py`: To manage account information, balances, and positions.
    *   `api_client.py`: To handle the connection to the Binance API using `ccxt`.
    *   `contract_manager.py`: To manage instrument details and contracts.
    *   `historical_data.py`: To fetch historical market data.
    *   `market_data.py`: To handle real-time market data streams.
    *   `order_manager.py`: To manage orders, trades, and positions.
    *   `binance_mappings.py`: To map Binance-specific data to the application's internal data models.

2.  **Use `.env.example`:** Ensure the `.env.example` file includes separate API keys for spot and futures, for both testnet and production environments. (No changes are needed here as the file is already correct).

3.  **Implement `api_client.py`:**
    *   Create a `BinanceApiClient` class.
    *   In the constructor, initialize the `ccxt` Binance client.
    *   Use environment variables to load the API key and secret key.
    *   Add separate methods to connect to the spot and futures APIs.

4.  **Implement `account_manager.py`:**
    *   Create a `BinanceAccountManager` class.
    *   Implement methods to fetch account balance, positions, and other account-related data using the `BinanceApiClient`.

5.  **Implement `contract_manager.py`:**
    *   Create a `BinanceContractManager` class.
    *   Implement methods to fetch contract details for both spot and futures markets.

6.  **Implement `historical_data.py`:**
    *   Create a `BinanceHistoricalData` class.
    *   Implement methods to fetch historical OHLCV data for specified symbols and timeframes.

7.  **Implement `market_data.py`:**
    *   Create a `BinanceMarketData` class.
    *   Implement methods to subscribe to real-time market data streams (e.g., order book, trades).

8.  **Implement `order_manager.py`:**
    *   Create a `BinanceOrderManager` class.
    *   Implement methods to create, cancel, and query orders for both spot and futures.
    *   Implement methods to fetch trade history.

9.  **Implement `binance.py`:**
    *   Refactor the main `BinanceAdapter` class in `binance.py`.
    *   This class will now act as a facade, composing the functionality from the new manager classes (`AccountManager`, `ContractManager`, etc.).
    *   It will inherit from `BaseAdapter` and implement its abstract methods.

10. **Implement `binance_mappings.py`:**
    *   Create mapping functions to convert data from the `ccxt` library's format to the application's internal data structures.

11. **Add Unit Tests:** Create a new test directory `tests/unit/adapter/binance/` and add unit tests for each of the new modules to ensure they function correctly. This will involve mocking the `ccxt` library.
