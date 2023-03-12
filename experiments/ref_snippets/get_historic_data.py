'''
First, you need to sign up for an API key. Go to https://developer.yahoo.com/login/ and log in or create an account. 
Once you're logged in, go to the Yahoo Finance API page (https://developer.yahoo.com/apis/yahoo-finance/) 
and click on "Get API Key". 
Follow the instructions to create an API key.

'''
import requests

# set the API endpoint and parameters
url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data"
params = {
    "symbol": "AAPL",
    "region": "US",
    "interval": "1h",
    "range": "5d",
}

# set the headers and API key
headers = {
    "x-rapidapi-key": "<your API key>",
    "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com",
}

# make the API request
response = requests.get(url, params=params, headers=headers)

# extract the historical data from the response
data = response.json()["prices"]
for item in data:
    date = item["date"]
    close_price = item["close"]
    print(f"On {date}, the closing price of AAPL was {close_price}")
