"""End-to-end dispatch audit packet generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from amdep.data_contracts import validate_frames
from amdep.dispatch_gym import DispatchAuditResult, run_dispatch_audit
from amdep.ingestion import load_customer_bundle, normalize_bundle
from amdep.integrations.exports import export_integration_bundle
from amdep.reports import export_csvs
from amdep.utils import dollars, hours, pct


def run_csv_audit(
    *,
    workers_path: Path,
    jobsites_path: Path,
    output_dir: Path,
    assignments_path: Path | None = None,
    assets_path: Path | None = None,
    seed: int = 1776,
    calibration_trials: int = 18,
) -> DispatchAuditResult:
    frames = load_customer_bundle(
        workers_path=workers_path,
        jobsites_path=jobsites_path,
        assignments_path=assignments_path,
        assets_path=assets_path,
    )
    validation = validate_frames(frames)
    output_dir.mkdir(parents=True, exist_ok=True)
    validation.to_frame().to_csv(output_dir / "validation_report.csv", index=False)
    normalized = normalize_bundle(frames)
    result = run_dispatch_audit(
        workers=normalized["workers"],
        jobs=normalized["jobsites"],
        assets=normalized["assets"],
        baseline_assignments=normalized.get("assignments"),
        seed=seed,
        calibration_trials=calibration_trials,
    )
    write_audit_packet(result, output_dir=output_dir)
    return result


def write_audit_packet(result: DispatchAuditResult, *, output_dir: Path) -> list[Path]:
    """Write markdown + CSV packet for a deployment waste audit."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = export_csvs(
        output_dir,
        baseline_assignments=result.baseline_assignments,
        optimized_assignments=result.optimized_assignments,
        top_waste_findings=result.waste_findings,
        personnel_burden=result.personnel_burden,
        job_staffing_status=result.job_staffing_status,
        robotics_plan=result.robotics_plan,
        calibration_trials=result.calibration.trials,
        recommended_weights=pd.DataFrame(
            [{"weight": key, "value": value} for key, value in result.calibration.recommended_weights.items()]
        ),
    )
    summary_path = output_dir / "dispatch_audit_summary.md"
    summary_path.write_text(render_audit_summary(result), encoding="utf-8")
    paths.append(summary_path)
    html_path = output_dir / "dispatch_audit_summary.html"
    html_path.write_text(render_audit_html(result), encoding="utf-8")
    paths.append(html_path)
    paths.extend(export_integration_bundle(result, output_dir))
    return paths


def render_audit_summary(result: DispatchAuditResult) -> str:
    top_waste = result.waste_findings.head(8).to_dict("records") if not result.waste_findings.empty else []
    lines = [
        "# American Deployment Project Staff Audit",
        "",
        "_Synthetic commercial GC staffing packet. Directional output until calibrated against customer outcomes._",
        "",
        "## Operations Brief",
        "",
        f"- Baseline route burn: {hours(result.baseline_kpis['total_route_burn_hours'])}/day",
        f"- Optimized route burn: {hours(result.optimized_kpis['total_route_burn_hours'])}/day",
        f"- Recovered project-team capacity: {hours(result.comparison['dispatch_delta'])}/day",
        f"- 18-month deployment impact: {dollars(result.deployment_economics['implementation_horizon_impact'])}",
        f"- Annualized deployment run-rate: {dollars(result.deployment_economics['annual_deployment_run_rate'])}",
        f"- Projects fully staffed after hard constraints: {pct(result.optimized_kpis['jobs_fully_staffed_pct'])}",
        "",
        "## Calibration Gym",
        "",
        f"- Method: `{result.calibration.method}`",
        f"- Baseline policy cost: {result.calibration.baseline_cost:,.0f}",
        f"- Calibrated policy cost: {result.calibration.calibrated_cost:,.0f}",
        f"- Policy-cost improvement: {pct(result.calibration.improvement_pct)}",
        f"- Caveat: {result.calibration.caveat}",
        "",
        "## Monday Morning Moves",
        "",
        "1. Review and approve the top project-staff swaps before changing headcount.",
        "2. Rebalance superintendents and PMs whose active work is geographically scattered.",
        "3. Fix the most constrained safety, QA/QC, and project-phase certifications before they block more projects.",
        "4. Use progress capture on inspection-heavy or closeout-heavy sites to remove avoidable trips.",
        "",
        "## Top Assignment Conflicts",
        "",
    ]
    if top_waste:
        for finding in top_waste:
            lines.append(
                f"- {finding['assigned_worker']} to {finding['job_name']}: "
                f"{finding['reason']} Annualized hit: {dollars(finding['annualized_cost'])}."
            )
    else:
        lines.append("- No high-severity waste findings in this run.")
    lines.extend(
        [
            "",
            "## Data Needed For Real Training",
            "",
            "- 4-12 weeks of assignments",
            "- actual start/end times",
            "- missed-window, overtime, no-show, delay, callback/rework, and turnover outcomes",
            "- operations overrides and override reasons",
            "- job revenue or gross margin if available",
            "",
            "That outcome history is what turns the synthetic policy search into customer-calibrated deployment intelligence.",
        ]
    )
    return "\n".join(lines)


def render_audit_html(result: DispatchAuditResult) -> str:
    """Render a static executive packet that can be opened without a web server."""
    top_waste = result.waste_findings.head(8).to_dict("records") if not result.waste_findings.empty else []
    calibration_rows = result.calibration.trials.head(6).to_dict("records") if not result.calibration.trials.empty else []
    style = """
    :root {
      --ink: #17212b;
      --navy: #10243a;
      --steel: #4d5c68;
      --line: #d8d0c3;
      --paper: #f7f2e8;
      --card: #fffdf8;
      --orange: #c8511d;
      --green: #1f7a4f;
      --gold: #9b7b34;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--paper);
      line-height: 1.45;
    }
    .shell { max-width: 1180px; margin: 0 auto; padding: 42px 26px 64px; }
    .hero {
      border: 1px solid var(--line);
      background: linear-gradient(135deg, #fffdf8 0%, #f0e7d8 100%);
      padding: 34px;
      box-shadow: 0 18px 40px rgba(23, 33, 43, 0.10);
    }
    .eyebrow { color: var(--orange); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; font-size: 12px; }
    h1 { margin: 8px 0 10px; font-size: clamp(34px, 5vw, 64px); line-height: .94; letter-spacing: -0.03em; }
    h2 { margin: 34px 0 14px; font-size: 24px; }
    p { color: var(--steel); max-width: 760px; }
    .grid { display: grid; gap: 14px; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 22px; }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      padding: 18px;
      min-height: 118px;
    }
    .label { color: var(--steel); font-size: 13px; font-weight: 700; }
    .value { margin-top: 12px; color: var(--navy); font-size: 30px; font-weight: 850; letter-spacing: -0.04em; }
    .value.green { color: var(--green); }
    .value.orange { color: var(--orange); }
    .section {
      background: var(--card);
      border: 1px solid var(--line);
      padding: 24px;
      margin-top: 18px;
    }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { padding: 11px 10px; border-bottom: 1px solid #e7dfd1; text-align: left; vertical-align: top; }
    th { color: var(--navy); font-size: 12px; text-transform: uppercase; letter-spacing: .06em; }
    .callout {
      border-left: 5px solid var(--orange);
      background: #fff7ed;
      padding: 16px 18px;
      margin-top: 18px;
      font-weight: 760;
    }
    .fineprint { margin-top: 30px; font-size: 13px; color: #6e6a63; }
    @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
    @media (max-width: 560px) { .grid { grid-template-columns: 1fr; } .hero, .section { padding: 20px; } }
    """
    waste_rows = "\n".join(
        f"<tr><td>{_esc(row.get('assigned_worker', ''))}</td><td>{_esc(row.get('job_name', ''))}</td>"
        f"<td>{float(row.get('assigned_commute_minutes', 0)):.0f} min</td>"
        f"<td>{_esc(row.get('closer_qualified_name', ''))}</td>"
        f"<td>${float(row.get('annualized_cost', 0)):,.0f}</td>"
        f"<td>{_esc(row.get('reason', ''))}</td></tr>"
        for row in top_waste
    )
    if not waste_rows:
        waste_rows = "<tr><td colspan='6'>No high-severity waste findings in this run.</td></tr>"
    trial_rows = "\n".join(
        f"<tr><td>{int(row.get('trial', 0))}</td><td>{float(row.get('policy_cost', 0)):,.0f}</td>"
        f"<td>{_esc(row.get('solver_status', ''))}</td><td>{float(row.get('commute_reduction', 0)):.2f}</td>"
        f"<td>{float(row.get('retention_protection', 0)):.2f}</td><td>{float(row.get('job_urgency', 0)):.2f}</td></tr>"
        for row in calibration_rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>American Deployment Project Staff Audit Packet</title>
  <style>{style}</style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">American Deployment Community Edition</div>
      <h1>Project staff audit packet</h1>
      <p>Algorithm-first deployment intelligence for commercial builders. This packet replays baseline project staffing, runs constrained optimization, and produces integration-ready recommendations for operations review.</p>
      <div class="grid">
        <div class="card"><div class="label">Baseline route burn</div><div class="value">{hours(result.baseline_kpis['total_route_burn_hours'])}</div></div>
        <div class="card"><div class="label">Optimized route burn</div><div class="value green">{hours(result.optimized_kpis['total_route_burn_hours'])}</div></div>
        <div class="card"><div class="label">Recovered capacity</div><div class="value orange">{hours(result.comparison['dispatch_delta'])}</div></div>
        <div class="card"><div class="label">18-month deployment impact</div><div class="value green">{dollars(result.deployment_economics['implementation_horizon_impact'])}</div></div>
      </div>
      <div class="callout">The current staffing pattern carries {hours(result.baseline_kpis['total_route_burn_hours'])}/day in route burden before accounting for coverage gaps, role fit, superintendent/PM load, OSHA/safety coverage, QA support, punch, closeout burden, and schedule risk. The constraint-checked plan recovers {pct(result.comparison['route_burn_recovery_pct'])} of route load while preserving role, OSHA/certification, capacity, and project-phase rules. Annualized deployment run-rate is {dollars(result.deployment_economics['annual_deployment_run_rate'])}; 18-month implementation impact is {dollars(result.deployment_economics['implementation_horizon_impact'])}.</div>
    </section>

    <section class="section">
      <h2>Top assignment conflicts</h2>
      <table>
        <thead><tr><th>Assigned worker</th><th>Job</th><th>Commute</th><th>Closer qualified option</th><th>Annualized hit</th><th>Reason</th></tr></thead>
        <tbody>{waste_rows}</tbody>
      </table>
    </section>

    <section class="section">
      <h2>Calibration gym</h2>
      <p>Method: <strong>{_esc(result.calibration.method)}</strong>. { _esc(result.calibration.caveat) }</p>
      <table>
        <thead><tr><th>Trial</th><th>Policy cost</th><th>Solver</th><th>Commute</th><th>Retention</th><th>Urgency</th></tr></thead>
        <tbody>{trial_rows}</tbody>
      </table>
    </section>

    <section class="section">
      <h2>Monday morning moves</h2>
      <ol>
        <li>Review the top project-staff swaps before changing headcount.</li>
        <li>Rebalance superintendents and PMs whose work is geographically scattered.</li>
        <li>Fix constrained safety, QA/QC, and project-phase certifications before they block more projects.</li>
        <li>Use progress capture on inspection-heavy or closeout-heavy sites to remove avoidable trips.</li>
      </ol>
    </section>

    <p class="fineprint">Synthetic demo data and synthetic risk scores are directional. Customer-calibrated performance requires historical schedules, outcomes, operations overrides, job-cost records, and time-based validation.</p>
  </main>
</body>
</html>"""


def _esc(value: object) -> str:
    import html

    return html.escape("" if value is None else str(value))
