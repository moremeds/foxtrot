## Binance Testnet End-to-End (E2E) Test

This script performs an end-to-end test of the Binance adapter against the **Binance Testnet API**.

### Running the Test

To run the Binance end-to-end test, you need to have your Binance Testnet API credentials set as environment variables.

1.  **Create a `.env` file** in the root of the project (`/home/ubuntu/projects/foxtrot`) and add your testnet API keys and secrets:

    ```
    BINANCE_TESTNET_SPOT_API_KEY=your_spot_testnet_api_key
    BINANCE_TESTNET_SPOT_SECRET_KEY=your_spot_testnet_secret_key
    BINANCE_TESTNET_FUTURES_API_KEY=your_futures_testnet_api_key
    BINANCE_TESTNET_FUTURES_SECRET_KEY=your_futures_testnet_secret_key
    ```

2.  **Run the script** from the project root directory:

    ```bash
    python examples/e2e/binance/e2e_test.py
    ```

**Disclaimer:** This script will execute live trades on your Binance Testnet account. Use it with caution and at your own risk.
