# American Deployment

**American Deployment / AmDep** is an algorithm-first deployment audit and project-staff optimization engine for commercial builders.

Tagline: **Project-staff deployment intelligence for commercial builders.**

AmDep is a deployment intelligence layer: it ingests project staff rosters, jobsites, assignments, skills, certifications, project leaders, teams, equipment, and outcomes; replays current staffing behavior; trains demo risk models; runs constrained optimization; and writes an audit packet operators can review.

The product thesis is direct: commercial builders leak value when qualified project staff, superintendents, PMs, safety, QA/QC, and closeout resources are deployed with incomplete information. AmDep turns that into measurable evidence across management capacity, retention / rehiring, role fit, OSHA / certification coverage, schedule variance, QA/rework, change-order/admin drag, margin fade, and downstream compounding effects.

## What You Can Run

```bash
git clone <repo-url>
cd amdep
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_demo.sh
```

Or run the audit command directly:

```bash
python -m amdep.run_audit \
  --workers data/sample_workers.csv \
  --jobsites data/sample_jobsites.csv \
  --assignments data/sample_assignments.csv \
  --assets data/sample_assets.csv \
  --output reports/demo_audit \
  --trials 18
```

Open:

```text
reports/demo_audit/dispatch_audit_summary.html
reports/demo_audit/dispatch_audit_summary.md
```

No API keys. No paid services. No customer data required for the demo.

## Web Command Center Demo

For the cross-platform buyer demo, run:

```bash
python -m amdep.web_demo
```

That command refreshes the synthetic audit packet, serves the responsive web app, and opens:

```text
http://127.0.0.1:8088/web/index.html
```

The demo is browser-based so it works across macOS, Windows, Linux, ChromeOS, iOS, Android, tablets, and desktops. It is intentionally not a native mobile app. Operations reviews on desktop or tablet; project leaders can use the same PWA-style interface on mobile.

If you only want to inspect a prebuilt synthetic packet, open:

```text
examples/demo_audit/dispatch_audit_summary.html
```

## Core Outputs

The audit packet writes:

- `dispatch_audit_summary.html` static executive packet
- `dispatch_audit_summary.md` markdown packet
- `baseline_assignments.csv`
- `optimized_assignments.csv`
- `top_waste_findings.csv`
- `personnel_burden.csv`
- `job_staffing_status.csv`
- `robotics_plan.csv`
- `calibration_trials.csv`
- `recommended_weights.csv`
- `validation_report.csv`
- `integrations/` adapter-ready recommendation exports

The HTML file is the fastest thing to show an operator. The CSVs are the proof layer.

## Three-Layer Engine

1. **Ontology Layer**
   Personnel, supervisors, crews, jobsites, equipment, vehicles, robotic assets, skills, certifications, regions, assignments, and constraints.

2. **Optimization Layer**
   OR-Tools CP-SAT optimizer with hard constraints for certifications, one assignment per person per day, staffing targets, and supervisor capacity pressure. Soft costs include commute, skill fit, fatigue, retention burden, no-show risk, crew compatibility, job urgency, and robotics suitability.

3. **Learning Layer**
   Synthetic scikit-learn models demonstrate risk scoring for burden, delay, no-show, team continuity, and remote verification suitability. These are clearly marked as synthetic until trained and validated on customer outcomes.

## Integration Posture

AmDep is designed to plug into existing contractor software stacks instead of replacing them on day one.

The Community Edition ships adapter-ready exports for:

- Generic CSV / Excel / BI
- Procore Resource Planning
- ServiceTitan
- HCSS HeavyJob
- Sage Construction Management
- Trimble Viewpoint Vista
- Autodesk Construction Cloud
- AccuLynx
- Foundry-style ontology imports

The public repo does not include authenticated production connectors. It produces review queues and payload drafts that a customer-approved integration can push back into systems of record.

See [docs/INTEGRATION_STRATEGY.md](docs/INTEGRATION_STRATEGY.md).

## Customer Data Contract

Minimum useful fields:

- personnel roster
- home ZIP, depot, region, or coordinates
- skills
- certifications
- supervisor mapping
- crew mapping
- jobsites or work orders
- job locations
- required skills/certifications
- assignment history
- equipment/vehicle availability

High-value calibration fields:

- scheduled start/end
- actual start/end
- overtime
- no-show
- late arrival
- missed window
- delay
- callback/rework
- productivity shortfall
- turnover or quit-within-90-days label
- operations override and override reason

## What The Demo Proves

The demo proves the workflow:

- ingest data
- validate schemas
- replay current assignments
- quantify route burn
- identify closer qualified alternatives
- estimate burden risk
- run constrained optimization
- calibrate policy weights with a lightweight gym
- generate recommendation exports for existing software stacks

For a Kyle-facing explanation of the sample data, model/optimizer layer, economic methodology, and pilot posture, see [docs/DEMO_METHODOLOGY_AND_DEPLOYMENT.md](docs/DEMO_METHODOLOGY_AND_DEPLOYMENT.md).

## What It Does Not Prove

This repository uses randomized commercial GC staffing data. Modeled impact is directional until validated against historical assignments, schedules, outcomes, overrides, and job-cost records.

Real predictive value requires customer history, outcome labels, time-based validation, calibration, drift monitoring, and human override tracking.

## License

Community Edition is MIT-licensed. See [LICENSE](LICENSE).

Do not put private customer data, proprietary calibrated policies, production connectors, or commercial model weights into a public fork. See [COMMERCIAL.md](COMMERCIAL.md).

## Contact

For audits, integration pilots, or commercial licensing, DM **SHADOWPR0** on X.
