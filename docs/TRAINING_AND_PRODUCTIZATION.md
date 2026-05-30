# Training And Productization

## 1. Audit Mode

Use historical schedules first. Import customer assignments, personnel, jobsites, skills, certifications, supervisor mappings, crews, vehicles, and equipment.

The first productized artifact is the CLI audit packet:

```bash
python -m amdep.run_audit \
  --workers customer_workers.csv \
  --jobsites customer_jobsites.csv \
  --assignments customer_assignments.csv \
  --assets customer_assets.csv \
  --output reports/customer_audit
```

Deliver:

- route burn baseline
- deployment waste map
- bad assignment ranking
- certification bottleneck map
- supervisor spread analysis
- burden-risk table
- ROI range

## 2. Calibration Mode

Add outcomes:

- late arrivals
- overtime events
- delays
- callbacks
- rework
- turnover
- safety proxies
- asset idle time
- override decisions

Train boring models first. Compare against rules and simple baselines. Calibrate probabilities. Show error analysis before confidence.

## 3. Live Deployment Mode

Run daily recommendations:

- qualified personnel options
- optimized deployment
- rejected alternatives
- binding constraints
- expected route burn
- burden impact
- supervisor load
- robotics candidates

Dispatchers approve, edit, or override.

## 4. Continuous Learning

Every live decision should create a learning record:

- recommendation
- operator action
- override reason
- actual assignment
- outcome
- late changes
- weather/context
- final cost and timing

## Productization Priorities

1. CSV audit runner and generated operator packet.
2. Schema validation and messy-data normalization.
3. Dispatch replay and policy scoring.
4. Calibration gym using historical outcomes.
5. Customer-specific ontology mapping.
6. Batch optimizer API.
7. Lightweight reviewer UI.
8. Geocoding and address normalization.
9. Audit log and override capture.
10. Integrations with existing field systems.
11. Real database and durable runs.
12. Robotics/fleet deployment API.
