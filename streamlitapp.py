import streamlit as st
import json
import pandas as pd

# Load JSON file
with open("signals.json", "r") as f:
    data = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(data)

# Calculate profit for closed trades
df["profit"] = df.apply(
    lambda row: (row["exit"] - row["entry"]) if row["status"] == "closed" else None,
    axis=1,
)

st.title("📈 Stock Signals Dashboard")

st.subheader("Trade Signals")
st.dataframe(df)

# Show only closed trades with profit
closed_trades = df[df["status"] == "closed"]

st.subheader("Closed Trades & Profit")
st.bar_chart(closed_trades.set_index("symbol")["profit"])

# Show total profit
total_profit = closed_trades["profit"].sum()
st.metric("Total Profit", f"${total_profit:.2f}")
