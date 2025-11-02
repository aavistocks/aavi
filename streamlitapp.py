import streamlit as st
import json
import pandas as pd
import subprocess

# --- Helper Functions ---
def to_float(v):
    try:
        return float(str(v).replace(",", "").strip())
    except:
        return None

#def clean_date(val):
#    try:
#        return pd.to_datetime(val, errors="coerce").date()
#    except:
#        return None
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
        
# --- Load Data ---
with open("signals.json", "r") as f:
    data = json.load(f)

#exit_all = data.get("exit_all", 0)

# --- Build Trades List ---
trades = []
total_invested = 0.0

for symbol, details in data.items():
    exit_all = details.get("exit_all",0)

    #if symbol == "exit_all":
    #    continue
    closing_price = to_float(details.get("closing_price"))
    for i in range(1, 5):
        entry = to_float(details.get(f"entry {i}"))
        entry_date = clean_date(details.get(f"entry {i} date"))
        exit_val = to_float(details.get(f"exit {i}"))
        exit_date = clean_date(details.get(f"exit {i} date"))
        max_price = to_float(details.get(f"entry{i}_max_price"))
        forceExitdate = clean_date(details.get(f"exit_all_date"))
        if entry is None and exit_val is None and closing_price is not None:
            continue
        if not ((entry and entry_date) or (exit_val and exit_date)):
            continue
        if entry_date and exit_date and exit_date < entry_date:
            exit_val = None
            exit_date = None

        realized = unrealized = profit = max_profit = None
        status = "open"

        if entry and exit_val:
            profit = exit_val - entry
            realized = profit
            status = "closed"
        elif entry and closing_price:
            profit = closing_price - entry
            unrealized = profit
            max_profit = max_price - entry if max_price else None
        elif exit_all == 1 and forceExitdate is not None and entry_date is not None and forceExitdate > entry_date :
                exit_val = closing_price
                realized = closing_price - entry
                unrealized = None
                status = "forceExit11"
        elif not entry and exit_val:
            status = "exit-only"

        #if entry and status == "open":
        #    total_invested += entry

        trades.append({
            "symbol": symbol,
            "level": i,
            "entry": entry,
            "entry_date": entry_date,
            "exit": exit_val,
            "exit_date": exit_date,
            "closing_price": closing_price,
            "realized_profit": realized,
            "unrealized_profit": unrealized,
            "status": status,
            "del1": to_float(details.get(f"delper1")),
            "delAvg3": to_float(details.get(f"delper3")),
            "delAvg5": to_float(details.get(f"delper5")),
            "delAvg15": to_float(details.get(f"delper15")),
            "delAvg20": to_float(details.get(f"delper20")),
        })
#"max_profit": max_profit, #"profit": profit,
# --- DataFrames ---
trades_df = pd.DataFrame(trades)
'''
profit_summary = trades_df.groupby("symbol").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum",
    "max_profit": "sum"
}).reset_index().fillna(0)
'''
total_realized = profit_summary["realized_profit"].sum()
total_unrealized = profit_summary["unrealized_profit"].sum()
total_max_profit = profit_summary["max_profit"].sum()

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
    # --- Footer Notes ---
    st.markdown("""
    > **How to Use the Dashboard:**  
    > 1. "open position" tab give list of all open trades.  
    > 2. "various types of profit like realized, unrealized and max profit can be checked. Max profit = Max closing from entry - open price. 
    > 3. Performance analysis tracks the past performance of the algo. The start date is from 26Sept25 closing candle.
    > 4. Recent updates gives details of latest changes. specifically note when the analysis was last run.
    Usage:
    > 1. The "Entry" and "exit" along with respective dates indicate when the algo would have brought or sold 1 share. Basis this the profits are calculated
    > 2 The entry/exit are level-wise.
    > 3. The analysis to check which entry/exit levels are performing best is provided in performance tab.  
    
    General:
    > 1. Click column headers in the tables to sort or filter column of interest.
    > 2. Make your own trading decision—this app does **not** execute trades.
    
    > **Note 1:** This application is for educational purposes only. Any trades based on the data here require users to validate before taking actual trades.  
    > **Note 2:** The suggestions given are based on daily closing candles. Once an entry is shown, a user can exit once their target is achieved. The level exit can be considered as the last exit option.
    """)
with tab2:
    st.subheader("✅ Profit Summary (Realized vs Unrealized)")
    st.dataframe(profit_summary, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Realized", f"₹{total_realized:.2f}")
    col2.metric("📈 Total Unrealized", f"₹{total_unrealized:.2f}")
    col3.metric("📊 Max Possible Profit", f"₹{total_max_profit:.2f}")
    col4.metric("💼 Total Invested", f"₹{total_invested:.2f}")

    st.subheader("📊 Profit Analysis by Entry/Exit Level")
    st.dataframe(level_summary, use_container_width=True)

with tab3:
    st.subheader("📝 Git Change Log")
    try:
        log = subprocess.check_output(["git", "log", "--pretty=format:%h - %s (%cr)"]).decode("utf-8")
        st.text(log)
    except Exception:
        st.warning("Git log not available. Make sure this app is inside a Git repository.")


