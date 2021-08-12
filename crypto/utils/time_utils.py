import datetime
from datetime import timedelta
import pandas as pd

def timestamp_to_str(time_stamp, format='%Y-%m-%d %H:%M:%S'):
    timestamp_obj = datetime.datetime.fromtimestamp(time_stamp)
    return timestamp_obj.strftime(format)

def numpy64_to_str(numpy_64_date, format='%Y-%m-%d %H:%M:%S'):
    return pd.to_datetime(str(numpy_64_date)).strftime(format)

def delta_day(dtm, delta_days=0, format='%Y%m%d'):
    date = datetime.strptime(dtm, format)
    date += timedelta(days=delta_days)
    return date.strftime(format)
