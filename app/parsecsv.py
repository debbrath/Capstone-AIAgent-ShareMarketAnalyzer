import pandas as pd

# Load the CSV file
df = pd.read_csv('historical_data.csv')

# Convert 'Date' column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# Filter data for the desired date range
start_date = '2025-10-23'
end_date = '2025-10-25'
df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# Extract 'Date' and 'Close' columns
df_filtered = df_filtered[['Date', 'Close']]

# Convert to list format
dates = df_filtered['Date'].dt.strftime('%Y-%m-%d').tolist()
prices = df_filtered['Close'].tolist()

# Prepare the final output
output = {
    "axis": [{"x": dates, "y": prices, "name": "Price"}],
    "source_url": "https://www.amarstock.com/csv-data-download"
}

print(output)