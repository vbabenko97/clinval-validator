Use the Opus 4.8 prompting guide / skill if available. If that skill is not available in this environment, proceed using current Claude Code best practices: be explicit, inspect the repository first, plan before editing, keep context focused, and define verification checks.

Think hard before planning.

<context>
I am building a project for the "Built with Claude: Life Sciences" hackathon.

Track: Builder Track.
Goal: build working software that a named user could use without me in the room.

Project idea:
A clinical AI validation tool for medical imaging ML models. The tool analyzes a predictions.csv file and detects:
1. patient-level data leakage across train/test,
2. weak evaluation splits such as random split vs patient/site-grouped split,
3. subgroup performance degradation across scanners/sites/patient groups,
4. unsafe performance claims that would not survive clinical deployment scrutiny.

Important architecture rule:
Python computes all deterministic metrics and validation checks.
Claude only explains the results in human-readable language:
- validation risk report,
- unsafe claim warnings,
- reviewer-style critique,
- suggested next validation steps.

Data plan:
Use synthetic RSNA mammography-like prediction tables.
No PHI.
No confidential clinical data.
No real patient data.
No dependency on downloading full medical image datasets for the MVP.

Expected synthetic schema:
patient_id, image_id, machine_id, site_id, age, density, y_true, y_prob, split

The synthetic generator should intentionally create:
- repeated patient_id across train/test for leakage detection,
- random split that looks over-optimistic,
- patient/site-grouped split that exposes degraded performance,
- one scanner or site subgroup with clearly worse performance,
- reproducible random seed.

Hackathon constraints:
- project must be built from scratch during the hackathon,
- submitted work must be open-source,
- avoid code/data/assets I do not have rights to,
- prioritize a working demo over broad unfinished features.
</context>

<current_task>
Start project planning inside this repository.

Do not implement the full tool yet.

First, inspect the current repository structure and files.
Then create or update only planning/scaffolding documents needed to guide implementation.

I want a practical implementation plan for the MVP, not a generic product strategy.
</current_task>

<deliverables>
Create the following files if they do not already exist:

1. README.md
   Include:
   - project name: clinval-validator for now,
   - one-sentence purpose,
   - hackathon note: built from scratch for Built with Claude: Life Sciences,
   - no PHI / synthetic data only disclaimer,
   - MVP scope,
   - expected input CSV schema,
   - planned demo narrative.

2. PROJECT_PLAN.md
   Include:
   - problem statement,
   - named user,
   - MVP definition,
   - non-goals,
   - architecture,
   - data generation plan,
   - validation checks,
   - Claude-generated report plan,
   - risks and scope cuts,
   - demo story.

3. TASKS.md
   Include a staged implementation checklist:
   Phase 1: synthetic data generator.
   Phase 2: deterministic validation core.
   Phase 3: report JSON schema.
   Phase 4: Claude report generation.
   Phase 5: minimal CLI or Streamlit demo.
   Phase 6: demo script and submission polish.

4. CLAUDE.md
   Include repo-specific instructions for future Claude Code sessions:
   - Python 3.10+,
   - minimal dependencies,
   - deterministic checks before LLM calls,
   - no PHI,
   - no hidden external data assumptions,
   - small testable functions,
   - run tests after edits,
   - keep scope focused on the MVP.
</deliverables>

<quality_bar>
The plan must be concrete enough that the next Claude Code session can start implementing Phase 1 immediately.

Avoid vague items like "improve model" or "add AI magic."
Every task should produce a file, function, test, CLI command, or demo artifact.

Keep the MVP small:
- synthetic predictions.csv generator,
- leakage detector,
- split comparison,
- subgroup degradation check,
- structured risk report.

Put TRIPOD+AI / CLAIM mapping under stretch goals only.
Do not make standards mapping part of the Phase 1 MVP.
</quality_bar>

<verification_plan>
Define how we will verify the project without relying on real medical data:
- unit tests for generated schema,
- unit test that leakage is actually injected,
- unit test that detector catches train/test patient overlap,
- unit test that subgroup degradation is detectable,
- CLI smoke test that runs end-to-end on synthetic data.
</verification_plan>

<output_format>
After editing files, respond with:

1. Files created/updated.
2. The final MVP scope in 5 bullets max.
3. The first implementation command/task for the next step.
4. Any assumptions you made.

Do not start coding the generator yet unless I explicitly approve the plan.
</output_format>