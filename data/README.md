# data/

This folder contains this README. A local `data/rsna/` directory may hold `train.csv` from the Radiological Society of North America (RSNA) Screening Mammography Breast Cancer Detection dataset. That directory is gitignored. The RSNA license bans redistribution, so the raw table is not in the repository.

The fixtures the validators read are in [`claude-science-artifacts/scenarios/`](../claude-science-artifacts/scenarios/). Each scenario is a `*.csv` plus a `*.manifest.json`.

The demo in [docs/DEMO.md](../docs/DEMO.md) uses `optimistic_site_shortcut`.
