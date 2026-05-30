# Deployment Ontology

AmDep models field operations as typed entities and relationships. The ontology is code-first in `amdep/ontology.py` and graph-ready through `amdep/graph_analysis.py`.

## Entities

- **Personnel:** field worker, trade specialist, project engineer, superintendent, assistant superintendent, robotics tech.
- **Supervisor:** personnel with management capacity and geographic responsibility.
- **Crew:** group of workers with shared history and cohesion score.
- **Jobsite:** physical work location with phase, urgency, staffing demand, required skills, certifications, and equipment.
- **Skill:** trade or operating capability.
- **Certification:** hard requirement such as OSHA 30, confined space, electrical journeyman, lift operation, or robotics operations.
- **Equipment:** trucks, lifts, cameras, generators, fiber test kits, and field tools.
- **RoboticAsset:** drones, rovers, site capture units, inspection robots, and material movement assets.
- **Vehicle:** field mobility asset assigned to a person or crew.
- **Assignment:** personnel-job link that creates commute burden, fatigue risk, throughput impact, and cost.
- **DeploymentDay:** daily assignment set.
- **Region:** geography around Southwest Florida / Florida Gulf Coast.
- **Constraint:** hard or soft rule that governs optimizer behavior.
- **OptimizationResult:** solver status, objective value, staffing gaps, and notes.

## Relationships

- Personnel lives_in Region
- Personnel has_skill Skill
- Personnel has_cert Certification
- Personnel assigned_to Jobsite
- Personnel reports_to Supervisor
- Personnel compatible_with Crew
- Supervisor manages Personnel
- Jobsite requires Skill
- Jobsite requires Certification
- Jobsite requires Equipment
- Jobsite can_accept RoboticAsset
- Equipment assigned_to Jobsite
- Vehicle assigned_to Personnel/Crew
- Assignment creates commute burden
- Assignment creates fatigue risk
- Assignment affects retention risk
- Assignment affects project throughput

## Hard Constraints

- required certifications must be met
- personnel assigned max once per day
- job headcount should be met when qualified capacity exists
- supervisor capacity pressure is modeled
- robotic assets must match compatible sites
- unavailable equipment cannot be assigned

## Soft Constraints

- shorter commute preferred
- mission fit preferred
- crew cohesion preferred
- avoid repeated long-haul burden
- avoid high fatigue personnel
- avoid schedule churn
- keep supervisors near logical geography
- deploy robotics where they reduce inspection and travel burden

## Graph Analytics

NetworkX exposes:

- overloaded supervisors
- geographic mismatch clusters
- certification bottlenecks
- workers with repeated bad deployment burden
- underutilized personnel
- high-value reassignment opportunities
- crew cohesion breakdowns
- asset underutilization
- future robotics deployment candidates

