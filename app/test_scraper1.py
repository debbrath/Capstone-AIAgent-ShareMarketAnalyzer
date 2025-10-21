import pandas as pd
from stocksurferbd import PriceData

# -----------------------------
# 1️⃣ Download historical data
# -----------------------------
loader = PriceData()
loader.save_history_data(symbol='ACI', file_name='ACI_history.xlsx', market='DSE')

# -----------------------------
# 2️⃣ Read the Excel file
# -----------------------------
df = pd.read_excel('ACI_history.xlsx')

# -----------------------------
# 3️⃣ Normalize column names
# -----------------------------
df.columns = df.columns.str.strip().str.lower()  # all lowercase, no spaces
print(df.columns)  # for verification

# -----------------------------
# 4️⃣ Convert 'date' column to proper datetime
# -----------------------------
df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

# -----------------------------
# 5️⃣ Filter for a specific date
# -----------------------------
input_date = "2025-10-14"
df_filtered = df[df['date'] == input_date]

# -----------------------------
# 6️⃣ Extract X/Y values
# -----------------------------
x_vals = df_filtered['date'].tolist()
y_vals = df_filtered['close'].tolist()

print("X-axis (Dates):", x_vals)
print("Y-axis (Closing Prices):", y_vals)