# Meeting notes 

# March 12, 2023 

Looking for data source to get US & India's stock data on daily, hourly and 15 min timeframes
1. yahoo finance: not free anymore

```
There are several API sources that you can use to get stock related data for NSE listed stocks. Here are some options:

    Alpha Vantage: Alpha Vantage provides free and paid APIs for retrieving real-time and historical data for stocks and other financial instruments. They support NSE listed stocks, and you can retrieve data in various timeframes including daily, weekly, and hourly. Alpha Vantage also provides technical indicators and other features.

    Yahoo Finance: Yahoo Finance provides an API for retrieving stock data, news, and other financial information. However, their free API service was discontinued in 2018, and the new paid API service is available on the RapidAPI platform.

    Quandl: Quandl provides a wide range of financial and economic data, including data for NSE listed stocks. They have both free and paid APIs, and you can retrieve data in various formats including JSON, CSV, and Excel. Quandl also provides data from several other sources, and they offer a variety of data analytics tools.

    Tiingo: Tiingo provides a financial data API for stocks, bonds, and other assets. They support NSE listed stocks, and you can retrieve data in various timeframes including daily, weekly, and monthly. Tiingo also provides fundamental data, news, and other features.
```

For Alpha Vantage: 
> community of users for up to 5 API requests per minute and 500 requests per day. 

Use following URL to get data 
```python
BSE
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=TCS.BSE&outputsize=full&apikey={api_key}'
NASDAQ
    symbol = 'IBM'

    # Construct the API endpoint URL
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}'

```

For Yahoo finance 
>  500 / month Hard Limit
    10,000 / month
   + $0.002 each other ( for 10$ per month)
	