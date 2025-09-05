import yfinance as yf
import pandas as pd

from time_utils import normalize_index
from logger_config import get_logger

logger = get_logger(__name__)

_STOCK_HISTORY_CACHE: dict[tuple[str, str, str], pd.DataFrame] = {}
_SPLITS_CACHE: dict[str, pd.Series] = {}
_DIVIDENDS_CACHE: dict[str, pd.Series] = {}


def get_stock_history(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    key = (str(ticker).upper(), str(start_date), str(end_date))
    hist = _STOCK_HISTORY_CACHE.get(key)
    if hist is not None:
        return hist
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    hist.index = normalize_index(hist.index)
    _STOCK_HISTORY_CACHE[key] = hist
    return hist


def get_splits_series(ticker: str) -> pd.Series:
    key = str(ticker).upper()
    series = _SPLITS_CACHE.get(key)
    if series is not None:
        return series
    series = yf.Ticker(ticker).splits
    series.index = normalize_index(series.index)
    _SPLITS_CACHE[key] = series
    return series


def get_dividends_series(ticker: str) -> pd.Series:
    key = str(ticker).upper()
    series = _DIVIDENDS_CACHE.get(key)
    if series is not None:
        return series
    series = yf.Ticker(ticker).dividends
    series.index = normalize_index(series.index)
    _DIVIDENDS_CACHE[key] = series
    return series


