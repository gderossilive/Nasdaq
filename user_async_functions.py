# Python 3
import requests
import json
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import Set, Callable, Any

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='async-app.log', encoding='utf-8', level=logging.DEBUG)

async def plot_time_series(data):
    """
    Plot a time series starting from the json data.
    :param data: The JSON response from the API
    :return: The time series as a pandas DataFrame
    """
    logging.info('Entering in plot_time_series()')
    # Convert the JSON response to a pandas DataFrame
    df = pd.DataFrame(data['data'])
    # Convert the date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    # Set the date as the index
    df.set_index('date', inplace=True)
    # Plot the time series in a line plot stored in a file
    plt.imsave('time_series.png', df.plot( ).get_figure())
    logging.info('Generated  time_series.png')
    # Return the file name
    return 'time_series.png'

async def get_news(symbols) -> str:
    """
    Get the news for a given symbol or a given list of symbols, separated by commas.
    :param symbol: One or more symbols to get the news for
    :return: The JSON response organized as follows:
        meta > found:	                                The number of articles found for the request.
        meta > returned:	                            The number of articles returned on the page. This is useful to determine the end of the result set as if this is lower than limit, there are no more articles after this page.
        meta > limit:	                                The limit based on the limit parameter.
        meta > page:	                                The page number based on the page parameter.
        data > uuid:	                                The unique identifier for an article in our system. Store this and use it to find specific articles using our single article endpoint.
        data > title:	                                The article title.
        data > description:	                            The article meta description.
        data > keywords:	                            The article meta keywords.
        data > snippet:	                                A short snippet of the article body.
        data > url:	                                    The URL to the article.
        data > image_url:	                            The URL to the article image.
        data > language:	                            The language of the source.
        data > published_at:	                        The datetime the article was published.
        data > source:	                                The domain of the source.
        data > relevance_score:	                        Relevance score based on the search parameter. If the search parameter is not used, this will be null.
        data > entities > symbol:	                    Symbol of the identified entity.
        data > entities > name:	                        Name of the identified entity.
        data > entities > exchange:	                    Exchange identifier of the identified entity.
        data > entities > exchange_long:	            Exchange name of the identified entity.
        data > entities > country:	                    Exchange country of the identified entity.
        data > entities > type:	                        Type of the identified entity.
        data > entities > industry:	                    Industry of the identified entity.
        data > entities > match_score:	                The overall strength of the matching for the identified entity.
        data > entities > sentiment_score:	            Average sentiment of all highlighted text found for the identified entity.
        data > entities > highlights > highlight:	    Snippet of text from the article where the entity has been identified.
        data > entities > highlights > sentiment:	    The sentiment of the highlighed text.
        data > entities > highlights > highlighted_in:	Where the highlight was found (title | main_text).
        data > similar:	                                Array of news articles which are very similar to the main article.
    
    """
    logging.info('Getting news for symbol: %s', symbols)
    # Define the endpoint
    url = "https://api.stockdata.org//v1/news/all"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "api_token": "zYrWkwgLVNH2Okm1GUyvsv437fEKSH8wNDxHl8w8",
        "symbols": symbols,
        "limit": 2
    }
    # Make the GET request
    response = requests.get(url, headers=headers, params=params)
    logging.info('get_news() response: %s', response.json())
    # Return the JSON response
    return json.dumps(response.json())


async def get_quote(symbols) -> str:
    """
    Get the quote for a given symbol or a given list of symbols, separated by commas.
    :param symbol: One or more symbols to get the quotes for
    :return: The JSON response organized as follows:
        meta > requested:	                The number of symbols requested.
        meta > returned:                    The number of symbols returned.
        data > ticker:	                    The symbol/ticker of the quote.
        data > name:                        The name of the stock.
        data > exchange_short:	            The listing exchange of the stock (short code).
        data > exchange_long:	            The listing exchange of the stock (full name).
        data > mic_code:	                The exchanges ISO 10383 market identifier code.
        data > currency:	                Currency of the stock.
        data > price:	                    Last trade price.
        data > day_high:	                Highest trade price that day.
        data > day_low:	                    Lowest trade price that day.
        data > day_open:	                Opening price.
        data > 52_week_high:	            Highest trade price in the past 52 weeks.
        data > 52_week_low:	                Lowest trade price in the past 52 weeks.
        data > market_cap:	                Market cap of the stock.
        data > previous_close_price:	    Previous close price.
        data > previous_close_price_time:	Time of the previous close price (local time).
        data > day_change:	                Percentage difference between price and previous_close_price.
        data > volume:	                    Total of all trades for the stock.
        data > is_extended_hours_price:	    Boolean to identify if the quote is provided from extended hours data.
        data > last_trade_time:	            The time the last trade was identified (local time).
    """
    logging.info('Getting quote for symbol: %s', symbols)
    # Define the endpoint
    url = "https://api.stockdata.org/v1/data/quote"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "api_token": "zYrWkwgLVNH2Okm1GUyvsv437fEKSH8wNDxHl8w8",
        "symbols": symbols
    }
    # Make the GET request
    response = requests.get(url, headers=headers, params=params)
    logging.info('get_quote() response: %s', response.json())
    # Return the JSON response
    return json.dumps(response.json())

async def get_historical_eod(symbol) -> str:
    """
    Get historical end of day data for US stocks, adjusted for splits.
    :param symbol: One symbol to get the quotes for
    :return: The JSON response organized as follows:
        meta > date_from:   	Date that data was collected from.
        meta > date_to:     	Date that data was collected to. This will be overridden if the interval max period is exceeded.
        meta > max_period_days:	Max period in days depending on the interval. Will return null if no max period is specified for the interval.
        data > date:        	Date of the related data (local time).
        data > ticker:      	The symbol/ticker of the quote.
        data > data > open:	    Open price for the specified date/time range.
        data > data > high: 	Highest price for the specified date/time range.
        data > data > low:  	Lowest price for the specified date/time range.
        data > data > close:	Close price for the specified date/time range.
        data > data > volume:	Trading volume for the specified date/time range.
    """
    logging.info('Getting historical quotes for symbol: %s', symbol)
    # Define the endpoint
    url = "https://api.stockdata.org/v1/data/eod"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "api_token": "zYrWkwgLVNH2Okm1GUyvsv437fEKSH8wNDxHl8w8",
        "symbols": symbol
    }
    # Make the GET request
    response = requests.get(url, headers=headers, params=params)
    logging.info('get_historical_eod() response: %s', response.json())
    # Return the JSON response
    return json.dumps(response.json())

user_async_functions: Set[Callable[..., Any]] = {
    get_quote,
    get_news,
    get_historical_eod,
    plot_time_series
}

#quote=get_quote('MSFT,GOOGL')
#print(quote)

#news = get_news('MSFT')
#json_data = json.loads(news.decode('utf-8'))

# Extract titles
#titles = [item['title'] for item in json_data['data']]
#urls = [item['url'] for item in json_data['data']]

# Print items
#for item in json_data['data']:
#    print(item['title'] + '\n')
#    print(item['description'] + '\n')
#    print(item['snippet'] + '\n')
#    print(item['url'] + '\n')
#    response = requests.get(item['url'])
#    soup = BeautifulSoup(response.content, 'html.parser')
#    paragraphs = soup.find_all('p')
#    for paragraph in paragraphs:
#        print(paragraph.text)
#    print('-------------------------------------------------------------------\n')  
