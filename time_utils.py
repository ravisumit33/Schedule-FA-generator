import pandas as pd


def normalize_timestamp(ts: pd.Timestamp) -> pd.Timestamp:
    ts_pd = pd.to_datetime(ts)
    if isinstance(ts_pd, pd.Timestamp) and ts_pd.tz is not None:
        ts_pd = ts_pd.tz_convert("America/New_York").tz_localize(None)
    return ts_pd.normalize()


def normalize_index(idx: pd.Index) -> pd.DatetimeIndex:
    dti = pd.DatetimeIndex(pd.to_datetime(idx))
    if dti.tz is not None:
        dti = dti.tz_convert("America/New_York").tz_localize(None)
    return dti.normalize()


def fy_start_end(year: int) -> tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(f"{year}-01-01")
    end = pd.Timestamp(f"{year}-12-31")
    return start, end


def fy_quarter(date_ts: pd.Timestamp) -> str:
    dt = normalize_timestamp(date_ts)
    if 1 <= dt.month <= 3:
        return "Q1"
    if 4 <= dt.month <= 6:
        return "Q2"
    if 7 <= dt.month <= 9:
        return "Q3"
    return "Q4"


