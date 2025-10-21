import os
import sys

# Add project root to Python path (so 'utils' can be imported)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import pandas as pd
import streamlit as st
from stocksurferbd import PriceData
from utils.config import build_connection_string
from utils.database_manager import DatabaseManager
from services.sharemarket_service import ShareMarketService
from sqlalchemy import text


# -------------------------------
# Streamlit Page Config
# -------------------------------
st.set_page_config(page_title="Stock History Bot", layout="wide")

# -------------------------------
# Sidebar: Chatbot History
# -------------------------------
st.sidebar.title("💬 Chat History")

# Initialize chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous chat interactions
for i, msg in enumerate(st.session_state.chat_history):
    with st.sidebar.expander(f"Session {i + 1}", expanded=False):
        st.write(msg)


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Stock History Bot", layout="wide")

st.title("📈 Stock History Chatbot")
st.write("Enter a stock symbol to download historical data and save it to SQL Server.")

# Database setup
connection_string = build_connection_string()
db_manager = DatabaseManager(connection_string)
share_service = ShareMarketService(db_manager)


# Input: Stock symbol
symbol = st.text_input("Enter Stock Symbol (e.g., ACI):").strip().upper()
market = "DSE"  # default market

# Ensure 'db' folder exists
db_folder = "db"
os.makedirs(db_folder, exist_ok=True)
file_name = f"{symbol}_history.xlsx"
file_path = os.path.join(db_folder, file_name)

# -------------------------------
# Button: Fetch Existing Trading Codes
# -------------------------------
if st.button("🔍 Show All Trading Codes"):
    try:
        session = db_manager.get_session()
        result = session.execute(text("SELECT DISTINCT trading_code FROM market_history ORDER BY trading_code")).fetchall()
        codes = [r[0] for r in result]
        st.success(f"✅ Found {len(codes)} trading codes.")
        st.dataframe(pd.DataFrame(codes, columns=["Trading Codes"]))
        st.session_state.chat_history.append(f"Fetched {len(codes)} trading codes from database.")
    except Exception as e:
        st.error(f"❌ Error fetching trading list: {e}")
    finally:
        session.close()


# -------------------------------
# Button: Download & Save New Data
# -------------------------------

if st.button("Download & Save Data"):
    if not symbol:
        st.warning("⚠️ Please enter a stock symbol!")
    else:
        # Step 1: Download
        st.info(f"🔄 Downloading historical data for {symbol} from {market}...")
        loader = PriceData()
        try:
            loader.save_history_data(symbol=symbol, file_name=file_path, market=market)
            st.success(f"✅ Data saved successfully to '{file_path}'")
        except Exception as e:
            st.error(f"❌ Error downloading data: {e}")
            st.stop()

        # Step 2: Load and preview
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip().str.lower()

            st.subheader("📊 Preview of downloaded data:")
            st.dataframe(df.head())

            st.subheader("🧾 Columns and Data Types:")
            st.write(df.dtypes)
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {e}")
            st.stop()

        # Step 3: Save to SQL Server
        try:
            connection_string = build_connection_string()
            db_manager = DatabaseManager(connection_string)
            session = db_manager.get_session()

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
            st.success("✅ Data successfully saved to 'market_history' table in SQL Server")
        except Exception as e:
            st.error(f"❌ Error saving data to DB: {e}")
        finally:
            session.close()
            db_manager.close()


# -------------------------------
# Sidebar: Clear History Button
# -------------------------------
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history.clear()
    st.sidebar.success("Chat history cleared!")

# -------------------------------
# Cleanup
# -------------------------------
db_manager.close()