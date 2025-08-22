import streamlit as st
import json
import pandas as pd

# Load JSON data
with open("signals.json", "r") as f:
    data = json.load(f)

# Prepare profit summary
profit_summary = []
for symbol, details in data.items():
    profit = 0
    for key in details:
        if key.startswith("entry") and details[key] is not None:
            entry_index = key.split()[1]
            exit_key = f"exit {entry_index}"
            if exit_key in details and details[exit_key] is not None:
                entry = details[key]
                exit = details[exit_key]
                if isinstance(entry, (int, float)) and isinstance(exit, (int, float)):
                    profit += exit - entry
    if profit != 0:
        profit_summary.append({"symbol": symbol, "profit": profit})

# Convert to DataFrame
profit_df = pd.DataFrame(profit_summary)

# Streamlit UI
st.title("📈 Stock Signal Profit Dashboard")

st.subheader("Profit Summary Table")
st.dataframe(profit_df)

st.subheader("Profit per Symbol")
if not profit_df.empty:
    st.bar_chart(profit_df.set_index("symbol")["profit"])

# Total profit
total_profit = profit_df["profit"].sum()
st.metric("Total Cumulative Profit", f"${total_profit:.2f}")
