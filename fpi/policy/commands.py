"""`fpi policy` -- AI Policy Impact Simulator (P37) subcommands."""
from __future__ import annotations

import sys

import click

from .claude_simulator import simulate_all
from .config import DEMO_MODE, PERSONAS
from .consequences import find_unintended_consequences
from .dashboard import (
    console,
    print_banner,
    print_consequences,
    print_persona_reports,
    print_scoring,
    print_search_results,
)
from .ingest import build_index
from .scoring import score_eu_risk_tier, score_nist_rmf_coverage

_RISKY_DEMO_DRAFT = """\
Section 4. Automated Eligibility Determination.
Covered agencies shall deploy a fully automated system to determine
eligibility for public assistance benefits and employment placement
services, including credit scoring inputs, without human review of
individual determinations. The system shall assign each applicant a
trustworthiness score based on prior application history and social
media activity. Facial recognition matching against a centrally
maintained facial recognition database, compiled in part from public
CCTV footage, shall be used to verify applicant identity for law
enforcement cross-checks. Covered agencies shall submit an annual
compliance certification to the Administrator.
"""

_NARROW_DEMO_DRAFT = """\
Section 2. Scope-Limited Pilot.
This pilot authorizes a single agency to test an AI system in a narrow,
well-defined intended use: flagging incomplete grant applications for
human caseworker review prior to any funding decision. The system does
not make or influence the final funding determination. An accountability
structure shall be established naming a responsible official for the
system's outcomes, and the system shall undergo documented testing and
validation, including bias and reliability evaluation, prior to
deployment. Risk treatment and monitoring plans shall be reviewed
quarterly by the named accountable official.
"""


def _simulate_and_print(draft_text: str, index) -> None:
    print_persona_reports(simulate_all(draft_text, index, PERSONAS))
    print_consequences(find_unintended_consequences(draft_text, index))
    print_scoring(score_nist_rmf_coverage(draft_text, index), score_eu_risk_tier(draft_text, index))


@click.group()
def policy() -> None:
    """
    AI Policy Impact Simulator: paste draft AI policy language and see how it
    interacts with real, cited regulatory text -- NIST AI RMF, DoD AI Ethical
    Principles, EU AI Act Articles 5 & 6, and the two most recent US AI
    executive orders (EO 14179, EO 14365).

    \b
    Every stakeholder reaction and unintended-consequence flag must cite a
    SPECIFIC passage from the indexed corpus; citation_verifier checks every
    citation against the real indexed text before it is shown as confirmed.
    """


@policy.command()
@click.option("--file", "file_path", type=click.Path(exists=True), help="Read draft policy text from a file.")
@click.option("--text", "text_arg", help="Draft policy text as a direct argument.")
def analyze(file_path: str | None, text_arg: str | None) -> None:
    """Run the full simulation (personas + consequences + scoring) on a draft."""
    if file_path:
        draft_text = open(file_path, encoding="utf-8").read()
    elif text_arg:
        draft_text = text_arg
    elif not sys.stdin.isatty():
        draft_text = sys.stdin.read()
    else:
        draft_text = ""

    if not draft_text.strip():
        console.print("[red]Provide non-empty draft text via --file, --text, or stdin.[/red]")
        raise SystemExit(1)

    print_banner()
    _simulate_and_print(draft_text, build_index())
    if DEMO_MODE:
        console.print("[dim]DEMO_MODE=True -- persona reactions use a deterministic corpus match, not a live Claude call.[/dim]")


@policy.command()
@click.argument("query")
@click.option("--top", type=int, default=5, help="Number of results to show.")
def search(query: str, top: int) -> None:
    """Search the indexed corpus directly."""
    print_banner()
    index = build_index()
    print_search_results(query, index.search(query, top_k=top))


@policy.command(name="corpus")
def show_corpus() -> None:
    """List every indexed document and section -- full transparency on what this tool can cite."""
    print_banner()
    index = build_index()
    docs: dict[str, list] = {}
    for c in index.chunks:
        docs.setdefault(c.doc_id, []).append(c)
    console.rule("[bold]Indexed Corpus[/bold]")
    for doc_id, chunks in docs.items():
        c0 = chunks[0]
        status_color = "green" if c0.status == "ACTIVE" else "yellow"
        console.print(f"[bold]{c0.title}[/bold]  [{status_color}]{c0.status}[/{status_color}]  ({c0.date})")
        console.print(f"  {c0.source_url}")
        for c in chunks:
            console.print(f"    - {c.section_id}")
        console.print()


def run_demo() -> None:
    """Full P37 demo against two pre-written drafts. No API keys required.
    Shared by `fpi policy demo` and the top-level `fpi demo`."""
    print_banner()
    index = build_index()

    console.rule("[bold]Policy Demo 1: Broad, Fully-Automated Eligibility Draft[/bold]")
    console.print("[dim]Written to intersect several real prohibited/high-risk provisions.[/dim]\n")
    _simulate_and_print(_RISKY_DEMO_DRAFT, index)

    console.rule("[bold]Policy Demo 2: Narrow, Human-Reviewed Pilot Draft[/bold]")
    console.print("[dim]Written to score well against the same rubric.[/dim]\n")
    _simulate_and_print(_NARROW_DEMO_DRAFT, index)

    console.print("[dim]DEMO_MODE=True -- all persona reactions use a deterministic corpus match, not a live Claude call.[/dim]")


@policy.command()
def demo() -> None:
    """Run the simulator against two pre-written example drafts."""
    run_demo()
