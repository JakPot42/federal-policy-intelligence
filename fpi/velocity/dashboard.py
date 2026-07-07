"""Rich terminal dashboard -- ASCII-safe for Windows cp1252 console."""
from __future__ import annotations

import json

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import ALERT_COLORS, DOMAINS, HISTORY_MONTHS, RECENT_MONTHS
from .velocity_engine import DomainVelocity

console = Console()

_BANNER = (
    "[bold cyan]Regulatory Velocity Tracker[/bold cyan]  [dim]v1.0[/dim]\n"
    "[dim]Measures how fast defense regulations are changing -- not what the rules say.[/dim]\n"
    "[dim]Source: Federal Register API (free, public) | Domains: DFARS CMMC ITAR BIS SEAD[/dim]"
)


def _bar(value: float, max_val: float, width: int = 20) -> str:
    if max_val <= 0:
        return "." * width
    filled = max(0, min(width, int(value / max_val * width)))
    return "#" * filled + "." * (width - filled)


def _accel_str(pct: float) -> str:
    if abs(pct) < 0.5:
        return " 0%"
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.0f}%"


def print_banner() -> None:
    console.print(_BANNER)
    console.print()


def print_compare(velocities: dict[str, DomainVelocity]) -> None:
    """All-domain velocity comparison table."""
    console.rule("[bold]Regulatory Velocity -- All Domains[/bold]")
    console.print()

    # overflow="fold": on a narrow console this wide table WRAPS cells instead
    # of truncating with a Unicode ellipsis (U+2026), which would crash a strict
    # OEM console (cp850/cp437). Keeps output pure ASCII at any console width.
    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("Domain", style="bold", width=6, overflow="fold")
    t.add_column("Name", width=38, overflow="fold")
    t.add_column("Level", width=10, overflow="fold")
    t.add_column("Z-Score", justify="right", width=8, overflow="fold")
    t.add_column("Recent/mo", justify="right", width=10, overflow="fold")
    t.add_column("Baseline", justify="right", width=9, overflow="fold")
    t.add_column("Accel", justify="right", width=7, overflow="fold")

    for domain, vel in velocities.items():
        color = ALERT_COLORS.get(vel.alert_level, "white")
        t.add_row(
            domain,
            vel.domain_name,
            f"[{color}]{vel.alert_level}[/{color}]",
            f"[{color}]{vel.z_score:+.2f}[/{color}]",
            f"{vel.recent_avg:.1f}",
            f"{vel.baseline_mean:.1f}",
            f"[{color}]{_accel_str(vel.acceleration_pct)}[/{color}]",
        )

    console.print(t)
    console.print()


def print_alerts(velocities: dict[str, DomainVelocity]) -> None:
    """Print only SURGE and ELEVATED domains, with detail."""
    active = {
        d: v for d, v in velocities.items()
        if v.alert_level in ("SURGE", "ELEVATED")
    }
    if not active:
        console.print("[green]No domains currently at ELEVATED or SURGE level.[/green]")
        return

    console.rule("[bold red]Velocity Alerts[/bold red]")
    console.print()

    for domain, vel in active.items():
        color = ALERT_COLORS[vel.alert_level]
        console.print(
            f"  [{color}][bold]{vel.alert_level}[/bold][/{color}]  "
            f"[bold]{domain}[/bold] -- {vel.domain_name}"
        )
        console.print(
            f"        z={vel.z_score:+.2f}  recent={vel.recent_avg:.1f}/mo  "
            f"baseline={vel.baseline_mean:.1f}/mo  accel={_accel_str(vel.acceleration_pct)}"
        )
        console.print()


def print_velocity(vel: DomainVelocity) -> None:
    """Monthly time-series bar chart for a single domain."""
    color = ALERT_COLORS.get(vel.alert_level, "white")
    real_counts = [c for c in vel.counts if c is not None]
    max_count = max(real_counts) if real_counts else 1

    console.rule(f"[bold]{vel.domain} -- {vel.domain_name}[/bold]")
    console.print()

    # Sparkline -- one row per month. A None count is a FAILED fetch (data
    # unknown for that month), shown as a gap, never as a zero-height bar.
    for month, count in zip(vel.months, vel.counts):
        # Highlight recent window
        is_recent = month >= vel.months[-RECENT_MONTHS]
        label_color = color if is_recent else "dim"
        marker = " <<" if month == vel.months[-1] else "   "
        if count is None:
            bar = "." * 30
            count_str = "n/a"
        else:
            bar = _bar(count, max_count, width=30)
            count_str = f"{count:3d}"
        console.print(
            f"  [{label_color}]{month}[/{label_color}]  "
            f"[{label_color}]{bar}[/{label_color}]  "
            f"[{label_color}]{count_str:>3}[/{label_color}]{marker}"
        )

    console.print()
    console.print(
        f"  Alert level  : [{color}]{vel.alert_level}[/{color}]"
    )
    console.print(f"  Z-score      : {vel.z_score:+.2f}")
    console.print(f"  Recent avg   : {vel.recent_avg:.1f} publications/month "
                  f"(last {RECENT_MONTHS} months)")
    console.print(f"  Baseline     : {vel.baseline_mean:.1f} +/- {vel.baseline_std:.1f} "
                  f"publications/month ({HISTORY_MONTHS - RECENT_MONTHS}-month window)")
    console.print(f"  Acceleration : {_accel_str(vel.acceleration_pct)} vs prior equal window")
    console.print(f"  Peak month   : {vel.peak_month} ({vel.peak_count} publications)")
    console.print()


def print_brief(domain: str | None, text: str) -> None:
    title = (
        f"[bold]Regulatory Climate Brief -- {domain} ({DOMAINS[domain]['name']})[/bold]"
        if domain
        else "[bold]Regulatory Climate Brief -- All Defense Domains[/bold]"
    )
    console.print(Panel(text, title=title, border_style="cyan"))
    console.print()


def print_json_export(velocities: dict[str, DomainVelocity]) -> None:
    data = {
        domain: {
            "alert_level": vel.alert_level,
            "z_score": vel.z_score,
            "recent_avg_per_month": vel.recent_avg,
            "baseline_mean": vel.baseline_mean,
            "baseline_std": vel.baseline_std,
            "acceleration_pct": vel.acceleration_pct,
            "peak_month": vel.peak_month,
            "peak_count": vel.peak_count,
            "months": vel.months,
            "counts": vel.counts,
        }
        for domain, vel in velocities.items()
    }
    console.print(json.dumps(data, indent=2))
