import os
from stocksurferbd import PriceData
import pandas as pd
from utils.config import build_connection_string
from utils.database_manager import DatabaseManager
from sqlalchemy import text

# -------------------------------
# Step 1: Take user input
# -------------------------------
symbol = input("Enter the stock symbol (e.g., ACI): ").strip().upper()

# Default market = DSE
market = "DSE"

# -------------------------------
# Step 2: Ensure 'db' folder exists
# -------------------------------
db_folder = "db"
os.makedirs(db_folder, exist_ok=True)

file_name = f"{symbol}_history.xlsx"
file_path = os.path.join(db_folder, file_name)


# -------------------------------
# Step 3: Initialize and download
# -------------------------------
print(f"\n🔄 Downloading historical data for {symbol} from {market}...")
loader = PriceData()

try:
    loader.save_history_data(symbol=symbol, file_name=file_path, market=market)
    print(f"✅ Data saved successfully to db/'{file_path}'")
except Exception as e:
    print(f"❌ Error downloading data: {e}")
    exit()

# -------------------------------
# Step 4: Load and clean data
# -------------------------------
try:
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower()
    
    print("\n📊 Preview of downloaded data:")
    print(df.head())

    print("\n✅ Columns in your data:", list(df.columns))

    # 🔹 Print data types of each column
    print("\n🧾 Data types of each column:")
    print(df.dtypes)

except Exception as e:
    print(f"❌ Error reading Excel file: {e}")



# -------------------------------
# Step 5: Save to MSSQL 'market_history' table
# -------------------------------
try:
    connection_string = build_connection_string()
    db_manager = DatabaseManager(connection_string)
    session = db_manager.get_session()

    # 🔹 Optional: create table if not exists (basic example)
    # create_table_sql = text("""
    # IF OBJECT_ID('dbo.market_history', 'U') IS NULL
    # CREATE TABLE dbo.market_history (
    #     symbol NVARCHAR(50),
    #     trade_date DATE,
    #     open_price FLOAT,
    #     high_price FLOAT,
    #     low_price FLOAT,
    #     close_price FLOAT,
    #     volume BIGINT
    # )
    # """)
    # session.execute(create_table_sql)
    # session.commit()

    # 🔹 Insert data row by row
    for _, row in df.iterrows():
        insert_sql = text("""
        INSERT INTO dbo.market_history (unnamed,date,trading_code, ltp, high, low, openp, closep, ycp, trade, value_mn, volume)
        VALUES (:unnamed,:date, :trading_code, :ltp, :high, :low, :openp, :closep, :ycp, :trade, :value_mn, :volume)
        """)
        session.execute(insert_sql, {
            "unnamed": symbol,
            "date": row.get("date"),
            "trading_code": row.get("trading_code"),
            "ltp": row.get("ltp"),
            "high": row.get("high"),
            "low": row.get("low"),
            "openp": row.get("openp"),
            "closep": row.get("closep"),
            "ycp": row.get("ycp"),
            "trade": row.get("trade"),
            "value_mn": row.get("value_mn"),
            "volume": row.get("volume")
        })
    session.commit()
    print(f"\n✅ Data successfully saved to 'market_history' table in SQL Server")

except Exception as e:
    print(f"❌ Error saving data to DB: {e}")

finally:
    session.close()
    db_manager.close()
