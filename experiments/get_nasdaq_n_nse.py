import requests
import pandas as pd 

# Replace YOUR_API_KEY with your actual API key
number_of_rows = 400

TESTING = False

def get_and_preprocess(symbol, api_key, colmn_rename):
    # Construct the API endpoint URL
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}'

    # Make a GET request to the API endpoint
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the close data from the response JSON
        data = response.json()['Time Series (Daily)']
        close_data = {date: float(values['4. close']) for date, values in data.items()}
        print(f'data sanokes recieved from api {len(close_data)} for {symbol}')
        # print(close_data)
    else:
        print(f'Request failed with status code {response.status_code} for {symbol}')


    df_tmp = pd.DataFrame(data) \
        .T.reset_index() \
        .rename_axis('index', axis='columns') \
        .rename(columns = colmn_rename) 

    cols = list(df_tmp.columns)
    cols.remove('date')
    df_tmp[cols] = df_tmp[cols].apply(pd.to_numeric, errors='coerce')
    df_tmp['date'] = df_tmp['date'].apply(pd.to_datetime,format='%Y-%m-%d') 
    df_tmp['close_percent_change'] = round(df_tmp.loc[::-1].close.pct_change() * 100, 4)

    return df_tmp

def write_data_to_file(df_all, symbol, number_of_rows=400):
    

    df_fresh = df_all.iloc[:number_of_rows]
    df2_old = df_all.tail(-number_of_rows)


    print(f'Writing data about {symbol}')
    df_all.to_parquet(f'data/all/parquet/{symbol}.parquet')
    df2_old.to_parquet(f'data/old/parquet/{symbol}.parquet')
    df_fresh.to_csv(f'data/new/csv/{symbol}.csv.gz')
    if TESTING:
        df_fresh.to_csv(f'data/new/csv/{symbol}.csv')




if __name__=="__main__":
    print('HERE')
    api_key = 'xD'
    colmn_rename = {
        'index': 'date',
        '1. open':'open',
        '2. high':'high',
        '3. low' : 'low',	
        '4. close' : 'close',
        '5. adjusted close' :	'adjusted_close',
        '6. volume'	: 'volume',
        '7. dividend amount'	: 'dividend_amount',
        '8. split coefficient' : 'split_coefficient'
    }
    
    symbol = 'AMD'

    df_all = get_and_preprocess(symbol, api_key, colmn_rename)

    write_data_to_file(df_all, symbol)



