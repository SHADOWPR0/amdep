# Integration Strategy

AmDep should not ask a contractor to rip out its operating system.

The fastest adoption path is:

1. Export data from the current stack.
2. Normalize it into the AmDep ontology.
3. Run the audit and optimizer.
4. Return a review queue of recommended assignments.
5. Let a dispatcher approve, reject, or override.
6. Push approved decisions back only through customer-approved integration paths.

## Known Stack Posture

| Stack | Best first use | Integration surface |
| --- | --- | --- |
| Generic CSV / Excel / BI | Fastest audit path | CSV export/import, data warehouse tables |
| Procore Resource Planning | Workforce assignments and project context | Resource Planning exports/API/sandbox |
| ServiceTitan | Jobs, appointments, technicians, shifts, capacity | Developer APIs and tenant auth |
| HCSS HeavyJob | Heavy civil timecards, equipment, foremen, job cost context | HeavyJob API scopes |
| Sage Construction Management | Labor/equipment timecards, project financials | REST API, OAuth, webhooks |
| Trimble Viewpoint Vista | ERP project/labor/equipment truth | Vista API/customer exports |
| Autodesk Construction Cloud | Project/workflow context | Autodesk Platform Services APIs |
| AccuLynx | Roofing/storm restoration job operations | API key, Zapier, calendar/job exports |

## Review-First Writeback

The public MVP intentionally avoids blind writeback.

Every integration export is a recommendation queue with:

- recommendation ID
- proposed worker/job assignment
- reason
- route burden
- risk terms
- approval status
- target stack fields

Production connectors should preserve:

- dispatcher approval
- override reason
- timestamp
- source system ID
- before/after assignment state
- user identity

That override trail is training data. It is also political safety for the operation.

## Where The Moat Lives

The durable product edge is not a dashboard.

It is:

- normalized field-ops ontology
- customer-specific policy calibration
- validated risk models
- dispatch override learning
- practical constraints learned from operators
- integrations that respect systems of record
- benchmark corpus across deployment-heavy operators

The public repo proves the engine shape. Production value comes from calibration, deployment, and trust.
