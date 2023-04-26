import requests
import pandas as pd 
import os
import json
import time
from prefect import flow, task
# Replace YOUR_API_KEY with your actual API key
# number_of_rows = 400


TESTING = True
@task
def get_api_key():
    f = open('../api_key.json')
    try:
        data = json.load(f)
    except Exception as e:
        print(f'Error: json read\n {e}')
        return "-1"
    
    if "alphavantage" in data.keys():
        print(f'Key found; returning key')
        return data["alphavantage"]
    else:
        print('Key not found; file should be following\n\t {"alphavantage" : "your_key"}')
        return "-1"

@task
def get_and_preprocess(symbol, api_key, colmn_rename):
    # Construct the API endpoint URL
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={api_key}'

    # Make a GET request to the API endpoint
    response = requests.get(url)
    # 5 api calls for every 5 min, hence need to sleep 1m every api call :)) 
    print(f'Sleeping for 1min....')
    time.sleep(60)
    # Check if the request was successful
    if response.status_code == 200:
        # Get the close data from the response JSON
        try:
            data = response.json()['Time Series (Daily)']
        except Exception as e:
            print(f'Data for {symbol} not found\n error = {e}')
            print(f'Data = {response.json()}')
            df = pd.DataFrame()
            return df
        close_data = {date: float(values['4. close']) for date, values in data.items()}
        print(f'data recieved from api {len(close_data)} for {symbol}')
        # print(close_data)
    else:
        print(f'Request failed with status code {response.status_code} for {symbol}')
        df = pd.DataFrame()
        return df


    df_tmp = pd.DataFrame(data) \
        .T.reset_index() \
        .rename_axis('index', axis='columns') \
        .rename(columns = colmn_rename) 

    cols = list(df_tmp.columns)
    cols.remove('date')
    df_tmp[cols] = df_tmp[cols].apply(pd.to_numeric, errors='coerce')
    df_tmp['date'] = df_tmp['date'].apply(pd.to_datetime,format='%Y-%m-%d') 
    df_tmp['close_percent_change'] = round(df_tmp.loc[::-1].close.pct_change() * 100, 4)
    df_tmp['adjusted_close'] = df_tmp['adjusted_close'].round(decimals=4)
    df_tmp['company'] = symbol

    return df_tmp

@task
def write_data_to_file(df, company):

    min_year = min(df.date).year
    max_year = max(df.date).year
    
    # create historic folder 
    for year in range (min_year, max_year):
        df_year = df[df['date'].dt.year == year]
        # include = df[df['Date'].dt.year == year]
        print(f'{company}: {year}: {len(df_year)}')
        path_historic = f'data/price_n_volume/historic/{year}/'
        isExist = os.path.exists(path_historic)
        if not isExist:

           # Create a new directory because it does not exist
           os.makedirs(path_historic)
           print(f"The new directory is created! {path_historic}")

        df_year.to_parquet(f'{path_historic}/{company}.parquet', index=False)
        # df_year.to_csv(f'{path}/{company}.csv')
    
    # create recent folder, this year and last year;
    # hdr = False  if os.path.isfile('filename.csv') else True
    # df.to_csv('filename.csv', mode='a', header=hdr)
    for year in range (max_year -1, max_year + 1):
        df_year = df[df['date'].dt.year == year]
        for date_ in df_year.date.unique():
            df_date = df_year[df_year['date'] == date_]
            path_recent = f'data/price_n_volume/recent/'
            isExist = os.path.exists(path_recent)
            if not isExist:
                os.makedirs(path_recent)
                print(f"The new directory is created! {path_recent}")
            
            date_csv_path = f'{path_recent}/{date_}.csv'
            hdr = False  if os.path.isfile(date_csv_path) else True
            df_date.to_csv(date_csv_path, mode='a', header=hdr, index=False)


def write_last_n_days_data(df, company, last_n_days = 5):
    # from full dataframe sort for last n days 
    # in each file, check if entry of same date, company is present,if yes, do not append 
    # else append
    df_write = df.head(last_n_days)
    print(f'df_write.shape = {df_write.shape}')
    for date_ in df_write.date.unique():
        df_date = df_write[df_write['date'] == date_]
        path_recent = f'data/price_n_volume/recent/'
        isExist = os.path.exists(path_recent)
        if not isExist:
            os.makedirs(path_recent)
            print(f"The new directory is created! {path_recent}")
        
        date_csv_path = f'{path_recent}/{date_}.csv'
        hdr = False  if os.path.isfile(date_csv_path) else True
        print(f'date_csv_path = {date_csv_path}, hdr = {hdr}')
        if hdr:
            df_date.to_csv(date_csv_path, mode='a', header=hdr, index=False)
        else:
            df_read = pd.read_csv(date_csv_path)
            df_company = df_read[df_read['company'] == company]
            print(df_company, type(df_company))
            if df_company.empty:
                df_date.to_csv(date_csv_path, mode='a', header=hdr, index=False)
                print(f'Writing for {company} in {date_csv_path}')
            else:
                print(f'Not writing for {company} in {date_csv_path} to avoid duplicate')
    
    pass    

@flow
def initialize_flow():
    api_key = get_api_key()
    
    if api_key == "-1":
        exit(1)
    
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
    
    # symbol = 'AMD'
    filename = 'nasdaq100.log'
    temp = open(filename,'r').read().split('\n')
    print(f'All files listed in file: {temp}')

    if TESTING == False:
        _range = len(temp)
    else:
        _range = 10

    print(f'Amount of data to get from api: {_range}')
    for i in range(_range):
        symbol = temp[i]

        df_all = get_and_preprocess(symbol, api_key, colmn_rename)

        if not df_all.empty:
            write_data_to_file(df_all, symbol)


if __name__=="__main__":
    initialize_flow()

