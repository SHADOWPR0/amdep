"""Transparent ROI model for AmDep deployment scenarios."""

from __future__ import annotations

from pydantic import BaseModel, Field

from config import DEFAULT_ROI_ASSUMPTIONS


class ROIAssumptions(BaseModel):
    loaded_labor_cost_per_hour: float = Field(default=55.0, ge=0)
    vehicle_cost_per_hour: float = Field(default=22.0, ge=0)
    workdays_per_year: int = Field(default=250, ge=1)
    impact_realization_factor: float = Field(default=0.35, ge=0, le=1)
    replacement_cost_per_lost_employee: float = Field(default=18_000.0, ge=0)
    supervisor_cost_per_hour: float = Field(default=85.0, ge=0)
    robotic_asset_cost_per_day: float = Field(default=300.0, ge=0)
    inspection_rework_cost: float = Field(default=2_500.0, ge=0)
    attrition_reduction_sensitivity: float = Field(default=0.25, ge=0, le=1)

    @classmethod
    def defaults(cls) -> "ROIAssumptions":
        return cls(**DEFAULT_ROI_ASSUMPTIONS)


def calculate_roi_cases(
    naive_kpis: dict[str, float],
    optimized_kpis: dict[str, float],
    *,
    assumptions: ROIAssumptions | None = None,
    high_burden_reduction: int = 0,
    robotics_trip_savings: float = 0.0,
) -> dict[str, dict[str, float]]:
    """Return conservative/base/aggressive savings under transparent assumptions."""
    active = assumptions or ROIAssumptions.defaults()
    route_daily = max(0.0, naive_kpis["daily_deployment_cost"] - optimized_kpis["daily_deployment_cost"])
    annual_route = route_daily * active.workdays_per_year * active.impact_realization_factor
    burden_savings = (
        max(0, high_burden_reduction)
        * active.replacement_cost_per_lost_employee
        * active.attrition_reduction_sensitivity
    )
    robotics_savings = max(0.0, robotics_trip_savings) * active.inspection_rework_cost
    base = annual_route + burden_savings + robotics_savings
    return {
        "conservative": {
            "annual_route_savings": annual_route * 0.65,
            "burden_retention_savings": burden_savings * 0.35,
            "robotics_inspection_savings": robotics_savings * 0.40,
            "total_annual_savings": base * 0.55,
        },
        "base": {
            "annual_route_savings": annual_route,
            "burden_retention_savings": burden_savings,
            "robotics_inspection_savings": robotics_savings,
            "total_annual_savings": base,
        },
        "aggressive": {
            "annual_route_savings": annual_route * 1.35,
            "burden_retention_savings": burden_savings * 1.55,
            "robotics_inspection_savings": robotics_savings * 1.75,
            "total_annual_savings": base * 1.45,
        },
    }
