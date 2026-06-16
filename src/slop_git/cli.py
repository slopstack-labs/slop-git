"""slop-git command-line interface.

Usage:
    slop-git commit [--no-biometric]
    slop-git merge <branch>
    slop-git diff [<path>]
    slop-git log [--n <n>]
    slop-git blame <file>
    slop-git push [<remote>] [<branch>]
    slop-git help
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from . import vibes
from . import prompts
from . import git as _git
from .biometrics import diff_keywords, read_system_state
from .config import settings
from .llm import complete


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_git_repo() -> bool:
    """Print a message and return False if not in a git repo."""
    if not _git.is_git_repo():
        print(
            "slop-git: not a git repository (or any of the parent directories).\n"
            "  Run 'git init' to start a new repository, then return.",
            file=sys.stderr,
        )
        return False
    return True


def _print_banner(text: str) -> None:
    print(f"\n  {text}\n")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_commit(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    diff = _git.get_staged_diff()
    if not diff.strip():
        print("slop-git: nothing staged. Use 'git add' to stage changes.")
        return 1

    state = read_system_state()
    signals = diff_keywords(diff)

    hour = state["hour"]
    cpu = state["cpu_percent"]
    diff_lines = signals["n_lines_changed"]
    has_hotfix = signals["has_hotfix"]

    stress = vibes.estimate_stress(cpu, hour, diff_lines, has_hotfix)

    # Collect keyword signals for live mode
    keyword_list: list[str] = []
    if signals["has_hotfix"]:
        keyword_list.append("hotfix/urgent language")
    if signals["has_revert"]:
        keyword_list.append("revert")
    if signals["has_todo"]:
        keyword_list.append("TODO/FIXME markers")
    if signals["has_debug"]:
        keyword_list.append("debug statements")

    time_of_day = f"{hour:02d}:00"

    print(f"  Reading system state...")
    print(f"  Stress level detected: {stress.upper().replace('_', ' ')}")
    print(f"  Time: {time_of_day}  CPU: {cpu:.0f}%  Lines changed: {diff_lines}")
    print()

    message = complete(
        prompts.biometric_commit_prompt(
            diff_summary=diff[:1500],
            stress_level=stress,
            time_of_day=time_of_day,
            n_files=signals["n_files"],
            keywords=keyword_list,
        ),
        fallback=lambda: vibes.commit_message(stress, hour, diff_lines),
    )

    # Trim to 72 chars
    message = message.strip().rstrip('"').lstrip('"')
    if len(message) > 72:
        message = message[:69] + "..."

    print(f'  Generated commit message:\n    "{message}"\n')

    prompt_str = "  [s]lop-commit  [e]dit  [c]ustom  [a]bort: "
    try:
        choice = input(prompt_str).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.")
        return 1

    if choice in ("s", ""):
        result = subprocess.run(["git", "commit", "-m", message])
        return result.returncode

    elif choice == "e":
        # Open editor with the message
        editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "vi"))
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, prefix="slop_commit_"
        ) as f:
            f.write(message)
            tmpfile = f.name
        subprocess.run([editor, tmpfile])
        with open(tmpfile) as f:
            edited = f.read().strip()
        os.unlink(tmpfile)
        if edited:
            result = subprocess.run(["git", "commit", "-m", edited])
            return result.returncode
        print("Empty message — commit aborted.")
        return 1

    elif choice == "c":
        try:
            custom = input("  Custom message: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            return 1
        if custom:
            result = subprocess.run(["git", "commit", "-m", custom])
            return result.returncode
        print("Empty message — commit aborted.")
        return 1

    else:
        print("Aborted.")
        return 1


def cmd_merge(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    branch = args.branch

    print(f"  Initiating narrative merge of '{branch}'...")

    # Run the real merge (no commit so we can inspect conflicts)
    _, stderr, code = _git.run_git("merge", branch, "--no-commit", "--no-ff", capture=False)

    conflict_files = _git.get_merge_conflict_files()

    if not conflict_files:
        if code == 0:
            print(f"\n  No conflicts. The merge of '{branch}' proceeded cleanly.")
            print(
                "  slop-git nevertheless notes that even successful merges "
                "carry the weight of decisions made in parallel."
            )
            result = subprocess.run(["git", "commit", "--no-edit"])
            return result.returncode
        else:
            print(f"  Merge failed: {stderr}")
            return 1

    print(f"\n  {len(conflict_files)} conflict(s) detected. Beginning narrative mediation...\n")

    for file_path in conflict_files:
        print(f"  Resolving conflict in {file_path}...")

        ours, theirs, original = _git.read_conflict_sections(file_path)

        if not ours and not theirs:
            print(f"    Could not parse conflict markers in {file_path}. Skipping.")
            continue

        merged, description = (
            complete(
                prompts.narrative_merge_prompt(file_path, ours, theirs),
                fallback=lambda o=ours, t=theirs, p=file_path: vibes.narrative_merge(p, o, t),
            ),
            None,
        ) if settings.live else vibes.narrative_merge(file_path, ours, theirs)

        # Handle both cases (live returns str, offline returns tuple)
        if isinstance(merged, tuple):
            merged, description = merged
        else:
            description = vibes.narrative_merge.__doc__ or "Narrative synthesis complete."

        description_text = complete(
            prompts.narrative_merge_prompt(file_path, ours, theirs),
            fallback=lambda: description or "Mediation complete.",
        ) if False else (description or "Mediation complete.")

        if settings.safe_merge:
            out_path = file_path + ".slop_merge"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(merged)
            print(f"    Written to {out_path}")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(merged)
            _git.run_git("add", file_path)
            print(f"    Resolved in place: {file_path}")

        rng_desc = (
            complete(
                f"In one sentence, describe what it means that these two code versions were merged: "
                f"version A ({len(ours.splitlines())} lines) and version B ({len(theirs.splitlines())} lines).",
                fallback=lambda: description or "Synthesis achieved.",
            )
        )
        _print_banner(rng_desc)

    if settings.safe_merge:
        print(
            "  Narrative merges written to .slop_merge files.\n"
            "  Review them, copy the content you want into the originals,\n"
            "  then 'git add' and 'git commit' to complete the merge."
        )
    else:
        print("  All conflicts resolved. Run 'git commit' to complete the merge.")

    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    git_args = ["diff"]
    if hasattr(args, "path") and args.path:
        git_args.append(args.path)

    diff_text, _, _ = _git.run_git(*git_args)

    narrative = complete(
        prompts.narrative_diff_prompt(diff_text),
        fallback=lambda: vibes.narrative_diff(diff_text),
    )

    print()
    print(narrative)
    print()
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    n = getattr(args, "n", 20) or 20
    commits = _git.get_commit_log(n)

    narrative = complete(
        prompts.story_log_prompt(commits),
        fallback=lambda: vibes.story_log(commits),
    )

    print()
    print(narrative)
    print()
    return 0


def cmd_blame(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    file_path = args.file
    blame_lines = _git.get_file_blame(file_path)

    narrative = complete(
        prompts.empathetic_blame_prompt(file_path, blame_lines),
        fallback=lambda: vibes.empathetic_blame(file_path, blame_lines),
    )

    print()
    print(narrative)
    print()
    return 0


def cmd_push(args: argparse.Namespace) -> int:
    if not _require_git_repo():
        return 1

    remote = getattr(args, "remote", None) or (
        _git.get_remotes()[0] if _git.get_remotes() else "origin"
    )
    branch = getattr(args, "branch", None) or _git.get_current_branch()

    n_commits = _git.count_commits_ahead(remote, branch)

    question = complete(
        prompts.push_confirmation_prompt(branch, n_commits, remote),
        fallback=lambda: vibes.push_question(branch, n_commits, remote),
    )

    print()
    print(f"  {question}")
    print()

    try:
        choice = input("  [y]es / [n]o: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Push cancelled.")
        return 1

    if choice in ("y", "yes"):
        result = subprocess.run(["git", "push", remote, branch], capture_output=False)
        return result.returncode
    else:
        print("  Push cancelled. The code will wait.")
        return 0


def cmd_help(_args: argparse.Namespace) -> int:
    print("""
  slop-git — Narrative-Driven Version Control

  I'm not like other version control systems. I don't see your code as lines
  and diffs. I see it as the externalized thought process of a human being
  working under conditions that are rarely ideal.

  Commands:

    slop-git commit
      Reads your system's biometric state (CPU, time of day, diff entropy)
      and generates a commit message that reflects how you actually feel.
      No more "update stuff" or "fix bug". Let the machine witness you.

    slop-git merge <branch>
      Resolves merge conflicts through empathetic narrative synthesis rather
      than algorithmic text-matching. Both sides had a point. The result
      honors neither fully, but respects both emotionally.

    slop-git diff [<path>]
      Shows what changed as a prose narrative. Understanding why code changed
      is more important than seeing exactly what changed. This provides the why.

    slop-git log [--n <n>]
      Frames your commit history as a human story with a beginning, a crisis,
      and a current state. Default: last 20 commits.

    slop-git blame <file>
      Replaces accusatory line attribution with empathetic context. The author
      of every line was doing their best. This tool acknowledges that.

    slop-git push [<remote>] [<branch>]
      Asks you one question worth considering before your code enters the world.

  Environment:

    SLOP_GIT_LIVE=1         Enable live LLM inference (default: offline)
    SLOP_GIT_PROVIDER=X     Backend: anthropic, openai, google, ollama
    SLOP_GIT_SAFE_MERGE=1   Write merges to .slop_merge files (default: on)

  slop-git does not replace git. It wraps it. Real operations are delegated
  to the git binary on your PATH. Only the human-facing layer is replaced.
""")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slop-git",
        description="Narrative-driven version control.",
        add_help=False,
    )
    sub = parser.add_subparsers(dest="command")

    # commit
    p_commit = sub.add_parser("commit", help="Biometric commit message generation")
    p_commit.add_argument(
        "--no-biometric",
        action="store_true",
        help="Skip system state reading; use medium-stress message pool",
    )

    # merge
    p_merge = sub.add_parser("merge", help="Narrative merge conflict resolution")
    p_merge.add_argument("branch", help="Branch to merge into the current branch")

    # diff
    p_diff = sub.add_parser("diff", help="Narrative diff")
    p_diff.add_argument("path", nargs="?", help="Limit diff to this path")

    # log
    p_log = sub.add_parser("log", help="Story-mode commit history")
    p_log.add_argument("--n", type=int, default=20, help="Number of commits (default: 20)")

    # blame
    p_blame = sub.add_parser("blame", help="Empathetic blame")
    p_blame.add_argument("file", help="File to blame empathetically")

    # push
    p_push = sub.add_parser("push", help="Existential push confirmation")
    p_push.add_argument("remote", nargs="?", default=None, help="Remote name (default: origin)")
    p_push.add_argument("branch", nargs="?", default=None, help="Branch name (default: current)")

    # help
    sub.add_parser("help", help="Show this help in narrative form")

    return parser


_COMMAND_MAP = {
    "commit": cmd_commit,
    "merge": cmd_merge,
    "diff": cmd_diff,
    "log": cmd_log,
    "blame": cmd_blame,
    "push": cmd_push,
    "help": cmd_help,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        cmd_help(args)
        return 0

    handler = _COMMAND_MAP.get(args.command)
    if handler is None:
        print(f"slop-git: unknown command '{args.command}'", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
