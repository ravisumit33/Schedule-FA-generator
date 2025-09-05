import pandas as pd

from constants import TICKER_DETAILS
from time_utils import normalize_timestamp, cy_start_end
from market import get_stock_history, get_splits_series, get_dividends_series
from forex import fetch_inr_rates, get_inr_rate
from logger_config import get_logger

logger = get_logger(__name__)


def _prefetch_inr_rates(xls: dict, start_date: str, end_date: str) -> None:
    """Prefetch INR exchange rates once from the earliest acquisition date across all tickers."""
    global_min_acq = None
    for _, df_all in xls.items():
        acq_series_all = pd.to_datetime(
            df_all.get("Date of acquiring the interest"), errors="coerce"
        )
        if acq_series_all is not None and not acq_series_all.dropna().empty:
            min_acq_all = acq_series_all.min()
            if global_min_acq is None or min_acq_all < global_min_acq:
                global_min_acq = min_acq_all
    if global_min_acq is None:
        global_min_acq = pd.to_datetime(start_date)
    start_date_with_buffer = global_min_acq - pd.Timedelta(days=5)
    fetch_inr_rates(start_date_with_buffer.strftime("%Y-%m-%d"), end_date)


def _prefetch_stock_history(
    ticker: str, df: pd.DataFrame, start_date: str, end_date: str
) -> pd.DataFrame:
    """Prefetch stock history from 5 days before its earliest acquisition date for better backfill coverage."""
    df_acq_series = pd.to_datetime(
        df.get("Date of acquiring the interest"), errors="coerce"
    )
    if df_acq_series is None or df_acq_series.dropna().empty:
        min_acq_for_ticker = pd.to_datetime(start_date)
    else:
        min_acq_for_ticker = df_acq_series.min()

    start_date_with_buffer = min_acq_for_ticker - pd.Timedelta(days=5)
    hist_full = get_stock_history(
        ticker, start_date_with_buffer.strftime("%Y-%m-%d"), end_date
    )
    return hist_full


def _calculate_effective_quantity(
    quantity: float, ticker: str, acq_norm: pd.Timestamp
) -> float:
    """Adjust original quantity with stock splits, if any"""
    splits = get_splits_series(ticker)
    eff_quantity = quantity
    if splits.empty:
        return eff_quantity
    for dt, ratio in splits.items():
        split_date_norm = normalize_timestamp(dt.to_pydatetime())
        if acq_norm <= split_date_norm:
            eff_quantity *= ratio  # e.g., 2 means 2-for-1 split
    return float(eff_quantity)


def _calculate_peak_value(
    hist_holding: pd.DataFrame, quantity: float, ticker: str, acq_norm: pd.Timestamp
) -> float:
    """Calculate peak value during the holding period."""
    peak_idx = hist_holding["Close"].idxmax()
    peak_price = float(hist_holding["Close"].max())
    rate_peak = get_inr_rate(peak_idx)
    eff_qty_peak = _calculate_effective_quantity(quantity, ticker, acq_norm)
    peak_value = round(peak_price * eff_qty_peak * rate_peak, 2)
    return peak_value


def _calculate_closing_value(
    hist_holding: pd.DataFrame, quantity: float, ticker: str, acq_norm: pd.Timestamp
) -> float:
    """Calculate closing value at the end of the holding period."""
    closing_price = float(hist_holding["Close"].iloc[-1])
    closing_date = hist_holding.index[-1]
    rate_closing = get_inr_rate(closing_date)
    eff_qty_close = _calculate_effective_quantity(quantity, ticker, acq_norm)
    closing_value = round(closing_price * eff_qty_close * rate_closing, 2)
    return closing_value


def _calculate_dividends(
    ticker: str,
    quantity: float,
    acq_norm: pd.Timestamp,
    holding_start: pd.Timestamp,
    holding_end: pd.Timestamp,
    ticker_quarter_dividends: dict,
) -> float:
    """Calculate dividends (per-share payouts, scale by split-adjusted quantity and FX)."""
    dividends_series = get_dividends_series(ticker)

    total_dividends_inr = 0.0
    total_dividends = 0.0
    if dividends_series is not None and not pd.Series(dividends_series).empty:
        div_in_period = dividends_series[
            (dividends_series.index >= holding_start)
            & (dividends_series.index <= holding_end)
        ]
        for dt, div_per_share in div_in_period.items():
            eff_qty = _calculate_effective_quantity(quantity, ticker, acq_norm)
            rate_div = get_inr_rate(dt)
            div_usd = float(div_per_share) * eff_qty
            div_inr = div_usd * rate_div
            total_dividends += div_usd
            total_dividends_inr += div_inr

            # Aggregate by CY quarter
            quarter = _cy_quarter_from_date(dt)
            ticker_quarter_dividends.setdefault(ticker, {}).setdefault(
                quarter, {"USD": 0.0, "INR": 0.0}
            )
            ticker_quarter_dividends[ticker][quarter]["USD"] += div_usd
            ticker_quarter_dividends[ticker][quarter]["INR"] += div_inr

    return round(total_dividends_inr, 2)


def _process_ticker_row(
    ticker: str,
    row: pd.Series,
    hist_full: pd.DataFrame,
    cy_start: pd.Timestamp,
    cy_end: pd.Timestamp,
    ticker_quarter_dividends: dict,
    year: int,
) -> dict:
    """Process a single row for a ticker."""
    quantity = float(row.get("Quantity", 0))
    acquisition_raw = row.get("Date of acquiring the interest")

    if quantity <= 0:
        raise ValueError(f"Invalid quantity for {ticker}: {row}")

    acq_date = pd.to_datetime(acquisition_raw, errors="coerce")
    if pd.isna(acq_date):
        raise ValueError(f"Invalid acquisition date for {ticker}: {acquisition_raw}")

    hist = hist_full

    if hist.empty:
        raise RuntimeError(f"No data found for {ticker} in {year}")

    acq_norm = normalize_timestamp(acq_date)

    holding_start = max(normalize_timestamp(acq_date), cy_start)
    holding_end = cy_end
    hist_holding = hist.loc[
        holding_start.strftime("%Y-%m-%d") : holding_end.strftime("%Y-%m-%d")
    ]

    if hist_holding.empty:
        raise ValueError(f"No trading data in holding period for {ticker}")

    peak_value = _calculate_peak_value(hist_holding, quantity, ticker, acq_norm)
    closing_value = _calculate_closing_value(hist_holding, quantity, ticker, acq_norm)
    total_dividends_inr = _calculate_dividends(
        ticker, quantity, acq_norm, holding_start, holding_end, ticker_quarter_dividends
    )

    base_details = dict(TICKER_DETAILS[ticker])
    computed_fields = {
        "Peak value of investment during the Period": peak_value,
        "Closing balance": closing_value,
        "Total gross amount paid/credited with respect to the holding during the period": total_dividends_inr,
        "Total gross proceeds from sale or redemption of investment during the period": 0,
    }
    other_columns = {
        k: v for k, v in row.items() if k != "Quantity" and k not in base_details
    }
    out_row = {**base_details, **other_columns, **computed_fields}
    return out_row


def _finalize_dataframe(updated_rows: list, detail_columns_order: list) -> pd.DataFrame:
    """Finalize the output dataframe with proper column ordering."""
    updated_df = pd.DataFrame(updated_rows)
    leading_cols = [c for c in detail_columns_order if c in updated_df.columns]
    remaining_cols = [c for c in updated_df.columns if c not in leading_cols]
    updated_df = updated_df[leading_cols + remaining_cols]
    updated_df = updated_df.drop(columns=["Quantity"], errors="ignore")
    return updated_df


def update_schedule_fa(input_excel: str, year: int):
    logger.info("Reading input workbook: %s", input_excel)
    xls = pd.read_excel(input_excel, sheet_name=None)
    updated_rows = []
    ticker_quarter_dividends: dict[str, dict[str, dict[str, float]]] = {}

    if not TICKER_DETAILS:
        raise ValueError(
            "TICKER_DETAILS is empty; cannot determine detail columns order"
        )
    detail_columns_order = list(next(iter(TICKER_DETAILS.values())).keys())

    cy_start, cy_end = cy_start_end(year)
    start_date = cy_start.strftime("%Y-%m-%d")
    end_date = cy_end.strftime("%Y-%m-%d")

    _prefetch_inr_rates(xls, start_date, end_date)

    for ticker, df in xls.items():
        ticker = str(ticker).strip()
        logger.info("Processing ticker: %s", ticker)
        if ticker not in TICKER_DETAILS:
            raise ValueError(f"Missing details for ticker '{ticker}' in TICKER_DETAILS")

        hist_full = _prefetch_stock_history(ticker, df, start_date, end_date)

        row_count = 0
        for _, row in df.iterrows():
            out_row = _process_ticker_row(
                ticker, row, hist_full, cy_start, cy_end, ticker_quarter_dividends, year
            )
            updated_rows.append(out_row)
            row_count += 1
        logger.info("Ticker %s processed: %d rows", ticker, row_count)

    updated_df = _finalize_dataframe(updated_rows, detail_columns_order)
    logger.info("Total rows processed: %d", len(updated_df))

    return updated_df, ticker_quarter_dividends


def _cy_quarter_from_date(dt) -> str:
    month = int(pd.to_datetime(dt).month)
    if 1 <= month <= 3:
        return "Q1"
    if 4 <= month <= 6:
        return "Q2"
    if 7 <= month <= 9:
        return "Q3"
    return "Q4"
