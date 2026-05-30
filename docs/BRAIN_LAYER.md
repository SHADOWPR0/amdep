# AmDep Brain Layer

The Brain Layer gives the optimizer risk signals without giving ML authority it has not earned.

## Operating Logic

1. **Rules define reality.**
   Skills, certifications, headcount, supervisor capacity, geography, and asset availability are hard operating facts.

2. **ML predicts hidden risk.**
   Synthetic demo models estimate attrition/burden risk, delay risk, no-show risk, crew compatibility, and robotics suitability.

3. **The optimizer makes constrained decisions.**
   OR-Tools consumes rules and risk scores. Certifications stay hard. Risk scores become costs and rewards.

4. **The dispatcher approves or overrides.**
   Humans keep authority. The product explains why a recommendation was made.

5. **Overrides become training data.**
   Override reason, operator identity, timestamp, and eventual outcome become future labels.

## V1 Models

- attrition/burden risk classifier
- job delay risk classifier
- crew compatibility scorer
- no-show risk classifier
- robotics suitability scorer

## Why Synthetic First

Synthetic models let the product demonstrate the shape of the workflow before customer data exists. They should be labeled clearly and treated as scoring heuristics.

## Future Neural Roadmap

Do not overbuild neural networks in V1.

When customer data justifies it, add:

- graph neural networks for personnel-job-supervisor relationships
- temporal models for fatigue, churn, and sequencing
- computer vision for robotics and site intelligence
- contextual bandits for controlled dispatch experimentation

