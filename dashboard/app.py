# dashboard/app.py
#
# WHAT: Reads state.json (written by the coordinator after
#       every round) and renders it as a live dashboard —
#       accuracy trend, per-node latency, decision history.
# WHY:  This is what makes the demo "land in a call" rather
#       than being a wall of terminal logs — the exact same
#       data, but visual and immediately readable by someone
#       who wasn't following the logs line by line.

import json
import os
import time

import pandas as pd
import streamlit as st

st.set_page_config(page_title="APPCD Federation Dashboard", layout="wide")

STATE_FILE = os.environ.get("STATE_FILE", "state.json")

st.title("APPCD — Federated LR-DDoS Detection")
st.caption("Live view of federated training across distributed edge nodes")

# ── Load state ────────────────────────────────────────────
try:
    with open(STATE_FILE) as f:
        state = json.load(f)
except FileNotFoundError:
    st.warning(f"No state file found at '{STATE_FILE}' — "
               f"the coordinator hasn't produced any results yet.")
    st.stop()

rounds = [r for r in state.get("rounds", []) if r.get("status") == "ok"]

if not rounds:
    st.warning("state.json exists but contains no completed rounds yet.")
    st.stop()

# ── Top-line metrics ──────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rounds completed", len(state["rounds"]))
col2.metric("Best macro validation",
            f"{state['best']['macro_val']:.2f}%",
            f"round {state['best']['round']}")
col3.metric("Currently serving", f"v{state['serving_version']}")
col4.metric("Nodes in last round",
            ", ".join(sorted(rounds[-1]["reported"])))

st.divider()

# ── Accuracy trend ────────────────────────────────────────
st.subheader("Macro validation accuracy by round")
acc_df = pd.DataFrame(
    {"round": [r["round"] for r in rounds],
     "macro_val": [r["macro_val"] for r in rounds]}
).set_index("round")
st.line_chart(acc_df)

# ── Per-node latency — the cross-region evidence ──────────
st.subheader("Per-node round latency (seconds)")
st.caption("A node in a different region should show "
           "consistently higher latency — real geographic distance.")
latency_rows = [r["latency_s"] for r in rounds]
lat_df = pd.DataFrame(latency_rows, index=[r["round"] for r in rounds])
st.line_chart(lat_df)

# ── Per-node accuracy comparison ──────────────────────────
st.subheader("Per-node validation accuracy by round")
node_acc_rows = [r["per_node_val"] for r in rounds]
node_df = pd.DataFrame(node_acc_rows, index=[r["round"] for r in rounds])
st.line_chart(node_df)

# ── Bandwidth evidence ─────────────────────────────────────
st.subheader("Payload size per round (KB)")
payload_df = pd.DataFrame(
    {"round": [r["round"] for r in rounds],
     "payload_kb": [r["payload_kb"] for r in rounds]}
).set_index("round")
st.bar_chart(payload_df)
avg_payload = payload_df["payload_kb"].mean()
st.caption(f"Average payload: {avg_payload:.0f} KB per round across all nodes")

# ── Model release history — the canary decisions ──────────
st.subheader("Model release history (canary decisions)")
if state.get("deployments"):
    deploy_df = pd.DataFrame(state["deployments"])
    st.dataframe(deploy_df, use_container_width=True)

    promoted = sum(1 for d in state["deployments"] if d["decision"] == "promoted")
    rejected = sum(1 for d in state["deployments"] if d["decision"] == "rejected")
    st.caption(f"{promoted} promoted, {rejected} rejected out of "
               f"{len(state['deployments'])} candidate models evaluated")
else:
    st.text("No model releases recorded yet.")

# ── Node health at startup ─────────────────────────────────
st.subheader("Node health (last check)")
if state.get("node_status"):
    st.json(state["node_status"])

st.divider()
st.caption(f"Auto-refreshing every 5 seconds \u2014 last loaded at "
          f"{time.strftime('%H:%M:%S')}")
time.sleep(5)
st.rerun()