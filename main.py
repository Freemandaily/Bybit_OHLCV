import requests,asyncio,aiohttp
import time,logging
import pytz
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
    spot_url = f"https://api.bybit.com/v5/market/kline"
    perp_url = f"https://api.bybit.com/v5/market/kline"
    urls = [perp_url,spot_url]

    params = {
        'category':'linear',
        "symbol": symbol,
        "interval": interval,
        "start": start_time,
        "end": end_time,
        "limit": limit
    }

   

    for  index ,url in enumerate(urls):
        response = requests.get(url,params=params)
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Successfuflly Fetched Price For Symbol: {symbol} with Interval: {interval}")
            return data
        elif index == 1:
            return {"error": f"Failed to fetch data: {response.status_code}"}
        else:
            params['category'] = 'spot'
            continue
    
#-------------------------------------------------------------------------------------------------------------------------  

async def tickerRequests(symbol:str,paired:str|None=None):
    spot_url = 'https://api.bybit.com/v5/market/tickers'
    perp_url =  'https://api.bybit.com/v5/market/tickers'
    urls = [perp_url,spot_url]

    if paired:
        pair = f'{symbol.upper()}{paired.upper()}'
    else:
        paired = 'USDT'
        pair = f'{symbol.upper()}{paired.upper()}'
    params = {
    'category':'linear',
    'symbol':pair
    }

    async with aiohttp.ClientSession() as session:

        for index,url in enumerate(urls):

            async with session.get(url=url,params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result['retMsg'] == 'OK':
                        try:
                            symbol = result['result']['list'][0]['symbol']
                            return symbol
                        except:
                            if index == 1:
                                return {'Error':'No matching pairs'}
                            else:
                                params['category'] = 'spot'
                                continue
                elif index == 1:
                    return {'Error':f'Unable To Fetch Ticker.Error Code {response.status}'}
                else:
                    params['category'] = 'spot'
                    continue
    

@app.get('/bybit/tickers/')
async def search_Ticker(symbol:str,paired:str|None=None):
    if paired:
        ticker_info = await asyncio.create_task(tickerRequests(symbol=symbol,paired=paired))
        return ticker_info
    ticker_info = await asyncio.create_task(tickerRequests(symbol=symbol))
    return ticker_info


@app.get('/binance/tickers/')
async def search_Ticker(symbol:str):
    spot_url = 'https://api.binance.com/api/v3/ticker/price'
    perp_url = 'https://fapi.binance.com/fapi/v1/ticker/price'

    urls = [perp_url,spot_url]
    params = {
        'symbol':f'{symbol.upper()}USDT'
        }
    logging.info('About To Fetch Ticker On Binance')

    async with aiohttp.ClientSession() as session:
        
        for index,url in enumerate(urls):
            async with session.get(url=url,params=params) as response:
                if response.status == 200:
                    result = await response.json()

                    if result['symbol']:
                        try:
                            symbol = result['symbol']
                            return symbol
                        except:
                            if index == 1:
                                return {'Error':'No matching pairs'}
                            else:
                                continue
                elif index == 1:
                    return {'Error':f'Unable To Fetch Ticker.Error Code {response.status}'}
                else:
                    continue
   

@app.get('/binance/ohlcv')
async def get_binance_price_ohlcv(
    symbol="BTCUSDT",
    interval="1m",       
    start_time=None,
    end_time=None,
    limit=1000
    ):

    spot_url = 'https://api.binance.com/api/v3/klines'
    perp_url = 'https://fapi.binance.com/fapi/v1/klines'

    urls = [perp_url,spot_url]

    params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit
        }
    
    for index, url in enumerate(urls):
        response = requests.get(url,params=params)

        if response.status_code == 200:
            data = response.json()
            logging.info(f"Successfuflly Fetched Price For Symbol: {symbol} with Interval: {interval}")
            return data
        elif index == 1:
            return {"error": f"Failed to fetch data: {response.status_code}"}
        else:
            continue
        

@app.get('/onchain_price')
async def fetchPrice(network,pair,tweeted_date,timeframe,poolId): 
    async def Priceswharehouse(session,from_timestamp,to_timestamp,poolId):
        # headers = {
        #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        #     "Accept": "application/json"
        # }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://www.geckoterminal.com/",  
            "Origin": "https://www.geckoterminal.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        from_timestamp =  int(from_timestamp)
        to_timestamp = int(to_timestamp)
        retry_time = 5
        # time.sleep(4)
        for retry in range(retry_time):
            url = f'https://app.geckoterminal.com/api/p1/candlesticks/{poolId}?resolution=1&from_timestamp={from_timestamp}&to_timestamp={to_timestamp}&for_update=false&currency=usd&is_inverted=false'
            
            async with session.get(url=url,headers=headers) as response:
                if response.status !=200:
                    logging.warning(f"Fetching Price data with {url} Failed . Retrying for {retry} Times")
                    time.sleep(1)
                    continue
                result = await response.json()
                datas = result['data']
                price_data = [value for data in datas for key in ['o','h','l','c'] for value in [data[key]]]
                dates = [value for data in datas for key in ['dt'] for value in [data[key]]]

                """
                This fetch get data from the gecko terminal website,
                so the time is in GMT which is lagging 1 hour . 
                Also  some candle are missing in some chart , 
                below code is used to mitigate it. 
                i only use the time to check if the candle chart start from the self.from_timestamp
                """
                
                from datetime import datetime,timedelta
                new_dates_timestamp = [ ]
                for date in dates:
                    dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    unix_timestamp = int(dt.timestamp())
                    new_dates_timestamp.append(unix_timestamp)
                
                return price_data,new_dates_timestamp
        


    # async def fetch_ohlc_and_compute(session,endpoint_req) -> dict:
    async def fetch_ohlc_and_compute(session,network,from_timestamp,to_timestamp,timeframe,poolId) -> dict:
            try:
                task_price  = asyncio.create_task(Priceswharehouse(session,from_timestamp,to_timestamp,poolId))
                price_data,new_date_timestamp = await task_price
                if not price_data:
                    pass_check = []
                    return pass_check
                if int(from_timestamp) in new_date_timestamp:
                    open_price = price_data[4]
                    price_data = price_data[4:]
                else:
                    open_price = price_data[0]

                if int(to_timestamp) in new_date_timestamp:
                    price_data = price_data[:-4]

                close_price = price_data[-1]
                peak_price = max(price_data)
                lowest_price = min(price_data)
                max_so_far = price_data[0]
                max_drawdown  = 0
                entry_to_peak = str(round(((peak_price - open_price) /open_price) * 100,3)) +'%'
            except Exception as e:
                logging.error('This Token Hasnt Appeared On GeckoTerminal Api Yet AS AT Time Posted')
                # st.error(f'This Token Hasnt Appeared On GeckoTerminal Api Yet AS AT Time Posted {e}')
                pass_check = []
                return pass_check
            
            try:
                for price in price_data:
                    if price > max_so_far :
                        max_so_far = price
                    drawadown = (( price - max_so_far) / max_so_far) * 100
                    max_drawdown = min(drawadown,max_drawdown)
                price_info = {'open_price': open_price,
                            'close_price':close_price,
                            'lowest_price' : lowest_price,
                            'peak_price': peak_price,
                            'entry_to_peak':entry_to_peak,
                            'max_drawdown':str(round(max_drawdown,3)) +'%'
                            }
                return price_info
            except Exception as e:
                logging.error('This Token Hasnt Appeared On GeckoTerminal Api Yet AS AT Time Posted')
                # st.error(f'This Token Hasnt Appeared On GeckoTerminal Api Yet AS AT Time Posted{e}')
                # st.stop()
                pass_check = []
                return pass_check

    async def gecko_price_fetch(session,network,pair,from_timestamp,to_timestamp,timeframe,poolId):
        try:
            task1 = asyncio.create_task(fetch_ohlc_and_compute(session,network,from_timestamp,to_timestamp,timeframe,poolId))
            time_frame_Task = await task1
            
            if not time_frame_Task:
                pass_check = []
                return pass_check
            if int(timeframe) >= 60:
                hour = str(timeframe //60)
                minutes = timeframe %60
                timeframe = f'{hour}:{minutes}m'  if minutes > 0  else f'{hour}hr(s)' 
            else:
                timeframe = f'{timeframe}m'
            pair_data_info = {pair:{
                f'{timeframe}' : time_frame_Task
            }}
            return pair_data_info
        except Exception as e:
            logging.error(f'Please Choose Timeframe Within Token Traded Prices {e}')
            # st.error(f'Please Choose Timeframe Within Token Traded Prices')
            pass_check = []
            return pass_check
            

    def process_date_time(tweeted_date,added_minute):
        from datetime import datetime,timedelta
        combine = tweeted_date
        added_minute = added_minute + 1
        time_object = datetime.strptime(str(combine), "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.FixedOffset(60))
        processed_date_time = time_object + timedelta(minutes=added_minute) # added 1 beacuse of how gecko terminal fetch price, price begin at the previou timestamp
        from_timestamp = time_object.timestamp()
        to_timestamp = processed_date_time.timestamp()
        return from_timestamp,to_timestamp
    
    # async def main(network,pair,timestamp,timeframe):
    async def main(network,pair,from_timestamp,to_timestamp,timeframe,poolId):
       
        async with aiohttp.ClientSession() as session:
            task_container = [gecko_price_fetch(session,network,pair,from_timestamp,to_timestamp,timeframe,poolId)]
            pair_price_data = await asyncio.gather(*task_container)
            pair_price_data = [price_data for price_data in pair_price_data if price_data]
            
            return pair_price_data

    # def process_pair(pair,tweeted_date,timeframe):
    async def process_pair(network,pair,tweeted_date,timeframe,poolId):
        from_timestamp,to_timestamp = process_date_time(tweeted_date,int(timeframe))
        # pair_price_data = asyncio.run(main(network,pair,from_timestamp,to_timestamp,timeframe,poolId))
        pair_price_data = await main(network,pair,from_timestamp,to_timestamp,timeframe,poolId)
        return pair_price_data
    price_timeframes = await process_pair(network,pair,tweeted_date,int(timeframe),poolId)
    return price_timeframes 

