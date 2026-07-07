"""`fpi velocity` -- Regulatory Velocity Tracker (P65) subcommands."""
from __future__ import annotations

import click

from .config import DEMO_MODE, DOMAINS
from .federal_register_client import fetch_all_domains, fetch_domain_counts
from .velocity_engine import all_velocities, compute_velocity
from .brief import generate_brief
from .dashboard import (
    console,
    print_banner,
    print_compare,
    print_alerts,
    print_velocity,
    print_brief,
    print_json_export,
)

_DOMAIN_CHOICES = sorted(DOMAINS.keys())
_DEMO_HINT = "[dim]DEMO_MODE=True -- set DEMO_MODE=False for live Federal Register data.[/dim]"


@click.group()
def velocity() -> None:
    """
    Regulatory Velocity Tracker: measures how fast defense regulations are changing.

    \b
    Domains: DFARS CMMC ITAR BIS SEAD
    Data source: Federal Register API (free, public, no auth required)
    Algorithm  : z-score deviation from rolling baseline

    Set DEMO_MODE=False and provide ANTHROPIC_API_KEY for live mode.
    """


@velocity.command()
@click.argument("domain", type=click.Choice(_DOMAIN_CHOICES, case_sensitive=False))
@click.option("--months", "-m", default=24, show_default=True, help="Number of months of history to display.")
def series(domain: str, months: int) -> None:
    """Show the monthly publication-velocity time series for DOMAIN."""
    print_banner()
    labels, counts = fetch_domain_counts(domain.upper(), months_back=months)
    vel = compute_velocity(domain.upper(), labels, counts)
    print_velocity(vel)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@velocity.command()
def compare() -> None:
    """Compare velocity across all domains side by side."""
    print_banner()
    velocities = all_velocities(fetch_all_domains())
    print_compare(velocities)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@velocity.command()
def alerts() -> None:
    """Show only domains at SURGE or ELEVATED velocity level."""
    print_banner()
    velocities = all_velocities(fetch_all_domains())
    print_alerts(velocities)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@velocity.command()
@click.argument("domain", type=click.Choice(_DOMAIN_CHOICES + ["ALL"], case_sensitive=False), default="ALL", required=False)
def brief(domain: str) -> None:
    """
    Generate a Claude regulatory climate brief.

    \b
    Examples:
      brief         -- system-wide brief across all domains
      brief BIS     -- BIS-specific brief
    """
    print_banner()
    velocities = all_velocities(fetch_all_domains())
    target = None if domain.upper() == "ALL" else domain.upper()
    if target:
        console.print(
            f"[dim]Generating brief for {target} "
            f"(level={velocities[target].alert_level}, "
            f"z={velocities[target].z_score:+.2f})...[/dim]"
        )
    else:
        console.print("[dim]Generating system-wide regulatory climate brief...[/dim]")
    print_brief(target, generate_brief(velocities, target))


@velocity.command()
def export() -> None:
    """Export all domain velocity data as JSON."""
    print_json_export(all_velocities(fetch_all_domains()))


def run_demo() -> None:
    """Full P65 demo against seeded data. No API keys required.
    Shared by `fpi velocity demo` and the top-level `fpi demo`."""
    print_banner()
    velocities = all_velocities(fetch_all_domains(demo_mode=True))

    console.rule("[bold]Velocity Demo 1: All-Domain Comparison[/bold]")
    print_compare(velocities)

    console.rule("[bold]Velocity Demo 2: BIS Export Controls -- Time Series (SURGE)[/bold]")
    print_velocity(velocities["BIS"])

    console.rule("[bold]Velocity Demo 3: SEAD -- Time Series (QUIET)[/bold]")
    print_velocity(velocities["SEAD"])

    console.rule("[bold]Velocity Demo 4: Active Alerts[/bold]")
    print_alerts(velocities)

    console.rule("[bold]Velocity Demo 5: BIS Domain Brief[/bold]")
    print_brief("BIS", generate_brief(velocities, "BIS", demo_mode=True))


@velocity.command()
def demo() -> None:
    """Run all Regulatory Velocity Tracker demos against seeded data."""
    run_demo()
