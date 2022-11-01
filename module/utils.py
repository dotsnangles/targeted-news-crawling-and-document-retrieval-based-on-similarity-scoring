import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def filter_time(df):
    now = datetime.now()
    diff_days = timedelta(days=90)
    three_months_ago = now - diff_days
    three_months_ago = pd.to_datetime(three_months_ago, unit='ns', utc=True)
    # three_months_ago = np.datetime64(three_months_ago)

    df['time'] = pd.to_datetime(df['pubDate'], utc=True)
    # df['time'] = pd.to_datetime(df['pubDate']).dt.tz_convert(None)
    df = df.loc[(df['time'] >= three_months_ago)]
    df = df.drop(['time'], axis=1)
    return df