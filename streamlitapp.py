import streamlit as st
import json
import pandas as pd

# --- Load JSON ---
with open("signals.json", "r") as f:
    data = json.load(f)

# --- Build detailed trades table ---
trades = []
for symbol, details in data.items():
    all_notes = []  # collect entries & exits for notes
    trade_closed = False

    for i in range(1, 5):  # assuming up to 4 levels
        entry = details.get(f"entry {i}")
        entry_date = details.get(f"entry {i} date") if f"entry {i} date" in details else None
        exit_val = details.get(f"exit {i}")
        exit_date = details.get(f"exit {i} date") if f"exit {i} date" in details else None

        if entry is not None:
            all_notes.append(f"E{i}: {entry} ({entry_date})" if entry_date else f"E{i}: {entry}")
        if exit_val is not None:
            all_notes.append(f"X{i}: {exit_val} ({exit_date})" if exit_date else f"X{i}: {exit_val}")

        if entry is not None or exit_val is not None:
            profit = None
            status = "open"
            if entry is not None and exit_val is not None:
                profit = exit_val - entry
                status = "closed"
                trade_closed = True
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
                "status": status,
                "notes": None  # will fill later
            })

    #
