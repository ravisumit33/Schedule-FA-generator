import yfinance as yf
import pandas as pd

from time_utils import normalize_timestamp
from logger_config import get_logger

logger = get_logger(__name__)

_INR_EXCHANGE_RATE_CACHE: dict[str, float] = {}


def fetch_inr_rates(start_date: str, end_date: str) -> None:
    fx = yf.Ticker("INR=X")
    hist = fx.history(start=start_date, end=end_date)
    if hist.empty:
        return
    for dt, row in hist.iterrows():
        key = normalize_timestamp(dt.to_pydatetime()).strftime("%Y-%m-%d")
        _INR_EXCHANGE_RATE_CACHE[key] = float(row["Close"])


def get_inr_rate(date) -> float:
    ts = normalize_timestamp(pd.to_datetime(date))
    key = ts.strftime("%Y-%m-%d")
    rate = _INR_EXCHANGE_RATE_CACHE.get(key)
    if rate is None:
        # Backfill to previous available day within the year
        prev = ts
        first_jan = pd.Timestamp(year=ts.year, month=1, day=1)
        while rate is None and prev >= first_jan:
            prev -= pd.Timedelta(days=1)
            rate = _INR_EXCHANGE_RATE_CACHE.get(prev.strftime("%Y-%m-%d"))
    if rate is None:
        raise ValueError(f"Exchange rate not found for {key}")
    return float(rate)
