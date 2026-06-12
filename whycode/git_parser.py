"""Git parsing layer — blame, log, diff extraction via GitPython."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo
from git.exc import GitCommandError

from whycode.models import BlameChunk, CommitInfo


class GitParserError(Exception):
    """Raised when Git operations fail."""


class GitParser:
    """Wraps GitPython to extract blame chunks and commit context."""

    def __init__(self, repo_path: str | Path | None = None) -> None:
        search_path = str(repo_path) if repo_path else os.getcwd()
        try:
            self._repo = Repo(search_path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise GitParserError(
                f"No Git repository found at or above '{search_path}'"
            ) from exc

    # ── public API ────────────────────────────────────────────────────────────

    def blame_chunks(self, file_path: str | Path) -> list[BlameChunk]:
        """Return a deduplicated list of BlameChunk objects for *file_path*."""
        rel_path = self._relative(file_path)
        try:
            blame_output = self._repo.blame("HEAD", str(rel_path))
        except GitCommandError as exc:
            raise GitParserError(f"git blame failed for '{rel_path}': {exc}") from exc

        chunks: list[BlameChunk] = []
        current_line = 1

        for commit, lines in blame_output:
            raw_lines = [
                line.decode("utf-8", errors="replace") if isinstance(line, bytes) else line
                for line in lines
            ]
            end_line = current_line + len(raw_lines) - 1
            commit_info = self._commit_info(commit, str(rel_path))
            chunks.append(
                BlameChunk(
                    start_line=current_line,
                    end_line=end_line,
                    commit=commit_info,
                    lines=raw_lines,
                )
            )
            current_line = end_line + 1

        return self._merge_same_commit(chunks)

    def file_history(
        self, file_path: str | Path, max_commits: int = 40
    ) -> list[CommitInfo]:
        """Return the commit history for *file_path*, newest first."""
        rel_path = self._relative(file_path)
        commits: list[CommitInfo] = []
        try:
            for commit in self._repo.iter_commits(paths=str(rel_path), max_count=max_commits):
                commits.append(self._commit_info(commit, str(rel_path)))
        except GitCommandError as exc:
            raise GitParserError(f"git log failed for '{rel_path}': {exc}") from exc
        return commits

    # ── internals ────────────────────────────────────────────────────────────

    def _relative(self, file_path: str | Path) -> Path:
        """Return *file_path* relative to the repo root, resolving absolute paths."""
        p = Path(file_path)
        if p.is_absolute():
            try:
                return p.relative_to(Path(self._repo.working_dir))
            except ValueError:
                pass
        return p

    def _commit_info(self, commit, file_path: str) -> CommitInfo:
        """Build a CommitInfo from a GitPython Commit object."""
        diff = self._diff_for_file(commit, file_path)
        nearby = self._nearby_commits(commit, file_path)

        # Normalise timezone-aware datetime
        authored_date = datetime.fromtimestamp(commit.authored_date, tz=timezone.utc)

        return CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:7],
            author=commit.author.name or "Unknown",
            email=commit.author.email or "",
            date=authored_date,
            message=commit.message.strip(),
            diff=diff,
            nearby_commits=nearby,
        )

    def _diff_for_file(self, commit, file_path: str) -> str:
        """Return the unified diff for *file_path* in *commit*."""
        try:
            if not commit.parents:
                # Initial commit — diff against empty tree
                diffs = commit.diff(None, paths=[file_path], create_patch=True)
            else:
                diffs = commit.parents[0].diff(commit, paths=[file_path], create_patch=True)

            parts: list[str] = []
            for d in diffs:
                if d.diff:
                    parts.append(
                        d.diff.decode("utf-8", errors="replace")
                        if isinstance(d.diff, bytes)
                        else d.diff
                    )
            return "\n".join(parts)[:4000]  # cap to avoid huge prompts
        except Exception:  # noqa: BLE001
            return ""

    def _nearby_commits(self, commit, file_path: str, window: int = 3) -> list[str]:
        """Return short hashes of commits near *commit* that also touched *file_path*."""
        try:
            all_commits = list(
                self._repo.iter_commits(paths=file_path, max_count=50)
            )
            idx = next(
                (i for i, c in enumerate(all_commits) if c.hexsha == commit.hexsha),
                None,
            )
            if idx is None:
                return []
            start = max(0, idx - window)
            end = min(len(all_commits), idx + window + 1)
            return [
                c.hexsha[:7]
                for c in all_commits[start:end]
                if c.hexsha != commit.hexsha
            ]
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _merge_same_commit(chunks: list[BlameChunk]) -> list[BlameChunk]:
        """Merge consecutive chunks that share the same commit hash."""
        if not chunks:
            return []
        merged: list[BlameChunk] = [chunks[0]]
        for chunk in chunks[1:]:
            prev = merged[-1]
            if prev.commit.hash == chunk.commit.hash:
                prev.end_line = chunk.end_line
                prev.lines.extend(chunk.lines)
            else:
                merged.append(chunk)
        return merged
