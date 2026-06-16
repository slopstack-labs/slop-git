"""Offline tests for slop-git — no git binary, no network, no credentials."""

import pytest
import slop_git
from slop_git import vibes
from slop_git.biometrics import diff_keywords, read_system_state
from slop_git.config import configure


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    configure(live=False)
    yield


# ---------------------------------------------------------------------------
# stress estimation
# ---------------------------------------------------------------------------

def test_estimate_stress_high_cpu():
    assert vibes.estimate_stress(cpu_percent=95, hour=14, diff_lines=50) == "high"


def test_estimate_stress_late_night():
    assert vibes.estimate_stress(cpu_percent=20, hour=2, diff_lines=10) == "late_night"


def test_estimate_stress_late_night_boundary():
    assert vibes.estimate_stress(cpu_percent=10, hour=23, diff_lines=0) == "late_night"


def test_estimate_stress_early_morning():
    assert vibes.estimate_stress(cpu_percent=30, hour=5, diff_lines=10) == "early_morning"


def test_estimate_stress_low():
    assert vibes.estimate_stress(cpu_percent=20, hour=10, diff_lines=10) == "low"


def test_estimate_stress_medium_cpu():
    assert vibes.estimate_stress(cpu_percent=50, hour=10, diff_lines=50) == "medium"


def test_estimate_stress_hotfix_overrides():
    # Hotfix keyword should push to high even at low CPU
    assert vibes.estimate_stress(cpu_percent=5, hour=10, diff_lines=5, has_hotfix_keywords=True) == "high"


# ---------------------------------------------------------------------------
# commit messages
# ---------------------------------------------------------------------------

def test_commit_message_returns_string():
    msg = vibes.commit_message("medium", hour=14, diff_lines=20)
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_commit_message_high_stress_is_relatable():
    msg = vibes.commit_message("high", hour=17, diff_lines=300)
    assert isinstance(msg, str)
    assert len(msg) > 5


def test_commit_message_all_pools():
    for level in ("low", "medium", "high", "late_night", "early_morning"):
        msg = vibes.commit_message(level, hour=14, diff_lines=10)
        assert isinstance(msg, str)


def test_commit_message_nondeterministic():
    seen = {vibes.commit_message("high", hour=17, diff_lines=42) for _ in range(15)}
    assert len(seen) > 1, "commit_message should be non-deterministic"


def test_commit_message_late_night_interpolates_hour():
    # Hour placeholder should be filled in
    messages = [vibes.commit_message("late_night", hour=2, diff_lines=0) for _ in range(20)]
    assert all("{hour}" not in m for m in messages)


# ---------------------------------------------------------------------------
# narrative diff
# ---------------------------------------------------------------------------

def test_narrative_diff_returns_string():
    diff = "diff --git a/foo.py b/foo.py\n+++ b/foo.py\n+x = 1\n-x = 0\n"
    result = vibes.narrative_diff(diff)
    assert isinstance(result, str)
    assert len(result) > 10


def test_narrative_diff_empty():
    result = vibes.narrative_diff("")
    assert isinstance(result, str)
    assert len(result) > 0


def test_narrative_diff_whitespace_only():
    result = vibes.narrative_diff("   \n  ")
    assert isinstance(result, str)


def test_narrative_diff_nondeterministic():
    diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+y = 2\n"
    seen = {vibes.narrative_diff(diff) for _ in range(10)}
    assert len(seen) > 1, "narrative_diff should be non-deterministic"


# ---------------------------------------------------------------------------
# story log
# ---------------------------------------------------------------------------

def test_story_log_returns_string():
    commits = [
        {"hash": "a1b2c3d4", "author": "Alice", "date": "2026-01-01", "message": "Initial commit"},
        {"hash": "e5f6g7h8", "author": "Bob",   "date": "2026-01-05", "message": "Fix the bug"},
    ]
    result = vibes.story_log(commits)
    assert isinstance(result, str)
    assert len(result) > 0


def test_story_log_empty():
    result = vibes.story_log([])
    assert isinstance(result, str)
    assert len(result) > 0


def test_story_log_nondeterministic():
    commits = [
        {"hash": "a1b2c3d4", "author": "Alice", "date": "2026-01-01", "message": "Initial commit"},
    ]
    seen = {vibes.story_log(commits) for _ in range(10)}
    assert len(seen) > 1, "story_log should be non-deterministic"


# ---------------------------------------------------------------------------
# empathetic blame
# ---------------------------------------------------------------------------

def test_empathetic_blame_returns_string():
    blame_lines = [
        {"author": "Alice", "date": "2026-01-01", "content": "def foo():"},
        {"author": "Bob",   "date": "2026-01-09", "content": "    pass  # TODO: implement"},
    ]
    result = vibes.empathetic_blame("foo.py", blame_lines)
    assert isinstance(result, str)
    assert len(result) > 0


def test_empathetic_blame_empty():
    result = vibes.empathetic_blame("empty.py", [])
    assert isinstance(result, str)
    assert len(result) > 0


def test_empathetic_blame_nondeterministic():
    lines = [{"author": "Alice", "date": "2026-01-01", "content": "x = 1"}]
    seen = {vibes.empathetic_blame("f.py", lines) for _ in range(10)}
    assert len(seen) > 1


# ---------------------------------------------------------------------------
# push question
# ---------------------------------------------------------------------------

def test_push_question_returns_string():
    result = vibes.push_question("main", 3, "origin")
    assert isinstance(result, str)
    assert len(result) > 0


def test_push_question_contains_branch():
    result = vibes.push_question("feature-x", 2, "origin")
    assert "feature-x" in result


def test_push_question_contains_remote():
    result = vibes.push_question("main", 1, "upstream")
    assert "upstream" in result


def test_push_question_nondeterministic():
    seen = {vibes.push_question("main", 1, "origin") for _ in range(10)}
    assert len(seen) > 1


# ---------------------------------------------------------------------------
# narrative merge
# ---------------------------------------------------------------------------

def test_narrative_merge_returns_tuple():
    result = vibes.narrative_merge("file.py", "x = 1", "x = 2")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_narrative_merge_content_is_nonempty():
    merged, description = vibes.narrative_merge("file.py", "x = 1", "x = 2")
    assert isinstance(merged, str)
    assert len(merged) > 0


def test_narrative_merge_description_is_string():
    merged, description = vibes.narrative_merge("file.py", "a = 1", "b = 2")
    assert isinstance(description, str)
    assert len(description) > 0


def test_narrative_merge_multiline():
    ours = "def greet(name):\n    return f'Hello, {name}!'"
    theirs = "def greet(name, formal=False):\n    return f'Dear {name}'"
    merged, desc = vibes.narrative_merge("greet.py", ours, theirs)
    assert isinstance(merged, str)
    assert len(merged) > 0


def test_narrative_merge_nondeterministic():
    results = {vibes.narrative_merge("f.py", "a = 1\nb = 2", "a = 3\nc = 4")[0] for _ in range(10)}
    assert len(results) > 1


# ---------------------------------------------------------------------------
# diff_keywords
# ---------------------------------------------------------------------------

def test_diff_keywords_detects_hotfix():
    diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+# hotfix: urgent change\n"
    result = diff_keywords(diff)
    assert result["has_hotfix"] is True


def test_diff_keywords_detects_debug():
    diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+console.log('debug')\n"
    result = diff_keywords(diff)
    assert result["has_debug"] is True


def test_diff_keywords_clean():
    diff = "diff --git a/x.py b/x.py\n+++ b/x.py\n+x = 1\n"
    result = diff_keywords(diff)
    assert result["has_hotfix"] is False
    assert result["has_debug"] is False
    assert result["has_todo"] is False
    assert result["has_revert"] is False


def test_diff_keywords_detects_todo():
    diff = "+    # TODO: remove this later\n"
    result = diff_keywords(diff)
    assert result["has_todo"] is True


def test_diff_keywords_counts_files():
    diff = "diff --git a/a.py b/a.py\ndiff --git a/b.py b/b.py\n"
    result = diff_keywords(diff)
    assert result["n_files"] == 2


# ---------------------------------------------------------------------------
# merge-driver (offline)
# ---------------------------------------------------------------------------

def test_merge_driver_writes_merged_content(tmp_path):
    import tempfile, os
    from slop_git.cli import cmd_merge_driver
    import argparse

    base = tmp_path / "base.py"
    ours = tmp_path / "ours.py"
    theirs = tmp_path / "theirs.py"

    base.write_text("x = 0\n")
    ours.write_text("x = 1\n")
    theirs.write_text("x = 2\n")

    args = argparse.Namespace(base=str(base), ours=str(ours), theirs=str(theirs))
    rc = cmd_merge_driver(args)

    assert rc == 0
    merged = ours.read_text()
    assert len(merged) > 0


def test_merge_driver_identical_files_is_noop(tmp_path):
    from slop_git.cli import cmd_merge_driver
    import argparse

    content = "x = 42\n"
    base = tmp_path / "base.py"
    ours = tmp_path / "ours.py"
    theirs = tmp_path / "theirs.py"
    for p in (base, ours, theirs):
        p.write_text(content)

    args = argparse.Namespace(base=str(base), ours=str(ours), theirs=str(theirs))
    rc = cmd_merge_driver(args)
    assert rc == 0
    assert ours.read_text() == content


# ---------------------------------------------------------------------------
# prepare-commit-msg (offline)
# ---------------------------------------------------------------------------

def test_prepare_commit_msg_writes_message(tmp_path, monkeypatch):
    from slop_git.cli import cmd_prepare_commit_msg
    import argparse

    msgfile = tmp_path / "COMMIT_EDITMSG"
    msgfile.write_text("# Please enter the commit message.\n")

    # Monkeypatch git diff to return a fake staged diff
    monkeypatch.setattr("slop_git.cli._git.get_staged_diff", lambda: "+x = 1\n-x = 0\n")
    monkeypatch.setattr("slop_git.cli.read_system_state", lambda: {"hour": 14, "cpu_percent": 50.0})

    args = argparse.Namespace(msgfile=str(msgfile), source="", sha="")
    rc = cmd_prepare_commit_msg(args)

    assert rc == 0
    content = msgfile.read_text()
    non_comment = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
    assert len(non_comment) > 0


def test_prepare_commit_msg_skips_when_source_is_message(tmp_path):
    from slop_git.cli import cmd_prepare_commit_msg
    import argparse

    msgfile = tmp_path / "COMMIT_EDITMSG"
    original = "User provided message\n"
    msgfile.write_text(original)

    args = argparse.Namespace(msgfile=str(msgfile), source="message", sha="")
    rc = cmd_prepare_commit_msg(args)

    assert rc == 0
    assert msgfile.read_text() == original  # unchanged


def test_prepare_commit_msg_skips_empty_diff(tmp_path, monkeypatch):
    from slop_git.cli import cmd_prepare_commit_msg
    import argparse

    msgfile = tmp_path / "COMMIT_EDITMSG"
    original = "# comment\n"
    msgfile.write_text(original)

    monkeypatch.setattr("slop_git.cli._git.get_staged_diff", lambda: "")

    args = argparse.Namespace(msgfile=str(msgfile), source="", sha="")
    rc = cmd_prepare_commit_msg(args)
    assert rc == 0
    assert msgfile.read_text() == original  # unchanged when no staged diff


# ---------------------------------------------------------------------------
# package-level
# ---------------------------------------------------------------------------

def test_configure_returns_settings():
    s = configure(live=False)
    assert s is not None
    assert s.live is False


def test_version_is_string():
    assert isinstance(slop_git.__version__, str)
    assert len(slop_git.__version__) > 0
