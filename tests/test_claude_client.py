"""Tests for the shared Claude wrapper. Fully mocked -- no network, no SDK
calls. Exercises the raise-vs-fallback split, the broad-Exception catch
(missing-key TypeError), and parameter pass-through."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from fpi.shared import claude_client
from fpi.shared.claude_client import call_claude


class _FakeContentBlock:
    def __init__(self, text):
        self.text = text


class _FakeMessage:
    def __init__(self, text):
        self.content = [_FakeContentBlock(text)]


class _FakeMessages:
    def __init__(self, recorder, text):
        self._recorder = recorder
        self._text = text

    def create(self, **kwargs):
        self._recorder.update(kwargs)
        return _FakeMessage(self._text)


class _FakeClient:
    def __init__(self, recorder, text="  hello from claude  "):
        self.messages = _FakeMessages(recorder, text)


@pytest.fixture
def recorder():
    return {}


@pytest.fixture
def patch_ok(monkeypatch, recorder):
    """Patch _make_client to return a working fake client."""
    monkeypatch.setattr(
        claude_client, "_make_client",
        lambda api_key=None: _FakeClient(recorder),
    )
    return recorder


def _patch_raising(monkeypatch, exc):
    def _boom(api_key=None):
        raise exc
    monkeypatch.setattr(claude_client, "_make_client", _boom)


class TestSuccess:
    def test_returns_stripped_text(self, patch_ok):
        assert call_claude("hi") == "hello from claude"

    def test_passes_model_and_max_tokens(self, patch_ok):
        call_claude("hi", model="claude-x", max_tokens=222)
        assert patch_ok["model"] == "claude-x"
        assert patch_ok["max_tokens"] == 222

    def test_system_included_only_when_given(self, patch_ok):
        call_claude("hi", system="be terse")
        assert patch_ok["system"] == "be terse"

    def test_system_absent_by_default(self, patch_ok):
        call_claude("hi")
        assert "system" not in patch_ok

    def test_prompt_becomes_user_message(self, patch_ok):
        call_claude("analyze this")
        assert patch_ok["messages"] == [{"role": "user", "content": "analyze this"}]

    def test_default_model_is_pinned_haiku(self, patch_ok):
        call_claude("hi")
        assert patch_ok["model"] == claude_client.DEFAULT_MODEL
        assert "haiku" in claude_client.DEFAULT_MODEL


class TestOnErrorRaise:
    def test_wraps_exception_in_runtimeerror(self, monkeypatch):
        _patch_raising(monkeypatch, ValueError("network down"))
        with pytest.raises(RuntimeError, match="Claude API error"):
            call_claude("hi", on_error="raise")

    def test_missing_key_typeerror_is_caught_not_leaked(self, monkeypatch):
        # The SDK raises TypeError (not anthropic.APIError) on an empty key.
        _patch_raising(monkeypatch, TypeError("api_key must be set"))
        with pytest.raises(RuntimeError):
            call_claude("hi", on_error="raise")

    def test_raise_is_the_default(self, monkeypatch):
        _patch_raising(monkeypatch, RuntimeError("x"))
        with pytest.raises(RuntimeError):
            call_claude("hi")


class TestOnErrorFallback:
    def test_returns_none_by_default(self, monkeypatch):
        _patch_raising(monkeypatch, ValueError("boom"))
        assert call_claude("hi", on_error="fallback") is None

    def test_returns_supplied_fallback(self, monkeypatch):
        _patch_raising(monkeypatch, ValueError("boom"))
        assert call_claude("hi", on_error="fallback", fallback="DEMO TEXT") == "DEMO TEXT"

    def test_missing_key_typeerror_falls_back(self, monkeypatch):
        _patch_raising(monkeypatch, TypeError("api_key must be set"))
        assert call_claude("hi", on_error="fallback", fallback="fb") == "fb"

    def test_success_ignores_fallback(self, patch_ok):
        assert call_claude("hi", on_error="fallback", fallback="unused") == "hello from claude"


class TestValidation:
    def test_invalid_on_error_raises_valueerror(self, patch_ok):
        with pytest.raises(ValueError, match="on_error"):
            call_claude("hi", on_error="explode")
