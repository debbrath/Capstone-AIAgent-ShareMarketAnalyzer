from stocksurferbd import PriceData

# Initialize the loader
loader = PriceData()

# Download historical data for 'ACI' and save to an Excel file
loader.save_history_data(symbol='SQURPHARMA', file_name='SQURPHARMA_history.xlsx', market='DSE')


import pandas as pd

df = pd.read_excel('SQURPHARMA_history.xlsx')
print(df.head())


df.columns = df.columns.str.strip().str.lower()
print(df.columns)  # then use df['date'] instead of df['Date']


# 5️⃣ Take input date from user
# -----------------------------
input_date = input("Enter the date (YYYY-MM-DD): ").strip()

# -----------------------------
# 6️⃣ Filter for the input date
# -----------------------------
df_filtered = df[df['date'] == input_date]

# -----------------------------
# 7️⃣ Extract X/Y values
# -----------------------------
x_vals = df_filtered['date'].tolist()
y_vals = df_filtered['close'].tolist()

# -----------------------------
# 8️⃣ Print the results
# -----------------------------
if x_vals and y_vals:
    print("X-axis (Date):", x_vals)
    print("Y-axis (Closing Price):", y_vals)
else:
    print(f"No data found for {input_date}")