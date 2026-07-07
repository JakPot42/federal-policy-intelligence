"""`fpi comments` -- Rulemaking Comment Analyzer (P33) subcommands."""
from __future__ import annotations

import click

from .config import DEMO_MODE, DEMO_DOCKET_ID, STAKEHOLDER_TYPES, STANCES, THEMES
from .regulations_client import fetch_comments
from .comment_analyzer import analyze_comments
from .cluster_engine import build_summary, filter_analyses
from .memo_generator import generate_memo
from .dashboard import (
    console,
    print_banner,
    print_comments,
    print_memo,
    print_summary,
    print_themes,
    print_json_export,
)

_THEME_CHOICES = sorted(THEMES.keys()) + ["ALL"]
_STAK_CHOICES = sorted(STAKEHOLDER_TYPES.keys()) + ["ALL"]
_STANCE_CHOICES = sorted(STANCES.keys()) + ["ALL"]

_DEMO_HINT = "[dim]DEMO_MODE=True -- set DEMO_MODE=False for live Regulations.gov data.[/dim]"


@click.group()
def comments() -> None:
    """
    Rulemaking Comment Analyzer: ingests Regulations.gov public comments,
    clusters by theme and stakeholder type, generates structured decision memos.

    \b
    Data source: Regulations.gov API (free API key required for live mode)
    Demo docket: DoD-2023-OS-0063 (CMMC 2.0 Proposed Rule)

    Set DEMO_MODE=False + provide API keys for live mode.
    """


def _run_docket(docket_id: str, demo_mode: bool) -> tuple:
    """Shared: fetch -> analyze -> build_summary. Returns (summary, analyses)."""
    raw = fetch_comments(docket_id, demo_mode=demo_mode)
    if not raw:
        console.print(f"[red]No comments found for docket {docket_id}.[/red]")
        raise SystemExit(1)
    analyses = analyze_comments(raw, demo_mode=demo_mode)
    summary = build_summary(docket_id, analyses)
    return summary, analyses


@comments.command()
@click.argument("docket_id", default=DEMO_DOCKET_ID)
def analyze(docket_id: str) -> None:
    """Fetch and classify all comments for DOCKET_ID, then show the summary."""
    print_banner()
    console.print(f"[dim]Fetching comments for {docket_id}...[/dim]")
    summary, _ = _run_docket(docket_id, DEMO_MODE)
    print_summary(summary)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@comments.command()
@click.argument("docket_id", default=DEMO_DOCKET_ID)
def themes(docket_id: str) -> None:
    """Show per-theme comment breakdown for DOCKET_ID."""
    print_banner()
    summary, _ = _run_docket(docket_id, DEMO_MODE)
    print_summary(summary)
    print_themes(summary)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@comments.command()
@click.argument("docket_id", default=DEMO_DOCKET_ID)
@click.option("--theme", "-t", type=click.Choice(_THEME_CHOICES, case_sensitive=False), default="ALL", help="Filter by theme.")
@click.option("--stakeholder", "-s", type=click.Choice(_STAK_CHOICES, case_sensitive=False), default="ALL", help="Filter by stakeholder type.")
@click.option("--stance", type=click.Choice(_STANCE_CHOICES, case_sensitive=False), default="ALL", help="Filter by stance.")
@click.option("--limit", default=20, show_default=True, help="Max comments to show.")
def browse(docket_id: str, theme: str, stakeholder: str, stance: str, limit: int) -> None:
    """
    Browse comments for DOCKET_ID with optional filters.

    \b
    Examples:
      browse DoD-2023-OS-0063 --theme COST_AND_BURDEN
      browse DoD-2023-OS-0063 --stakeholder INDUSTRY --stance OPPOSE
    """
    print_banner()
    _, analyses = _run_docket(docket_id, DEMO_MODE)

    t = None if theme.upper() == "ALL" else theme.upper()
    s = None if stakeholder.upper() == "ALL" else stakeholder.upper()
    st = None if stance.upper() == "ALL" else stance.upper()

    filtered = filter_analyses(analyses, theme=t, stakeholder_type=s, stance=st)
    if not filtered:
        console.print("[yellow]No comments match the selected filters.[/yellow]")
        return
    console.print(
        f"  [dim]{len(filtered)} comment{'s' if len(filtered) != 1 else ''}"
        + (" matching filters" if any([t, s, st]) else "")
        + "[/dim]\n"
    )
    print_comments(filtered, max_show=limit)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@comments.command()
@click.argument("docket_id", default=DEMO_DOCKET_ID)
def memo(docket_id: str) -> None:
    """Generate a structured government decision memorandum for DOCKET_ID."""
    print_banner()
    console.print(f"[dim]Analyzing {docket_id} and generating decision memo...[/dim]")
    summary, _ = _run_docket(docket_id, DEMO_MODE)
    text = generate_memo(summary, demo_mode=DEMO_MODE)
    print_memo(text, docket_id)
    if DEMO_MODE:
        console.print(_DEMO_HINT)


@comments.command()
@click.argument("docket_id", default=DEMO_DOCKET_ID)
def export(docket_id: str) -> None:
    """Export comment analysis as JSON."""
    summary, _ = _run_docket(docket_id, DEMO_MODE)
    print_json_export(summary)


def run_demo() -> None:
    """Full P33 demo against seeded CMMC 2.0 data. No API keys required.
    Shared by `fpi comments demo` and the top-level `fpi demo`."""
    print_banner()
    docket_id = DEMO_DOCKET_ID

    console.rule(f"[bold]Comments Demo 1: Volume Summary -- {docket_id}[/bold]")
    summary, analyses = _run_docket(docket_id, demo_mode=True)
    print_summary(summary)

    console.rule("[bold]Comments Demo 2: Theme Breakdown[/bold]")
    print_themes(summary)

    console.rule("[bold]Comments Demo 3: OPPOSE Comments[/bold]")
    print_comments(filter_analyses(analyses, stance="OPPOSE"))

    console.rule("[bold]Comments Demo 4: INDUSTRY Stakeholder[/bold]")
    print_comments(filter_analyses(analyses, stakeholder_type="INDUSTRY"))

    console.rule("[bold]Comments Demo 5: Decision Memorandum[/bold]")
    print_memo(generate_memo(summary, demo_mode=True), docket_id)


@comments.command()
def demo() -> None:
    """Run all Comment Analyzer demos against seeded CMMC 2.0 data."""
    run_demo()
