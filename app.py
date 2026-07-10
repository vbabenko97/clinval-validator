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


def available_scenarios() -> dict[str, Path]:
    """Map each bundled scenario name to its predictions CSV (excludes the summary)."""
    return {p.stem: p for p in sorted(SCENARIOS_DIR.glob("*.csv")) if not p.name.startswith("_")}


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

    payload = _assemble_payload(df)
    leakage = payload["leakage"]
    flagged = [s for s in payload["subgroups"] if s["flagged"]]

    left, right = st.columns(2)

    with left:
        st.subheader("Deterministic flags")
        c1, c2, c3 = st.columns(3)
        c1.metric("Leaked patients", leakage["overlapping_patient_ids"])
        c2.metric("Leakage rate", f"{leakage['leakage_rate']:.1%}")
        c3.metric("Pooled AUC", f"{payload['pooled_metric']['value']:.3f}")
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

    with right:
        st.subheader("Claude report" if mode == "risk" else "Reviewer critique")
        if not generate:
            st.caption("Pick a mode and press **Generate with Claude**.")
        elif not api_key:
            st.warning("Set an Anthropic API key to render the report.", icon="🔑")
        else:
            os.environ[API_KEY_ENV] = api_key
            render = render_reviewer_critique if mode == "critique" else render_report
            with st.spinner(f"Asking claude-opus-4-8 for the {mode} report…"):
                st.markdown(render(payload))

    with st.expander("Raw payload JSON"):
        st.code(json.dumps(payload, indent=2), language="json")


if __name__ == "__main__":
    main()
