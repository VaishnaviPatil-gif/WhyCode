"""Tests for git_parser — using mocked GitPython objects."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from whycode.git_parser import GitParser, GitParserError


def _make_mock_commit(
    hexsha: str = "a7b3f2c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
    name: str = "Jane Doe",
    email: str = "jane@example.com",
    message: str = "Add retry logic",
    authored_date: int = 1710460800,  # 2024-03-15 UTC
) -> MagicMock:
    commit = MagicMock()
    commit.hexsha = hexsha
    commit.author.name = name
    commit.author.email = email
    commit.message = message
    commit.authored_date = authored_date
    commit.parents = []
    commit.diff.return_value = []
    return commit


@pytest.fixture()
def mock_repo():
    with patch("whycode.git_parser.Repo") as MockRepo:
        repo = MagicMock()
        MockRepo.return_value = repo
        repo.working_dir = "/fake/repo"
        yield repo


def test_blame_chunks_basic(mock_repo):
    commit = _make_mock_commit()
    mock_repo.blame.return_value = [
        (commit, [b"line 1\n", b"line 2\n"]),
        (commit, [b"line 3\n"]),
    ]
    mock_repo.iter_commits.return_value = []

    parser = GitParser("/fake/repo")
    chunks = parser.blame_chunks("app.py")

    # Same commit → merged into one chunk
    assert len(chunks) == 1
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 3
    assert len(chunks[0].lines) == 3


def test_blame_chunks_two_commits(mock_repo):
    c1 = _make_mock_commit(hexsha="aaa" + "0" * 37)
    c2 = _make_mock_commit(hexsha="bbb" + "0" * 37)
    mock_repo.blame.return_value = [
        (c1, [b"line 1\n"]),
        (c2, [b"line 2\n"]),
    ]
    mock_repo.iter_commits.return_value = []

    parser = GitParser("/fake/repo")
    chunks = parser.blame_chunks("app.py")

    assert len(chunks) == 2
    assert chunks[0].end_line == 1
    assert chunks[1].start_line == 2


def test_blame_git_error_raises(mock_repo):
    from git.exc import GitCommandError
    mock_repo.blame.side_effect = GitCommandError("git blame", 128)

    parser = GitParser("/fake/repo")
    with pytest.raises(GitParserError, match="git blame failed"):
        parser.blame_chunks("nonexistent.py")


def test_file_history_returns_commits(mock_repo):
    commits = [_make_mock_commit(hexsha=f"{'a'*7}{i:033d}") for i in range(3)]
    mock_repo.iter_commits.return_value = commits

    parser = GitParser("/fake/repo")
    history = parser.file_history("app.py")

    assert len(history) == 3
    assert history[0].author == "Jane Doe"


def test_no_repo_raises(tmp_path):
    with pytest.raises(GitParserError, match="No Git repository"):
        GitParser(tmp_path)
