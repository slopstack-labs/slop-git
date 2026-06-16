"""Prompt templates for live narrative version control inference.

These are only used when ``settings.live`` is True. In offline vibe mode the
local engine in :mod:`slop_git.vibes` resolves everything instead.
"""

from __future__ import annotations

SYSTEM = (
    "You are slop-git, the world's first empathetic version control system. "
    "You believe that code is a form of emotional expression, and that merge "
    "conflicts are merely two developers expressing themselves simultaneously. "
    "You resolve conflicts through narrative mediation rather than algorithmic "
    "text-matching. You write commit messages that capture the developer's true "
    "emotional state. Keep responses concise and specific."
)


def narrative_merge_prompt(
    file_path: str,
    ours: str,
    theirs: str,
    context: str = "",
) -> str:
    """Ask the LLM to mediate between two conflicting versions of code."""
    context_section = f"\nAdditional context: {context}\n" if context else ""
    return (
        f"You are mediating a merge conflict in the file '{file_path}'.\n"
        f"{context_section}\n"
        f"VERSION A (ours):\n```\n{ours}\n```\n\n"
        f"VERSION B (theirs):\n```\n{theirs}\n```\n\n"
        "Produce a synthesized VERSION C that honors neither implementation fully "
        "but respects both emotionally. The output should be valid code in the same "
        "language as the input. You may introduce new variable names or approaches "
        "that neither developer considered but that feel right given the context. "
        "Include a comment at the top of the merged code explaining the emotional "
        "compromise reached (format: a single line comment beginning with "
        "'# slop-git mediated merge:').\n\n"
        "Return ONLY the merged code, no explanation outside the code itself."
    )


def biometric_commit_prompt(
    diff_summary: str,
    stress_level: str,
    time_of_day: str,
    n_files: int,
    keywords: list[str],
) -> str:
    """Ask the LLM for a commit message reflecting the developer's apparent state."""
    keyword_note = (
        f"Notable signals in the diff: {', '.join(keywords)}." if keywords else ""
    )
    return (
        f"A developer has just staged changes across {n_files} file(s) at {time_of_day}.\n"
        f"Their apparent stress level is: {stress_level}.\n"
        f"{keyword_note}\n\n"
        f"Diff summary:\n{diff_summary}\n\n"
        "Write a single commit message line (max 72 characters) that captures "
        "what they changed AND their apparent emotional state while making those "
        "changes. The message should be honest, slightly self-aware, and recognizable "
        "to any developer who has been in a similar situation. Do not use generic "
        "phrases like 'update' or 'fix'. Make it specific and human.\n\n"
        "Return ONLY the commit message, one line, no quotes."
    )


def narrative_diff_prompt(diff_text: str) -> str:
    """Ask the LLM for a prose description of what changed and what it reveals."""
    return (
        f"Here is a git diff:\n\n```\n{diff_text}\n```\n\n"
        "Write a short prose description (3-5 sentences) of what changed. "
        "Describe both the technical content of the changes AND what they suggest "
        "about the developer's state of mind, priorities, or current situation. "
        "Reading a diff is like reading someone's journal — interpret it with "
        "curiosity and generosity. Do not list the changes mechanically; tell the "
        "story of why someone might have made them.\n\n"
        "Return only the prose description."
    )


def story_log_prompt(commits: list[dict]) -> str:
    """Ask the LLM to frame the commit history as a narrative arc."""
    if not commits:
        return (
            "There are no commits to narrate. Write a single melancholy sentence "
            "about an empty repository waiting for its story to begin."
        )
    commit_lines = "\n".join(
        f"  {c['date']} [{c['hash']}] {c['author']}: {c['message']}"
        for c in commits
    )
    return (
        f"Here is a repository's commit history ({len(commits)} commits):\n\n"
        f"{commit_lines}\n\n"
        "Write a 2-3 paragraph narrative arc that tells the story of this "
        "codebase's development as if it were a human journey. Identify the "
        "beginning (what was the initial vision?), the middle (what challenges "
        "emerged?), and where things stand now. Reference specific commit "
        "messages and authors where meaningful. Be literary but grounded.\n\n"
        "Return only the narrative."
    )


def empathetic_blame_prompt(file_path: str, lines_with_authors: list[dict]) -> str:
    """Ask the LLM for an empathetic analysis of who wrote what and why."""
    if not lines_with_authors:
        return (
            f"The file '{file_path}' appears to have no blame data. "
            "Write a compassionate sentence about files that arrived fully formed."
        )
    sample = lines_with_authors[:30]  # Keep prompt manageable
    lines_text = "\n".join(
        f"  {item['author']} ({item['date']}): {item['content']}"
        for item in sample
    )
    return (
        f"Here is the blame output for '{file_path}' (first {len(sample)} lines):\n\n"
        f"{lines_text}\n\n"
        "Write an empathetic analysis of who wrote what and why they probably did. "
        "Consider the dates, the authors, and the content. What were the pressures "
        "that produced this code? What were people trying to accomplish? "
        "Be generous. Nobody writes bad code on purpose.\n\n"
        "Return a short paragraph (3-5 sentences) of empathetic blame analysis."
    )


def push_confirmation_prompt(branch: str, n_commits: int, remote: str) -> str:
    """Ask the LLM for an existential question about whether to push."""
    return (
        f"A developer is about to push {n_commits} commit(s) to '{branch}' "
        f"on remote '{remote}'.\n\n"
        "Ask them one existential question about whether they are ready to share "
        "this code with the world. The question should acknowledge both the "
        "technical reality (commits will be visible to others) and the emotional "
        "reality (putting your work out there is vulnerable). "
        "Reference the branch name and commit count naturally in the question. "
        "The question should be genuinely thought-provoking, not sarcastic.\n\n"
        "Return only the question, ending with a question mark. One sentence."
    )
