import datetime as dt
import time
from egaugeapi import EgaugeApi
from dateutil.tz import gettz


def parse_dt(str):
    if str is None:
        return None
    try:
        return dt.strptime(str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return dt.strptime(str, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return dt.strptime(str, "%Y-%m-%d")


def floor_dt(dt_exact):
    dt_minute = dt_exact - dt.timedelta(seconds=dt_exact.second,
                                        microseconds=dt_exact.microsecond)
    return dt_minute


def test_round_datetime_to_oldest_minute():
    dt_now = dt.datetime.utcnow()
    ts_now = dt_now.timestamp()
    ts_then = ts_now - 180  # 180 seconds ago
    dt_then = dt.datetime.fromtimestamp(ts_then, dt.timezone.utc)
    floor_dt(dt_then)
    floor_dt(dt_now)


