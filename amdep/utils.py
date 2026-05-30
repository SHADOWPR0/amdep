"""Shared utility functions for AmDep."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def pipe_list(value: object) -> list[str]:
    """Parse a pipe-delimited cell into a clean list."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def encode_list(values: Iterable[str]) -> str:
    return "|".join(sorted({str(value).strip() for value in values if str(value).strip()}))


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in miles."""
    radius_miles = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return radius_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def travel_minutes(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    *,
    speed_mph: float = 38.0,
    traffic_factor: float = 1.22,
) -> float:
    """Estimate one-way field travel minutes from coordinates."""
    miles = haversine_miles(origin_lat, origin_lon, dest_lat, dest_lon)
    return float((miles / max(speed_mph, 1.0)) * 60.0 * traffic_factor + 6.0)


def normalize01(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    low = values.min()
    high = values.max()
    if high <= low:
        return pd.Series(np.zeros(len(values)), index=series.index)
    return (values - low) / (high - low)


def safe_pct(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator) / float(denominator)


def dollars(value: float) -> str:
    return f"${value:,.0f}"


def hours(value: float) -> str:
    return f"{value:,.1f} hrs"


def pct(value: float) -> str:
    return f"{value * 100:,.0f}%"


def weighted_percentile(values: pd.Series, percentile: float) -> float:
    if values.empty:
        return 0.0
    return float(np.percentile(pd.to_numeric(values, errors="coerce").fillna(0), percentile))

