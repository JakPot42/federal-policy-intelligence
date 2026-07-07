"""
Velocity engine — computes regulatory publication rate, z-score baseline deviation,
and acceleration metrics from monthly Federal Register document counts.

Uses pandas for time-series indexing and statistics.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

import pandas as pd

from .config import (
    DOMAINS,
    HISTORY_MONTHS,
    RECENT_MONTHS,
    MIN_BASELINE_MONTHS,
    ALERT_THRESHOLDS,
)


@dataclass
class DomainVelocity:
    domain: str
    domain_name: str
    months: list[str]           # ["2024-07", ..., "2026-06"] oldest → newest
    counts: list[int]           # monthly publication counts aligned with months
    series: object              # pd.Series with PeriodIndex (monthly)
    recent_avg: float           # mean of last RECENT_MONTHS months
    baseline_mean: float        # mean of baseline window (all months before recent)
    baseline_std: float         # population std of baseline window
    z_score: float              # (recent_avg - baseline_mean) / max(std, 0.5)
    alert_level: str            # SURGE / ELEVATED / NORMAL / QUIET / INSUFFICIENT_DATA
    acceleration_pct: float     # % change: recent avg vs prior equal-length window
    peak_month: str             # month with highest publication count
    peak_count: int             # highest single-month count


def _month_labels(months_back: int = HISTORY_MONTHS) -> list[str]:
    """Generate list of YYYY-MM labels for the past months_back months, oldest first."""
    today = date.today()
    labels: list[str] = []
    for i in range(months_back - 1, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        labels.append(f"{year}-{month:02d}")
    return labels


def build_series(months: list[str], counts: list[int | None]) -> pd.Series:
    """Build a monthly PeriodIndex pandas Series from parallel month/count lists.

    Months whose count is None (a FAILED fetch, not a genuine zero) are dropped
    entirely, so a missing month is excluded from every downstream statistic
    rather than being treated as a real quiet month. A genuine 0 is kept.
    """
    pairs = [(m, c) for m, c in zip(months, counts) if c is not None]
    idx = pd.PeriodIndex([pd.Period(m, "M") for m, _ in pairs], freq="M")
    return pd.Series([c for _, c in pairs], index=idx, dtype=float)


def _peak(series: pd.Series) -> tuple[str, int]:
    """Peak (month, count) derived from the series' own index -- robust to
    dropped (None) months, unlike positional indexing into the raw counts list."""
    if len(series) == 0:
        return "", 0
    peak_period = series.idxmax()
    return str(peak_period), int(series.loc[peak_period])


def compute_velocity(domain: str, months: list[str], counts: list[int | None]) -> DomainVelocity:
    """Compute all velocity metrics for a single domain."""
    series = build_series(months, counts)
    n = len(series)

    # Every real month failed to fetch -> nothing to compute over.
    if n == 0:
        return DomainVelocity(
            domain=domain,
            domain_name=DOMAINS[domain]["name"],
            months=months,
            counts=counts,
            series=series,
            recent_avg=0.0,
            baseline_mean=0.0,
            baseline_std=0.0,
            z_score=0.0,
            alert_level="INSUFFICIENT_DATA",
            acceleration_pct=0.0,
            peak_month="",
            peak_count=0,
        )

    recent_series = series.iloc[-RECENT_MONTHS:] if n >= RECENT_MONTHS else series
    recent_avg = float(recent_series.mean())

    baseline_series = series.iloc[:-RECENT_MONTHS] if n > RECENT_MONTHS else series.iloc[:0]

    if len(baseline_series) < MIN_BASELINE_MONTHS:
        peak_month, peak_count = _peak(series)
        return DomainVelocity(
            domain=domain,
            domain_name=DOMAINS[domain]["name"],
            months=months,
            counts=counts,
            series=series,
            recent_avg=round(recent_avg, 2),
            baseline_mean=0.0,
            baseline_std=0.0,
            z_score=0.0,
            alert_level="INSUFFICIENT_DATA",
            acceleration_pct=0.0,
            peak_month=peak_month,
            peak_count=peak_count,
        )

    # Population std (ddof=0) — consistent with BioMon baseline engine
    baseline_mean = float(baseline_series.mean())
    baseline_std = float(baseline_series.std(ddof=0))
    effective_std = max(baseline_std, 0.5)
    z = (recent_avg - baseline_mean) / effective_std

    if z >= ALERT_THRESHOLDS["SURGE"]:
        level = "SURGE"
    elif z >= ALERT_THRESHOLDS["ELEVATED"]:
        level = "ELEVATED"
    elif z >= ALERT_THRESHOLDS["QUIET"]:
        level = "NORMAL"
    else:
        level = "QUIET"

    # Acceleration: recent window vs the equal-length prior window
    prior_series = (
        series.iloc[-(RECENT_MONTHS * 2):-RECENT_MONTHS]
        if n >= RECENT_MONTHS * 2
        else series.iloc[:0]
    )
    if len(prior_series) > 0 and float(prior_series.mean()) > 0:
        prior_avg = float(prior_series.mean())
        accel = (recent_avg - prior_avg) / prior_avg * 100.0
    else:
        accel = 0.0

    peak_month, peak_count = _peak(series)

    return DomainVelocity(
        domain=domain,
        domain_name=DOMAINS[domain]["name"],
        months=months,
        counts=counts,
        series=series,
        recent_avg=round(recent_avg, 2),
        baseline_mean=round(baseline_mean, 2),
        baseline_std=round(baseline_std, 2),
        z_score=round(z, 2),
        alert_level=level,
        acceleration_pct=round(accel, 1),
        peak_month=peak_month,
        peak_count=peak_count,
    )


def all_velocities(
    domain_counts: dict[str, tuple[list[str], list[int]]],
) -> dict[str, DomainVelocity]:
    """Compute velocity for each domain from a {domain: (months, counts)} mapping."""
    return {
        domain: compute_velocity(domain, months, counts)
        for domain, (months, counts) in domain_counts.items()
    }
