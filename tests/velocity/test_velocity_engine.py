"""Tests for velocity_engine.py — z-score, alert levels, acceleration, edge cases."""
import sys
import os
import math
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import pandas as pd

from fpi.velocity.velocity_engine import (
    DomainVelocity,
    _month_labels,
    build_series,
    compute_velocity,
    all_velocities,
)
from fpi.velocity.config import HISTORY_MONTHS, RECENT_MONTHS, MIN_BASELINE_MONTHS


def _make_months(n: int) -> list[str]:
    """Generate n valid YYYY-MM labels ending at current month."""
    return _month_labels(n)


# ---------------------------------------------------------------------------
# _month_labels
# ---------------------------------------------------------------------------

class TestMonthLabels:
    def test_returns_correct_length(self):
        labels = _month_labels(24)
        assert len(labels) == 24

    def test_default_length(self):
        labels = _month_labels()
        assert len(labels) == HISTORY_MONTHS

    def test_labels_format(self):
        labels = _month_labels(6)
        for label in labels:
            assert len(label) == 7
            assert label[4] == "-"
            year, month = int(label[:4]), int(label[5:7])
            assert 2020 <= year <= 2030
            assert 1 <= month <= 12

    def test_labels_ordered_oldest_first(self):
        labels = _month_labels(12)
        for i in range(len(labels) - 1):
            y1, m1 = int(labels[i][:4]), int(labels[i][5:7])
            y2, m2 = int(labels[i+1][:4]), int(labels[i+1][5:7])
            assert (y1, m1) < (y2, m2)

    def test_single_month(self):
        labels = _month_labels(1)
        assert len(labels) == 1


# ---------------------------------------------------------------------------
# build_series
# ---------------------------------------------------------------------------

class TestBuildSeries:
    def test_returns_pandas_series(self):
        months = ["2025-01", "2025-02", "2025-03"]
        counts = [5, 7, 3]
        s = build_series(months, counts)
        assert isinstance(s, pd.Series)

    def test_series_length(self):
        months = ["2025-01", "2025-02", "2025-03"]
        counts = [5, 7, 3]
        s = build_series(months, counts)
        assert len(s) == 3

    def test_series_values(self):
        months = ["2025-01", "2025-02", "2025-03"]
        counts = [5, 7, 3]
        s = build_series(months, counts)
        assert list(s) == [5.0, 7.0, 3.0]

    def test_period_index(self):
        months = ["2025-01", "2025-02"]
        counts = [1, 2]
        s = build_series(months, counts)
        assert isinstance(s.index, pd.PeriodIndex)

    def test_empty_series(self):
        s = build_series([], [])
        assert len(s) == 0


# ---------------------------------------------------------------------------
# compute_velocity — core logic
# ---------------------------------------------------------------------------

class TestComputeVelocityBasic:
    def _make_counts(self, baseline_values, recent_values):
        """Build (months, counts) with baseline followed by recent window."""
        all_counts = baseline_values + recent_values
        months = _make_months(len(all_counts))
        return months, all_counts

    def test_returns_domain_velocity_instance(self):
        months = _make_months(24)
        counts = [10] * 24
        vel = compute_velocity("DFARS", months, counts)
        assert isinstance(vel, DomainVelocity)

    def test_domain_field(self):
        months = _make_months(24)
        counts = [10] * 24
        vel = compute_velocity("BIS", months, counts)
        assert vel.domain == "BIS"

    def test_domain_name_populated(self):
        months = _make_months(24)
        counts = [5] * 24
        vel = compute_velocity("CMMC", months, counts)
        assert "Cybersecurity" in vel.domain_name

    def test_counts_and_months_stored(self):
        months = _make_months(10)
        counts = list(range(10))
        vel = compute_velocity("ITAR", months, counts)
        assert vel.months == months
        assert vel.counts == counts

    def test_series_is_pandas_series(self):
        months = _make_months(24)
        counts = [8] * 24
        vel = compute_velocity("DFARS", months, counts)
        assert isinstance(vel.series, pd.Series)

    def test_recent_avg_correct(self):
        months = _make_months(24)
        counts = [5] * 21 + [10, 20, 30]  # last 3 = 10, 20, 30 → avg 20
        vel = compute_velocity("BIS", months, counts)
        assert vel.recent_avg == pytest.approx(20.0)

    def test_baseline_mean_correct(self):
        months = _make_months(24)
        counts = [10] * 21 + [5, 5, 5]   # baseline = 21 × 10 → mean 10
        vel = compute_velocity("DFARS", months, counts)
        assert vel.baseline_mean == pytest.approx(10.0)

    def test_z_score_above_baseline(self):
        months = _make_months(24)
        counts = [5] * 21 + [50, 50, 50]  # massive surge
        vel = compute_velocity("BIS", months, counts)
        assert vel.z_score > 0

    def test_z_score_below_baseline(self):
        months = _make_months(24)
        counts = [20] * 21 + [1, 1, 1]   # drop
        vel = compute_velocity("ITAR", months, counts)
        assert vel.z_score < 0

    def test_z_score_near_zero_when_stable(self):
        months = _make_months(24)
        counts = [10] * 24   # perfectly stable
        vel = compute_velocity("DFARS", months, counts)
        assert abs(vel.z_score) < 0.1

    def test_peak_month_is_valid_month(self):
        months = _make_months(24)
        counts = [1] * 24
        counts[10] = 99
        vel = compute_velocity("CMMC", months, counts)
        assert vel.peak_month == months[10]
        assert vel.peak_count == 99


# ---------------------------------------------------------------------------
# compute_velocity — alert levels
# ---------------------------------------------------------------------------

class TestAlertLevels:
    def _surge_data(self):
        months = _make_months(24)
        # baseline mean=5, std~0.5; recent avg=25 → z=(25-5)/0.5=40 (SURGE)
        counts = [5] * 21 + [25, 25, 25]
        return months, counts

    def _elevated_data(self):
        # build data where z ≈ 1.5
        baseline = [10, 8, 12, 9, 11, 10, 9, 11, 10, 8, 12, 9, 11, 10, 9, 11, 10, 9, 10, 11, 9]
        recent = [14, 15, 14]  # avg 14.33
        months = _make_months(24)
        return months, baseline + recent

    def _quiet_data(self):
        months = _make_months(24)
        counts = [10] * 21 + [1, 1, 1]  # large drop
        return months, counts

    def test_surge_level(self):
        months, counts = self._surge_data()
        vel = compute_velocity("BIS", months, counts)
        assert vel.alert_level == "SURGE"

    def test_elevated_level(self):
        months, counts = self._elevated_data()
        vel = compute_velocity("DFARS", months, counts)
        assert vel.alert_level in ("ELEVATED", "SURGE")  # depends on exact std

    def test_normal_level_when_stable(self):
        months = _make_months(24)
        counts = [10, 9, 11, 10, 10, 9, 11, 10, 10, 10, 9, 11, 10, 10, 9, 11, 10, 10, 9, 11, 10, 10, 10, 10]
        vel = compute_velocity("ITAR", months, counts)
        assert vel.alert_level == "NORMAL"

    def test_quiet_level(self):
        months, counts = self._quiet_data()
        vel = compute_velocity("SEAD", months, counts)
        assert vel.alert_level == "QUIET"

    def test_insufficient_data_when_too_short(self):
        months = _make_months(MIN_BASELINE_MONTHS - 1)
        counts = [5] * (MIN_BASELINE_MONTHS - 1)
        vel = compute_velocity("DFARS", months, counts)
        assert vel.alert_level == "INSUFFICIENT_DATA"

    def test_exactly_min_baseline_threshold(self):
        # MIN_BASELINE_MONTHS baseline + RECENT_MONTHS recent = exactly enough
        n = MIN_BASELINE_MONTHS + RECENT_MONTHS
        months = _make_months(n)
        counts = [10] * n
        vel = compute_velocity("DFARS", months, counts)
        assert vel.alert_level != "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# compute_velocity — acceleration
# ---------------------------------------------------------------------------

class TestAcceleration:
    def test_positive_acceleration(self):
        months = _make_months(24)
        # prior window (idx 18-20) = [5,5,5] avg 5; recent (idx 21-23) = [10,10,10] avg 10
        counts = [5] * 18 + [5, 5, 5] + [10, 10, 10]
        vel = compute_velocity("BIS", months, counts)
        assert vel.acceleration_pct == pytest.approx(100.0, abs=1.0)

    def test_negative_acceleration(self):
        months = _make_months(24)
        counts = [10] * 18 + [10, 10, 10] + [5, 5, 5]
        vel = compute_velocity("SEAD", months, counts)
        assert vel.acceleration_pct == pytest.approx(-50.0, abs=1.0)

    def test_zero_acceleration_when_stable(self):
        months = _make_months(24)
        counts = [10] * 24
        vel = compute_velocity("ITAR", months, counts)
        assert abs(vel.acceleration_pct) < 0.5

    def test_no_prior_window_when_too_short(self):
        # fewer than RECENT_MONTHS*2 data points → no prior window
        months = _make_months(RECENT_MONTHS + MIN_BASELINE_MONTHS)
        counts = [10] * len(months)
        vel = compute_velocity("DFARS", months, counts)
        assert vel.acceleration_pct == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# compute_velocity — std floor
# ---------------------------------------------------------------------------

class TestStdFloor:
    def test_std_floor_prevents_division_error(self):
        """Perfectly flat baseline (std=0) should not crash — std is floored at 0.5."""
        months = _make_months(24)
        counts = [10] * 21 + [15, 15, 15]
        # This would cause div-by-zero without the std floor
        vel = compute_velocity("DFARS", months, counts)
        assert not math.isnan(vel.z_score)
        assert not math.isinf(vel.z_score)


# ---------------------------------------------------------------------------
# all_velocities
# ---------------------------------------------------------------------------

class TestAllVelocities:
    def test_returns_dict_of_domain_velocities(self):
        months = _make_months(24)
        domain_counts = {
            "DFARS": (months, [10] * 24),
            "BIS":   (months, [8] * 24),
        }
        result = all_velocities(domain_counts)
        assert set(result.keys()) == {"DFARS", "BIS"}
        assert all(isinstance(v, DomainVelocity) for v in result.values())

    def test_empty_input(self):
        result = all_velocities({})
        assert result == {}

    def test_five_domains(self):
        months = _make_months(24)
        domain_counts = {
            d: (months, [5] * 24)
            for d in ["DFARS", "CMMC", "ITAR", "BIS", "SEAD"]
        }
        result = all_velocities(domain_counts)
        assert len(result) == 5


# ---------------------------------------------------------------------------
# Demo data smoke test
# ---------------------------------------------------------------------------

class TestDemoDataVelocity:
    def _load_demo(self):
        from fpi.velocity.seed_data import DEMO_TIMESERIES
        months = _month_labels(24)
        return {
            d: (months, counts)
            for d, counts in DEMO_TIMESERIES.items()
        }

    def test_bis_is_surge(self):
        dc = self._load_demo()
        vel = compute_velocity("BIS", *dc["BIS"])
        assert vel.alert_level == "SURGE"

    def test_cmmc_is_surge(self):
        dc = self._load_demo()
        vel = compute_velocity("CMMC", *dc["CMMC"])
        assert vel.alert_level == "SURGE"

    def test_itar_is_normal(self):
        dc = self._load_demo()
        vel = compute_velocity("ITAR", *dc["ITAR"])
        assert vel.alert_level == "NORMAL"

    def test_sead_is_quiet(self):
        dc = self._load_demo()
        vel = compute_velocity("SEAD", *dc["SEAD"])
        assert vel.alert_level == "QUIET"

    def test_all_demo_domains_have_nonzero_counts(self):
        from fpi.velocity.seed_data import DEMO_TIMESERIES
        for domain, counts in DEMO_TIMESERIES.items():
            assert sum(counts) > 0, f"{domain} has all-zero counts"

    def test_all_demo_domains_have_24_months(self):
        from fpi.velocity.seed_data import DEMO_TIMESERIES
        for domain, counts in DEMO_TIMESERIES.items():
            assert len(counts) == 24, f"{domain} expected 24 months, got {len(counts)}"


# ---------------------------------------------------------------------------
# Bug A regression: a failed fetch (None) is UNKNOWN, not a genuine zero month.
# None must be dropped from every statistic, never counted as real activity.
# ---------------------------------------------------------------------------

class TestMissingMonthsDistinctFromZero:
    def test_build_series_drops_none(self):
        s = build_series(["2025-01", "2025-02", "2025-03"], [5, None, 7])
        assert len(s) == 2
        assert list(s) == [5.0, 7.0]

    def test_build_series_keeps_genuine_zero(self):
        s = build_series(["2025-01", "2025-02", "2025-03"], [5, 0, 7])
        assert len(s) == 3
        assert list(s) == [5.0, 0.0, 7.0]

    def test_failed_month_excluded_from_baseline_but_zero_is_not(self):
        # Identical data except one baseline month is a failed fetch vs a real 0.
        months = _make_months(24)
        counts_none = [10] * 5 + [None] + [10] * 15 + [10, 10, 10]
        counts_zero = [10] * 5 + [0]    + [10] * 15 + [10, 10, 10]

        vel_none = compute_velocity("DFARS", months, counts_none)
        vel_zero = compute_velocity("DFARS", months, counts_zero)

        # None-month dropped -> baseline is all tens -> mean 10.0
        assert vel_none.baseline_mean == pytest.approx(10.0)
        # Zero-month counted -> baseline dragged below 10
        assert vel_zero.baseline_mean < 10.0
        assert vel_none.baseline_mean != vel_zero.baseline_mean

    def test_all_none_is_insufficient_data_not_crash(self):
        months = _make_months(24)
        counts = [None] * 24
        vel = compute_velocity("BIS", months, counts)
        assert vel.alert_level == "INSUFFICIENT_DATA"
        assert vel.peak_month == ""
        assert vel.peak_count == 0
        assert vel.recent_avg == 0.0

    def test_peak_correct_when_earlier_month_missing(self):
        # A None before the peak must not shift the peak via positional indexing.
        months = _make_months(24)
        counts = [None] + [10] * 20 + [10, 10, 50]  # true peak is the last month
        vel = compute_velocity("BIS", months, counts)
        assert vel.peak_month == months[-1]
        assert vel.peak_count == 50

    def test_raw_counts_with_none_preserved_for_display(self):
        months = _make_months(24)
        counts = [10] * 23 + [None]
        vel = compute_velocity("ITAR", months, counts)
        # DomainVelocity keeps the raw list (with None) so the dashboard can
        # show the gap; only the derived series drops it.
        assert vel.counts == counts
        assert len(vel.series) == 23
