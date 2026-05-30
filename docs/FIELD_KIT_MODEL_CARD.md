# AMDEP Field Kit Model Card

This document explains what the Field Kit runs during a local read-only pilot.

## Status

The Field Kit uses the AMDEP Community Edition engine. It is a working deployment audit and optimization workflow, but it is not a customer-trained production model until it has been calibrated against that customer's historical outcomes.

## Inputs

Minimum useful intake:

- people roster with IDs, roles, skills, certifications, and home base or location;
- active jobs/projects with IDs, names, required headcount, required skills/certifications, and job location;
- current assignments when available;
- assets/equipment when available.

High-value calibration fields:

- late arrival, no-show, overtime, missed-window, delay, callback/rework, productivity shortfall, safety proxy, and quit-within-90-days labels;
- operation overrides and override reasons;
- scheduled and actual start/end times;
- job-cost, gross margin, or cost-to-complete movement when approved.

## Feature Layer

Defined in `amdep/features.py`.

The engine builds worker-job pair features:

- commute minutes;
- skill match score;
- certification match score;
- home/job region match;
- fatigue, reliability, overtime, and long-haul history;
- crew affinity;
- job urgency, weather risk, schedule volatility, inspection need, and required headcount;
- supervisor flag and robot-ready job flag.

## Synthetic Brain Layer

Defined in `amdep/brain.py`.

For demos and first-run pilots, the Field Kit trains synthetic models on the customer-shaped entity graph:

- attrition risk: logistic regression;
- delay risk: histogram gradient boosting;
- crew compatibility: random forest;
- no-show risk: logistic regression;
- robotics suitability: random forest.

These models create cost and reward signals for the optimizer. They are transparent demo signals until replaced or calibrated with customer outcome labels.

## Optimization Layer

Defined in `amdep/optimizer.py`.

AMDEP uses OR-Tools CP-SAT when available, with a deterministic greedy fallback. Hard constraints include:

- required certifications;
- one assignment per person per day;
- target headcount by job;
- supervisor span pressure.

Soft costs include:

- commute burden;
- skill gap;
- certification gap;
- retention / attrition risk;
- no-show / workload risk;
- fatigue and overtime;
- crew incompatibility;
- delay risk weighted by job urgency;
- robotics suitability reward.

## Default Weights

Defined in `config.py`.

```text
commute_reduction: 1.0
skill_fit: 1.0
certification_strictness: 1.0
supervisor_balance: 0.8
retention_protection: 0.9
crew_cohesion: 0.7
overtime_reduction: 0.8
robotics_utilization: 0.5
job_urgency: 0.8
```

## Calibration

Defined in `amdep/calibration.py`.

Each run searches candidate optimizer weights. If customer outcome columns are present, policy cost uses those observed outcomes. If outcome columns are missing, policy cost uses synthetic risk terms and labels that caveat.

Each audit writes:

- `calibration_trials.csv`: candidate policies and policy costs;
- `recommended_weights.csv`: selected weights for that audit run;
- `validation_report.csv`: schema and data-quality findings.

## Economic Model

Defined in `amdep/metrics.py`.

The Field Kit estimates organizational value from before/after movement across:

- route capacity;
- coverage gaps;
- retention and rehiring exposure;
- role fit and certification fit;
- burden reduction;
- QA/rework/closeout support;
- schedule variance;
- change-order/admin drag;
- margin fade;
- admin operating model load;
- downstream compounding effects.

The output is directional until validated against customer history and finance-approved assumptions.

## Production Upgrade Path

1. Run the Field Kit on copied exports.
2. Confirm schema mappings with operations.
3. Add 4-12 weeks of assignment history and outcomes.
4. Use time-based train/test splits.
5. Calibrate probabilities.
6. Track overrides and outcomes.
7. Promote only approved connectors and writeback paths.
