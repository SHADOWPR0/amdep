"""Report generation and CSV export for AmDep."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from amdep.utils import dollars, hours, repo_root


def generate_markdown_roi_report(
    *,
    naive_kpis: dict[str, float],
    optimized_kpis: dict[str, float],
    comparison: dict[str, float],
    roi_cases: dict[str, dict[str, float]],
    wake_up_calls: list[str],
    waste_findings: pd.DataFrame,
    output_dir: Path | None = None,
) -> Path:
    report_dir = output_dir or repo_root() / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "example_roi_report.md"
    top_findings = waste_findings.head(8).to_dict("records") if not waste_findings.empty else []
    lines = [
        "# American Deployment ROI Report",
        "",
        "_Synthetic commercial GC staffing report. Modeled impact is directional until calibrated on real operating data._",
        "",
        "## Executive Snapshot",
        "",
        f"- Baseline route burn: {hours(naive_kpis['total_route_burn_hours'])}/day",
        f"- Optimized route burn: {hours(optimized_kpis['total_route_burn_hours'])}/day",
        f"- Recovered project-team capacity: {hours(comparison['dispatch_delta'])}/day",
        f"- Base-case modeled annual impact: {dollars(roi_cases['base']['total_annual_savings'])}",
        "",
        "## Operator Wake-Up Call",
        "",
    ]
    lines.extend([f"- {item}" for item in wake_up_calls])
    lines.extend(["", "## Savings Cases", ""])
    for case, values in roi_cases.items():
        lines.extend(
            [
                f"### {case.title()}",
                f"- Route impact: {dollars(values['annual_route_savings'])}",
                f"- Burden / retention proxy impact: {dollars(values['burden_retention_savings'])}",
                f"- Remote verification impact: {dollars(values['robotics_inspection_savings'])}",
                f"- Total modeled annual impact: {dollars(values['total_annual_savings'])}",
                "",
            ]
        )
    lines.extend(["## Top Assignment Conflicts", ""])
    if top_findings:
        for finding in top_findings:
            lines.append(
                f"- {finding['assigned_worker']} to {finding['job_name']}: {finding['reason']} "
                f"Modeled annualized impact: {dollars(finding['annualized_cost'])}."
            )
    else:
        lines.append("- No high-severity waste findings in this scenario.")
    lines.extend(
        [
            "",
            "## What This Proves",
            "",
            "The demo proves the deployment problem is measurable and optimizable under explicit assumptions. Real predictive value requires customer data, outcome labels, and time-based validation.",
            "",
            f"_Generated {datetime.now().isoformat(timespec='seconds')}._",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def export_csvs(output_dir: Path | None = None, **frames: pd.DataFrame) -> list[Path]:
    report_dir = output_dir or repo_root() / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, frame in frames.items():
        path = report_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths.append(path)
    return paths
