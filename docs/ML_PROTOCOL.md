# ML Protocol

AmDep V1 includes synthetic demonstration models. They are useful for proving the architecture, not for claiming customer performance.

## Demo Models

Implemented in:

- `amdep/brain.py`
- `amdep/features.py`
- `amdep/train_synthetic_models.py`
- `amdep/model_registry.py`

Synthetic models:

- attrition/burden risk classifier
- job delay risk classifier
- crew compatibility scorer
- no-show risk classifier
- robotics suitability scorer

Model families:

- LogisticRegression
- RandomForestClassifier
- HistGradientBoostingClassifier

## Real Targets

Once customer data exists, AmDep can train against:

- quit within 90 days
- late arrival
- overtime event
- project delay
- callback/rework event
- productivity shortfall
- safety incident proxy
- asset idle time
- robotics deployment success

## Feature Families

- commute features
- region features
- skill and certification match
- supervisor features
- crew history
- job phase
- weather
- schedule volatility
- workload
- overtime
- asset utilization
- robotics readiness

## Validation Rules

- use time-based train/test splits
- prevent leakage from future outcomes
- keep a logistic regression baseline
- compare tree models only after the baseline is defensible
- calibrate probabilities before exposing them
- inspect errors by region, supervisor, crew, project type, and season
- track feature importance
- prepare SHAP-compatible explanations
- monitor drift
- log dispatcher overrides and outcomes

## No Fake Accuracy

Do not show accuracy, AUC, lift, or savings claims from synthetic training as proof. Synthetic metrics test code mechanics. Customer metrics test reality.

