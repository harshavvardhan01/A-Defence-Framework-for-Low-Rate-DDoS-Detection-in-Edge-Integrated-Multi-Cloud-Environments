# The complete, final experimental results, presented
#       statically -- every number here is real, taken directly
#       from the thesis's own verified tables and figures. This
#       page needs NO live infrastructure to work; it's built
#       for presenting the finished results, not monitoring a
#       run in progress.

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Key Findings — APPCD", layout="wide")

TEAL = "#0E9384"
ORANGE = "#B45309"
PURPLE = "#6A4C93"
GREY = "#9AA5B1"

st.title("📊 Key Findings")
st.caption(
    "Every number on this page is drawn directly from the thesis's "
    "verified tables and figures — nothing here is illustrative."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "RQ1 — Detection Effectiveness",
        "RQ2 — Real Infrastructure",
        "RQ3 — Fault Tolerance",
        "RQ4 — Canary Gate",
        "Costs — What Got Worse",
    ]
)

# ══════════════════════════════════════════════════════════
# RQ1 — DETECTION EFFECTIVENESS
# ══════════════════════════════════════════════════════════
with tab1:
    st.subheader("Federated Learning Improves Detection Accuracy")

    col1, col2 = st.columns([3, 2])

    with col1:
        seeds = ["42", "123", "7", "2024", "99"]
        standalone_vals = [81.38, 82.04, 82.84, 81.60, 81.51]
        federated_vals = [98.13, 98.27, 97.16, 98.53, 98.80]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=seeds, y=standalone_vals, name="Standalone",
            marker_color=ORANGE,
            text=[f"{v:.2f}%" for v in standalone_vals], textposition="outside",
        ))
        fig.add_trace(go.Bar(
            x=seeds, y=federated_vals, name="Federated",
            marker_color=TEAL,
            text=[f"{v:.2f}%" for v in federated_vals], textposition="outside",
        ))
        fig.update_layout(
            barmode="group", yaxis_title="Macro Accuracy (%)",
            xaxis_title="Random Seed", yaxis_range=[0, 108],
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=420, margin=dict(t=60),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("Standalone (mean ± SD)", "81.87% ± 0.59%")
        st.metric("Federated (mean ± SD)", "98.18% ± 0.62%", "+16.30pp")
        st.write("")
        st.markdown(
            """
            **Statistical significance** (paired $t$-test, 5 seeds):
            - $t = 31.08$, $p < 0.0001$
            - Cohen's $d = 13.90$ (very large effect)
            - 95% CI on the difference: **[14.85, 17.76]** pp

            The true improvement is very unlikely to be smaller
            than 14.85pp, even accounting for 5-seed sample
            uncertainty.
            """
        )

    st.divider()
    st.subheader("The Real Question: What Does Federation Cost, vs. Just Pooling the Data?")

    cent_col1, cent_col2 = st.columns([3, 2])
    with cent_col1:
        conditions = ["Standalone\n(Node A only)", "Federated\n(A+B+D)", "Centralised\n(pooled training)"]
        accuracy = [82.93, 95.96, 98.98]
        colors = [ORANGE, TEAL, PURPLE]

        fig2 = go.Figure(go.Bar(
            x=conditions, y=accuracy, marker_color=colors,
            text=[f"{v:.2f}%" for v in accuracy], textposition="outside",
        ))
        fig2.update_layout(
            yaxis_title="Pooled Accuracy (%)", yaxis_range=[0, 108],
            height=380, margin=dict(t=40),
        )
        st.plotly_chart(fig2, use_container_width=True)

    with cent_col2:
        st.metric("Federation recovers", "96.95%", "of the centralised ceiling")
        st.write("")
        st.success(
            "**Federation recovers ~97% of the accuracy achievable by fully "
            "pooling all data — while transmitting no raw traffic between "
            "nodes at any point.**"
        )

    st.divider()
    st.subheader("The Node B Story — Where the Improvement Actually Comes From")

    nb_col1, nb_col2 = st.columns([3, 2])
    with nb_col1:
        nodes = ["Node A", "Node B", "Node D"]
        standalone_recall = [98.71, 0.00, 97.18]
        federated_recall = [98.71, 83.61, 97.18]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=nodes, y=standalone_recall, name="Standalone",
            marker_color=ORANGE,
            text=[f"{v:.2f}%" for v in standalone_recall], textposition="outside",
        ))
        fig3.add_trace(go.Bar(
            x=nodes, y=federated_recall, name="Federated",
            marker_color=TEAL,
            text=[f"{v:.2f}%" for v in federated_recall], textposition="outside",
        ))
        fig3.update_layout(
            barmode="group", yaxis_title="Recall (%)", yaxis_range=[0, 112],
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=400, margin=dict(t=60),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with nb_col2:
        st.markdown(
            """
            **Node A and Node D:** unchanged between conditions —
            both draw from BCCC-cPacket-Cloud-DDoS-2024, which
            either model already fits closely.

            **Node B (CIC-DDoS2019):** the standalone model detects
            **0 of 360** real attacks. Under federation: **301 of 360**
            (83.61% recall).

            This single node's swing is the entire pooled 21.18pp
            recall gain, diluted across three nodes' combined flows.
            """
        )
        with st.expander("Was this a bug, not a finding?"):
            st.markdown(
                """
                Checked directly before trusting this result:
                - Per-node feature scales are comparable across all
                  three nodes (no order-of-magnitude mismatch)
                - The same standalone model produces healthy,
                  high-confidence predictions on Node A (mean 0.949)
                  and Node D (mean 0.964) — proving it's fully
                  capable of confident output
                - It simply never learned CIC-DDoS2019's SYN-flood
                  signature — a genuine generalisation gap, not a
                  preprocessing artefact
                """
            )

# ══════════════════════════════════════════════════════════
# RQ2 — REAL INFRASTRUCTURE
# ══════════════════════════════════════════════════════════
with tab2:
    st.subheader("Deployed as Genuine, Geographically Distributed Infrastructure")

    ic1, ic2, ic3 = st.columns(3)
    ic1.metric("Regions", "2", "Dublin + N. Virginia")
    ic2.metric("Avg. payload/round", "≈1,136 KB", "structurally bounded")
    ic3.metric("Total AWS cost", "< €15", "entire project")

    st.write("")
    lat_col1, lat_col2 = st.columns([3, 2])

    with lat_col1:
        lat_nodes = ["Node A\n(Dublin)", "Node B\n(Dublin)", "Node D\n(Virginia)"]
        lat_means = [0.902, 0.827, 1.381]
        lat_sds = [0.029, 0.073, 0.032]

        fig4 = go.Figure(go.Bar(
            x=lat_nodes, y=lat_means,
            error_y=dict(type="data", array=lat_sds, visible=True),
            marker_color=[TEAL, TEAL, PURPLE],
            text=[f"{v:.3f}s" for v in lat_means], textposition="outside",
        ))
        fig4.update_layout(
            yaxis_title="Mean Round Latency (s)", yaxis_range=[0, 1.7],
            height=380, margin=dict(t=40),
        )
        st.plotly_chart(fig4, use_container_width=True)

    with lat_col2:
        st.markdown(
            """
            **Steady-state latency, n=27** (round 1 warm-up and two
            identified network-jitter rounds excluded, each named
            and justified):

            Node D (Virginia) shows a persistent ≈53% latency gap
            over the Dublin nodes, sustained across every round —
            confirming genuine geographic distance, not simulated
            or assumed.
            """
        )

    st.divider()
    st.markdown(
        """
        **Payload stays flat regardless of training progress** — only
        model weights cross the network, never raw traffic. At 53,761
        parameters (float32), the raw array is ≈210 KB; the measured
        ≈1,136 KB reflects JSON serialisation overhead and multi-node
        transmission, not a data leak.
        """
    )

# ══════════════════════════════════════════════════════════
# RQ3 — FAULT TOLERANCE
# ══════════════════════════════════════════════════════════
with tab3:
    st.subheader("A Real, Deliberately Induced Node Failure")

    st.markdown(
        "Node B's container was stopped mid-run, live, on real AWS "
        "infrastructure — no simulation. The complete round-by-round "
        "trace was captured via the DynamoDB round-state mirror."
    )

    rounds_list = list(range(20, 31))
    macro_vals = [98.67, 98.67, 98.67, 98.67, 86.31, 85.64, 83.78, 83.38, 83.33, 83.38, 83.2]

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=rounds_list, y=macro_vals, mode="lines+markers",
        line=dict(color=TEAL, width=3), marker=dict(size=7),
        name="Macro validation accuracy",
    ))
    fig5.add_vline(x=24, line_dash="dash", line_color=ORANGE,
                    annotation_text="Node B fault injected", annotation_position="top")
    fig5.update_layout(
        xaxis_title="Federated Round", yaxis_title="Macro Validation Accuracy (%)",
        yaxis_range=[78, 102], height=420,
    )
    st.plotly_chart(fig5, use_container_width=True)

    fc1, fc2, fc3 = st.columns(3)
    fc1.metric("Before fault (round 23)", "98.67%")
    fc2.metric("At fault (round 24)", "86.31%", "-12.36pp")
    fc3.metric("6 rounds later (round 30)", "83.2%", "-15.47pp total", delta_color="inverse")

    st.warning(
        "**Reported honestly, not softened:** the training trajectory "
        "*continued to decline* after the fault, not partially recovered. "
        "The canary gate protected the served model from ever promoting "
        "the degraded candidate — but the underlying training quality "
        "did not recover within the observed window. This is a genuine, "
        "disclosed limitation."
    )

    st.info(
        "**What did work:** the system continued training automatically "
        "at reduced quorum (2 of 3 nodes), with no manual intervention "
        "required to keep it running. A CloudWatch alarm independently "
        "confirmed the failure with a clean OK → ALARM → OK lifecycle."
    )

# ══════════════════════════════════════════════════════════
# RQ4 — CANARY GATE
# ══════════════════════════════════════════════════════════
with tab4:
    st.subheader("Safe Model Release — A Real, Logged Rejection")

    cg1, cg2 = st.columns([2, 3])
    with cg1:
        st.metric("Promoted", "25 / 30", "83%")
        st.metric("Correctly rejected", "5 / 30", "17%")

    with cg2:
        st.markdown("**A specific, verified rejection** (captured during the Node B fault):")
        rejection_df = pd.DataFrame({
            "Metric": ["Serving model accuracy", "Candidate model accuracy", "Regression", "Decision"],
            "Value": ["98.40%", "54.73%", "43.67pp", "❌ Rejected"],
        })
        st.dataframe(rejection_df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown(
        """
        **A real defect was found and fixed during development:** an
        earlier design checked a *fixed* pair of nodes each round. At
        small node counts, this created a blind spot — a degrading node
        could be repeatedly excluded from its own safety check. One
        specific case: a candidate with **59.60% accuracy** was promoted
        undetected because the degrading node wasn't in that round's
        fixed sample.

        **Fix:** canary sample size set equal to active node count, so
        every node is checked every round. Re-verified over a full
        30-round run with zero undetected regressions afterward.
        """
    )

# ══════════════════════════════════════════════════════════
# COSTS — WHAT GOT WORSE
# ══════════════════════════════════════════════════════════
with tab5:
    st.subheader("Reported With the Same Rigour as Everything That Improved")

    st.markdown(
        "Federating a detection agent improves detection quality — "
        "**at a measurable cost in every other dimension.** All four "
        "costs below are disclosed explicitly, not minimised."
    )

    cost_col1, cost_col2 = st.columns(2)

    with cost_col1:
        st.markdown("##### False Positive Rate")
        st.metric("Standalone → Federated", "0.00% → 0.97%", "+0.97pp", delta_color="inverse")
        st.caption(
            "Partly an artefact of the standalone model's 0.00% reflecting "
            "near-zero detection outside its own distribution, not a "
            "genuinely clean baseline."
        )

        st.markdown("##### Operational Complexity")
        st.caption(
            "Multiple containers, two-region infrastructure, and "
            "quorum/canary logic all required genuine diagnostic effort "
            "a single model never demands."
        )

    with cost_col2:
        st.markdown("##### Latency & Bandwidth")
        st.metric("Cross-region latency gap", "≈53%", "persistent, Node D vs. Dublin")
        st.metric("Bandwidth per round", "≈1,136 KB", "vs. 0 for single-node")

        st.markdown("##### Infrastructure Cost")
        st.metric("Cloud instances", "4", "vs. 1 for single-node baseline")
        st.caption("Kept small through disciplined start/stop hygiene — under €10 total for this comparison.")

    st.divider()
    st.success(
        "**Hypothesis confirmed on both counts:** federating a single "
        "detection agent improves detection quality — recall improved "
        "21.18pp, concentrated in generalisation to an environment the "
        "standalone model never observed — while FPR and decision "
        "latency both measurably increased."
    )