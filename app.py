"""Streamlit demo for ClinVal Validator.

A thin presentation layer over the existing pipeline: the deterministic
validators compute the payload offline, and — on demand — Claude renders the
risk report or the reviewer critique. No metric is computed here; this file only
wires the tested functions to a UI. Run it with ``streamlit run app.py``.

Streamlit is imported lazily inside :func:`main` so this module (and its pure
helper) can be imported without the optional ``streamlit`` dependency installed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

from cli import _assemble_payload
from reporter import API_KEY_ENV, render_report, render_reviewer_critique

SCENARIOS_DIR = Path(__file__).resolve().parent / "claude-science-artifacts" / "scenarios"

# The columns every validator needs. Checked at the upload boundary: an uploaded
# file is the one input this tool does not control, so a missing column must
# produce a readable message rather than a raw KeyError traceback.
REQUIRED_COLUMNS = ("patient_id", "machine_id", "site_id", "y_true", "y_prob", "split")


def available_scenarios() -> dict[str, Path]:
    """Map each bundled scenario name to its predictions CSV (excludes the summary)."""
    return {p.stem: p for p in sorted(SCENARIOS_DIR.glob("*.csv")) if not p.name.startswith("_")}


def missing_columns(df: pd.DataFrame) -> list[str]:
    """Return the required columns absent from ``df``; empty when the schema fits."""
    return sorted(set(REQUIRED_COLUMNS) - set(df.columns))


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title="ClinVal Validator", layout="wide")
    st.title("ClinVal Validator")
    st.caption(
        "Flag patient-level leakage, weak splits, and subgroup degradation in a "
        "model's predictions.csv — Python computes the flags, Claude explains the risk."
    )
    st.info(
        "Synthetic / public-schema data only, modeled on the RSNA Screening "
        "Mammography schema. No PHI, no real patient data. Not medical advice."
    )

    with st.sidebar:
        st.header("Input")
        source = st.radio("Predictions source", ["Bundled scenario", "Upload CSV"])
        if source == "Bundled scenario":
            scenarios = available_scenarios()
            name = st.selectbox("Scenario", list(scenarios))
            df = pd.read_csv(scenarios[name])
        else:
            upload = st.file_uploader("predictions.csv", type="csv")
            if upload is None:
                st.stop()
            df = pd.read_csv(upload)

        st.header("Claude report")
        mode = st.radio("Mode", ["risk", "critique"], format_func=str.capitalize)
        api_key = st.text_input(
            "Anthropic API key", value=os.environ.get(API_KEY_ENV, ""), type="password"
        )
        generate = st.button("Generate with Claude", type="primary")

    absent = missing_columns(df)
    if absent:
        st.error(
            f"This CSV is missing required column(s): {', '.join(absent)}. "
            f"A predictions table needs: {', '.join(REQUIRED_COLUMNS)}. "
            "See the README for the expected schema.",
            icon="🚫",
        )
        st.stop()

    payload = _assemble_payload(df)
    leakage = payload["leakage"]
    flagged = [s for s in payload["subgroups"] if s["flagged"]]

    left, right = st.columns(2)

    with left:
        st.subheader("Deterministic flags")
        audit = payload["split_audit"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Leaked patients", leakage["overlapping_patient_ids"])
        c2.metric("Leakage rate", f"{leakage['leakage_rate']:.1%}")
        # The only like-for-like pair: one fixed y_prob, two evaluation populations.
        # Labels stay split-agnostic because an uploaded file may already be grouped.
        c3.metric("AUC, test split as given", f"{audit['random_split']:.3f}")
        c4.metric(
            "AUC, patient-disjoint subset",
            f"{audit['grouped_split']:.3f}",
            delta=f"{audit['grouped_split'] - audit['random_split']:+.3f}",
        )
        st.caption(
            "No retraining — only the evaluation population changes. "
            "Pooled AUC and the per-subgroup breakdown are in the JSON below."
        )
        if leakage["overlapping_patient_ids"]:
            st.error(
                f"{leakage['overlapping_patient_ids']} patients appear in both "
                "train and test — the split is not leakage-safe.",
                icon="🚫",
            )
        elif flagged:
            st.warning(f"{len(flagged)} subgroup(s) flagged below pooled AUC.", icon="⚠️")
        else:
            st.success("No leakage and no subgroup flags.", icon="✅")
        st.caption("Payload sent to Claude (every number is computed here, not by the model):")
        st.json(payload)
        st.download_button(
            "Download payload (JSON)",
            json.dumps(payload, indent=2),
            file_name="clinval_payload.json",
            mime="application/json",
        )

    with right:
        st.subheader("Claude report" if mode == "risk" else "Reviewer critique")
        # Keyed by mode + payload so a stored report is never shown for a different
        # scenario, and so downloading it (which reruns the script) does not lose it.
        report_key = f"{mode}:{json.dumps(payload, sort_keys=True)}"
        cached = st.session_state.get("report")

        if generate and not api_key:
            st.warning("Set an Anthropic API key to render the report.", icon="🔑")
        elif generate:
            os.environ[API_KEY_ENV] = api_key
            render = render_reviewer_critique if mode == "critique" else render_report
            with st.spinner(f"Asking claude-opus-4-8 for the {mode} report…"):
                cached = (report_key, render(payload))
            st.session_state["report"] = cached

        if cached and cached[0] == report_key:
            st.markdown(cached[1])
            st.download_button(
                "Download report (Markdown)",
                cached[1],
                file_name=f"clinval_{mode}_report.md",
                mime="text/markdown",
            )
        elif not generate:
            st.caption("Pick a mode and press **Generate with Claude**.")

    with st.expander("Raw payload JSON"):
        st.code(json.dumps(payload, indent=2), language="json")


if __name__ == "__main__":
    main()
