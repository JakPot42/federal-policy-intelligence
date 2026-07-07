"""Tests for seed_data.py — structure, lengths, plausibility, brief coverage."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from fpi.velocity.seed_data import DEMO_TIMESERIES, DEMO_BRIEFS
from fpi.velocity.config import DOMAINS, HISTORY_MONTHS


class TestDemoTimeseries:
    def test_all_domains_present(self):
        for domain in DOMAINS.keys():
            assert domain in DEMO_TIMESERIES, f"{domain} missing from DEMO_TIMESERIES"

    def test_correct_length_for_all_domains(self):
        for domain, counts in DEMO_TIMESERIES.items():
            assert len(counts) == HISTORY_MONTHS, (
                f"{domain}: expected {HISTORY_MONTHS} months, got {len(counts)}"
            )

    def test_all_counts_are_nonneg_integers(self):
        for domain, counts in DEMO_TIMESERIES.items():
            for i, c in enumerate(counts):
                assert isinstance(c, int), f"{domain}[{i}] is not int"
                assert c >= 0, f"{domain}[{i}] is negative"

    def test_all_domains_have_nonzero_counts(self):
        for domain, counts in DEMO_TIMESERIES.items():
            assert sum(counts) > 0, f"{domain} all-zero counts"

    def test_bis_peak_in_recent_months(self):
        """BIS surge should be in the last few months."""
        counts = DEMO_TIMESERIES["BIS"]
        peak_idx = counts.index(max(counts))
        assert peak_idx >= len(counts) - 6, "BIS peak should be in last 6 months"

    def test_bis_recent_avg_above_baseline(self):
        counts = DEMO_TIMESERIES["BIS"]
        recent_avg = sum(counts[-3:]) / 3
        baseline_avg = sum(counts[:-3]) / len(counts[:-3])
        assert recent_avg > baseline_avg * 1.5

    def test_sead_recent_avg_below_baseline(self):
        counts = DEMO_TIMESERIES["SEAD"]
        recent_avg = sum(counts[-3:]) / 3
        baseline_avg = sum(counts[:-3]) / len(counts[:-3])
        assert recent_avg < baseline_avg

    def test_dfars_higher_than_cmmc_historically(self):
        """DFARS should have higher baseline than CMMC (more active domain)."""
        dfars_mean = sum(DEMO_TIMESERIES["DFARS"]) / len(DEMO_TIMESERIES["DFARS"])
        cmmc_mean = sum(DEMO_TIMESERIES["CMMC"]) / len(DEMO_TIMESERIES["CMMC"])
        assert dfars_mean > cmmc_mean

    def test_five_domains_total(self):
        assert len(DEMO_TIMESERIES) == 5

    def test_no_month_exceeds_plausible_max(self):
        """No domain should publish more than 50 Federal Register docs in a single month."""
        for domain, counts in DEMO_TIMESERIES.items():
            assert max(counts) <= 50, f"{domain} has implausibly high monthly count"

    def test_counts_are_list_not_tuple(self):
        for domain, counts in DEMO_TIMESERIES.items():
            assert isinstance(counts, list), f"{domain} counts should be a list"

    def test_cmmc_has_upward_trend(self):
        """CMMC should show higher counts in latter half vs first half (implementation ramp-up)."""
        counts = DEMO_TIMESERIES["CMMC"]
        first_half = sum(counts[:12]) / 12
        second_half = sum(counts[12:]) / 12
        assert second_half > first_half


class TestDemoBriefs:
    def test_all_domains_have_briefs(self):
        for domain in DOMAINS.keys():
            assert domain in DEMO_BRIEFS, f"{domain} missing from DEMO_BRIEFS"

    def test_system_brief_present(self):
        assert "_system" in DEMO_BRIEFS

    def test_all_briefs_are_strings(self):
        for key, brief in DEMO_BRIEFS.items():
            assert isinstance(brief, str), f"Brief for {key} is not a string"

    def test_all_briefs_nonempty(self):
        for key, brief in DEMO_BRIEFS.items():
            assert len(brief) > 50, f"Brief for {key} is too short"

    def test_bis_brief_mentions_export(self):
        assert any(w in DEMO_BRIEFS["BIS"].lower() for w in ["export", "bis", "semiconductor"])

    def test_cmmc_brief_mentions_cmmc(self):
        assert "cmmc" in DEMO_BRIEFS["CMMC"].lower() or "cybersecurity" in DEMO_BRIEFS["CMMC"].lower()

    def test_itar_brief_mentions_itar(self):
        assert "itar" in DEMO_BRIEFS["ITAR"].lower() or "arms" in DEMO_BRIEFS["ITAR"].lower()

    def test_dfars_brief_mentions_dfars(self):
        assert "dfars" in DEMO_BRIEFS["DFARS"].lower() or "acquisition" in DEMO_BRIEFS["DFARS"].lower()

    def test_sead_brief_mentions_security(self):
        assert any(w in DEMO_BRIEFS["SEAD"].lower() for w in ["security", "nispom", "clearance"])

    def test_system_brief_mentions_multiple_domains(self):
        brief = DEMO_BRIEFS["_system"].lower()
        domain_mentions = sum(1 for d in ["bis", "cmmc", "dfars", "itar", "sead"] if d in brief)
        assert domain_mentions >= 3, "System brief should mention at least 3 domains"

    def test_six_keys_total(self):
        # 5 domains + _system
        assert len(DEMO_BRIEFS) == 6
