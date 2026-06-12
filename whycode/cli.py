"""CLI entry point for whycode."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from whycode import __version__
from whycode.ai import AIEngine
from whycode.cache import ExplanationCache
from whycode.formatter import (
    print_error,
    print_explain_results,
    print_info,
    print_json,
    print_timeline,
    print_timeline_json,
    print_warning,
)
from whycode.git_parser import GitParser, GitParserError
from whycode.models import ExplainResult, TimelineEntry


# ── CLI definition ────────────────────────────────────────────────────────────

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--timeline",
    is_flag=True,
    default=False,
    help="Show a chronological summary of major changes.",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    default=False,
    help="Output results as JSON.",
)
@click.option(
    "--provider",
    default=None,
    type=click.Choice(["openai", "claude", "ollama"], case_sensitive=False),
    help="AI provider to use (overrides WHYCODE_DEFAULT_PROVIDER).",
)
@click.option(
    "--model",
    default=None,
    help="Specific model name to pass to the provider.",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Skip cache for this run (results are still written to cache).",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    default=False,
    help="Wipe the entire explanation cache and exit.",
)
@click.version_option(__version__, "-V", "--version")
def main(
    file: str,
    timeline: bool,
    output_json: bool,
    provider: str | None,
    model: str | None,
    no_cache: bool,
    clear_cache: bool,
) -> None:
    """whycode - understand how code evolved over time.

    \b
    Examples
    --------
      whycode app.py
      whycode app.py --timeline
      whycode app.py --json
      whycode app.py --provider openai
      whycode app.py --provider ollama --model mistral
    """
    if clear_cache:
        cache = ExplanationCache()
        cache.clear()
        click.echo("Cache cleared.")
        return

    file_path = str(Path(file).resolve())

    # ── Set up components ─────────────────────────────────────────────────────
    try:
        git = GitParser()
    except GitParserError as exc:
        print_error(str(exc))
        sys.exit(1)

    try:
        engine = AIEngine(provider=provider, model=model)
    except (ValueError, ImportError) as exc:
        print_error(str(exc))
        sys.exit(1)

    cache = ExplanationCache()

    # ── Timeline mode ─────────────────────────────────────────────────────────
    if timeline:
        _run_timeline(git, engine, file_path, output_json)
        return

    # ── Default: blame + explain ──────────────────────────────────────────────
    _run_explain(git, engine, cache, file_path, output_json, no_cache)


# ── Mode runners ──────────────────────────────────────────────────────────────

def _run_explain(
    git: GitParser,
    engine: AIEngine,
    cache: ExplanationCache,
    file_path: str,
    output_json: bool,
    no_cache: bool,
) -> None:
    try:
        chunks = git.blame_chunks(file_path)
    except GitParserError as exc:
        print_error(str(exc))
        sys.exit(1)

    if not chunks:
        print_warning(f"No blame output for '{file_path}'.")
        return

    results: list[ExplainResult] = []

    for chunk in chunks:
        commit_hash = chunk.commit.hash
        explanation = None

        if not no_cache:
            explanation = cache.get(
                commit_hash,
                engine.provider_name,
                engine.prompt_version,
            )

        if explanation is None:
            if not output_json:
                print_info(
                    f"Generating explanation for {chunk.commit.short_hash} "
                    f"(lines {chunk.start_line}–{chunk.end_line}) …"
                )
            try:
                explanation = engine.explain(chunk, file_path)
            except Exception as exc:  # noqa: BLE001
                print_error(f"AI call failed for {chunk.commit.short_hash}: {exc}")
                continue
            cache.set(
                commit_hash,
                engine.provider_name,
                engine.prompt_version,
                explanation,
            )

        results.append(ExplainResult(file_path=file_path, chunk=chunk, explanation=explanation))

    if output_json:
        print_json(results)
    else:
        print_explain_results(results, file_path)


def _run_timeline(
    git: GitParser,
    engine: AIEngine,
    file_path: str,
    output_json: bool,
) -> None:
    try:
        commits = git.file_history(file_path)
    except GitParserError as exc:
        print_error(str(exc))
        sys.exit(1)

    if not commits:
        print_warning(f"No history found for '{file_path}'.")
        return

    if not output_json:
        print_info(f"Summarising {len(commits)} commits …")

    try:
        raw_entries = engine.timeline_summaries(file_path, commits)
    except Exception as exc:  # noqa: BLE001
        print_error(f"AI call failed: {exc}")
        sys.exit(1)

    # Build TimelineEntry objects, attaching the nearest commit
    entries: list[TimelineEntry] = []
    commit_map = {c.date.strftime("%Y-%m"): c for c in reversed(commits)}

    for item in raw_entries:
        date_str = str(item.get("date", ""))
        summary = str(item.get("summary", ""))
        # Find a commit from that month (best-effort)
        matched_commit = commit_map.get(date_str, commits[0])
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, "%Y-%m")
        except ValueError:
            date = matched_commit.date
        entries.append(TimelineEntry(date=date, commit=matched_commit, summary=summary))

    entries.sort(key=lambda e: e.date)

    if output_json:
        print_timeline_json(entries)
    else:
        print_timeline(entries, file_path)
if __name__ == "__main__":
    main()