# Dispatch Optimization Gym

AmDep is strongest as an algorithmic audit and training package first.

The gym answers one practical question:

**Given the crews, jobs, geography, constraints, and outcomes this operator actually has, what dispatch policy performs better than the current one?**

## Pipeline

1. **Ingest**
   Load workers, jobsites, assets, and historical assignments from CSVs.

2. **Validate**
   Check required schema, duplicate IDs, missing coordinates, unknown assignment references, and whether outcome columns exist.

3. **Replay**
   Score the customer’s current or historical assignment pattern.

4. **Brain Layer**
   Generate demo risk scores for attrition/burden, delay, no-show, crew compatibility, and robotics suitability.

5. **Calibration Gym**
   Search optimizer weights. If outcome columns exist, score policies against observed outcomes. If outcomes are missing, score against synthetic risk and label that caveat.

6. **Optimize**
   Run OR-Tools CP-SAT to create a constrained counterfactual deployment.

7. **Report**
   Write a packet: summary, calibration trials, recommended weights, optimized assignments, top waste findings, personnel burden, staffing status, and robotics plan.

## Outcome Columns

The gym becomes materially better when assignments include:

- `late_arrival`
- `overtime_event`
- `project_delay`
- `callback_rework_event`
- `productivity_shortfall`
- `safety_incident_proxy`
- `no_show`
- `quit_within_90_days`
- `dispatcher_override`
- `override_reason`
- actual start/end times
- actual duration

These fields let AmDep tune policy around what the operator actually cares about.

## Why This Beats A Dashboard-First MVP

Contractors do not need another screen first. They need proof that better dispatch decisions exist.

The gym creates that proof:

- baseline replay
- optimized counterfactual
- explicit constraints
- measurable route burn
- policy calibration
- Monday morning actions

The UI should remain a reviewer surface until the engine earns the right to become a daily workflow.

