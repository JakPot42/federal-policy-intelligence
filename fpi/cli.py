"""Federal Policy Intelligence -- unified `fpi` CLI.

Three federal regulatory/policy analysis tools under one command, each a
subcommand group:

  fpi comments   Rulemaking Comment Analyzer (P33)   -- Regulations.gov
  fpi policy     AI Policy Impact Simulator (P37)     -- cited-corpus simulation
  fpi velocity   Regulatory Velocity Tracker (P65)    -- Federal Register

Nesting resolves the command-name collisions the three standalone tools
had (each had its own `analyze`/`export`/`demo`).
"""
from __future__ import annotations

import click
from rich.console import Console

from fpi.comments.commands import comments, run_demo as _comments_demo
from fpi.policy.commands import policy, run_demo as _policy_demo
from fpi.velocity.commands import velocity, run_demo as _velocity_demo

_console = Console()


@click.group()
def cli() -> None:
    """
    Federal Policy Intelligence (fpi): three federal regulatory/policy
    analysis tools under one CLI.

    \b
      fpi comments   Rulemaking Comment Analyzer (Regulations.gov)
      fpi policy     AI Policy Impact Simulator (cited-corpus simulation)
      fpi velocity   Regulatory Velocity Tracker (Federal Register)
      fpi demo       Run all three tool demos end to end (no API keys)

    All three default to DEMO_MODE=True. Set DEMO_MODE=False for live data.
    """


cli.add_command(comments)
cli.add_command(policy)
cli.add_command(velocity)


@cli.command()
def demo() -> None:
    """Run all three tool demos end to end. No API keys required."""
    _console.rule("[bold cyan]FEDERAL POLICY INTELLIGENCE -- FULL DEMO[/bold cyan]")
    _console.print("[dim]comments (P33) + policy (P37) + velocity (P65)[/dim]\n")

    _console.rule("[bold]== 1/3  fpi comments ==[/bold]")
    _comments_demo()
    _console.rule("[bold]== 2/3  fpi policy ==[/bold]")
    _policy_demo()
    _console.rule("[bold]== 3/3  fpi velocity ==[/bold]")
    _velocity_demo()

    _console.rule("[bold cyan]END FULL DEMO[/bold cyan]")


if __name__ == "__main__":
    cli()
