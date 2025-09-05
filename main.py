import argparse
from datetime import datetime

from logger_config import get_logger
from processor import update_schedule_fa
from summary import build_dividend_summary_table


logger = get_logger(__file__)


def main():
    parser = argparse.ArgumentParser(
        description="Update Schedule FA using stock and forex data (Excel input, CSV output)"
    )
    parser.add_argument(
        "--input-excel",
        "-i",
        default="Schedule FA.xlsx",
        help="Path to input Excel file (default: Schedule FA.xlsx)",
    )
    parser.add_argument(
        "--output-csv",
        "-o",
        default="Schedule-FA.csv",
        help="Path to output CSV (default: Schedule-FA.csv)",
    )
    parser.add_argument(
        "--year",
        "-y",
        type=int,
        default=datetime.now().year,
        help="Reporting financial year starting calendar year (default: current year)",
    )

    args = parser.parse_args()

    logger.info("Run started for year=%s", args.year)
    updated_df, quarter_dividends = update_schedule_fa(args.input_excel, year=args.year)

    # Write updated CSV
    updated_df.to_csv(args.output_csv, index=False)
    logger.info("Updated Schedule FA CSV saved as: %s", args.output_csv)

    # Build and write summary Excel
    table_df = build_dividend_summary_table(quarter_dividends)
    summary_path = f"Dividends-Summary-FY-{args.year}-{args.year + 1}.xlsx"
    table_df.to_excel(summary_path, index=False, sheet_name="Dividends Summary")
    logger.info("Dividends summary written to %s", summary_path)


if __name__ == "__main__":
    main()
