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

from clinval_validators import run_checks, validate_predictions
from reporter import (
    API_KEY_ENV,
    MODEL,
    ReportNotRenderedError,
    render_report,
    render_reviewer_critique,
)

SCENARIOS_DIR = Path(__file__).resolve().parent / "claude-science-artifacts" / "scenarios"


def available_scenarios() -> dict[str, Path]:
    """Map each bundled scenario name to its predictions CSV (excludes the summary)."""
    return {p.stem: p for p in sorted(SCENARIOS_DIR.glob("*.csv")) if not p.name.startswith("_")}


def _run_checks(df: pd.DataFrame):
    """Streamlit-cacheable wrapper. The cache lives on this function, not on a session."""
    return run_checks(df)


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

    problems = validate_predictions(df)
    if problems:
        st.error("\n\n".join(problems), icon="🚫")
        st.stop()

    payload = st.cache_data(_run_checks)(df)
    leakage = payload["leakage"]
    level = payload["risk"]["level"]
    reasons = " ".join(payload["risk"]["reasons"])

    left, right = st.columns(2)

    with left:
        st.subheader("Deterministic flags")
        audit = payload["split_audit"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Leaked patients", leakage["overlapping_patient_ids"])
        c2.metric("Leakage rate", f"{leakage['leakage_rate']:.1%}")
        # Same fixed predictions. The sample draws patients from every row,
        # including training rows, so it is not a second look at the test split.
        c3.metric("AUC, test split as given", f"{audit['test_split_as_given']:.3f}")
        # A small table can draw a one-class sample; the audit then reports None.
        sample = audit["patient_disjoint_sample"]
        c4.metric(
            "AUC, patient-disjoint sample",
            "n/a (one class)" if sample is None else f"{sample:.3f}",
            delta=None if sample is None else f"{sample - audit['test_split_as_given']:+.3f}",
        )
        range95 = audit["sample_range95"]
        range_text = (
            ""
            if range95 is None
            else f"Over the seeds 0–199 whose sample holds both classes, that sample "
            f"AUC stays within {range95[0]:.3f}–{range95[1]:.3f}. "
        )
        st.caption(
            "Both AUCs use the same fixed predictions. The patient-disjoint "
            "sample is drawn from all rows, including training rows, so this "
            "comparison cannot measure how much leakage inflated the metric. "
            f"{range_text}"
            "Pooled AUC and the per-subgroup breakdown are in the JSON below."
        )
        if level == "RED":
            st.error(f"{level}. {reasons}", icon="🚫")
        elif level == "YELLOW":
            st.warning(f"{level}. {reasons}", icon="⚠️")
        else:
            st.success(f"{level}. {reasons}", icon="✅")
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
            render = render_reviewer_critique if mode == "critique" else render_report
            try:
                with st.spinner(f"Asking {MODEL} for the {mode} report…"):
                    cached = (report_key, render(payload, api_key=api_key))
                st.session_state["report"] = cached
            except ReportNotRenderedError as exc:
                st.error(f"{exc} The deterministic payload on the left is complete.", icon="🚫")

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
