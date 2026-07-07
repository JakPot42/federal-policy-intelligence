"""Shared Claude call wrapper for Federal Policy Intelligence.

One place to make an Anthropic call, reconciling the two genuinely
different -- and both intentional -- failure behaviors the three merged
tools had:

  * comment_analyzer (P33, memo_generator) and regulatory_velocity
    (P65, brief) RAISE loudly on any Claude failure: their live path
    wraps the call in `try/except Exception -> raise RuntimeError`.
  * ai_policy_simulator (P37, claude_simulator) FALLS BACK to a
    deterministic template on any Claude failure, so the CLI keeps
    working with no API key.

Rather than pick one, `call_claude` takes an explicit
`on_error="raise"|"fallback"` parameter -- the same design the
Installation Resilience cluster used for its shared `claude_brief`. No
call site has to guess which behavior another one needs.

Doctrine preserved from every Claude call site in this portfolio: catch
broad `Exception`, not `anthropic.APIError` -- the SDK raises `TypeError`
(not an APIError subclass) when the API key is missing/empty, which is the
single most common real failure in this portfolio's deploy environments.

The wrapper returns the raw response TEXT. Any structured parsing (e.g.
P37's strict-JSON persona output) stays at the call site: a caller that
needs to fall back on a JSON-parse failure too should request
`on_error="fallback"` here and wrap its own parse in a try that returns
the same fallback -- see claude_simulator for that pattern.
"""
from __future__ import annotations

import os

# Single pinned model for the whole toolkit (all three tools pinned this
# exact id). Overridable via one env var instead of the three separate
# ones the standalone tools used (RCA_MODEL / REGVEL_MODEL / none).
DEFAULT_MODEL = os.getenv("FPI_MODEL", "claude-haiku-4-5-20251001")

_VALID_ON_ERROR = ("raise", "fallback")


def _make_client(api_key: str | None = None):
    """Construct an Anthropic client. Isolated so tests can monkeypatch it
    without depending on the SDK's internals. Imported lazily so this module
    imports even where the SDK isn't installed."""
    import anthropic

    # Passing api_key=None lets the SDK pick it up from the environment
    # (P37's style); passing an explicit value matches P33/P65's style. An
    # empty string raises TypeError inside the SDK -- deliberately caught by
    # call_claude below, same as any other failure.
    if api_key is None:
        return anthropic.Anthropic()
    return anthropic.Anthropic(api_key=api_key)


def call_claude(
    prompt: str,
    *,
    system: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
    on_error: str = "raise",
    fallback: str | None = None,
    api_key: str | None = None,
) -> str | None:
    """Make a single Claude call and return the response text (stripped).

    on_error:
      "raise"    -- wrap any failure in RuntimeError and raise (P33/P65).
      "fallback" -- return `fallback` (default None) instead of raising,
                    so the caller can substitute a deterministic result
                    (P37). None is a deliberate sentinel: the caller checks
                    for it and runs its own deterministic path.
    """
    if on_error not in _VALID_ON_ERROR:
        raise ValueError(
            f"on_error must be one of {_VALID_ON_ERROR}, got {on_error!r}"
        )

    try:
        client = _make_client(api_key)
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        msg = client.messages.create(**kwargs)
        return msg.content[0].text.strip()
    except Exception as exc:  # NOT anthropic.APIError -- see module docstring
        if on_error == "fallback":
            return fallback
        raise RuntimeError(f"Claude API error: {exc}") from exc
