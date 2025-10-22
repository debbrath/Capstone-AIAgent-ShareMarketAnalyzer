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
import datetime

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
    ["🔍 View Trading Codes", "⬇️ Download & Save Data", "📈 Get History by Code", "📈 Get Data Analysis by Code","🗑️ Clear Chat History"]
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
                    SELECT TOP (:limit) date, ltp, high, low, openp, closep,trade, value_mn, volume
                    FROM market_history
                    WHERE trading_code = :code
                    ORDER BY date DESC
                """)
                rows = session.execute(query, {"limit": limit, "code": selected_code}).fetchall()
                session.close()

                if rows:
                    df = pd.DataFrame(rows, columns=["Date", "LTP", "High", "Low", "Open", "Close","Trade", "Value (Mn)", "Volume"])
                    st.subheader(f"📊 Last {limit} Records for {selected_code}")
                    st.dataframe(df)
                    st.line_chart(df.set_index("Date")["LTP"])
                    st.session_state.chat_history.append(f"Fetched {len(df)} records for {selected_code}.")
                else:
                    st.warning(f"No records found for {selected_code}.")
            except Exception as e:
                st.error(f"❌ Error fetching history: {e}")

# -------------------------------
# Menu Option 4: Get History by Code
# -------------------------------
elif menu == "📈 Get Data Analysis by Code":
    st.title("📈 Get Data Analysis by Trading Code")
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
                    SELECT date, ltp, high, low, openp, closep, trade, value_mn, volume
                    FROM market_history
                    WHERE trading_code = :code
                    ORDER BY date ASC
                """)
                rows = session.execute(query, {"code": selected_code}).fetchall()
                session.close()

                if rows:
                    df = pd.DataFrame(rows, columns=[
                    "Date", "LTP", "High", "Low", "Open", "Close", "Trade", "Value (Mn)", "Volume"
                    ])
                    df["Date"] = pd.to_datetime(df["Date"])

                    # 🔹 Convert Decimal to float
                    for col in ["LTP", "High", "Low", "Open", "Close", "Trade", "Value (Mn)", "Volume"]:
                        df[col] = df[col].astype(float)

                    st.subheader(f"📊 Full Historical Data for {selected_code}")
                    st.dataframe(df.tail(limit))  # show last N rows
                    st.line_chart(df.set_index("Date")["LTP"])

                    # ---------------------------
                    # 📅 Latest Market Data
                    # ---------------------------
                    st.subheader("📅 Latest Available Market Data")

                    latest_date = df["Date"].max()
                    latest_row = df.loc[df["Date"] == latest_date].iloc[0]

                    st.markdown(f"### 🗓️ **Date:** {latest_date.date()}")
                    st.write("Here’s the most recent market data for this trading code:")

                    latest_data = {
                        "LTP": latest_row["LTP"],
                        "Open": latest_row["Open"],
                        "Close": latest_row["Close"],
                        "High": latest_row["High"],
                        "Low": latest_row["Low"],
                        "Trade": latest_row["Trade"],
                        "Value (Mn)": latest_row["Value (Mn)"],
                        "Volume": latest_row["Volume"]
                    }

                    st.dataframe(pd.DataFrame([latest_data]).T.rename(columns={0: "Value"}))

                    st.info(
                        f"**Latest Data ({latest_date.date()})** — "
                        f"LTP: {latest_row['LTP']:.2f}, Open: {latest_row['Open']:.2f}, "
                        f"Close: {latest_row['Close']:.2f}, High: {latest_row['High']:.2f}, "
                        f"Low: {latest_row['Low']:.2f}, Trade: {latest_row['Trade']:.0f}, "
                        f"Value(Mn): {latest_row['Value (Mn)']:.2f}, Volume: {latest_row['Volume']:.0f}"
                    )


                    # ---------------------------
                    # 📈 Enhanced Analysis Section
                    # ---------------------------
                    st.subheader("📈 Market Analysis Summary")

                    # Sort to find two lowest and two highest closes
                    buy_candidates = df.nsmallest(2, "Close")
                    sell_candidates = df.nlargest(2, "Close")

                    buy1_price, buy1_date = buy_candidates.iloc[0]["Close"], buy_candidates.iloc[0]["Date"]
                    buy2_price, buy2_date = buy_candidates.iloc[1]["Close"], buy_candidates.iloc[1]["Date"]

                    sell1_price, sell1_date = sell_candidates.iloc[0]["Close"], sell_candidates.iloc[0]["Date"]
                    sell2_price, sell2_date = sell_candidates.iloc[1]["Close"], sell_candidates.iloc[1]["Date"]

                    avg_price = df["Close"].mean()
                    volatility = df["Close"].std()

                    # 🟢 Display Buy Zones
                    st.markdown("### 🟢 Recommended Buy Zones")
                    col1, col2 = st.columns(2)
                    col1.metric("Buy Limit 1", f"{buy1_price:.2f}", f"on {buy1_date.date()}")
                    col2.metric("Buy Limit 2", f"{buy2_price:.2f}", f"on {buy2_date.date()}")

                    # 🔴 Display Sell Zones
                    st.markdown("### 🔴 Recommended Sell Targets")
                    col3, col4 = st.columns(2)
                    col3.metric("Sell Limit 1", f"{sell1_price:.2f}", f"on {sell1_date.date()}")
                    col4.metric("Sell Limit 2", f"{sell2_price:.2f}", f"on {sell2_date.date()}")

                    # 🧮 Compute potential profit ranges
                    avg_buy = (buy1_price + buy2_price) / 2
                    avg_sell = (sell1_price + sell2_price) / 2
                    profit = avg_sell - avg_buy
                    profit_pct = (profit / avg_buy) * 100

                    st.markdown("### 💹 Performance Summary")
                    st.metric("Expected Average Profit %", f"{profit_pct:.2f}%")
                    st.info(f"Average Close: {avg_price:.2f} | Volatility: {volatility:.2f}")

                    # Save to chat history
                    summary_msg = (
                        f"{selected_code} → Buy at {buy1_price:.2f}/{buy2_price:.2f}, "
                        f"Sell at {sell1_price:.2f}/{sell2_price:.2f}, "
                        f"Profit ≈ {profit_pct:.2f}%"
                    )
                    st.session_state.chat_history.append(summary_msg)


                    # 🔹 Filter last 1 year (365 days)
                    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=365)
                    df_recent = df[df["Date"] >= cutoff_date]

                    st.subheader(f"📊 Last 1 Year Data for {selected_code}")
                    st.dataframe(df_recent.tail(limit))
                    st.line_chart(df_recent.set_index("Date")["LTP"])

                    # ---------------------------
                    # 📈 Analysis on Last 1 Year
                    # ---------------------------
                    st.subheader("📈 1-Year Market Analysis Summary")

                    if len(df_recent) >= 4:
                        # 🔹 Two lowest and two highest close prices in last year
                        buy_candidates = df_recent.nsmallest(2, "Close")
                        sell_candidates = df_recent.nlargest(2, "Close")

                        # 🟢 Buy limits
                        buy1 = buy_candidates.iloc[0]
                        buy2 = buy_candidates.iloc[1]
                        # 🔴 Sell limits
                        sell1 = sell_candidates.iloc[0]
                        sell2 = sell_candidates.iloc[1]

                        avg_price = df_recent["Close"].mean()
                        volatility = df_recent["Close"].std()

                        # 🟢 Buy Zones
                        st.markdown("### 🟢 Recommended Buy Zones (1-Year Range)")
                        col1, col2 = st.columns(2)
                        col1.metric(
                            "Buy Limit 1",
                            f"{buy1['Close']:.2f}",
                            f"{buy1['Date'].strftime('%b %d, %Y')}"
                        )
                        col2.metric(
                            "Buy Limit 2",
                            f"{buy2['Close']:.2f}",
                            f"{buy2['Date'].strftime('%b %d, %Y')}"
                        )

                        # 🔴 Sell Zones
                        st.markdown("### 🔴 Recommended Sell Targets (1-Year Range)")
                        col3, col4 = st.columns(2)
                        col3.metric(
                            "Sell Limit 1",
                            f"{sell1['Close']:.2f}",
                            f"{sell1['Date'].strftime('%b %d, %Y')}"
                        )
                        col4.metric(
                            "Sell Limit 2",
                            f"{sell2['Close']:.2f}",
                            f"{sell2['Date'].strftime('%b %d, %Y')}"
                        )

                        # 💹 Profit Calculation
                        avg_buy = (buy1["Close"] + buy2["Close"]) / 2
                        avg_sell = (sell1["Close"] + sell2["Close"]) / 2
                        profit = avg_sell - avg_buy
                        profit_pct = (profit / avg_buy) * 100

                        st.markdown("### 💹 Performance Summary (1-Year Range)")
                        st.metric("Expected Average Profit %", f"{profit_pct:.2f}%")
                        st.info(f"Average Close: {avg_price:.2f} | Volatility: {volatility:.2f}")

                        # 🕒 Latest Data Point
                        latest_row = df_recent.iloc[-1]
                        st.markdown("### 🕒 Latest Market Data")
                        st.metric(
                            "Latest LTP",
                            f"{latest_row['LTP']:.2f}",
                            f"{latest_row['Date'].strftime('%b %d, %Y')}"
                        )
                        
                else:
                    st.warning(f"No records found for {selected_code}.")
            except Exception as e:
                st.error(f"❌ Error fetching history: {e}")


# -------------------------------
# Menu Option 5: Clear Chat History
# -------------------------------
elif menu == "🗑️ Clear Chat History":
    st.session_state.chat_history.clear()
    st.sidebar.success("Chat history cleared!")
    st.write("🧹 Chat history has been cleared!")


# -------------------------------
# Cleanup
# -------------------------------
db_manager.close()


#(.venv) PS F:\Python\Capstone_AIAgent_Prediction> set PYTHONPATH=%CD%
#>> streamlit run app/sharemarket_chatbot.py