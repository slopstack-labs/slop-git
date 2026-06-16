"""Helpers for calling real git commands via subprocess.

Every function returns gracefully on error rather than raising — a missing git
binary or a directory that is not a git repository should produce a friendly
message at the CLI layer, not a traceback.
"""

from __future__ import annotations

import subprocess


def run_git(*args: str, capture: bool = True, cwd: str | None = None) -> tuple[str, str, int]:
    """Run a real git command, return (stdout, stderr, returncode)."""
    result = subprocess.run(
        ["git"] + list(args),
        capture_output=capture,
        text=True,
        cwd=cwd,
    )
    return result.stdout, result.stderr, result.returncode


def get_staged_diff() -> str:
    """Return the currently staged diff as a string."""
    out, _, _ = run_git("diff", "--cached")
    return out


def get_current_branch() -> str:
    """Return the name of the current branch."""
    out, _, _ = run_git("rev-parse", "--abbrev-ref", "HEAD")
    return out.strip()


def get_commit_log(n: int = 20) -> list[dict]:
    """Return last n commits as list of dicts with hash, author, date, message."""
    fmt = "%H\x1f%an\x1f%ad\x1f%s"
    out, _, _ = run_git("log", f"-{n}", f"--format={fmt}", "--date=short")
    commits = []
    for line in out.strip().splitlines():
        if line:
            parts = line.split("\x1f")
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                })
    return commits


def get_remotes() -> list[str]:
    """Return a list of configured remote names."""
    out, _, _ = run_git("remote")
    return [r for r in out.strip().splitlines() if r]


def count_commits_ahead(remote: str, branch: str) -> int:
    """Return the number of local commits not yet on remote/branch."""
    ref = f"{remote}/{branch}"
    out, _, code = run_git("rev-list", "--count", f"{ref}..HEAD")
    if code != 0:
        # If the remote ref doesn't exist yet, count all commits
        out, _, code = run_git("rev-list", "--count", "HEAD")
        if code != 0:
            return 0
    try:
        return int(out.strip())
    except ValueError:
        return 0


def get_file_blame(file_path: str) -> list[dict]:
    """Return blame info as list of dicts with author, date, content."""
    out, _, code = run_git("blame", "--line-porcelain", file_path)
    if code != 0:
        return []
    lines = []
    current: dict = {}
    for line in out.splitlines():
        if line.startswith("author "):
            current["author"] = line[7:]
        elif line.startswith("author-time "):
            import datetime
            try:
                ts = int(line[12:])
                current["date"] = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except (ValueError, OSError):
                current["date"] = "unknown"
        elif line.startswith("\t"):
            current["content"] = line[1:]
            lines.append(dict(current))
            current = {}
    return lines


def get_merge_conflict_files() -> list[str]:
    """Return list of files with merge conflicts (unmerged paths)."""
    out, _, _ = run_git("diff", "--name-only", "--diff-filter=U")
    return [f for f in out.strip().splitlines() if f]


def read_conflict_sections(file_path: str) -> tuple[str, str, str]:
    """Parse a file with merge conflict markers.

    Returns (ours_content, theirs_content, full_original).
    ours_content is the HEAD version, theirs_content is the incoming version.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return "", "", ""

    ours_parts: list[str] = []
    theirs_parts: list[str] = []
    in_ours = False
    in_theirs = False

    for line in content.splitlines():
        if line.startswith("<<<<<<<"):
            in_ours = True
            in_theirs = False
        elif line.startswith("=======") and in_ours:
            in_ours = False
            in_theirs = True
        elif line.startswith(">>>>>>>") and in_theirs:
            in_theirs = False
        elif in_ours:
            ours_parts.append(line)
        elif in_theirs:
            theirs_parts.append(line)

    return "\n".join(ours_parts), "\n".join(theirs_parts), content


def is_git_repo() -> bool:
    """Return True if the current directory is inside a git repository."""
    _, _, code = run_git("rev-parse", "--git-dir")
    return code == 0
