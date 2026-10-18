#!/usr/bin/env bash
# Spine of the 3-minute demo: a GREEN control, then the leakage scenario.
# Requires ANTHROPIC_API_KEY (the report step calls Claude; see MODEL in reporter/report.py).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIOS="$REPO_ROOT/claude-science-artifacts/scenarios"

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "ANTHROPIC_API_KEY is not set — the report step needs it. Export your key and re-run." >&2
  exit 1
fi

run() {
  local scenario="$1" expectation="$2"
  echo "============================================================"
  echo "  $scenario  ($expectation)"
  echo "============================================================"
  clinval-validate --predictions "$SCENARIOS/$scenario.csv"
  echo
}

run clean_patient_grouped "expect GREEN — no leakage, no flagged subgroup"
run optimistic_site_shortcut "expect RED — 990 patients in both train and test"
