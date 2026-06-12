"""Rich terminal output and JSON formatter."""

from __future__ import annotations

import json
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box
from rich.text import Text

from whycode.models import ExplainResult, TimelineEntry

console = Console(stderr=False)
err_console = Console(stderr=True)


# ── Confidence colour helper ──────────────────────────────────────────────────

def _confidence_colour(score: int) -> str:
    if score >= 75:
        return "green"
    if score >= 45:
        return "yellow"
    return "red"


def _context_quality_colour(value: str) -> str:
    if value == "High":
        return "green"
    if value == "Medium":
        return "yellow"
    return "red"


# ── Rich output ───────────────────────────────────────────────────────────────

def print_explain_results(results: list[ExplainResult], file_path: str) -> None:
    """Render blame + AI explanation results to the terminal."""
    console.print()
    console.print(
        Rule(f"[bold cyan]whycode[/bold cyan]  [dim]{file_path}[/dim]", style="cyan")
    )

    for res in results:
        c = res.chunk.commit
        exp = res.explanation
        colour = _confidence_colour(exp.confidence)
        quality_colour = _context_quality_colour(exp.context_quality)

        # ── header ────────────────────────────────────────────────────────────
        header = (
            f"[bold]Lines {res.chunk.start_line}–{res.chunk.end_line}[/bold]  "
            f"[dim]│[/dim]  "
            f"[magenta]{c.short_hash}[/magenta]  "
            f"[dim]by[/dim] [cyan]{c.author}[/cyan]  "
            f"[dim]{c.date.strftime('%Y-%m-%d')}[/dim]"
        )
        console.print()
        console.print(header)
        console.print(f"  [italic dim]{c.message}[/italic dim]")

        # ── AI explanation panel ──────────────────────────────────────────────
        body = (
            f"[bold]Summary:[/bold] {exp.summary}\n\n"
            f"[bold]Rationale:[/bold] {exp.rationale}\n\n"
            f"[bold]Confidence:[/bold] [{colour}]{exp.confidence}/100[/{colour}]\n"
            f"[bold]Context Quality:[/bold] "
            f"[{quality_colour}]{exp.context_quality}[/{quality_colour}]"
        )
        console.print(
            Panel(body, border_style="dim", padding=(0, 2))
        )

    console.print()


def print_timeline(entries: list[TimelineEntry], file_path: str) -> None:
    """Render the timeline view."""
    console.print()
    console.print(
        Rule(
            f"[bold cyan]whycode timeline[/bold cyan]  [dim]{file_path}[/dim]",
            style="cyan",
        )
    )
    console.print()

    table = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("date", style="bold yellow", no_wrap=True)
    table.add_column("summary", style="white")

    for entry in entries:
        table.add_row(entry.date.strftime("%Y-%m"), entry.summary)

    console.print(table)
    console.print()


# ── JSON output ───────────────────────────────────────────────────────────────

def print_json(results: list[ExplainResult]) -> None:
    """Dump results as pretty-printed JSON to stdout."""
    data = [r.to_dict() for r in results]
    print(json.dumps(data, indent=2, default=str))


def print_timeline_json(entries: list[TimelineEntry]) -> None:
    data = [e.to_dict() for e in entries]
    print(json.dumps(data, indent=2, default=str))


# ── Error / info helpers ──────────────────────────────────────────────────────

def print_error(message: str) -> None:
    err_console.print(f"[bold red]Error:[/bold red] {message}")


def print_info(message: str) -> None:
    err_console.print(f"[dim]{message}[/dim]")


def print_warning(message: str) -> None:
    err_console.print(f"[bold yellow]Warning:[/bold yellow] {message}")
