"""Shared DEMO_MODE resolution for Federal Policy Intelligence.

The three merged tools parsed DEMO_MODE two different ways:

  * comment_analyzer (P33) and regulatory_velocity (P65) -- PERMISSIVE:
        os.getenv("DEMO_MODE", "True").lower() not in ("false", "0", "no")
    Default True; only an explicit false-ish value disables demo mode.

  * ai_policy_simulator (P37) -- STRICT:
        os.environ.get("DEMO_MODE", "True") == "True"
    Only the exact string "True" enables it; "true", "1", "yes" all read
    as live mode.

This module adopts the PERMISSIVE convention as canonical -- it is what 2
of the 3 tools already used, and it is the same reconciliation the
Installation Resilience cluster made when it folded joule's strict
`== "True"` parse into GridPulse/Water Monitor's permissive one. The
practical effect on P37: `DEMO_MODE=true` (lowercase) now keeps demo mode
on instead of silently switching to live mode and trying to reach the
Anthropic API without a key.
"""
from __future__ import annotations

import os
from typing import Mapping

# Values that, case-insensitively, turn demo mode OFF. Everything else
# (including an unset DEMO_MODE, which defaults to "True") keeps it ON.
_DISABLING_VALUES = ("false", "0", "no")


def is_demo_mode(env: Mapping[str, str] | None = None) -> bool:
    """Return True when demo mode is active (the default).

    env is accepted for testability; when omitted, os.environ is read.
    """
    raw = (env if env is not None else os.environ).get("DEMO_MODE", "True")
    return raw.strip().lower() not in _DISABLING_VALUES
