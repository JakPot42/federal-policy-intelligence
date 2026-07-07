"""Tests for the shared DEMO_MODE resolver -- confirms the permissive
convention is canonical and P37's strict outlier is reconciled into it."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fpi.shared.demo_mode import is_demo_mode


class TestDefaultAndOnValues:
    def test_unset_defaults_to_demo(self):
        assert is_demo_mode({}) is True

    def test_exact_True(self):
        assert is_demo_mode({"DEMO_MODE": "True"}) is True

    def test_arbitrary_value_keeps_demo_on(self):
        # Permissive: anything not explicitly disabling keeps demo on.
        assert is_demo_mode({"DEMO_MODE": "1"}) is True
        assert is_demo_mode({"DEMO_MODE": "yes"}) is True
        assert is_demo_mode({"DEMO_MODE": "anything"}) is True


class TestDisablingValues:
    def test_false_variants_disable(self):
        for v in ("false", "False", "FALSE"):
            assert is_demo_mode({"DEMO_MODE": v}) is False

    def test_zero_disables(self):
        assert is_demo_mode({"DEMO_MODE": "0"}) is False

    def test_no_disables(self):
        assert is_demo_mode({"DEMO_MODE": "no"}) is False

    def test_surrounding_whitespace_tolerated(self):
        assert is_demo_mode({"DEMO_MODE": "  False  "}) is False
        assert is_demo_mode({"DEMO_MODE": " true "}) is True


class TestReconciliationOfP37StrictOutlier:
    def test_lowercase_true_stays_demo(self):
        # P37's old strict `== "True"` would have read "true" as LIVE mode
        # (False). The canonical permissive parse keeps it in demo mode.
        assert is_demo_mode({"DEMO_MODE": "true"}) is True


class TestReadsRealEnvWhenNoMappingGiven:
    def test_reads_os_environ(self, monkeypatch):
        monkeypatch.setenv("DEMO_MODE", "false")
        assert is_demo_mode() is False
        monkeypatch.setenv("DEMO_MODE", "True")
        assert is_demo_mode() is True

    def test_unset_env_defaults_true(self, monkeypatch):
        monkeypatch.delenv("DEMO_MODE", raising=False)
        assert is_demo_mode() is True
