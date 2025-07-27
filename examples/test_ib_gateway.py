import asyncio
import nest_asyncio
from ib_async import IB
from ib_async.contract import Stock

nest_asyncio.apply()

async def main():
    ib = IB()
    try:
        await ib.connect('127.0.0.1', 4001, clientId=1)
        print("✅ 成功连接 IB Gateway")
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        return

    summary = await ib.req_account_summary()
    for k, v in summary.items():
        print(f"{k}: {v}")

    contract = Stock('AAPL', 'SMART', 'USD')
    ticker = await ib.req_mkt_data(contract)
    print(f"AAPL 最新价格: {ticker.last}")

    await ib.disconnect()

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

loop.run_until_complete(main())
