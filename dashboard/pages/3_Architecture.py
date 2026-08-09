#Displays the production architecture diagram, plus a
#       direct download button for the same high-resolution
#       PNG — built once, used both in the dashboard and
#       directly droppable into the presentation slides.

import os

import streamlit as st

st.set_page_config(page_title="Architecture — APPCD", layout="wide")

TEAL = "#0E9384"
ORANGE = "#B45309"
PURPLE = "#6A4C93"

st.title("🏗️ Production Architecture")
st.caption(
    "Three-tier system, deployed as real infrastructure across two AWS "
    "regions — not simulated, not diagrammed-but-unbuilt."
)

ASSET_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "architecture_presentation.png")

if os.path.exists(ASSET_PATH):
    st.image(ASSET_PATH, use_container_width=True)

    with open(ASSET_PATH, "rb") as f:
        st.download_button(
            label="⬇️ Download high-resolution PNG (for slides)",
            data=f,
            file_name="appcd_architecture.png",
            mime="image/png",
        )
else:
    st.error(
        f"Architecture diagram not found at {ASSET_PATH}. "
        f"Make sure dashboard/assets/architecture_presentation.png exists."
    )

st.divider()

# ── Tier-by-tier explanation, for narrating the diagram live ──
st.subheader("Reading the Diagram")

t1, t2, t3 = st.columns(3)

with t1:
    st.markdown(
        f"""
        <div style="border-left: 4px solid {PURPLE}; padding-left: 12px;">
        <h5>Tier 1 — CI/CD & Identity</h5>
        <p style="font-size: 0.9rem;">
        Every push to <code>main</code> triggers GitHub Actions to build
        and publish a new image — verified by pulling from a separate
        machine and confirming a fresh digest. Every AWS-facing
        instance authenticates via a least-privilege IAM role, never
        an embedded credential.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with t2:
    st.markdown(
        f"""
        <div style="border-left: 4px solid {TEAL}; padding-left: 12px;">
        <h5>Tier 2 — Compute & Federated Learning</h5>
        <p style="font-size: 0.9rem;">
        The Coordinator orchestrates federated rounds across three real
        nodes, spanning two real AWS regions — not a single machine
        pretending to be distributed. A canary gate protects every
        model promotion; a real, induced node failure was survived
        without manual intervention.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with t3:
    st.markdown(
        f"""
        <div style="border-left: 4px solid {ORANGE}; padding-left: 12px;">
        <h5>Tier 3 — Data & Observability</h5>
        <p style="font-size: 0.9rem;">
        Every promoted model is versioned in S3; every round's outcome
        is durably logged in DynamoDB; every node failure is
        independently confirmed by a CloudWatch alarm with a verified
        OK → ALARM → OK lifecycle.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

st.subheader("What Makes This Different From a Diagram-Only Design")
st.markdown(
    """
    Every component shown above is **implemented and independently
    verified**, not aspirational:

    - The IAM role was confirmed genuinely discoverable by querying the
      instance metadata service from inside a running container
    - The S3 mirror was verified by independently listing bucket
      contents and checking file sizes/timestamps
    - The DynamoDB store was verified by scanning the table and
      matching item counts to completed rounds
    - The CloudWatch alarm was verified through a live kill-node test,
      showing the full OK → ALARM → OK lifecycle
    - The CI/CD pipeline was verified by pulling the image from a
      separate machine and confirming a fresh digest

    A small number of items remain design-only, stated explicitly
    rather than left implicit: a hierarchical regional aggregation
    tier (needed only past the three-node scale evaluated here),
    certificate-based mutual TLS in place of the current shared-token
    authentication, and asynchronous message buffering (SQS) in place
    of direct HTTP calls.
    """
)