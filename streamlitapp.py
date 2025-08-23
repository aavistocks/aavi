import streamlit as st
import json
import pandas as pd

# --- Load JSON ---
with open("signals.json", "r") as f:
    data = json.load(f)

# --- Build detailed trades table ---
trades = []
for symbol, details in data.items():
    for i in range(1, 5):  # assuming up to 4 levels
        entry = details.get(f"entry {i}")
        entry_date = details.get(f"entry {i} date") if f"entry {i} date" in details else None
        exit_val = details.get(f"exit {i}")
        exit_date = details.get(f"exit {i} date") if f"exit {i} date" in details else None

        if entry is not None or exit_val is not None:
            profit = None
            status = "open"
            if entry is not None and exit_val is not None:
                profit = exit_val - entry
                status = "closed"
            elif entry is None and exit_val is not None:
                status = "exit-only"

            trades.append({
                "symbol": symbol,
                "level": i,
                "entry": entry,
                "entry_date": entry_date,
                "exit": exit_val,
                "exit_date": exit_date,
                "profit": profit,
                "status": status
            })

# --- Convert to DataFrame ---
trades_df = pd.DataFrame(trades)

# --- Handle dates only if present ---
if "entry_date" in trades_df.columns and trades_df["entry_date"].notnull().any():
    trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"], errors="coerce")
    trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"], errors="coerce")
    trades_df = trades_df.sort_values(by=["entry_date", "level"], ascending=[False, True])
else:
    # fallback: just sort by level for consistency
    trades_df = trades_df.sort_values(by=["level"])

# --- Profit summary per symbol ---
profit_summary = trades_df[trades_df["profit"].notnull()] \
    .groupby("symbol")["profit"].sum().reset_index()

# --- Streamlit UI ---
st.title("📊 Stock Signal Dashboard")

st.subheader("📋 All Trades (Entry/Exit)")
st.dataframe(trades_df)

st.subheader("✅ Closed Trades & Profit Summary")
st.dataframe(profit_summary)

st.subheader("📈 Profit per Symbol")
if not profit_summary.empty:
    st.bar_chart(profit_summary.set_index("symbol")["profit"])
else:
    st.info("No closed trades yet.")

# --- Total cumulative profit ---
total_profit = profit_summary["profit"].sum()
st.metric("💰 Total Cumulative Profit", f"${total_profit:.2f}")
