"""Shared core for Federal Policy Intelligence: DEMO_MODE resolution and the
single Claude call wrapper used by all three merged tools."""
from fpi.shared.demo_mode import is_demo_mode
from fpi.shared.claude_client import call_claude, DEFAULT_MODEL

__all__ = ["is_demo_mode", "call_claude", "DEFAULT_MODEL"]
