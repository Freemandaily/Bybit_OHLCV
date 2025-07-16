import requests,asyncio,aiohttp
import time,logging
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



app  = FastAPI()

@app.get("/bybit/ohlcv")
def get_bybit_price_ohlcv(
    symbol="BTCUSDT",
    interval="15",       
    start_time=None,
    end_time=None,
    limit=1000,
    checkAlive: bool = False
):
    if checkAlive:
        logging.info("Checking if Bybit API is alive...")
        return {"status": "API is alive"}
      
    # url = f"https://api.bybit.com/v5/market/kline?symbol={symbol}&interval={interval}&start={start_time}&end={end_time}&limit={limit}"
    url = f"https://api.bybit.com/v5/market/kline"
    params = {
        'category':'spot',
        "symbol": symbol,
        "interval": interval,
        "start": start_time,
        "end": end_time,
        "limit": limit
    }

    response = requests.get(url,params=params)
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.status_code}"}
    data = response.json()
    logging.info(f"Successfuflly Fetched Price For Symbol: {symbol} with Interval: {interval}")
    return data
#-------------------------------------------------------------------------------------------------------------------------  

async def tickerRequests(symbol:str,paired:str|None=None):
    url = 'https://api.bybit.com/v5/market/tickers'
    if paired:
        pair = f'{symbol.upper()}{paired.upper()}'
    else:
        paired = 'USDT'
        pair = f'{symbol.upper()}{paired.upper()}'
    params = {
    'category':'spot',
    'symbol':pair
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url,params=params) as response:
            if response.status == 200:
                result = await response.json()
                if result['retMsg'] == 'OK':
                    try:
                        symbol = result['result']['list'][0]['symbol']
                        return symbol
                    except:
                        return {'Error':'No matching pairs'}
            return {'Error':f'Unable To Fetch Ticker.Error Code {response.status}'}
   

@app.get('/bybit/tickers/')
async def search_Ticker(symbol:str,paired:str|None=None):
    if paired:
        ticker_info = await asyncio.create_task(tickerRequests(symbol=symbol,paired=paired))
        return ticker_info
    ticker_info = await asyncio.create_task(tickerRequests(symbol=symbol))
    return ticker_info