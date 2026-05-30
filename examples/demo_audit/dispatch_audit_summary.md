# American Deployment Dispatch Audit

_Algorithm-first MVP packet. Synthetic risk scores are demo-only unless customer outcome labels were provided._

## Owner Brief

- Baseline route burn: 203.8 hrs/day
- Optimized route burn: 58.5 hrs/day
- Dispatch delta: 145.3 hrs/day
- Annualized route savings: $2,797,943
- Jobs fully staffed after hard constraints: 71%

## Calibration Gym

- Method: `synthetic_risk_search`
- Baseline policy cost: 59,537
- Calibrated policy cost: 19,957
- Policy-cost improvement: 66%
- Caveat: Weights were searched against synthetic Brain Layer risk because no real outcome labels were provided.

## Monday Morning Moves

1. Review and approve the top route swaps before changing headcount.
2. Rebalance supervisors whose active work is geographically scattered.
3. Fix the most constrained certifications before they block more jobs.
4. Use robotics or capture units on inspection-heavy sites to remove avoidable trips.

## Top Avoidable Bad Deployments

- Luke Hughes to Naples Restoration 19: Drove 143 minutes despite a qualified worker within 10 minutes. Annualized hit: $85,381.
- Nate Foster to Naples Utilities 44: Drove 131 minutes despite a qualified worker within 9 minutes. Annualized hit: $78,432.
- Jack Hayes to Naples Roofing 28: Drove 133 minutes despite a qualified worker within 21 minutes. Annualized hit: $72,136.
- Troy Foster to Bonita Springs / Estero Telecom/Fiber 49: Drove 112 minutes despite a qualified worker within 12 minutes. Annualized hit: $64,387.
- Cole Foster to Cape Coral Utilities 55: Drove 89 minutes despite a qualified worker within 7 minutes. Annualized hit: $52,602.
- Luke Hughes to Lehigh Acres / Immokalee Electrical 35: Drove 92 minutes despite a qualified worker within 12 minutes. Annualized hit: $51,067.
- June Hayes to Cape Coral Commercial Construction 13: Drove 98 minutes despite a qualified worker within 22 minutes. Annualized hit: $48,740.
- Nora Walker to Fort Myers Commercial Construction 45: Drove 87 minutes despite a qualified worker within 12 minutes. Annualized hit: $48,009.

## What To Give AmDep Next

- 4-12 weeks of assignments
- actual start/end times
- missed-window, overtime, no-show, delay, callback/rework, and turnover outcomes
- dispatcher overrides and override reasons
- job revenue or gross margin if available

That outcome history is what turns the policy gym from synthetic risk scoring into customer-calibrated dispatch intelligence.