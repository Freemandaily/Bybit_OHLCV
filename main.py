from urllib import response
import requests,re
import logging
from fastapi import FastAPI
import time,os,sys
import asyncio,aiohttp
from datetime import datetime,timedelta


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

RAPID_API_KEY = os.environ.get('RAPID_KEY')
RAPID_API_KEY = '41e1b8b4cemsh4eb6e7e87dd7de3p19f087jsn33c4e7be015d'
API_KEY =  os.environ.get('ApiKey')
GEMINI_API = os.environ.get('GEMINIKEY')

# Twitter.io api key
API_KEY = 'ebb13b162cb24e1980e4d6842f9991b5' #'c382a3389a524e31a6f4d91c96f3a111' #'d152f89dae1d45d8939a975482e21a53' #'f64fa2c9cb4242b787839f617a5f46cb'
GEMINI_API = 'AIzaSyBTQxOuDtPXPbqhpBiq0bMrO2nbl8Z8e1g' 
BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
GEMINI_URL =  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
BYBIT_OHLCV_URL = 'https://bybit-ohlcv-170603173514.europe-west1.run.app/bybit/ohlcv'
BINANCE_OHLCV_URL = 'https://bybit-ohlcv-170603173514.europe-west1.run.app/binance/ohlcv' # For binance price
BINANCE_TICKER_URL = 'https://bybit-ohlcv-170603173514.europe-west1.run.app/binance/tickers'
BYBIT_TICKER_URL =  'https://bybit-ohlcv-170603173514.europe-west1.run.app/bybit/tickers'
# BASESEARCH_LINK_URL = 'https://basesearchV3.onrender.com/link_search/'
BASESEARCH_LINK_URL = 'http://127.0.0.1:8000/link_search/'
# BASESEARCH_LINK_URL= 'https://basesearchv3-71083952794.europe-west3.run.app/link_search/'
app = FastAPI()




async def _tweet_info(tweet_results:dict)->dict:
    from datetime import datetime,timedelta
    try:
        followers = date_tweeted = tweet_results['result']['core']['user_results']['result']['legacy']['followers_count']
        
        date_tweeted = tweet_results['result']['legacy']['created_at']
        date = datetime.strptime(date_tweeted, "%a %b %d %H:%M:%S %z %Y")
        date_utc_plus_one = date + timedelta(hours=1)
        tweet_date = date_utc_plus_one.strftime("%Y-%m-%d %H:%M:%S")

        tweet_content = tweet_results['result']['legacy']['full_text']

        contract_patterns = r'\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}|T[1-9A-HJ-NP-Za-km-z]{33})\b'
        contracts  = re.findall(contract_patterns,tweet_content) 

        ticker_names = await asyncio.create_task(GeminiRefine(tweet_content))

        tweet_info = {
            'ticker_names':ticker_names,
            'contracts':contracts,
            'followers':followers,
            'date_tweeted':tweet_date[:-3]+':00',
            }
        
        return tweet_content,tweet_info
    except:
        return None,None


async def _get_userId(username:str)->int:
    url = f'https://twitter241.p.rapidapi.com/user?username={username}' 
    headers = {
    'x-rapidapi-host': 'twitter241.p.rapidapi.com',
    'x-rapidapi-key': RAPID_API_KEY
    }
    
    response = requests.get(url=url,headers=headers) 
    if response.status_code == 200:
        result =  response.json()
        user_id = result['result']['data']['user']['result']['rest_id']
        logging.info('Requested For Username Id')
        return user_id
    return None

                            

@app.get('/SearchUserTweet')
async def SearchUserTweet(username:str='zoomerfied',limit:int=10) -> dict:
    # call function to get userId 
    userId = await _get_userId(username)

    if userId is None:
        logging.error('Invalid X Username. Check And Retry!')
        return {'Error':'Invalid X Username. Check And Retry!'}
    
    url = f'https://twitter241.p.rapidapi.com/user-tweets?user={userId}&count=40'
    headers = {
        'x-rapidapi-host': 'twitter241.p.rapidapi.com' ,
        'x-rapidapi-key': RAPID_API_KEY  
    }
    params = {'cursor':''}
    
    distinct_tweet_verify = []
    all_tweet_info = []

    while True:
        
        response = requests.get(url,headers=headers,params=params)
        if response.status_code != 200:
            logging.error(f"Unable To Search For User Tweets! Error Code {response.status_code}")
            return {"Error":f"Unable To Search For User Tweets! Error Code {response.status_code}"}
        try:
            results =  response.json()
            cursor = results['cursor']['bottom']
            tweet_container = results['result']['timeline']['instructions']
            
            for container in tweet_container:
                try:
                    entries_name = list(container.keys())[1]
                except:
                    continue

                if entries_name == 'entry':
                    tweet_results = container['entry']['content']['itemContent']['tweet_results']
                    
                    tweet_content,tweet_info = await _tweet_info(tweet_results)
                    
                    if tweet_content != None and tweet_content not in distinct_tweet_verify:
                        distinct_tweet_verify.append(tweet_content)
                        all_tweet_info.append(tweet_info)

                        if len(all_tweet_info) >= limit:
                            logging.info('Succesfully Retrived User Tweets Data')
                            return {username:all_tweet_info}
                                
                        all_tweet_info.append(tweet_info)
                        
                elif entries_name == 'entries':
                    tweet_entry = container['entries']
                    
                    for entry in tweet_entry:
                        try:
                            tweet_results = entry['content']['itemContent']['tweet_results']
                        except:
                            pass
                        
                        tweet_content,tweet_info = await _tweet_info(tweet_results)
                    
                        if tweet_content != None and tweet_content not in distinct_tweet_verify:
                            distinct_tweet_verify.append(tweet_content)

                            if len(all_tweet_info) >= limit:
                                logging.info('Succesfully Retrived User Tweets Data')
                                return {username:all_tweet_info}
                            
                            all_tweet_info.append(tweet_info)

            params['cursor'] = cursor
        except Exception as e:
            logging.error(f'Unable  To Fetch {username} Tweets! Error Issue:{e}')
            return {'Error':f'Unable  To Fetch {username} Tweets! Error Issue:{e}'}



# @app.get('/SearchUserTweet')
async def SearchUserTweet(username:str='Elonmusk',limit:int=10) -> dict:
    logging.info('Searching User Tweets')
    from datetime import timedelta,datetime
    all_tweets = []
    url = "https://api.twitterapi.io/twitter/user/last_tweets"
    header = {
            'X-API-Key': API_KEY
    }
    params = {
            'userName':username
    }
    async with aiohttp.ClientSession() as session:
        while True:
            logging.info('fetching')
            async with session.get(url=url,headers=header,params=params) as response:
                try:
                    if response.status != 200:
                        logging.error('There is an error Requestng for User Tweets')
                        return {username:all_tweets}
                    data = await response.json()
                    tweets = data.get('data')['tweets']
                    if not tweets:
                        logging.info("No tweets found for the given query.")
                        if all_tweets:
                            return {username:all_tweets}
                        break
                    for tweet in tweets:
                        user_folowers = int(tweet.get('author',{}).get('followers'))
                        dt = datetime.strptime(tweet.get("createdAt"), "%a %b %d %H:%M:%S %z %Y")
                        date_utc_plus_one = dt + timedelta(hours=1)
                        # tweet_date = date_utc_plus_one.strftime("%a %b %d %H:%M:%S %z %Y")
                        tweet_date = date_utc_plus_one.strftime("%Y-%m-%d %H:%M:%S")
                        contract_patterns = r'\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}|T[1-9A-HJ-NP-Za-km-z]{33})\b'
                        ticker_partterns = r'\$[A-Za-z0-9_-]+'
                        await asyncio.sleep(5)

                        try:
                            # ticker_names = re.findall(ticker_partterns,tweet['text'])
                            ticker_names = await asyncio.create_task(GeminiRefine(tweet['text']))
                            contracts  = re.findall(contract_patterns,tweet['text']) 
                        except:
                            # ticker_names = re.findall(ticker_partterns,tweet['text'])
                            ticker_names = await asyncio.create_task(GeminiRefine(tweet['text']))
                            contracts  = re.findall(contract_patterns,tweet['text']) 
                        tweet_info = {
                        'ticker_names':ticker_names,#list(set([ticker[1:] for ticker in ticker_names])), # Remove whene gemini is in
                        'contracts':contracts,
                        'followers':user_folowers,
                        'date_tweeted':tweet_date[:-3]+':00',
                        }
                        if len(all_tweets) == limit:
                            return {username:all_tweets}
                        all_tweets.append(tweet_info)
                    if not data['next_cursor']:
                        logging.warning("No more tweets found or reached the end of results.")
                        return {username:all_tweets}

                    params['cursor'] = data['next_cursor']
                    logging.info(f"Fetched {len(data['data']['tweets'])} tweets, moving to next page...") 
                except requests.exceptions.HTTPError as http_err:
                    logging.error(f"HTTP error occurred: {http_err}")
                except requests.exceptions.RequestException as err:
                    logging.error(f"Error occurred: {err}")
                except ValueError as json_err:
                    logging.error(f"Error parsing JSON response: {json_err}")
   

def search(params:dict,followers_threshold:int|None=None):
    from datetime import timedelta,datetime
    header = {
                "X-API-Key": API_KEY
            }
    all_tweets = []
    try:
        while True:
            # Make the GET request to the TwitterAPI.io endpoint
            response = requests.get(BASE_URL, headers=header, params=params)
            data = response.json()
            tweets = data.get('tweets', [])
            if not tweets:
                logging.info("No tweets found for the given query. Checking Next Hours Tweets")
                if all_tweets:
                    return all_tweets
                break
            for tweet in tweets:
                print(tweet)
                user_folowers = int(tweet.get('author',{}).get('followers'))
                if followers_threshold and user_folowers < followers_threshold:
                    continue
                dt = datetime.strptime(tweet.get("createdAt"), "%a %b %d %H:%M:%S %z %Y")
                date_utc_plus_one = dt + timedelta(hours=1)
                tweet_date = date_utc_plus_one.strftime("%a %b %d %H:%M:%S %z %Y")
                tweet_info = {
                    "userName": tweet.get("author", {}).get("userName"),
                    "text": tweet.get("text"),
                    'followers':user_folowers,
                    "createdAt": tweet_date,
                    'tweet_link': tweet.get('url')
                }
                all_tweets.append(tweet_info)
            if not data['next_cursor']:
                logging.warning("No more tweets found or reached the end of results.")
                return all_tweets

            params['cursor'] = data['next_cursor']
            logging.info(f"Fetched {len(data['tweets'])} tweets, moving to next page...") 
            
    
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error occurred: {err}")
    except ValueError as json_err:
        logging.error(f"Error parsing JSON response: {json_err}")

@app.get('/search/{keyword}/{date}')
def search_tweets(keyword:str,date:str,from_date:str|None = None,time_search:str|None=None,followers_threshold:int|None=None,limit:int = 1,checkAlive:bool = False):
    if from_date:
        keyword = f"{keyword} since:{from_date}"
    EarlyTweets = []
    if checkAlive:
        logging.info('Checking if Api is Alive')
        return {'Status':200}
    hour = 0
    time_hour = 0
    if time_search:
        time_hour = int(str(time_search[:2]))
    
    if followers_threshold:
        if followers_threshold < 100:
            followers_threshold = None

    while True:
        hour += 1
        if time_search:
            time_hour += 1

            keyword_date = f"{keyword} since:{date}_{time_search}_UTC until:{date}_{time_hour}:00:00_UTC"
           
        else:
            keyword_date = f"{keyword} until:{date}_{hour}:00:00_UTC"
        
        params = {
            "query": keyword_date,
            'cursor':"",
            'hash_next_page':True
            }
        params['query'] = keyword_date
        if hour == 24 or time_hour ==24:
            logging.warning("Reached 24 hours limit, stopping search.")
            if all_tweets:
                break
            return {'Error': 'No tweets found for the given query. Change the keyword or date.'}
        all_tweets= search(params,followers_threshold)
        
        if all_tweets and len(all_tweets) >= limit:
            logging.info(f"Fetched {len(all_tweets)} tweets for keyword: {keyword_date}")
            break
    for tweet in reversed(all_tweets):
        if len(EarlyTweets) == limit:
            break
        EarlyTweets.append(tweet)
    return EarlyTweets 


async def GeminiRefine(tweet_text:str):
    search_prompt = f'You are an expert at analyzing cryptocurrency-related tweets and news. Based on the context of the provided text, extract the ticker symbol(s)  of the main cryptocurrency or token being discussed. If the text focuses on a crypto platform (e.g., an exchange or blockchain) rather than a specific token, identify and return the ticker symbol of the platform’s native token, if applicable (e.g., Telegram → TON, Binance → BNB). If the text mentions a founder, team member, or associate tied to a cryptocurrency or platform, extract the ticker symbol of the specific token associated with them (e.g., Pavel Durov → TON, Vitalik Buterin → ETH, Anatoly Yakovenko → SOL). Use known associations between founders, platforms, and tokens to infer the token even if not explicitly mentioned. If multiple tokens are mentioned, prioritize the token(s) that are the primary focus of the text based on context. If no specific token, platform, or founder is mentioned, or if the focus is unclear, return "None." Only return the ticker symbol(s) (e.g., BTC, ETH, SOL) without additional explanation.'

    headers = {
        "x-goog-api-key": GEMINI_API,
        "Content-Type": "application/json"
    }  
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f'''{search_prompt}
                        Tweet: {tweet_text}'''
                    }
                ]
            }
        ],
        "generationConfig": {
            "thinkingConfig": {
                "thinkingBudget": 0
            }
        }
    }
    async with aiohttp.ClientSession() as session:
        
        async with session.post(url=GEMINI_URL,json=payload,headers=headers,) as response:
            if response.status == 200:
                result = await response.json()
                token_mentioned = result['candidates'][0]['content']['parts'][0]['text']
                if token_mentioned != 'None':
                    token_mentioned = token_mentioned.split(',')
                    return token_mentioned
                else:
                    empty = []
                    return empty
            else:
                empty = []
                return empty




async def link_search(tweet_id:str):
    from datetime import datetime,timedelta
    logging.info(f'Searchig Tweet With Id')
    url = f"https://api.twitterapi.io/twitter/tweets?tweet_ids={tweet_id}"
        
    header = {
                "X-API-Key": API_KEY
            }
    response = requests.get(url=url,headers=header)
    if response.status_code == 200:
        result = response.json()
        tweets = result['tweets']
        
        if tweets:
            dt = datetime.strptime(tweets[0]["createdAt"], "%a %b %d %H:%M:%S %z %Y")
            date_utc_plus_one = dt + timedelta(hours=1)
            tweet_date = date_utc_plus_one.strftime("%Y-%m-%d %H:%M:%S")
            contract_patterns = r'\b(0x[a-fA-F0-9]{40}|[1-9A-HJ-NP-Za-km-z]{32,44}|T[1-9A-HJ-NP-Za-km-z]{33})\b'
            ticker_partterns = r'\$[A-Za-z0-9_-]+'
            ticker_names = re.findall(ticker_partterns,tweets[0]['text'])
            contracts  = re.findall(contract_patterns,tweets[0]['text']) 
           
            if not ticker_names:
                ticker_names = await asyncio.create_task(GeminiRefine(tweets[0]['text']))
            if not ticker_names and not contracts:
                return {'Error': 'No Ticker Or Contract Found In This Tweet'}
            tweet_info = {
                'ticker_names':ticker_names,
                'contracts':contracts,
                'date_tweeted':tweet_date,
                'followers':tweets[0]['author']['followers']
            }
            print(tweet_info)
            return tweet_info
        else:
            return {'Error':'Couldnt Search With This Link'}
    else:
        print(response.status_code)
        return {'Error': f'Couldnt Search With Link. Code {response.status_code}'}



@app.get('/link_search')
async def search_with_link(url:str):
    url = url.lower()
    if url.startswith('https://x.com/'):
        print(url)
        try:
            tweet_id_search = re.search(r"status/(\d+)",url)
            # tweet_id = url.split('/')[-1]
            # username = url.split('/')[-3]
            if tweet_id_search and len(tweet_id_search.group(1)) == 19:
                tweet_id = tweet_id_search.group(1)
                tweet_data = await link_search(tweet_id=tweet_id)
                return tweet_data
            else:
                return {'Error':'Invalid Tweet_id'}
        except:
            return {'Error':'Invalid X link'}
    else:
        return {'Error': 'Invalid X Link: Link is not X link'}


# Search Tweet and grab Ticker mentioned then Get price price Using Tweet date time
@app.get("/link")
def process_link(tweet_url:str,timeframe:str) ->list:
    timeframes = process_timeframe(timeframe)
    logging.info('Ready To Search Tweet With Tweet Link')
    # url = 'https://basesearch.onrender.com/link_search/'
    params = {
        'url':tweet_url
    }
    reaponse = requests.get(url=BASESEARCH_LINK_URL,params=params)
    result = reaponse.json()
    ticker_names = result['ticker_names']
    ticker_names =   list({ticker[1:] if ticker.startswith('$') else ticker for ticker in ticker_names})
    tweeted_date = result['date_tweeted'][:-3]+':00'
    
    async def main():
        search_tasks = [Bybit_Price_data(symbol=ticker,timeframes=timeframes,start_date_time=tweeted_date) for ticker in ticker_names]
        ticker_price_data = await asyncio.gather(*search_tasks)
        ticker_price_data.append({'date_tweeted':tweeted_date})
        return ticker_price_data

    ticker_price_data = asyncio.run(main())
    return ticker_price_data


async def scoring(timeframe,price_change):
    prototype  = {
                                'hour':{'100_percnt growth':4,   
                                    '50percnt growth':2,
                                    '20percnt growth':1}
      
                         }
    if price_change == None:
        score = 0
        return score
    else:
        if price_change[:1] == '-':
            score = 0
            return score
        
        price_change = float(price_change[:-1])

    async def givescore(timeframe_score_board,timeframe,price_change,hour_minute):
        if timeframe >= list(timeframe_score_board.keys())[0]:
            for increase_perc,score in timeframe_score_board[hour_minute].items():
                if price_change >= increase_perc:
                    return score
                else:
                    score = 0
            return score
        else:
            score = 0
            return score

    hour_score = {
        2:{0.00002:4,   
           0.00015:2,
           0.0001:1}
    }
    minutes_score = {
        15:{1.0:8,
           0.0000015:4,
           0.000001:2}
    }
    if int(timeframe) >= 60:
        
        hour = int(timeframe //60)
        score = await asyncio.create_task(givescore(hour_score,hour,price_change,2))
        return score
    else:
        minutes = int(timeframe)
        score = await asyncio.create_task(givescore(minutes_score,minutes,price_change,15))
        return score

async def Process_price_Data(price_data,Ai=False):
    logging.info('Processing Price Data')
    timeframeData = price_data['Timeframe_minute']
    timeframe = list(timeframeData.keys())[0]
    start_timestamp = int(price_data['start_time'])

    end_timestamp = price_data['end_time']
    bybit_price_info = timeframeData[timeframe]
                # 'lastprice'                                                                    start price
    price_info = [float(price) for data in bybit_price_info for index, price in enumerate(data) if index in [1,2,3,4]]
    timestamp_info = [int(timestamp) for data in bybit_price_info for index, timestamp in enumerate(data) if index in [0]]
    

    # For AI Which Uses 24hr Timeframe (1440)
    if Ai and timeframe == 1440:
        close_prices_for_Ai = [float(price) for data in bybit_price_info for index, price in enumerate(data) if index in [4]]
        
        close_prices_for_Ai = list(reversed(close_prices_for_Ai))
        timestamp_info = list(reversed(timestamp_info))
        
        matched_price_timestamp = {}

        for index, timestamp in enumerate(timestamp_info):
            matched_price_timestamp[f'{timestamp}'] = close_prices_for_Ai[index]
        # we just need the price info and the timestamp for the Ai Integration.

    if start_timestamp in timestamp_info:
        entry_price = price_info[-1]
        price_info = price_info[:-4]
    else:
        entry_price = price_info[-4]

    close_price = price_info[3] 
    peak_price = round(max(price_info),7)
    lowest_price = round(min(price_info),7)
    max_so_far = price_info[-4]
    max_drawdown  = 0 
    
    percentage_change = str(round(((close_price - entry_price)/entry_price) * 100,3)) + '%'
    entry_to_peak = str(round(((peak_price - entry_price) /entry_price) * 100,3)) +'%'
    entry_price = "{:.13f}".format(entry_price).rstrip("0") 
    close_price = "{:.13f}".format(close_price).rstrip("0")
    lowest_price =  "{:.13f}".format(lowest_price).rstrip("0")
    peak_price = "{:.13f}".format(peak_price).rstrip("0")
    score = await asyncio.create_task(scoring(timeframe,percentage_change))

    for price in reversed(price_info):# Using Reversed Here Beacause the price data started from the last item of the  list.
        if price > max_so_far :
            max_so_far = price
        drawadown = (( price - max_so_far) / max_so_far) * 100
        max_drawdown = min(drawadown,max_drawdown)

    if int(timeframe) >= 60:
        hour = int(timeframe) // 60
        minute_check = int(timeframe) % 60
        if minute_check > 0:
            timeframe = f'{hour}hr:{minute_check}m'
        else:
            timeframe = f'{hour}hr'
    else:
        timeframe = f'{timeframe}m'

    price_info = {
                'timeframe':timeframe,
                'Entry_Price': entry_price,
                'Price':close_price,
                '%_Change':percentage_change,
                'score':score,
                'Peak_Price':peak_price,
                '%_Entry_to_Peak': entry_to_peak,
                'lowest_Price' : lowest_price,
                'Max_Drawdown': round(max_drawdown,7)
                }
    
    # Added In Order To Get The Data To Be Used In Ai Integration To Fetch The Profitable Timeframe
    if Ai and timeframe == '24hr':
        price_info['Ai'] = matched_price_timestamp

    return price_info 

async def Fetch_Price(session,params,end_time,limit):
    logging.info('Fetching Prices')
    searchCount = 0
    expectedSearch = (limit/1000) + 1
    params['end_time'] = end_time
    params['limit'] = limit
    prices_info = []
    # url = 'https://bybit-ohlcv.onrender.com/bybit/ohlcv'
    while True:
        async with session.get(url=BYBIT_OHLCV_URL,params=params) as response:
            if response.status == 200:
                await asyncio.sleep(4)
                result = await response.json()
                if result['result']:
                    searchCount += 1
                    price_data = result['result']['list']
                    prices_info = prices_info + price_data
                    if len(prices_info) >= limit:
                        return {'Timeframe_minute':{limit:prices_info},'start_time':params['start_time'],'end_time':end_time}
                    elif searchCount >= expectedSearch:
                        return {'Timeframe_minute':{limit:prices_info},'start_time':params['start_time'],'end_time':end_time}
                    else:
                        first_entry = price_data[-1]
                        params['end_time'] = first_entry[0]
                        continue
                else:
                    logging.error(f'Empty Price Data. Check Your Parameters')
                    return {'Error':f'Empty Price Data. Check Your Parameters'}
            else:
                logging.error(f'Unable to Fetch Price: code= {response.status }')
                return {'Error':f'Unable to Fetch Price: code= {response.status }'}


async def Fetch_Price_Binance(session,params,end_time,limit):
    logging.info('Fetching Prices (Binance)')
    searchCount = 0
    expectedSearch = (limit/1000) + 1
    params['end_time'] = end_time
    params['limit'] = limit
    params['interval'] = '1m'
    original_start_time = params['start_time']
    prices_info = []
    #url = 'https://bybit-ohlcv2.onrender.com/binance/ohlcv'
    while True:
        async with session.get(url=BINANCE_OHLCV_URL,params=params) as response:
            if response.status == 200:
                await asyncio.sleep(4)
                result = await response.json()
                if result:
                    searchCount += 1
                    price_data = result
                    prices_info = prices_info + price_data
                    
                    if len(prices_info) >= limit:
                        return {'Timeframe_minute':{limit:list(reversed(prices_info))},'start_time':original_start_time,'end_time':end_time}
                       
                    elif searchCount >= expectedSearch:
                        return {'Timeframe_minute':{limit:list(reversed(prices_info))},'start_time':original_start_time,'end_time':end_time}
                    else:
                        first_entry = price_data[-1]
                        params['start_time'] = first_entry[0]
                        continue
                else:
                    logging.error(f'Empty Price Data. Check Your Parameters')
                    return {'Error':f'Empty Price Data. Check Your Parameters'}
            else:
                logging.error(f'Unable to Fetch Price: code= {response.status }')
                return {'Error':f'Unable to Fetch Price: code= {response.status }'}

async def fetch_symbol(symbol:str,url:str) -> str:
    logging.info(f'Fetcing Symbol {symbol} From Bybit')
    # url = 'https://bybit-ohlcv.onrender.com/bybit/tickers'
    params = {
        'symbol':symbol
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url,params=params) as response:
            if response.status == 200:
                result = await response.text()
                return result[1:-1]
            logging.error(f'Unable to Fetch symbol: code= {response.status }')
            # return {'Error':f'Unable to Fetch symbol: code= {response.status }'}


async def time_Convert(time_str:str,timeframe):
    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    added_timeframe = dt + timedelta(minutes=timeframe)
    end_time = str(int(time.mktime(time.strptime(str(added_timeframe), "%Y-%m-%d %H:%M:%S"))) * 1000)
    return end_time

async def Bybit_Price_data(symbol:str,timeframes:str|list,start_date_time:str,Ai:bool=False) -> dict:
    logging.info('Activating Bybit Price Searcher')
    start_time = str(int(time.mktime(time.strptime(start_date_time, "%Y-%m-%d %H:%M:%S"))) * 1000)
    if isinstance(timeframes,list):
        limits = [timeframe for timeframe in timeframes]
        times_tasks = [time_Convert(start_date_time,timeframe) for timeframe in timeframes]
        end_times = await asyncio.gather(*times_tasks)
    elif isinstance(timeframes,str) or isinstance(timeframes,int):
        limits = [timeframes]
        times_tasks = [time_Convert(start_date_time,limit) for limit in limits]
        end_times = await asyncio.gather(*times_tasks)

    Ticker_url_used = None
    Ticker_url_used = BYBIT_TICKER_URL
    symbol_task = asyncio.create_task(fetch_symbol(symbol,Ticker_url_used))
    symbol_pair = await symbol_task

    try:
        symbol_error = symbol_pair[1:]
        if symbol_error.startswith('Error'):
            Ticker_url_used = BINANCE_TICKER_URL
            symbol_task = asyncio.create_task(fetch_symbol(symbol,Ticker_url_used))
            symbol_pair = await symbol_task
            try:
                symbol_error = symbol_pair[1:]
                if symbol_error.startswith('Error'):
                    return {f'${symbol}': 'Not On Exchange'}#'Not On Bybit'}
            except:
                pass
        # added binance price fetch 
    except:
        pass
    params = {
            "symbol":str(symbol_pair),
            'interval':1,
            "start_time": start_time
        }
    
    async with aiohttp.ClientSession() as session:
        if Ticker_url_used == BINANCE_TICKER_URL:
            prices_Fetch = [Fetch_Price_Binance(session=session,params=params,end_time=end_times[index],limit=limit) for index, limit in enumerate(limits) ]
        else:
            prices_Fetch = [Fetch_Price(session=session,params=params,end_time=end_times[index],limit=limit) for index, limit in enumerate(limits) ]
        timeframe_Prices = await asyncio.gather(*prices_Fetch)
        Process_price_task = [Process_price_Data(timeframe_price_data,Ai=Ai) for timeframe_price_data in timeframe_Prices]
        price_infos = await asyncio.gather(*Process_price_task)
        return {f'${symbol}':price_infos}


def process_timeframe(input_string):
    items = input_string.split(',')
    result = []
    
    for item in items:
        if ':' in item:
            hours, minutes = map(int, item.split(':'))
            total_minutes = hours * 60 + minutes
            result.append(total_minutes)
        else:
            result.append(int(item))
    return sorted(result)

#Search Ticker On  Cex
@app.get("/ticker")
def process_link(tickers:str,start_date:str,timeframe:str,Ai:bool=False) ->list: # Add Ai for prompt separation
    logging.info('Ready To Search Ticker On Cex')
    timeframes = process_timeframe(timeframe)
    tickers = list(set(tickers.split()))
    start_date_time = str(start_date)
    
    async def main():
        search_tasks = [Bybit_Price_data(symbol=ticker,timeframes=timeframes,start_date_time=start_date_time,Ai=Ai) for ticker in tickers]
        ticker_price_data = await asyncio.gather(*search_tasks)
        ticker_price_data.append({'date_tweeted':start_date_time})
        return ticker_price_data
    ticker_price_data = asyncio.run(main())
    return ticker_price_data


