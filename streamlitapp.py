import streamlit as st
import json
import pandas as pd

# -------------------------
# Helper: safe float conversion
# -------------------------
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
    try:
        return pd.to_datetime(s, format="%y-%m-%d", errors="coerce").date()
    except Exception:
        return pd.to_datetime(s, errors="coerce").date()

# -------------------------
# Load JSON (no caching for now)
# -------------------------
def load_data():
    with open("signals.json", "r") as f:
        return json.load(f)

data = load_data()

# -------------------------
# Build trades list
# -------------------------
trades = []
for symbol, details in data.items():
    closing_price = to_float(details.get("closing_price"))
    exit_all = to_float(details.get("exit_all"))
    exit_all_date = details.get("exit_all_date")

    for i in range(1, 5):
        entry = to_float(details.get(f"entry {i}"))
        entry_date = details.get(f"entry {i} date")
        exit_val = to_float(details.get(f"exit {i}"))
        exit_date = details.get(f"exit {i} date")
        max_price = to_float(details.get(f"entry{i}_max_price"))

        # force dates to None if entry/exit missing
        if entry is None:
            entry_date = None
        if exit_val is None:
            exit_date = None

        # profits
        realized = None
        unrealized = None
        max_profit = None
        profit = None
        status = "open"

        if entry is not None and exit_val is not None:
            profit = exit_val - entry
            realized = profit
            status = "closed"

        elif entry is not None and exit_all is not None:
            profit = exit_all - entry
            realized = profit
            exit_date = exit_all_date
            status = "forceExit"

        elif entry is not None and exit_val is None and closing_price is not None:
            profit = closing_price - entry
            unrealized = profit
            status = "open"

        elif entry is None and exit_val is not None:
            status = "exit-only"

        # calculate max profit if available
        if entry is not None and max_price is not None:
            max_profit = max_price - entry

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
            "max_profit": max_profit,
            "status": status,
        })

# -------------------------
# DataFrame
# -------------------------
trades_df = pd.DataFrame(trades)

# --- Clean dates with YY-MM-DD parser ---
if "entry_date" in trades_df.columns:
    trades_df["entry_date"] = trades_df["entry_date"].apply(clean_date)
if "exit_date" in trades_df.columns:
    trades_df["exit_date"] = trades_df["exit_date"].apply(clean_date)

# Profit summary
profit_summary = trades_df.groupby("symbol").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum",
    "max_profit": "sum"
}).reset_index().fillna(0)

total_realized = profit_summary["realized_profit"].sum()
total_unrealized = profit_summary["unrealized_profit"].sum()
total_max = profit_summary["max_profit"].sum()
total_invested = trades_df["entry"].sum(skipna=True)

# Missed opportunity
missed_opportunity = total_max - total_realized

# -------------------------
# Streamlit UI
# -------------------------
st.title("📊 Stock Signal Dashboard — Realized, Unrealized, Max Profits & Missed Opportunity")

# Debug section
st.subheader("🔎 Debug — First Few Trades")
st.write(trades_df.head(10))

# Profit summary
st.subheader("✅ Profit Summary (Realized, Unrealized, Max, Missed)")
st.dataframe(profit_summary, use_container_width=True)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Realized", f"₹{total_realized:.2f}")
col2.metric("📈 Total Unrealized", f"₹{total_unrealized:.2f}")
col3.metric("🚀 Total Max Possible", f"₹{total_max:.2f}")
col4.metric("💸 Total Invested", f"₹{total_invested:.2f}")
col5.metric("⚠️ Missed Opportunity", f"₹{missed_opportunity:.2f}")

# Chart
st.subheader("📊 Realized vs Unrealized vs Max per Symbol")
if not profit_summary.empty:
    chart_data = profit_summary.set_index("symbol")[["realized_profit", "unrealized_profit", "max_profit"]]
    st.bar_chart(chart_data)
else:
    st.info("No profit data available yet.")

# Full trades table
st.subheader("📋 All Trades")
st.dataframe(trades_df, use_container_width=True)
