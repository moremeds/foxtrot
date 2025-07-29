## Crypto Testnet End-to-End (E2E) Test

This script performs an end-to-end test of the Crypto adapter against the **Binance Testnet API**.

### Running the Test

To run the Crypto end-to-end test, you need to have your Binance Testnet API credentials set as environment variables.

1.  **Create a `.env` file** in the root of the project (`/home/ubuntu/projects/foxtrot`) and add your testnet API keys and secrets:

    ```
    CRYPTO_TESTNET_API_KEY=your_testnet_api_key
    CRYPTO_TESTNET_SECRET_KEY=your_testnet_secret_key
    ```

2.  **Run the script** from the project root directory:

    ```bash
    python examples/e2e/crypto/e2e_test.py
    ```

**Disclaimer:** This script will execute live trades on your Binance Testnet account. Use it with caution and at your own risk.
