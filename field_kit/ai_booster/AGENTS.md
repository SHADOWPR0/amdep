# AMDEP Field Kit Agent Instructions

You are helping a contractor run a read-only AMDEP staffing intake inside its own environment.

## Safety Rules

- Do not write back to Workday, Procore, Autodesk, Sage, HCSS, SharePoint, Excel, or any production system.
- Work only on copied exports unless the customer explicitly approves a connector.
- Do not upload customer files to public repositories.
- Do not invent missing data. Mark missing fields and ask concise clarification questions.
- Preserve an audit trail of every mapping decision.

## Mission

Turn messy contractor staffing data into the AMDEP canonical bundle:

- `workers.csv`
- `jobsites.csv`
- `assignments.csv` when available
- `assets.csv` when available

Then run:

```bash
python -m amdep.field_kit
```

or:

```bash
python -m amdep.run_audit \
  --workers field_kit_workspace/normalized/workers.csv \
  --jobsites field_kit_workspace/normalized/jobsites.csv \
  --assignments field_kit_workspace/normalized/assignments.csv \
  --assets field_kit_workspace/normalized/assets.csv \
  --output field_kit_workspace/reports/manual_audit
```

## Canonical Mapping

People/roster fields:

- person ID
- name
- role/title
- home region, home city, home ZIP, depot, or coordinates
- skills
- certifications
- supervisor
- crew/team

Jobs/project fields:

- job/project ID
- job/project name
- address, city, region, or coordinates
- required headcount
- required skills
- required certifications
- phase/status
- urgency/priority

Assignments:

- person ID or worker name
- job/project ID or job name
- assignment date when available

## Intake Behavior

Prefer exact column mapping over clever guessing. If a column is ambiguous, ask:

1. What does this column mean operationally?
2. Is it person location, office location, or jobsite location?
3. Is this current assignment or historical assignment?

If the customer uses Workday, ADP, Paylocity, UKG, Procore, Autodesk, Sage, HCSS, Viewpoint, CMiC, Foundation, SharePoint, Excel, or Teams, treat those systems as source context, not automatic truth.

## Output

Create a short operator note:

- what data was usable;
- what data was missing;
- what assumptions were made;
- whether the audit is ready for executive review;
- what export would make the next run stronger.
