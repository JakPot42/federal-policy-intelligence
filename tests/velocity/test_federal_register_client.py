"""Tests for federal_register_client.py — DEMO_MODE routing, URL parameters, structure."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from fpi.velocity.federal_register_client import fetch_domain_counts, fetch_all_domains, type_codes
from fpi.velocity.config import DOMAINS, FR_TYPE_CODES, HISTORY_MONTHS
from fpi.velocity.velocity_engine import _month_labels


class TestTypeCodes:
    """Bug B regression: the FR API `conditions[type]` filter needs enum codes
    (RULE/PRORULE/NOTICE), not the human-readable labels. Sending labels returns
    HTTP 200 with count=0, so the whole live path silently read as empty."""

    def test_maps_labels_to_fr_codes(self):
        assert type_codes(["Rule", "Proposed Rule", "Notice"]) == ["RULE", "PRORULE", "NOTICE"]

    def test_unknown_label_raises(self):
        with pytest.raises(ValueError):
            type_codes(["Interim Final Rule"])

    def test_every_configured_doc_type_is_mappable(self):
        # Guards against a future DOMAINS edit adding a label with no code.
        for domain, cfg in DOMAINS.items():
            for label in cfg["doc_types"]:
                assert label in FR_TYPE_CODES, f"{domain} uses unmapped type {label!r}"

    def test_codes_are_never_the_raw_labels(self):
        for label, code in FR_TYPE_CODES.items():
            assert code.isupper()
            assert " " not in code


class TestFetchDomainCountsDemoMode:
    def test_returns_tuple(self):
        result = fetch_domain_counts("DFARS", demo_mode=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_months_and_counts_same_length(self):
        months, counts = fetch_domain_counts("BIS", demo_mode=True)
        assert len(months) == len(counts)

    def test_default_history_length(self):
        months, counts = fetch_domain_counts("DFARS", demo_mode=True)
        assert len(months) == HISTORY_MONTHS

    def test_custom_months_back(self):
        months, counts = fetch_domain_counts("CMMC", months_back=12, demo_mode=True)
        assert len(months) == 12

    def test_months_are_valid_format(self):
        months, _ = fetch_domain_counts("ITAR", demo_mode=True)
        for m in months:
            assert len(m) == 7
            assert m[4] == "-"
            assert 1 <= int(m[5:7]) <= 12

    def test_months_ordered_oldest_first(self):
        months, _ = fetch_domain_counts("SEAD", demo_mode=True)
        for i in range(len(months) - 1):
            assert months[i] < months[i + 1]

    def test_counts_are_nonnegative_integers(self):
        _, counts = fetch_domain_counts("BIS", demo_mode=True)
        for c in counts:
            assert isinstance(c, int)
            assert c >= 0

    def test_bis_demo_has_surge_pattern(self):
        """Last 3 months of BIS should be higher than baseline."""
        months, counts = fetch_domain_counts("BIS", demo_mode=True)
        recent_avg = sum(counts[-3:]) / 3
        baseline_avg = sum(counts[:-3]) / len(counts[:-3])
        assert recent_avg > baseline_avg * 1.5, "BIS recent should be > 1.5x baseline"

    def test_sead_demo_has_quiet_pattern(self):
        """Last 3 months of SEAD should be lower than baseline."""
        months, counts = fetch_domain_counts("SEAD", demo_mode=True)
        recent_avg = sum(counts[-3:]) / 3
        baseline_avg = sum(counts[:-3]) / len(counts[:-3])
        assert recent_avg < baseline_avg

    def test_all_five_domains_returnable(self):
        for domain in DOMAINS.keys():
            months, counts = fetch_domain_counts(domain, demo_mode=True)
            assert len(months) == HISTORY_MONTHS

    def test_months_match_month_labels_function(self):
        months, _ = fetch_domain_counts("DFARS", demo_mode=True)
        expected = _month_labels(HISTORY_MONTHS)
        assert months == expected


class TestFetchAllDomainsDemoMode:
    def test_returns_dict(self):
        result = fetch_all_domains(demo_mode=True)
        assert isinstance(result, dict)

    def test_all_domains_present_by_default(self):
        result = fetch_all_domains(demo_mode=True)
        assert set(result.keys()) == set(DOMAINS.keys())

    def test_subset_of_domains(self):
        result = fetch_all_domains(domains=["DFARS", "BIS"], demo_mode=True)
        assert set(result.keys()) == {"DFARS", "BIS"}

    def test_each_value_is_months_counts_tuple(self):
        result = fetch_all_domains(demo_mode=True)
        for domain, (months, counts) in result.items():
            assert len(months) == HISTORY_MONTHS
            assert len(counts) == HISTORY_MONTHS

    def test_empty_domains_list(self):
        result = fetch_all_domains(domains=[], demo_mode=True)
        assert result == {}

    def test_custom_months_back(self):
        result = fetch_all_domains(months_back=12, demo_mode=True)
        for domain, (months, counts) in result.items():
            assert len(months) == 12
