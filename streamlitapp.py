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
'''

import streamlit as st
import streamlit_analytics

# Track usage
with streamlit_analytics.track():
    st.title("📊 Aavi Stocks")
    st.write("Welcome to the stock analytics app!")

    # Example UI
    if st.button("Show Stock Insights"):
        st.write("Insights coming soon...")
#streamlit as st
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

# -------------------------
# Build trades list
# -------------------------
trades = []
for symbol, details in data.items():
    closing_price = to_float(details.get("closing_price"))

    for i in range(1, 5):
        entry = to_float(details.get(f"entry {i}"))
        entry_date_raw = details.get(f"entry {i} date")
        exit_val = to_float(details.get(f"exit {i}"))
        exit_date_raw = details.get(f"exit {i} date")

        # clean dates
        entry_date = clean_date(entry_date_raw)
        exit_date = clean_date(exit_date_raw)

        # Skip case: only closing_price present
        if entry is None and exit_val is None and closing_price is not None:
            continue

        # Skip case: no valid entry-date or exit-date pair
        if not ((entry is not None and entry_date is not None) or (exit_val is not None and exit_date is not None)):
            continue

        # Invalidate exit if it's earlier than entry
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
            "status": status,
        })

# -------------------------
# DataFrame
# -------------------------
trades_df = pd.DataFrame(trades)

# Profit summary by symbol
profit_summary = trades_df.groupby("symbol").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum"
}).reset_index().fillna(0)

total_realized = profit_summary["realized_profit"].sum()
total_unrealized = profit_summary["unrealized_profit"].sum()

# -------------------------
# Profit by Entry/Exit Level
# -------------------------
level_summary = trades_df.groupby("level").agg({
    "realized_profit": "sum",
    "unrealized_profit": "sum",
    "profit": ["sum", "mean", "count"]
}).reset_index()

# flatten multi-level columns
level_summary.columns = ["level", "realized_profit", "unrealized_profit", "total_profit", "avg_profit_per_trade", "trade_count"]

# -------------------------
# Streamlit UI
# -------------------------
st.title("📊 Stock Signal Dashboard — Realized & Unrealized Profits")

# Debug section
st.subheader("🔎 Debug — First Few Trades")
st.write(trades_df.head(10))

# Profit summary
st.subheader("✅ Profit Summary (Realized vs Unrealized)")
st.dataframe(profit_summary, use_container_width=True)

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Realized", f"${total_realized:.2f}")
col2.metric("📈 Total Unrealized", f"${total_unrealized:.2f}")
col3.metric("💵 Combined", f"${(total_realized + total_unrealized):.2f}")

# Chart
st.subheader("📊 Realized vs Unrealized per Symbol")
if not profit_summary.empty:
    chart_data = profit_summary.set_index("symbol")[["realized_profit", "unrealized_profit"]]
    st.bar_chart(chart_data)
else:
    st.info("No profit data available yet.")

# Level-wise analysis
st.subheader("📊 Profit Analysis by Entry/Exit Level")
st.dataframe(level_summary, use_container_width=True)

if not level_summary.empty:
    chart_data_levels = level_summary.set_index("level")[["realized_profit", "unrealized_profit", "total_profit", "avg_profit_per_trade"]]
    st.bar_chart(chart_data_levels)
else:
    st.info("No level-wise profit data available yet.")

# Full trades table
st.subheader("📋 All Trades")
st.dataframe(trades_df, use_container_width=True)


if st.sidebar.button("Show Analytics"):
    streamlit_analytics.show()


