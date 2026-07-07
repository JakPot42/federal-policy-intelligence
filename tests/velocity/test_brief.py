"""Tests for brief.py — DEMO_MODE returns, prompt structure, error handling."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from fpi.velocity.brief import generate_brief, _build_prompt
from fpi.velocity.federal_register_client import fetch_all_domains
from fpi.velocity.velocity_engine import all_velocities, _month_labels
from fpi.velocity.config import DOMAINS


def _demo_velocities():
    domain_counts = fetch_all_domains(demo_mode=True)
    return all_velocities(domain_counts)


class TestGenerateBriefDemoMode:
    def test_returns_string(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, demo_mode=True)
        assert isinstance(result, str)

    def test_system_brief_nonempty(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, demo_mode=True)
        assert len(result) > 50

    def test_domain_brief_returns_string(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "BIS", demo_mode=True)
        assert isinstance(result, str)
        assert len(result) > 50

    def test_bis_brief_contains_relevant_text(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "BIS", demo_mode=True)
        text_lower = result.lower()
        assert any(word in text_lower for word in ["export", "bis", "semiconductor", "surge"])

    def test_cmmc_brief_references_cmmc(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "CMMC", demo_mode=True)
        assert "cmmc" in result.lower() or "cybersecurity" in result.lower()

    def test_itar_brief_references_itar(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "ITAR", demo_mode=True)
        assert "itar" in result.lower() or "arms" in result.lower()

    def test_dfars_brief_references_dfars(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "DFARS", demo_mode=True)
        assert "dfars" in result.lower() or "acquisition" in result.lower()

    def test_sead_brief_references_security(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, "SEAD", demo_mode=True)
        assert any(w in result.lower() for w in ["security", "nispom", "clearance", "quiet"])

    def test_system_brief_mentions_bis_or_cmmc(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, None, demo_mode=True)
        text_lower = result.lower()
        assert "bis" in text_lower or "cmmc" in text_lower or "export" in text_lower

    def test_all_domain_briefs_available(self):
        velocities = _demo_velocities()
        for domain in DOMAINS.keys():
            result = generate_brief(velocities, domain, demo_mode=True)
            assert len(result) > 30, f"Brief for {domain} too short"

    def test_none_domain_returns_system_brief(self):
        velocities = _demo_velocities()
        result = generate_brief(velocities, None, demo_mode=True)
        assert isinstance(result, str)
        assert len(result) > 50


class TestBuildPrompt:
    def test_domain_prompt_includes_domain(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, "BIS")
        assert "BIS" in prompt

    def test_domain_prompt_includes_z_score(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, "BIS")
        assert "z_score" in prompt.lower() or "z-score" in prompt.lower() or "Z-score" in prompt

    def test_domain_prompt_includes_alert_level(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, "BIS")
        assert velocities["BIS"].alert_level in prompt

    def test_system_prompt_includes_all_domains(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, None)
        for domain in DOMAINS.keys():
            assert domain in prompt

    def test_system_prompt_is_string(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, None)
        assert isinstance(prompt, str)

    def test_domain_prompt_includes_acceleration(self):
        velocities = _demo_velocities()
        prompt = _build_prompt(velocities, "CMMC")
        assert "accel" in prompt.lower() or "Acceleration" in prompt
