# Algorithm Productization

The algorithm is the product.

The user experience should be simple:

1. Upload or export field-ops data.
2. Run the audit.
3. Review the dispatch delta.
4. Approve practical recommendations.
5. Feed overrides and outcomes back into the policy.

The backend can be serious without making the user operate an optimization lab.

## V1 Product Boundary

V1 should stay narrow:

- one-day and short-horizon dispatch audits
- personnel/job/equipment ontology
- constrained assignment optimizer
- synthetic Brain Layer demo
- calibration gym
- recommendation exports
- static audit packet

Do not overbuild neural networks in V1. Do not lead with autonomous dispatch. Do not make unsupported savings claims.

## Calibration Gym

The Community Edition uses lightweight random search over optimizer weights.

Production can upgrade this to:

- Optuna policy search
- Bayesian optimization
- company-specific constraints
- dispatcher-specific policy profiles
- objective functions tied to real outcomes
- scenario simulation across weather, backlog, and surge events

## Customer-Trained Brain Layer

Synthetic models are placeholders for the workflow.

Real models need:

- time-based train/test splits
- leakage prevention
- calibration
- drift monitoring
- feature importance / SHAP-ready explainability
- human override tracking
- periodic retraining

Targets:

- no-show
- late arrival
- overtime event
- missed window
- project delay
- callback/rework
- productivity shortfall
- quit within 90 days
- safety incident proxy
- robotics deployment success

## Production Architecture

Production should split cleanly:

- ingestion adapters
- canonical ontology store
- feature builder
- model registry
- optimizer service
- recommendation review queue
- writeback adapter
- audit/report generator
- monitoring and drift layer

The public repo demonstrates these boundaries without carrying private customer data or commercial policies.
