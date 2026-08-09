# dashboard/app.py
#
# WHAT: The landing page for the presentation dashboard.
#       Gives the thesis's one-paragraph story and headline
#       numbers up front, then points to the two detail pages
#       (Live Federation, Key Findings) in the sidebar.
# WHY:  A presentation needs an entry point that works even
#       before anyone clicks anything -- the story should be
#       readable in the first 10 seconds on screen.

import streamlit as st

st.set_page_config(
    page_title="APPCD — Federated LR-DDoS Detection",
    page_icon="🛡️",
    layout="wide",
)

# ── Consistent colour palette, matching the thesis's own figures ──
TEAL = "#0E9384"      # federated / positive result
ORANGE = "#B45309"    # standalone / baseline
PURPLE = "#6A4C93"    # centralised / infrastructure

st.markdown(
    f"""
    <style>
    .metric-card {{
        background-color: #F7F8FA;
        border: 1px solid #E1E4E8;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
    }}
    .metric-value {{
        font-size: 2.1rem;
        font-weight: 700;
        color: {TEAL};
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #6B7280;
        margin-top: 0.3rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ APPCD — Federated Detection for Low-Rate DDoS")
st.caption(
    "A distributed collaborative defence framework, addressing future work "
    "identified by Zhou et al. (2025), deployed as production-representative "
    "cloud infrastructure across two AWS regions."
)

st.divider()

# ── The one-paragraph story ────────────────────────────────
st.markdown(
    """
    ### The Question

    Zhou et al. (2025) built a single-agent moving-target-defence system for
    low-rate DDoS mitigation — strong results, but confined to one node,
    observing one traffic distribution. They explicitly name **distributed
    collaborative defence** as unaddressed future work.

    **This project implements and empirically validates that framework** —
    federated detection across two genuinely independent real-world traffic
    sources, partitioned across three heterogeneous nodes, deployed as real
    infrastructure across two AWS regions, not simulated on one machine.
    """
)

st.divider()

# ── Headline numbers ────────────────────────────────────────
st.subheader("Headline Results")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-value">+16.30pp</div>
        <div class="metric-label">Macro accuracy improvement<br>over best standalone agent</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-value">96.95%</div>
        <div class="metric-label">Of the centralised-training<br>ceiling recovered, zero data shared</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-value">2 regions</div>
        <div class="metric-label">Real AWS infrastructure<br>Dublin + N. Virginia</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""<div class="metric-card">
        <div class="metric-value">p&lt;0.0001</div>
        <div class="metric-label">Statistical significance<br>t=31.08, 5 independent seeds</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.write("")
st.info(
    "👈 **Use the sidebar** to explore: **Live Federation** shows a real "
    "training run's round-by-round progress; **Key Findings** presents the "
    "complete, final experimental results supporting every claim above."
)

st.divider()

# ── What was actually built ─────────────────────────────────
st.subheader("What Was Built, Not Just Simulated")

b1, b2, b3 = st.columns(3)
with b1:
    st.markdown(
        """
        **Real infrastructure**
        - Terraform-provisioned, two AWS regions
        - Docker containers, one image, four roles
        - IAM instance roles, no embedded credentials
        - GitHub Actions CI/CD, independently verified
        """
    )
with b2:
    st.markdown(
        """
        **Real evaluation**
        - Two independently captured real datasets
        - 5-seed statistical validation (paired t-test)
        - A real induced node failure on live infrastructure
        - A real canary rejection, logged and numeric
        """
    )
with b3:
    st.markdown(
        """
        **Real honesty**
        - Every cost disclosed: FPR, latency, complexity
        - A genuine training-trajectory limitation reported,
          not hidden
        - Node B's result independently checked against a
          scaling-artefact hypothesis before being trusted
        """
    )