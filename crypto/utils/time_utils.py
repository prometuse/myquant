import datetime

def timestamp_to_str(time_stamp, format='%Y-%m-%d %H:%M:%S'):
    timestamp_obj = datetime.datetime.fromtimestamp(time_stamp)
    return timestamp_obj.strftime(format)