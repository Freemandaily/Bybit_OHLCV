import requests
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
      
    url = f"https://api.bybit.com/v5/market/kline?symbol={symbol}&interval={interval}&start={start_time}&end={end_time}&limit={limit}"
    # params = {
    #     "symbol": symbol,
    #     "interval": interval,
    #     "start": start_time,
    #     "end": end_time,
    #     "limit": limit
    # }

    response = requests.get(url)
    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.status_code}"}
    data = response.json()
    logging.info(f"Successfuflly Fetched Price For Symbol: {symbol} with Interval: {interval}")
    return data
    
