"""Claude Haiku regulatory climate narrative brief."""
from __future__ import annotations

from fpi.shared import call_claude
from .config import DEMO_MODE, DOMAINS
from .velocity_engine import DomainVelocity


def generate_brief(
    velocities: dict[str, DomainVelocity],
    domain: str | None = None,
    *,
    demo_mode: bool = DEMO_MODE,
) -> str:
    """
    Generate a plain-language regulatory climate brief.

    domain=None → system-wide brief across all domains.
    domain="BIS" → domain-specific brief.
    """
    if demo_mode:
        from .seed_data import DEMO_BRIEFS
        if domain and domain in DEMO_BRIEFS:
            return DEMO_BRIEFS[domain]
        return DEMO_BRIEFS.get("_system", "No demo brief available.")

    # P65 raises loudly on any Claude failure -- preserved via on_error="raise".
    return call_claude(
        _build_prompt(velocities, domain),
        max_tokens=450,
        on_error="raise",
    )


def _build_prompt(
    velocities: dict[str, DomainVelocity], domain: str | None
) -> str:
    if domain:
        vel = velocities[domain]
        lines = [
            f"Write a 3-4 sentence plain-language brief explaining what is driving the "
            f"current regulatory velocity for {domain} ({vel.domain_name}). "
            f"Focus on real-world policy drivers, not statistical artifacts. "
            f"Reference the velocity data. Frame for a defense contractor audience. "
            f"Do not hedge with disclaimers.",
            "",
            f"Domain: {domain} ({vel.domain_name})",
            f"Context: {DOMAINS[domain]['context']}",
            f"Alert level: {vel.alert_level}",
            f"Z-score: {vel.z_score:.2f} (standard deviations above/below historical baseline)",
            f"Recent 3-month average: {vel.recent_avg:.1f} publications/month",
            f"Historical baseline mean: {vel.baseline_mean:.1f} publications/month",
            f"Acceleration vs prior period: {vel.acceleration_pct:+.1f}%",
            f"Peak month: {vel.peak_month} ({vel.peak_count} publications)",
        ]
    else:
        lines = [
            "Write a 4-5 sentence plain-language regulatory climate brief covering all "
            "defense domains below. Identify which are surging/elevated and what policy "
            "events are driving them. Frame for a defense contractor audience. "
            "Do not hedge with disclaimers.",
            "",
        ]
        for d, vel in velocities.items():
            lines.append(
                f"{d} ({vel.domain_name}): {vel.alert_level}, "
                f"z={vel.z_score:.2f}, recent={vel.recent_avg:.1f}/mo, "
                f"accel={vel.acceleration_pct:+.1f}%"
            )
    return "\n".join(lines)
