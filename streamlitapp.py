import streamlit as st
import pandas as pd
import json
from datetime import datetime
import sqlite3
import os

st.set_page_config(page_title="Trade Signals", layout="wide")

# ---------- Simple Visit Logger ----------
def log_visit():
    conn = sqlite3.connect("visitors.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            ip TEXT,
            user_agent TEXT
        )
    """)
    ip = st.query_params.get("ip", ["unknown"])[0]
    ua = st.session_state.get("user_agent", "unknown")
    c.execute(
        "INSERT INTO visits (ts, ip, user_agent) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), ip, ua)
    )
    conn.commit()
    conn.close()

log_visit()

# ---------- Top Info Banner ----------
st.info(
    "📌 **Aavi Stocks**\n\n"
    "This dashboard highlights current **entry & exit positions** based on daily candles. "
    "Past profits are shown only to help gauge the algorithm's effectiveness. "
    "Educational use only – validate before trading."
)

# ---------- Load signals.json directly ----------
json_path = os.path.join(os.path.dirname(__file__), "signals.json")
if not os.path.exists(json_path):
    st.error("❌ signals.json file not found in the same folder as this script.")
else:
    with open(json_path, "r") as f:
        signals = json.load(f)

    # Build All Trades Table
    trades_data = []
    for symbol, data in signals.items():
        for i in range(1, 5):
            e_price, e_date = data.get(f"entry {i}"), data.get(f"entry {i} date")
            x_price, x_date = data.get(f"exit {i}"), data.get(f"exit {i} date")

            # validations
            if e_price and not e_date:
                e_price, e_date = None, None
            if x_price and not x_date:
                x_price, x_date = None, None
            if e_date and x_date:
                try:
                    e_dt = datetime.strptime(e_date, "%y-%m-%d")
                    x_dt = datetime.strptime(x_date, "%y-%m-%d")
                    if x_dt < e_dt:
                        x_price, x_date = None, None
                except:
                    x_price, x_date = None, None

            if e_price or x_price:
                trades_data.append({
                    "Symbol": symbol,
                    "Entry Price": e_price,
                    "Entry Date": e_date,
                    "Exit Price": x_price,
                    "Exit Date": x_date,
                    "Closing Price": data.get("closing_price")
                })

    trades_df = pd.DataFrame(trades_data)

    # Profit History Table
    profit_rows = []
    for symbol, data in signals.items():
        for i in range(1, 5):
            e_price, e_date = data.get(f"entry {i}"), data.get(f"entry {i} date")
            x_price, x_date = data.get(f"exit {i}"), data.get(f"exit {i} date")
            if e_price and e_date and x_price and x_date:
                try:
                    if datetime.strptime(x_date, "%y-%m-%d") >= datetime.strptime(e_date, "%y-%m-%d"):
                        profit_rows.append({
                            "Symbol": symbol,
                            "Profit": round(x_price - e_price, 2)
                        })
                except:
                    pass

    profit_df = pd.DataFrame(profit_rows) if profit_rows else pd.DataFrame()

    # ---------- Tabs ----------
    tab_signals, tab_performance, tab_visitors = st.tabs(
        ["📊 Current Signals", "📈 Performance History", "📊 Visitor Analytics"]
    )

    with tab_signals:
        st.subheader("Current Entry & Exit Positions")
        st.caption("Sort or filter to find stocks of interest. These are today's available signals.")
        st.dataframe(trades_df, use_container_width=True)

    with tab_performance:
        st.subheader("Past Performance")
        if not profit_df.empty:
            st.dataframe(profit_df, use_container_width=True)
        else:
            st.info("No completed trades to show profit yet.")

    with tab_visitors:
        st.subheader("Visitor Analytics")
        conn = sqlite3.connect("visitors.db")
        df = pd.read_sql("SELECT date(ts) AS day, COUNT(*) AS visits FROM visits GROUP BY day", conn)
        st.bar_chart(df.set_index("day"))
        conn.close()

    # ---------- Quick Start Guide ----------
    with st.expander("👋 Quick Start Guide"):
        st.markdown(
            "1. **Current Signals** tab shows live entry/exit positions.\n"
            "2. **Performance History** tab shows how past trades performed.\n"
            "3. **Visitor Analytics** tab shows daily visit counts."
        )
