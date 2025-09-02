import streamlit as st
import json
import pandas as pd

# --- Cache data loading so it doesn't reload on every rerun ---
@st.cache_data
def load_data():
    with open("signals.json", "r") as f:
        return json.load(f)

# Load once
data = load_data()

# --- Build detailed trades table ---
trades = []
for symbol, details in data.items():
    all_notes = []  # collect entries & exits for notes
    trade_closed = False
    closing_price = details.get("closing_price")

    for i in range(1, 5):  # assuming up to 4 levels
        entry = details.get(f"entry {i}")
        entry_date = details.get(f"entry {i} date") if f"entry {i} date" in details else None
        exit_val = details.get(f"exit {i}")
        exit_date = details.get(f"exit {i} date") if f"exit {i} date" in details else None

        # Force dates to None if entry/exit missing
        if entry is None:
            entry_date = None
        if exit_val is None:
            exit_date = None

        if entry is not None:
            all_notes.append(f"E{i}: {entry} ({entry_date})" if entry_date else f"E{i}: {entry}")
        if exit_val is not None:
            all_notes.append(f"X{i}: {exit_val} ({exit_date})" if exit_date else f"X{i}: {exit_val}")

        profit = None
        realized = None
        unrealized = None
        status = "open"

        if entry is not None and exit_val is not None:
            # closed trade
            profit = exit_val - entry
            realized = profit
            status = "closed"
            trade_closed = True
        elif entry is not None and exit_val is None and closing_price is not None:
            # open trade → unrealized profit
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
            "status": status,
            "notes": None  # will fill later
        })

    # Add combined notes for closed trades
    if trade_closed and all_notes:
        for t in trades:
            if t["symbol"] == symbol:
                t["notes"] = " | ".join(all_notes)

# --- Convert to DataFrame ---
trades_df = pd.DataFrame(trades)

# --- Handle dates if present ---
if "entry_date" in trades_df.columns and trades_df["entry_date"].notnull().any():
    trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"], errors="coerce").dt.date
    trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"], errors="coerce").dt.date

# --- Profit summaries ---
profit_summary = trades_df.groupby("symbol").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum"
}).reset_index()

# Fill NaNs with 0 for cleaner display
profit_summary = profit_summary.fillna(0)

# Total profits
total_realized = profit_summary["realized_profit"].sum()
total_unrealized = profit_summary["unrealized_profit"].sum()

# --- Streamlit UI ---
st.title("📊 Stock Signal Dashboard")

# Show overall summary first
st.subheader("✅ Profit Summary (Realized vs Unrealized)")
st.dataframe(profit_summary, use_container_width=True)

st.metric("💰 Total Realized Profit", f"${total_realized:.2f}")
st.metric("📊 Total Unrealized Profit", f"${total_unrealized:.2f}")
st.metric("💵 Combined Profit", f"${(total_realized + total_unrealized):.2f}")

# --- Profit chart ---
st.subheader("📈 Realized vs Unrealized Profit per Symbol")
if not profit_summary.empty:
    chart_data = profit_summary.set_index("symbol")[["realized_profit", "unrealized_profit"]]
    st.bar_chart(chart_data)
else:
    st.info("No profit data available yet.")

# --- Show full trades table ---
st.subheader("📋 All Trades")
st.dataframe(trades_df, use_container_width=True)
