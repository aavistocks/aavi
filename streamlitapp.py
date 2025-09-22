'''import streamlit as st
import streamlit.components.v1 as components

# Replace with your actual GA Measurement ID
GA_MEASUREMENT_ID = "G-GSHZQ8WWBC"

GA_SCRIPT = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>
"""

# Inject into Streamlit
components.html(GA_SCRIPT, height=0, width=0)


import streamlit as st
import streamlit_analytics

# Track usage
with streamlit_analytics.track():
    st.title("📊 Aavi Stocks")
    st.write("Welcome to the stock analytics app!")

    # Example UI
    if st.button("Show Stock Insights"):
        st.write("Insights coming soon...")
'''
import streamlit as st
import json
import pandas as pd
import subprocess

# --- Helper Functions ---
def to_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip())
    except:
        return None

# -------------------------
# Helper: parse YY-MM-DD format safely
# -------------------------
def clean_date(val):
    if val is None:
        return None
    s = str(val).strip()
    if s in ["", "None", "null", "NaN", "nan"]:
        return None
    # Try strict YY-MM-DD (e.g. 25-09-02 → 2025-09-02)
    try:
        return pd.to_datetime(s, format="%y-%m-%d", errors="coerce").date()
    except Exception:
        # fallback: let pandas guess
        return pd.to_datetime(s, errors="coerce").date()

# -------------------------
# Load JSON (no caching for now)
# -------------------------
def load_data():
    with open("signals.json", "r") as f:
        return json.load(f)

data = load_data()

# --- Build Trades List ---
trades = []
for symbol, details in data.items():
    closing_price = to_float(details.get("closing_price"))
    for i in range(1, 5):
        entry = to_float(details.get(f"entry {i}"))
        entry_date = clean_date(details.get(f"entry {i} date"))
        exit_val = to_float(details.get(f"exit {i}"))
        exit_date = clean_date(details.get(f"exit {i} date"))

        if entry is None and exit_val is None and closing_price is not None:
            continue

        # Skip case: no valid entry-date or exit-date pair
        if not ((entry is not None and entry_date is not None) or (exit_val is not None and exit_date is not None)):
            continue
        if entry_date and exit_date and exit_date < entry_date:
            exit_val = None
            exit_date = None

        # profits
        realized = None
        unrealized = None
        profit = None
        status = "open"

        if entry is not None and exit_val is not None:
            profit = exit_val - entry
            realized = profit
            status = "closed"
        elif entry is not None and closing_price is not None:
            # unrealized ONLY from entry and closing price
            profit = closing_price - entry
            unrealized = profit
            status = "open"
        elif entry is None and exit_val is not None:
            status = "exit-only"

        trades.append({
            "symbol": symbol,
            "level": i,
            "entry": entry,
            "entry_date": entry_date,
            "exit": exit_val,
            "exit_date": exit_date,
            "closing_price": closing_price,
            "profit": profit,
            "realized_profit": realized,
            "unrealized_profit": unrealized,
            "status": status
        })

# --- DataFrames ---
trades_df = pd.DataFrame(trades)

profit_summary = trades_df.groupby("symbol").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum"
}).reset_index().fillna(0)

total_realized = profit_summary["realized_profit"].sum()
total_unrealized = profit_summary["unrealized_profit"].sum()

level_summary = trades_df.groupby("level").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum",
    "profit": ["sum", "mean", "count"]
}).reset_index()
level_summary.columns = ["level", "realized_profit", "unrealized_profit", "total_profit", "avg_profit_per_trade", "trade_count"]

# --- Streamlit UI ---
st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 Stock Signal Dashboard")

tab1, tab2, tab3 = st.tabs(["📂 Open Positions", "📈 Performance Analysis", "📝 Recent Updates"])

with tab1:
    st.subheader("📋 All Trades")
    st.dataframe(trades_df, use_container_width=True)

with tab2:
    st.subheader("✅ Profit Summary (Realized vs Unrealized)")
    st.dataframe(profit_summary, use_container_width=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Realized", f"${total_realized:.2f}")
    col2.metric("📈 Total Unrealized", f"${total_unrealized:.2f}")
    col3.metric("💵 Combined", f"${(total_realized + total_unrealized):.2f}")

    st.subheader("📊 Profit Analysis by Entry/Exit Level")
    st.dataframe(level_summary, use_container_width=True)

with tab3:
    st.subheader("📝 Git Change Log")
    try:
        log = subprocess.check_output(["git", "log", "--pretty=format:%h - %s (%cr)"]).decode("utf-8")
        st.text(log)
    except Exception:
        st.warning("Git log not available. Make sure this app is inside a Git repository.")
st.markdown(
    "> **How to Use the Dashboard:**\n"
    "> 1. Review the profit summaries and charts to see overall market signals.\n"
    "> 2. Click column headers in the tables to sort or filter stocks of interest.\n"
    "> 3. Use the level-wise analysis to check which entry/exit levels are performing best.\n"
    "> 4. Make your own trading decision—this app does **not** execute trades."
)

st.markdown("> **Note 1:** This application is for educational purposes only. Any trades based on the data here require users to validate before taking actual trades.")
st.markdown("> **Note 2:** The suggestions given are based on daily or weekly candles. Once an entry is shown, a user can exit once their target is achieved. The level exit can be considered as the last exit option.")

# ----------------------------------------------------------
# OPTIONAL: Reset Profit Feature (DISABLED BY DEFAULT)
# ----------------------------------------------------------
# Uncomment the block below whenever you want to enable
# a one-click profit reset. It will set realized/unrealized
# profit columns to zero and refresh the dashboard.
#
#if st.sidebar.button("🔄 Reset All Profits"):
#    # Set profit columns to zero
#    trades_df["realized_profit"] = 0.0
#    trades_df["unrealized_profit"] = 0.0
#    trades_df["profit"] = 0.0

    # Optionally, persist this reset to disk if you store
    # trades_df somewhere (e.g., overwrite signals.json or
    # write to a database). For now, it only resets in memory.
#    st.experimental_rerun()

#
# NOTE:
# - This reset only affects the live session unless you
#   add code to write the updated trades back to storage.
# - Keep the block commented until you truly need it.
# ----------------------------------------------------------