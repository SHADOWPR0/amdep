# AMDEP Demo Delivery

The delivery system should stay simple: one local command, one browser URL, one synthetic packet.

## Recommended Format

- Desktop or tablet command center for owners, executives, operations managers, and project leaders.
- Mobile-responsive project companion view for superintendents, PMs, and field leadership.
- PWA-style shell before native iOS or Android.
- Existing systems remain the source of record; AMDEP generates review queues and export payloads.

## Run

```bash
python -m amdep.web_demo
```

Optional:

```bash
python -m amdep.web_demo --skip-audit
python -m amdep.web_demo --port 8090
python -m amdep.web_demo --host 0.0.0.0
```

Use `--host 0.0.0.0` only for a controlled LAN demo where a phone or tablet needs to open the app from the presenting laptop.

## Demo Flow

1. Start on `Overview`.
2. Point out the sample-data disclaimer before showing numbers.
3. Show baseline route burn, optimized route burn, dispatch delta, and annualized route value.
4. Open `Decisions` and approve one recommendation, mark one as review, reject one.
5. Open `Mobile` to show the same assignment in a field-safe view.
6. Open `Exports` to show Procore, Autodesk, HCSS, Sage, generic CSV, and Foundry-ready payloads.

## Buyer Framing

AMDEP is the deployment brain above existing construction systems. It does not ask a contractor to rip out Procore, Autodesk Build, HCSS, Sage, ERP exports, or internal spreadsheets on day one.

The correct claim is:

> This synthetic demo proves the workflow: ingest, validate, score, optimize, review, and export. Customer savings and model accuracy require customer history and validation.
