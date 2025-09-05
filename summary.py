import pandas as pd


def build_dividend_summary_table(ticker_quarter_dividends: dict[str, dict[str, dict[str, float]]]) -> pd.DataFrame:
    rows = []
    for ticker, qdata in ticker_quarter_dividends.items():
        q1_usd = float(qdata.get("Q1", {}).get("USD", 0.0))
        q1_inr = float(qdata.get("Q1", {}).get("INR", 0.0))
        q2_usd = float(qdata.get("Q2", {}).get("USD", 0.0))
        q2_inr = float(qdata.get("Q2", {}).get("INR", 0.0))
        q3_usd = float(qdata.get("Q3", {}).get("USD", 0.0))
        q3_inr = float(qdata.get("Q3", {}).get("INR", 0.0))
        q4_usd = float(qdata.get("Q4", {}).get("USD", 0.0))
        q4_inr = float(qdata.get("Q4", {}).get("INR", 0.0))
        total_usd = q1_usd + q2_usd + q3_usd + q4_usd
        total_inr = q1_inr + q2_inr + q3_inr + q4_inr

        rows.append(
            {
                "Ticker": ticker,
                "Q1 (USD/INR)": f"{q1_usd:.2f} / {q1_inr:.2f}",
                "Q2 (USD/INR)": f"{q2_usd:.2f} / {q2_inr:.2f}",
                "Q3 (USD/INR)": f"{q3_usd:.2f} / {q3_inr:.2f}",
                "Q4 (USD/INR)": f"{q4_usd:.2f} / {q4_inr:.2f}",
                "Total (USD/INR)": f"{total_usd:.2f} / {total_inr:.2f}",
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "Ticker",
            "Q1 (USD/INR)",
            "Q2 (USD/INR)",
            "Q3 (USD/INR)",
            "Q4 (USD/INR)",
            "Total (USD/INR)",
        ],
    )


