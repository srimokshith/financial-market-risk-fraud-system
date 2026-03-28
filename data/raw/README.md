# Raw Data Directory

This folder contains the raw market data files required for the analysis. CSV files are intentionally excluded from version control.

## Required Files

Place the following CSV files in this directory:

- `NIFTY_50.csv` - NIFTY 50 index historical data
- `USD_INR.csv` - USD/INR exchange rate data
- `Aligned_Returns.csv` - Pre-calculated aligned returns (optional)

## Data Sources

You can obtain the data from:

1. **Yahoo Finance** - Download historical data for `^NSEI` (NIFTY 50) and `INR=X` (USD/INR)
2. **NSE India** - Official NIFTY 50 data from [nseindia.com](https://www.nseindia.com/)
3. **RBI** - USD/INR rates from Reserve Bank of India
4. **yfinance** - The pipeline can automatically fetch data using the `yfinance` library if local files are missing

## CSV Format

Expected columns:
- `Date` - Date in YYYY-MM-DD format
- `Close` - Closing price/rate
- Additional columns (Open, High, Low, Volume) are optional

## Note

If CSV files are not present, the pipeline will attempt to fetch data automatically using `yfinance`.
