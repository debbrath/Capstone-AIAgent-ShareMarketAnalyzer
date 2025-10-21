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
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Stock History Bot", layout="wide")


# -------------------------------
# Sidebar: Chatbot History + Menu
# -------------------------------
st.sidebar.title("💬 Chat History")

# Sidebar menu
menu = st.sidebar.radio(
    "Select Action",
    ["🔍 View Trading Codes", "⬇️ Download & Save Data", "📈 Get History by Code", "🗑️ Clear Chat History"]
)

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
# Display previous chat interactions
for i, msg in enumerate(st.session_state.chat_history):
    with st.sidebar.expander(f"Session {i + 1}", expanded=False):
        st.write(msg)

# Database setup
connection_string = build_connection_string()
db_manager = DatabaseManager(connection_string)
share_service = ShareMarketService(db_manager)

# -------------------------------
# Menu Option 1: View All Trading Codes
# -------------------------------
if menu == "🔍 View Trading Codes":
    st.title("🔍 View Trading Codes")
    try:
        codes = share_service.get_trading_list()  # Call service method
        if codes:
            st.success(f"✅ Found {len(codes)} trading codes.")
            st.dataframe(pd.DataFrame(codes, columns=["Trading Codes"]))
            st.session_state.chat_history.append(f"Fetched {len(codes)} trading codes from database.")
        else:
            st.warning("⚠️ No trading codes found in the database.")
            st.session_state.chat_history.append("⚠️ No trading codes found in the database.")
    except Exception as e:
        st.error(f"❌ Error fetching trading list: {e}")
        st.session_state.chat_history.append(f"❌ Error fetching trading list: {e}")


# -------------------------------
# Menu Option 2: Download & Save New Data
# -------------------------------
elif menu == "⬇️ Download & Save Data":
    st.title("⬇️ Download & Save Stock Data")
    # Input: Stock symbol
    symbol = st.text_input("Enter Stock Symbol (e.g., ACI):").strip().upper()
    market = "DSE"  # default market

    # Ensure 'db' folder exists
    db_folder = "db"
    os.makedirs(db_folder, exist_ok=True)
    file_name = f"{symbol}_history.xlsx"
    file_path = os.path.join(db_folder, file_name)

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
# Menu Option 3: Get History by Code
# -------------------------------
elif menu == "📈 Get History by Code":
    st.title("📈 Get History by Trading Code")

    try:
        session = db_manager.get_session()
        result = session.execute(text("SELECT DISTINCT trading_code FROM market_history ORDER BY trading_code")).fetchall()
        trading_codes = [r[0] for r in result]
        session.close()
    except Exception as e:
        st.error(f"❌ Could not load trading codes: {e}")
        trading_codes = []

    if trading_codes:
        selected_code = st.selectbox("Select a Trading Code:", trading_codes)
        limit = st.number_input("Number of recent records to view:", min_value=1, max_value=500, value=10)

        if st.button("Fetch History"):
            try:
                session = db_manager.get_session()
                query = text("""
                    SELECT TOP (:limit) date, ltp, high, low, openp, closep, value_mn, volume
                    FROM market_history
                    WHERE trading_code = :code
                    ORDER BY date DESC
                """)
                rows = session.execute(query, {"limit": limit, "code": selected_code}).fetchall()
                session.close()

                if rows:
                    df = pd.DataFrame(rows, columns=["Date", "LTP", "High", "Low", "Open", "Close", "Value (Mn)", "Volume"])
                    st.subheader(f"📊 Last {limit} Records for {selected_code}")
                    st.dataframe(df)
                    st.line_chart(df.set_index("Date")["LTP"])
                    st.session_state.chat_history.append(f"Fetched {len(df)} records for {selected_code}.")
                else:
                    st.warning(f"No records found for {selected_code}.")
            except Exception as e:
                st.error(f"❌ Error fetching history: {e}")


# -------------------------------
# Menu Option 4: Clear Chat History
# -------------------------------
elif menu == "🗑️ Clear Chat History":
    st.session_state.chat_history.clear()
    st.sidebar.success("Chat history cleared!")
    st.write("🧹 Chat history has been cleared!")


# -------------------------------
# Cleanup
# -------------------------------
db_manager.close()