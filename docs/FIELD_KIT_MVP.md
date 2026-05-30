# AMDEP Field Kit MVP

AMDEP Field Kit is the local, FDE-led pilot package.

It is not a hosted SaaS deployment and it is not meant to be handed to a contractor cold. The first real deployment should be operator-assisted: the FDE brings the kit, collects copied exports, maps the customer's current staffing process, runs the audit locally, and leaves behind a report plus a data-readiness plan.

## What Ships

- Local intake web app.
- Private local workspace.
- File drop zone for copied exports.
- File classifier for rosters, jobs, assignments, certs, and assets.
- Canonical AMDEP normalization.
- Local audit runner.
- Local executive audit packet.
- Local command-center UI using the same AMDEP interface pattern as the demo.
- AI booster instructions for Codex, Claude Code, Claude Cowork, Cursor, Copilot, or similar tools.
- Model card explaining features, synthetic risk models, optimizer weights, calibration, and caveats.

## What It Does Not Require

- Public hosting.
- Customer data on GitHub.
- Production system access.
- Writeback privileges.
- Frontier AI API key.

## Install Posture

This is a technical handoff kit, not a consumer app store install.

An FDE, internal IT lead, ops analyst, or reasonably technical project-controls person should be able to unzip it, confirm Python 3.11+, run the launcher, and walk the operating team through the browser UI.

If Python is missing, the launchers stop with a plain install message. The recommended path is to install Python from `python.org`, then rerun:

- macOS: `run_field_kit.command`
- Windows: `run_field_kit.bat`

For a customer-owned environment, IT should approve the machine, Python install, package install from `requirements.txt`, and the copied-export workflow before any real customer data is used.

## Workflow Modes

### Analogue / spreadsheet shop

The FDE or customer operator exports rosters, job lists, schedules, and certification sheets to Excel or CSV. The Field Kit classifies the files, maps columns, runs the local audit, and records missing fields.

### IT-assisted shop

Internal IT provides read-only exports from systems such as Workday, ADP, Procore, Autodesk, Sage, HCSS, Viewpoint, CMiC, Foundation, SharePoint, or OneDrive. The first run stays read-only. Any recurring connector or writeback is a later approval path.

### Agentic / enterprise-AI shop

If the customer already has Codex, Claude Code, Claude Cowork, Copilot, Gemini, or another approved enterprise AI tool connected to their environment, the `field_kit/ai_booster/` instructions can be dropped into that environment. The agent maps data into the AMDEP canonical bundle and runs the same local audit, still with no writeback by default.

## Model And Weights

See `docs/FIELD_KIT_MODEL_CARD.md`.

Each local audit writes:

- `recommended_weights.csv`
- `calibration_trials.csv`
- `validation_report.csv`
- `dispatch_audit_summary.html`
- local command-center `demo-data.json`

## FDE Runbook

1. Ask how staffing currently works.
2. Ask which systems they use: Workday, ADP, Procore, Autodesk, Sage, HCSS, Viewpoint, CMiC, Foundation, SharePoint, Excel, Teams, whiteboard, or something else.
3. Request copied exports only.
4. Drop files into the Field Kit.
5. Let AMDEP classify the files.
6. Confirm ambiguous mappings with the operator.
7. Run the local audit.
8. Open the local command center and executive packet.
9. Record data gaps and the next export request.

## Packaging

For a pilot, package the repo folder or release zip with:

- `run_field_kit.command` for macOS.
- `run_field_kit.bat` for Windows.
- `.venv` or setup instructions if not bundling Python.
- `field_kit/`
- `amdep/`
- `data/`
- `requirements.txt`
- `field_kit/ai_booster/`
- `docs/FIELD_KIT_MODEL_CARD.md`

The private working directory is `field_kit_workspace/` and should never be committed.

## Command

```bash
python -m amdep.field_kit
```

Open:

```text
http://127.0.0.1:8095/
```

Build a portable zip:

```bash
python scripts/package_field_kit.py
```

Output:

```text
dist/amdep-field-kit.zip
```

## Positioning

The first sale is not "install our platform."

The first sale is:

> Give us copied exports from whatever you already use. We will run a read-only staffing intelligence audit locally and show you the waste, the data gaps, and the first recommendation queue.
