import asyncio
import os

from dotenv import load_dotenv

from foxtrot.adapter.crypto import CryptoAdapter
from foxtrot.core.event_engine import EventEngine
from foxtrot.util.constants import Direction, Exchange, OrderType
from foxtrot.util.object import OrderRequest

# Load environment variables from .env file
load_dotenv()

# API Key Mapping
API_KEYS = {
    "binance": {
        "key": os.getenv("BINANCE_TESTNET_SPOT_API_KEY"),
        "secret": os.getenv("BINANCE_TESTNET_SPOT_SECRET_KEY"),
    },
    "binanceusdm": {
        "key": os.getenv("BINANCE_TESTNET_FUTURES_API_KEY"),
        "secret": os.getenv("BINANCE_TESTNET_FUTURES_SECRET_KEY"),
    },
    # Add other exchanges here
    # "bybit": {
    #     "key": os.getenv("BYBIT_TESTNET_API_KEY"),
    #     "secret": os.getenv("BYBIT_TESTNET_SECRET_KEY"),
    # },
}


async def get_top_5_traded_pairs(client):
    """Gets the top 5 most traded pairs by quote volume."""
    try:
        tickers = client.exchange.fetch_tickers()
        # Filter out non-USDT pairs and sort by quoteVolume
        usdt_tickers = {k: v for k, v in tickers.items() if k.endswith("/USDT")}
        sorted_tickers = sorted(
            usdt_tickers.values(), key=lambda x: x.get("quoteVolume", 0), reverse=True
        )
        top_5 = [ticker["symbol"] for ticker in sorted_tickers[:5]]
        return top_5
    except Exception as e:
        print(f"Error fetching top traded pairs: {e}")
        return []


async def main():
    """
    End-to-end test script for the Crypto adapter.
    """
    spot_exchange_name = "binance"
    futures_exchange_name = "binanceusdm"

    spot_api_key = API_KEYS.get(spot_exchange_name, {}).get("key")
    spot_api_secret = API_KEYS.get(spot_exchange_name, {}).get("secret")
    futures_api_key = API_KEYS.get(futures_exchange_name, {}).get("key")
    futures_api_secret = API_KEYS.get(futures_exchange_name, {}).get("secret")

    if not all([spot_api_key, spot_api_secret, futures_api_key, futures_api_secret]):
        print("Error: Testnet API keys not set.")
        return

    # --- Initialize Clients ---
    event_engine = EventEngine()

    # Spot Client
    spot_client = CryptoAdapter(event_engine, "crypto_spot")
    spot_settings = {
        "Exchange": spot_exchange_name,
        "API Key": spot_api_key,
        "Secret": spot_api_secret,
        "Sandbox": True,
    }
    spot_client.connect(spot_settings)
    spot_client.exchange.load_markets()

    # Futures Client
    futures_client = CryptoAdapter(event_engine, "crypto_futures")
    futures_settings = {
        "Exchange": futures_exchange_name,
        "API Key": futures_api_key,
        "Secret": futures_api_secret,
        "Sandbox": True,
        "options": {
            "defaultType": "future",
        },
    }
    futures_client.connect(futures_settings)

    top_5_pairs = []
    order_quantities = {}
    try:
        # --- 1. Display Balances ---
        print("--- Fetching Balances ---")
        spot_balance = spot_client.account_manager.query_account()
        futures_balance = futures_client.account_manager.query_account()
        print(f"Spot Balance: {spot_balance}")
        print(f"Futures Balance: {futures_balance}")
        print("-" * 20)

        # --- Get Top 5 Traded Pairs ---
        print("--- Getting Top 5 Traded Pairs ---")
        top_5_pairs = await get_top_5_traded_pairs(spot_client)
        print(f"Top 5 pairs: {top_5_pairs}")
        print("-" * 20)

        # --- Place Trades on Top 5 Pairs ---
        for pair in top_5_pairs:
            print(f"--- Placing Spot Trade for {pair} ---")
            market = spot_client.exchange.market(pair)
            price = spot_client.exchange.fetch_ticker(pair)["last"]

            # Calculate quantity for a notional value of ~11 USDT
            amount = 11 / price
            quantity = float(spot_client.exchange.amount_to_precision(pair, amount))
            order_quantities[pair] = quantity

            order_req = OrderRequest(
                symbol=f"{market['id']}.{spot_exchange_name.upper()}",
                exchange=Exchange[spot_exchange_name.upper()],
                direction=Direction.LONG,
                type=OrderType.MARKET,
                volume=quantity,
            )
            trade_result = spot_client.order_manager.send_order(order_req)
            if trade_result:
                order_details = spot_client.order_manager.query_order(trade_result)
                print(f"Trade Result for {pair}: {order_details}")
            else:
                print(f"Failed to place trade for {pair}")
            print("-" * 20)

        # --- 3. Place a Futures Trade ---
        print("--- Placing Futures Trade ---")
        futures_order_req = OrderRequest(
            symbol="BTCUSDT.BINANCE",
            exchange=Exchange.BINANCE,
            direction=Direction.LONG,
            type=OrderType.MARKET,
            volume=0.001,
        )

        futures_trade_result = futures_client.order_manager.send_order(futures_order_req)
        if futures_trade_result:
            order_details = futures_client.order_manager.query_order(futures_trade_result)
            print(f"Futures Trade Result: {order_details}")
        else:
            print("Failed to place futures trade")
        print("-" * 20)

    finally:
        # --- 4. Flatten All Positions ---
        print("--- Flattening All Positions ---")

        # Flatten Top 5 Pairs
        for pair in top_5_pairs:
            print(f"Flattening Position for {pair}...")
            market = spot_client.exchange.market(pair)
            quantity = order_quantities.get(pair)
            if not quantity:
                continue

            flatten_req = OrderRequest(
                symbol=f"{market['id']}.{spot_exchange_name.upper()}",
                exchange=Exchange[spot_exchange_name.upper()],
                direction=Direction.SHORT,
                type=OrderType.MARKET,
                volume=quantity,
            )
            flatten_result = spot_client.order_manager.send_order(flatten_req)
            print(f"Flatten Result for {pair}: {flatten_result}")

        # Flatten Futures
        print("Flattening Futures Position...")
        open_positions = futures_client.account_manager.query_position()
        for position in open_positions:
            if position.symbol == "BTCUSDT.BINANCE":
                flatten_futures_req = OrderRequest(
                    symbol="BTCUSDT.BINANCE",
                    exchange=Exchange.BINANCE,
                    direction=Direction.SHORT if float(position.volume) > 0 else Direction.LONG,
                    type=OrderType.MARKET,
                    volume=abs(float(position.volume)),
                )

                flatten_futures_result = futures_client.order_manager.send_order(
                    flatten_futures_req
                )
                print(f"Flatten Futures Result: {flatten_futures_result}")

        print("--- Cleanup Complete ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Script interrupted by user.")
