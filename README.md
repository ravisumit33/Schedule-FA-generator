# Schedule FA CSV Generator

## Overview

Generate a Schedule FA CSV from an Excel workbook of your foreign equity holdings, and produce a quarter-wise dividends summary (USD/INR) for verification.

## Input format

- The input must be an Excel workbook (.xlsx) with one sheet per ticker.
- Each sheet’s name must be the ticker symbol (e.g., ADBE, MSFT, META).
- Each sheet must contain at least these columns:
  - Date of acquiring the interest
  - Quantity

## What it does

- For each ticker/sheet, fetches historical prices and dividends, adjusts for stock splits, and converts values to INR using historical FX rates.
- Computes for the selected calendar year (Jan 1–Dec 31):
  - Initial value of the investment
  - Peak value of investment during the period
  - Closing balance
  - Total gross amount paid/credited with respect to the holding during the period (dividends)
- Produces two outputs:
  1. Schedule FA CSV file with all computed values
  2. Excel summary of dividends aggregated per quarter (USD / INR) for each ticker

### Important notes

- Dividend amounts in the summary are inclusive of any tax withheld at source. In other words,
  `Amount of dividend = Tax Withheld + Net dividend`.
- The CSV output will exclude the Quantity column (it is used for calculations but not included in the final CSV).

## Usage

From the project root, run:

```sh
uv run main.py -i "Schedule FA.xlsx" -o Schedule-FA.csv -y 2024
```

where:

- `-i/--input-excel`: path to the Excel input (default: Schedule FA.xlsx)
- `-o/--output-csv`: path to write the updated CSV (default: Schedule-FA-updated.csv)
- `-y/--year`: calendar year to compute (default: current year)

### Outputs

- The updated Schedule FA CSV is suitable for direct upload to the ITR-2 Schedule FA portal.
- The dividends summary Excel (`Dividends-Summary-FY-<year>-<year+1>.xlsx`) can be used to cross-verify dividends received in your stock broker apps.
