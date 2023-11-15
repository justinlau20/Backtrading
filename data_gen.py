# %%
from binance.client import Client
import pandas as pd
from time import sleep
import datetime


client = Client()

# %%
def get_klines_between_time(symbol, interval, start_time, end_time):
    klines = []
    start_timestamp = int(start_time.timestamp()) * 1000  # Convert start time to milliseconds
    end_timestamp = int(end_time.timestamp()) * 1000  # Convert end time to milliseconds

    while True:
        # Retrieve klines with a limit of 1000 (maximum allowed by Binance)
        response = client.futures_klines(
            symbol=symbol,
            interval=interval,
            startTime=start_timestamp,
            endTime=end_timestamp,
            limit=1000
        )

        klines.extend(response)  # Concatenate the response klines to the existing list

        kline_timestamp = int(response[-1][0]) // 1000  # Convert the last kline timestamp to seconds

        if kline_timestamp >= end_timestamp:
            break

        if len(response) < 1000:
            break

        # Update the start timestamp for the next request
        start_timestamp = int(response[-1][0]) + 1

    return klines

# %%
def klines_to_df(klines):
    columns = [
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        "quote_av", "trades", "tb_base_av", "tb_quote_av", "ignore"
    ]
    df = pd.DataFrame(klines)
    df.columns = columns
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize(None)
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms').dt.tz_localize(None)
    return df

# %%
def get_df(symbol, interval, start_time, end_time):
    klines = get_klines_between_time(symbol, interval, start_time, end_time)
    return klines_to_df(klines)

def save_df(symbol, interval, start_time=datetime.datetime(2023, 1, 1, 8, 0), end_time=datetime.datetime(2023, 11, 15, 7, 59)):
    for sym in symbol:
        for intrvl in interval:
            df = get_df(sym + 'usdt', intrvl, start_time, end_time)
            df.to_csv(f'./data/{sym.upper()}_USDT_PERP_{intrvl}.csv', index=False, date_format="%Y-%m-%d %H:%M:%S")
            sleep(5)

# %%
save_df(['ETH', 'MATIC', "SOL", "BTC"], ['5m', '30m', '2h'])



