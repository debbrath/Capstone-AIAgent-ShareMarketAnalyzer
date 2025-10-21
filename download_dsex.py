# download_dsex.py
import yfinance as yf
import pandas as pd

# Define the ticker symbol for the DSEX index
ticker_symbol = "^DSEX"

# Download historical data
data = yf.download(ticker_symbol, start="2013-01-01", end="2025-10-20")

# Display the first few rows of the data
print(data.head())

# Save the data to a CSV file
data.to_csv("DSEX_historical_data.csv")