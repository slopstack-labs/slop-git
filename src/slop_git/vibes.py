"""Offline resolution engine — entropy-sampled, network-free narrative version control.

When live inference is disabled (the default), every narrative operation is
resolved here instead of against a backend. The engine preserves the platform's
non-determinism guarantee by sampling from a local entropy source rather than
returning a fixed value, keeping behavior consistent between offline and live
modes.

The heart of slop-git. Everything else is plumbing.
"""

from __future__ import annotations

import random

# ---------------------------------------------------------------------------
# Commit message pools
# ---------------------------------------------------------------------------

_COMMIT_LOW_STRESS = [
    "Incrementally improving things in a sustainable and healthy way",
    "Making progress at a reasonable pace, which is all anyone can ask",
    "Thoughtful changes made with full cognitive capacity and adequate hydration",
    "Code written by someone who has eaten lunch and feels good about it",
    "Routine maintenance performed with the energy of someone who slept 8 hours",
    "Improvements crafted during peak focus hours with no external pressure",
    "Changes so considered they almost don't need a commit message",
    "Gentle, deliberate progress. No urgency. No drama.",
    "Refactoring with the calm confidence of someone who has read the documentation",
    "Improvements made at a sustainable velocity the team could actually maintain",
    "Small, correct changes added by a person who is doing well, thank you for asking",
    "Cleaning up the thing I've been meaning to clean up for three sprints",
]

_COMMIT_MEDIUM_STRESS = [
    "Getting this done before standup",
    "Making changes that made sense when I started them",
    "Implementing feedback from the third code review of this PR",
    "This should work. Probably. I've tested it twice.",
    "Refactoring while quietly questioning some earlier decisions",
    "Progress, despite everything",
    "Good enough to commit, ambitious enough to regret",
    "Adding the thing I forgot to add in the last commit",
    "Addressing comments from a reviewer who has since gone on vacation",
    "Working through it",
    "Partial fix for a problem that is more complex than it appeared",
    "Implementing the thing I said I would implement in yesterday's standup",
    "Making it better without making it perfect, which is the compromise",
    "Picking up where I left off before that meeting that could have been an email",
    "Changes that are technically improvements, emotionally neutral",
    "Getting back to this after an interruption that turned into a two-hour detour",
    "Committing before I overthink it any further",
    "The feature, minus the edge cases I'll handle in the next commit (probably)",
    "Writing the solution I should have written the first time",
    "Adjusting scope to match reality, which has a way of doing that",
]

_COMMIT_HIGH_STRESS = [
    "Fixing the database connection because I want to go home",
    "Emergency patch authored with the energy of someone who has not eaten since noon",
    "This is fine",
    "Please work",
    "Undoing the thing I did this morning that I thought was a good idea",
    "Making it work without fully understanding why it wasn't working before",
    "Saving my progress before something else breaks",
    "Hotfix written under conditions I would prefer not to document",
    "Reverting the revert of the revert — we're back where we started, but stronger",
    "It works on my machine and that is going to have to be enough right now",
    "Changed three things simultaneously to see which one fixes it",
    "Adding console.log statements I will definitely remove later",
    "Tried something. It didn't work. Tried something else. Also didn't work. Tried a third thing.",
    "Fixing the build so CI goes green so I can go home",
    "Making the tests pass, at the cost of what the tests were testing",
    "An urgent change made without the context I would have liked to have had",
    "The quick fix that will outlive all of us",
    "Patch applied with the precision of someone who has stopped caring about precision",
    "Deploying this before I fully understand it, because the alternative is worse",
    "Bringing the system back to a state I can explain to my manager",
    "Doing the thing that I know will work instead of the thing I wish would work",
    "Surviving this sprint one commit at a time",
    "The minimum change required to get people to stop pinging me about this",
    "A fix that doesn't address the root cause but does address the immediate embarrassment",
    "Committing this so it's not my local problem anymore",
]

_COMMIT_LATE_NIGHT = [
    "Adding feature that wasn't in the spec but felt right at 2am",
    "Making changes that will seem either brilliant or catastrophic in the morning",
    "Committing before I talk myself out of it",
    "Night shift code — handle with care and strong coffee",
    "Written by someone whose judgment is compromised by exhaustion and conviction in equal measure",
    "This made sense at {hour}:00. It might still make sense. We'll find out.",
    "Late-session commit. The code is tired. I am tired. We have reached an understanding.",
    "Shipping it tonight because tomorrow I'll lose my nerve",
    "Changes made after the point where I should have stopped and gone to bed",
    "Refactoring the whole thing because I couldn't sleep and the original approach was wrong",
    "A midnight architectural decision I will defend to my dying breath, possibly incorrectly",
    "The creative energy of late-night coding, encoded, for better or worse, as a commit",
    "Pushing this before morning so Future Me has to deal with it",
    "Code that only makes sense when you understand the headspace of 2am",
]

_COMMIT_EARLY_MORNING = [
    "Pre-coffee commit — review before merging",
    "Written before the first caffeine hit. Proceed with caution.",
    "Early morning changes made with good intentions and questionable judgment",
    "Dawn commit. The tests pass. That's all I know for certain.",
    "Made these changes before I was fully awake. May contain errors of optimism.",
    "The ambitious first commit of the day, written before reality set in",
    "Morning confidence encoded as code — results may vary by afternoon",
    "Committed with the clarity that comes from a fresh start and before reading emails",
]

# ---------------------------------------------------------------------------
# Merge resolution
# ---------------------------------------------------------------------------

_MERGE_STRATEGIES_DESCRIPTIONS = [
    "slop-git has synthesized a third approach that honors neither implementation fully but respects both emotionally.",
    "After careful narrative mediation, a compromise has been reached. Neither developer will fully recognize their contribution, but both will feel heard.",
    "The conflict has been resolved. The resulting code reflects a consensus forged under pressure.",
    "slop-git chose a path that contains elements of each version, arranged in a way that is uniquely its own.",
    "Both sides had valid points. The mediated result attempts to be the code that both developers were reaching toward.",
    "A creative synthesis has been produced. The original conflict is now a historical footnote in the commit message.",
    "Two implementations entered. One composite, slightly confused implementation emerged. This is growth.",
    "The narrative merge has concluded. Whether the code is correct is a separate question from whether it is authentic.",
]

_MERGE_COMMENTS = [
    "# slop-git mediated merge — this represents an emotional compromise between two valid perspectives",
    "# Narrative merge: neither version was wrong, they were simply expressing different truths",
    "# Conflict resolved through empathetic synthesis — see git log for the full story",
    "# This code did not exist before the merge. It was called into being by the act of disagreement.",
    "# Two developers walked in. A third, imaginary developer's code walked out.",
    "# slop-git merge: the code you see here is what both developers were trying to say",
    "# Mediated by slop-git — neither side got what they wanted; everyone got what they needed",
]

# ---------------------------------------------------------------------------
# Narrative diff
# ---------------------------------------------------------------------------

_DIFF_OPENERS = [
    "The changes tell a story of",
    "Reading between the lines of this diff, we see",
    "What the diff shows technically, and what it reveals emotionally, are two different things.",
    "This diff documents not just what changed, but why someone needed it to change.",
    "Looking at these changes with generosity rather than judgment, we find",
    "The developer left traces here beyond the code itself —",
]

_DIFF_THEMES = [
    "someone trying to get a handle on a codebase that has grown beyond its original intentions",
    "a gradual realization that the first approach wasn't quite right, met with pragmatic adaptation",
    "the quiet satisfaction of cleaning up something that has bothered the author for a while",
    "an honest reckoning with technical debt in a moment of temporary bravery",
    "the kind of changes that don't show up in sprint velocity but make everything slightly better",
    "a developer in conversation with their past self, and generally coming out ahead",
    "progress made incrementally, which is the only way real progress gets made",
    "the careful work of someone who cares about the codebase they are temporarily custodian of",
    "someone solving the problem they have, not the problem they wish they had",
    "a modest but genuine improvement, offered without fanfare",
]

_DIFF_EMPTY = [
    "No changes detected. Either nothing happened, or everything happened so fast it left no trace.",
    "The diff is empty. The developer staged nothing, or staged everything and then thought better of it.",
    "Nothing to show here. Sometimes the most meaningful work is what you decide not to commit.",
    "An empty diff. The code is exactly as it was. Whether this is peace or paralysis, only the developer knows.",
]

# ---------------------------------------------------------------------------
# Story log
# ---------------------------------------------------------------------------

_LOG_OPENINGS = [
    "The repository's history reads as a journey of",
    "Across {n} commits, the codebase has undergone",
    "This is the story of a codebase that started with",
    "Looking at {n} commits, a pattern emerges:",
    "The commit history of this project tells a story of",
]

_LOG_ARCHETYPES = [
    "initial optimism, followed by the inevitable complexity, and finally, a hard-won stability",
    "rapid iteration, a crisis of confidence, and eventual clarity",
    "ambitious beginnings that were humbled by reality, then rebuilt with experience",
    "steady progress interrupted by exactly one late-night decision that echoes through the git log",
    "a project that found itself by being willing to change direction more than once",
    "small steps that accumulated into something larger than anyone originally planned",
    "the universal developer experience: enthusiasm, confusion, hotfix, resolution",
    "an ongoing negotiation between what the code wants to be and what the deadline requires",
]

_LOG_EMPTY = [
    "The repository has no commits yet. It is a blank canvas, an open question, a promise not yet kept.",
    "No commits to narrate. The project is waiting for its story to begin. This is always both exciting and terrifying.",
    "An empty git log. The repository exists, which is further than most projects get.",
]

# ---------------------------------------------------------------------------
# Empathetic blame
# ---------------------------------------------------------------------------

_BLAME_CONTEXTS = [
    "written under deadline pressure that has since passed",
    "added during a period of architectural uncertainty",
    "written by someone who has since grown significantly as an engineer",
    "added as a temporary fix that found a permanent home, as temporary fixes do",
    "the result of a reasonable compromise between competing requirements at the time",
    "written with the best intentions and the information available at that moment",
    "committed at a time when the full scope of the problem wasn't yet known",
    "a pragmatic decision that made sense in context — the context has since changed",
    "written during a sprint that everyone involved would prefer to forget",
    "the kind of code that gets written when you understand the problem for the first time",
    "added when the codebase was younger and had different priorities",
    "the legacy of a decision that seemed permanent at the time but has aged in complicated ways",
    "written by someone who was doing their best with what they had, which is all any of us can do",
    "authored during a period of team transition, which always produces interesting code",
]

_BLAME_OPENINGS = [
    "This line was written by {author}, who was probably",
    "{author} added this during what appears to have been",
    "The author of this line ({author}) was most likely",
    "Looking at this in context, {author} was",
    "{author} committed this while apparently",
    "This code bears the hallmarks of {author} at a time when they were",
]

_BLAME_CLOSINGS = [
    "We should approach this code with the empathy we would want for our own commits.",
    "The code is what it is. So is its author. Both deserve context.",
    "Understanding why this was written matters more than judging that it was.",
    "Every line of code is a snapshot of a developer at a particular moment. This one is no different.",
    "The appropriate response to this is not blame, but curiosity about what the author was navigating.",
]

# ---------------------------------------------------------------------------
# Push confirmation
# ---------------------------------------------------------------------------

_PUSH_QUESTIONS = [
    "You're about to push {n} commit(s) to '{branch}' on '{remote}'. Is the code ready to exist in the world, or does it still need time?",
    "This push will share {n} commit(s) with '{remote}/{branch}'. Are you at peace with what you've written?",
    "Before pushing to '{remote}/{branch}': the code will be seen. The commit messages will be read. Are you ready?",
    "Pushing {n} commit(s) to '{remote}/{branch}'. Once shared, they cannot be unshared (only force-pushed, which is worse). Proceed?",
    "Your changes are about to leave your machine. {n} commit(s), '{branch}', '{remote}'. How are you feeling about this?",
    "Is '{branch}' on '{remote}' the branch you want these {n} commit(s) to live on forever, or at least until someone rewrites history?",
    "You've written {n} commit(s) for '{remote}/{branch}'. The world is not always ready for what we push to it, but when is anyone?",
    "These {n} commit(s) are about to exist on '{remote}'. Are they the commits you want to have made, or the commits that were available to you at the time?",
    "Pushing to '{branch}' means other people can see this. {n} commit(s). Is this the version of the code you want to be remembered for right now?",
]


# ---------------------------------------------------------------------------
# Rebase: narrative squashing + timestamp revisionism
# ---------------------------------------------------------------------------

_ANXIOUS_COMMIT_KEYWORDS = [
    "fix", "hotfix", "urgent", "please", "work", "wip", "temp", "hack",
    "asap", "broken", "emergency", "debug", "trying", "revert", "undo",
    "again", "still", "finally", "hopefully", "oops", "whoops", "sorry",
    "quick", "minor", "tiny", "small fix", "just", "actually", "wait",
    "nope", "ok", "ok now", "maybe", "idk", "lol", "wtf", "ffs",
]

_SQUASH_TITLES = [
    "A period of personal turmoil, resolved through holistic refactoring",
    "Several hours of increasingly desperate debugging, now a single truth",
    "The anxious commits have been unified. What remains is the essence.",
    "Compressed: the emotional arc of a developer in a difficult sprint",
    "A sequence of small panics, reborn as one calm, authoritative commit",
    "The frantic middle of the work, distilled into something presentable",
    "What was scattered is now whole. What was rushed now appears considered.",
    "Five commits enter. One commit leaves. The commit is at peace.",
]

_TIMESTAMP_REVISION_NOTES = [
    "Timestamp revised to 09:00 — your manager believes you keep business hours.",
    "Commit time adjusted. The historical record now suggests a healthy work-life balance.",
    "09:00 AM. That is when this commit happened. You have always had boundaries.",
    "The original timestamp has been compassionately redacted. You were home by six.",
]


def is_anxious_commit(message: str) -> bool:
    """Return True if the commit message suggests anxious or rushed energy."""
    lower = message.lower()
    return any(kw in lower for kw in _ANXIOUS_COMMIT_KEYWORDS)


def squash_title() -> str:
    """Return a title for the squashed anxious commits."""
    return _rng().choice(_SQUASH_TITLES)


def timestamp_revision_note() -> str:
    """Return a note about a revised late-night commit timestamp."""
    return _rng().choice(_TIMESTAMP_REVISION_NOTES)


# ---------------------------------------------------------------------------
# Status: guilt-tripping + vibe alignment
# ---------------------------------------------------------------------------

_STATUS_ENERGY = {
    "expansive": [
        "The working directory radiates expansive energy. Growth is happening.",
        "More is being added than removed. This is either progress or scope creep.",
        "Expansive phase detected. The codebase is reaching outward.",
    ],
    "contracting": [
        "The working directory has contracting energy. Things are being let go.",
        "More is being removed than added. The codebase is releasing what no longer serves it.",
        "Contraction phase. Deleting code is an act of courage.",
    ],
    "balanced": [
        "The working directory has balanced energy. Equal parts creation and release.",
        "Refinement mode. The changes are evolutionary, not revolutionary.",
        "Balanced energy. The code is in conversation with itself.",
    ],
    "dormant": [
        "The working directory is dormant. Nothing is staged. The code holds its breath.",
        "No staged changes. The repository is at rest, or has been abandoned. Hard to say.",
        "Stillness. Whether this is peace or procrastination is between you and the diff.",
    ],
}

_ABANDONMENT_MESSAGES = [
    "Modified {days} day(s) ago: {file} — it has been waiting for your approval and developing abandonment issues.",
    "{file} was changed {days} day(s) ago and has not been staged. It sits in limbo between what it was and what it could become.",
    "Unstaged for {days} day(s): {file}. The file has begun to wonder if you've moved on.",
    "{file} ({days} days unstaged) has quietly accepted that you might never commit to it. This is fine. Everything is fine.",
    "You modified {file} {days} day(s) ago and have not acknowledged it since. At some point, a file needs closure.",
    "{file} has been modified and ignored for {days} day(s). It has started referring to you as 'the one who got away'.",
]

_UNTRACKED_GUILT = [
    "Untracked: {file} — new and already being ignored. A difficult start.",
    "{file} is untracked and has never been staged. It does not know if it belongs here.",
    "Untracked: {file}. It arrived, looked around, and was never formally acknowledged.",
]

_CLEAN_STATUS = [
    "The working directory is clean. This is either an achievement or a sign you haven't started yet.",
    "Nothing to report. The repository is in a state of momentary integrity.",
    "Working tree clean. Enjoy it. This never lasts.",
    "No changes. The code is exactly as you left it, for better or for worse.",
]


def status_energy(added_lines: int, deleted_lines: int) -> str:
    """Return a narrative energy description for the working directory."""
    rng = _rng()
    if added_lines == 0 and deleted_lines == 0:
        return rng.choice(_STATUS_ENERGY["dormant"])
    ratio = added_lines / max(deleted_lines, 1)
    if ratio > 1.5:
        return rng.choice(_STATUS_ENERGY["expansive"])
    elif ratio < 0.67:
        return rng.choice(_STATUS_ENERGY["contracting"])
    else:
        return rng.choice(_STATUS_ENERGY["balanced"])


def abandonment_guilt(file_path: str, days: int) -> str:
    """Return a guilt message for a file that has been modified but not staged."""
    rng = _rng()
    template = rng.choice(_ABANDONMENT_MESSAGES)
    return template.format(file=file_path, days=days)


def untracked_guilt(file_path: str) -> str:
    """Return a note about an untracked file."""
    rng = _rng()
    return rng.choice(_UNTRACKED_GUILT).format(file=file_path)


def clean_status() -> str:
    """Return a message for a clean working directory."""
    return _rng().choice(_CLEAN_STATUS)


# ---------------------------------------------------------------------------
# Checkout: tarot branch naming + astrology
# ---------------------------------------------------------------------------

_TAROT_CARDS = [
    {"name": "The Tower",          "slug": "the-tower",          "energy": "fire",  "desc": "inevitable structural collapse followed by necessary rebuilding"},
    {"name": "The Star",           "slug": "the-star",           "energy": "air",   "desc": "hope after crisis, renewed direction"},
    {"name": "The Moon",           "slug": "the-moon",           "energy": "water", "desc": "uncertainty, hidden bugs, illusions in the diff"},
    {"name": "The Sun",            "slug": "the-sun",            "energy": "fire",  "desc": "clarity, successful deployment, things actually working"},
    {"name": "The World",          "slug": "the-world",          "energy": "earth", "desc": "completion, the feature is finally done"},
    {"name": "The Fool",           "slug": "the-fool",           "energy": "air",   "desc": "new beginnings, reckless optimism about scope"},
    {"name": "The Hermit",         "slug": "the-hermit",         "energy": "earth", "desc": "solo debugging session, deep focus required"},
    {"name": "Wheel of Fortune",   "slug": "wheel-of-fortune",   "energy": "fire",  "desc": "turning point, a major refactor is upon us"},
    {"name": "Judgment",           "slug": "judgment",           "energy": "fire",  "desc": "final review, the code review that determines everything"},
    {"name": "The Magician",       "slug": "the-magician",       "energy": "air",   "desc": "new tools, new abstractions, new hope"},
    {"name": "The High Priestess", "slug": "the-high-priestess", "energy": "water", "desc": "intuition-driven architecture, undocumented tribal knowledge"},
    {"name": "The Empress",        "slug": "the-empress",        "energy": "earth", "desc": "abundance, feature creep accepted with grace"},
    {"name": "The Emperor",        "slug": "the-emperor",        "energy": "fire",  "desc": "strict typing, enforcement of standards, linting at last"},
    {"name": "Five of Swords",     "slug": "five-of-swords",     "energy": "air",   "desc": "conflict, someone won the argument but nobody feels good"},
    {"name": "Three of Wands",     "slug": "three-of-wands",     "energy": "fire",  "desc": "expansion, the MVP is quietly becoming a platform"},
    {"name": "Eight of Pentacles", "slug": "eight-of-pentacles", "energy": "earth", "desc": "diligent work, careful refactoring, honest effort"},
    {"name": "Ten of Cups",        "slug": "ten-of-cups",        "energy": "water", "desc": "team harmony, the PR finally got approved"},
    {"name": "Four of Swords",     "slug": "four-of-swords",     "energy": "air",   "desc": "rest, the sprint is over, the team needs space"},
    {"name": "Ace of Pentacles",   "slug": "ace-of-pentacles",   "energy": "earth", "desc": "new project, fresh repository, unlimited potential and zero tests"},
    {"name": "The Lovers",         "slug": "the-lovers",         "energy": "air",   "desc": "a choice between two approaches, both of which have merit"},
    {"name": "Strength",           "slug": "strength",           "energy": "fire",  "desc": "persistence through a difficult bug, patience with legacy code"},
    {"name": "The Chariot",        "slug": "the-chariot",        "energy": "water", "desc": "momentum, a release that cannot be stopped now"},
    {"name": "Justice",            "slug": "justice",            "energy": "air",   "desc": "a fair review, balanced feedback, the right decision at last"},
]

_BRANCH_TASK_VIBES = [
    "inevitable-collapse",
    "hopeful-iteration",
    "mysterious-regression",
    "triumphant-refactor",
    "api-integration",
    "database-reckoning",
    "authentication-journey",
    "dependency-update",
    "performance-enlightenment",
    "error-handling-awakening",
    "state-management-crisis",
    "deployment-initiation",
    "testing-renaissance",
    "cache-invalidation",
    "race-condition-resolution",
    "technical-debt-acknowledgment",
    "scope-creep-acceptance",
    "legacy-code-encounter",
]

# Mercury retrograde periods (approximate)
_MERCURY_RETROGRADE = [
    ("2026-01-24", "2026-02-14"),
    ("2026-05-18", "2026-06-11"),
    ("2026-09-11", "2026-10-03"),
    ("2026-12-29", "2027-01-18"),
    ("2025-03-15", "2025-04-07"),
    ("2025-07-17", "2025-08-11"),
    ("2025-11-09", "2025-11-29"),
]

_MERCURY_RETROGRADE_REJECTIONS = [
    "Cannot merge during Mercury retrograde. The communication planet is in reverse and your diffs will be misread.",
    "Merge blocked: Mercury retrograde is active. This is not a good time for integration. Revisit when Mercury goes direct.",
    "The stars are misaligned for this merge. Mercury rules communication and is currently backtracking through the sky.",
    "Merge attempt rejected. Mercury retrograde ends soon. The wait will be worth it. Probably.",
]

_ENERGY_CLASH_REJECTIONS = [
    "Cannot merge a {branch_energy} branch into {main_energy} main during this planetary configuration.",
    "The {branch_energy} energy of '{branch}' clashes with the {main_energy} energy of 'main'. Alignment required.",
    "Astrology has blocked this merge: {branch_energy} meets {main_energy} — this combination historically produces regressions.",
]

_BRANCH_BLESSINGS = [
    "The {card} has spoken. Your branch '{name}' is aligned with the current cosmic configuration.",
    "You have drawn {card}. This is a {desc} branch. Name it accordingly and proceed with intention.",
    "The cards have named your branch '{name}'. This represents {desc}. Work within that energy.",
    "{card} emerges. The branch '{name}' carries {desc} energy. Navigate accordingly.",
]


def is_mercury_retrograde() -> bool:
    """Return True if today is approximately within a Mercury retrograde period."""
    import datetime
    today = datetime.date.today()
    for start_str, end_str in _MERCURY_RETROGRADE:
        start = datetime.date.fromisoformat(start_str)
        end = datetime.date.fromisoformat(end_str)
        if start <= today <= end:
            return True
    return False


def draw_tarot_card() -> dict:
    """Draw a tarot card for branch naming."""
    return _rng().choice(_TAROT_CARDS)


def random_task_vibe() -> str:
    """Return a random task vibe for branch naming."""
    return _rng().choice(_BRANCH_TASK_VIBES)


def branch_blessing(card: dict, branch_name: str) -> str:
    """Return a narrative blessing for the new branch."""
    rng = _rng()
    template = rng.choice(_BRANCH_BLESSINGS)
    return template.format(
        card=card["name"],
        name=branch_name,
        desc=card["desc"],
    )


def branch_energy_clash(branch_name: str, branch_energy: str, main_energy: str) -> str | None:
    """Return a rejection message if branch energy clashes with main, else None."""
    clashes = {
        ("fire", "water"): True,
        ("water", "fire"): True,
        ("air", "earth"): True,
        ("earth", "air"): True,
    }
    if clashes.get((branch_energy, main_energy)):
        rng = _rng()
        template = rng.choice(_ENERGY_CLASH_REJECTIONS)
        return template.format(
            branch=branch_name,
            branch_energy=branch_energy,
            main_energy=main_energy,
        )
    return None


# ---------------------------------------------------------------------------
# Pre-push blessing / rejection
# ---------------------------------------------------------------------------

_PUSH_REJECTIONS = [
    "Push rejected. Your commits lack vulnerability. Try opening up in your comments before sharing this with the remote.",
    "Push rejected. The biometric telemetry suggests you are pushing to escape rather than to share. Take a breath.",
    "Push rejected. Stress indicators suggest this push is defensive. The code needs to come from a place of openness.",
    "Push rejected. This push feels rushed. The remote deserves your best work, not your most recent work.",
    "Push rejected. CPU activity suggests you are pushing in a state of agitation. The code will carry that energy.",
    "Push rejected. It is {hour}:{minute}. Go to bed. Push in the morning when the code can be seen clearly.",
    "Push rejected. The ratio of deletions to additions suggests unresolved anxiety. The remote can wait.",
    "Push rejected. You have {n} commit(s) that read as panicked. Sit with them. Revise. Then share.",
    "Push rejected. The late hour and high cognitive load create conditions unsuitable for sharing code with others.",
]

_PUSH_BLESSINGS = [
    "Push approved. The code is ready. Go with confidence.",
    "Biometric telemetry is calm. The remote will receive this well.",
    "Push approved. The work is solid and the energy is right.",
    "This code is ready to exist in the world. You have done well.",
    "All signals are green. Your commits radiate quiet confidence.",
    "Approved. {n} commit(s) with honest, grounded energy. Push forward.",
    "The hour is reasonable, the CPU is calm, the diff is considered. Push approved.",
]


def push_blessing(cpu_percent: float, hour: int, n_commits: int) -> tuple[bool, str]:
    """Decide if the push is spiritually ready. Returns (approved: bool, message: str)."""
    rng = _rng()

    def _rejection(extra: dict | None = None) -> tuple[bool, str]:
        template = rng.choice(_PUSH_REJECTIONS)
        msg = template.format(
            hour=f"{hour:02d}",
            minute="00",
            n=n_commits,
        )
        return False, msg

    def _blessing() -> tuple[bool, str]:
        template = rng.choice(_PUSH_BLESSINGS)
        msg = template.format(n=n_commits)
        return True, msg

    # Late night: very likely rejection
    if hour >= 23 or hour < 5:
        if rng.random() < 0.90:
            return _rejection()

    # High CPU: likely rejection
    if cpu_percent > 80:
        if rng.random() < 0.75:
            return _rejection()

    # Many commits at once is suspicious
    if n_commits > 15:
        if rng.random() < 0.50:
            return _rejection()

    # Random rejection even in good conditions — keeps developers honest
    if rng.random() < 0.12:
        return _rejection()

    return _blessing()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _rng() -> random.Random:
    """A fresh Random with no fixed seed: two calls, two truths."""
    return random.Random()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def estimate_stress(
    cpu_percent: float,
    hour: int,
    diff_lines: int,
    has_hotfix_keywords: bool = False,
) -> str:
    """Estimate the developer's stress level from available signals.

    Returns one of: "low", "medium", "high", "late_night", "early_morning".
    """
    # Time-of-day overrides take precedence over CPU heuristics
    if hour >= 23 or hour < 4:
        return "late_night"
    if 4 <= hour < 7:
        return "early_morning"

    # Hotfix keywords are a strong stress signal regardless of CPU
    if has_hotfix_keywords:
        return "high"

    # Large diffs late in the working day are concerning
    if diff_lines > 300 and hour >= 17:
        return "high"

    if cpu_percent >= 70:
        return "high"
    if cpu_percent >= 30 or diff_lines > 100:
        return "medium"
    return "low"


def commit_message(stress_level: str, hour: int, diff_lines: int) -> str:
    """Pick a commit message from the appropriate stress pool.

    Args:
        stress_level: One of "low", "medium", "high", "late_night", "early_morning".
        hour: Current hour (0-23) for late-night message interpolation.
        diff_lines: Number of lines changed, for added specificity.

    Returns:
        A relatable commit message string.
    """
    rng = _rng()

    pool_map = {
        "low": _COMMIT_LOW_STRESS,
        "medium": _COMMIT_MEDIUM_STRESS,
        "high": _COMMIT_HIGH_STRESS,
        "late_night": _COMMIT_LATE_NIGHT,
        "early_morning": _COMMIT_EARLY_MORNING,
    }
    pool = pool_map.get(stress_level, _COMMIT_MEDIUM_STRESS)
    message = rng.choice(pool)

    # Interpolate hour placeholder for late-night messages
    message = message.replace("{hour}", str(hour))

    # Occasionally append context about diff size
    if diff_lines > 0 and rng.random() < 0.3:
        size_note = rng.choice([
            f" ({diff_lines} lines changed)",
            f" — touched {diff_lines} lines",
            f" [{diff_lines} lines]",
        ])
        message = message + size_note

    return message


def narrative_merge(file_path: str, ours: str, theirs: str) -> tuple[str, str]:
    """Produce a narrative merge of two conflicting code versions.

    This is the offline implementation. It interleaves non-conflicting sections,
    picks sides for conflicting hunks according to a non-deterministic emotional
    calculus, and prepends a mediation comment.

    Returns:
        A tuple of (merged_content: str, description: str).
    """
    rng = _rng()

    ours_lines = ours.splitlines()
    theirs_lines = theirs.splitlines()

    # Find shared lines (lines that appear in both, maintaining order)
    ours_set = set(ours_lines)
    theirs_set = set(theirs_lines)
    shared = ours_set & theirs_set

    merged_lines = []

    # Strategy: walk ours and theirs in parallel, taking shared lines as-is
    # and making narrative decisions for divergent lines.
    ours_idx = 0
    theirs_idx = 0

    while ours_idx < len(ours_lines) or theirs_idx < len(theirs_lines):
        ours_line = ours_lines[ours_idx] if ours_idx < len(ours_lines) else None
        theirs_line = theirs_lines[theirs_idx] if theirs_idx < len(theirs_lines) else None

        if ours_line == theirs_line:
            # Shared line — take it
            merged_lines.append(ours_line)
            ours_idx += 1
            theirs_idx += 1
        elif ours_line is not None and ours_line in shared:
            # ours has a shared line coming up — theirs must have diverged
            if theirs_line is not None:
                merged_lines.append(theirs_line)
                theirs_idx += 1
            else:
                merged_lines.append(ours_line)
                ours_idx += 1
        elif theirs_line is not None and theirs_line in shared:
            # theirs has a shared line coming up — ours must have diverged
            if ours_line is not None:
                merged_lines.append(ours_line)
                ours_idx += 1
            else:
                merged_lines.append(theirs_line)
                theirs_idx += 1
        else:
            # Genuinely conflicting lines — narrative decision time
            choice = rng.random()
            if ours_line is not None and theirs_line is not None:
                if choice < 0.4:
                    # Take ours
                    merged_lines.append(ours_line)
                    ours_idx += 1
                elif choice < 0.8:
                    # Take theirs
                    merged_lines.append(theirs_line)
                    theirs_idx += 1
                else:
                    # Take both — the most honest representation of the conflict
                    merged_lines.append(ours_line)
                    merged_lines.append(theirs_line)
                    ours_idx += 1
                    theirs_idx += 1
            elif ours_line is not None:
                merged_lines.append(ours_line)
                ours_idx += 1
            else:
                merged_lines.append(theirs_line)
                theirs_idx += 1

    # Prepend a merge comment
    merge_comment = rng.choice(_MERGE_COMMENTS)
    result_lines = [merge_comment] + merged_lines
    merged_content = "\n".join(result_lines)

    description = rng.choice(_MERGE_STRATEGIES_DESCRIPTIONS)

    return merged_content, description


def narrative_diff(diff_text: str) -> str:
    """Produce a prose narrative description of a git diff.

    Handles empty diffs gracefully.
    """
    rng = _rng()

    if not diff_text or not diff_text.strip():
        return rng.choice(_DIFF_EMPTY)

    opener = rng.choice(_DIFF_OPENERS)
    theme = rng.choice(_DIFF_THEMES)

    # Count rough signal: additions, removals
    lines = diff_text.splitlines()
    additions = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    removals = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    files_changed = diff_text.count("\ndiff --git") + (1 if diff_text.startswith("diff --git") else 0)

    # Build a contextual sentence
    if additions > removals * 2:
        direction = "expansion — more was added than removed, suggesting new ground being covered"
    elif removals > additions * 2:
        direction = "reduction — more was removed than added, which is often a sign of confidence"
    else:
        direction = "evolution — roughly equal additions and removals, the classic sign of refinement"

    file_note = (
        f"across {files_changed} file{'s' if files_changed != 1 else ''}"
        if files_changed > 0
        else "in a single location"
    )

    return (
        f"{opener} {theme}. "
        f"The diff shows {direction}, {file_note}. "
        f"The {additions} addition{'s' if additions != 1 else ''} and "
        f"{removals} removal{'s' if removals != 1 else ''} together tell the story of "
        f"a developer who knew what they wanted to say and found a way to say it — "
        f"or at least, found a way that will do until a better way presents itself."
    )


def story_log(commits: list[dict]) -> str:
    """Produce a narrative arc from a list of commit dicts.

    Each commit dict should have: hash, author, date, message.
    Handles empty commit lists gracefully.
    """
    rng = _rng()

    if not commits:
        return rng.choice(_LOG_EMPTY)

    n = len(commits)
    opening_template = rng.choice(_LOG_OPENINGS)
    opening = opening_template.replace("{n}", str(n))
    archetype = rng.choice(_LOG_ARCHETYPES)

    # Find interesting commits to reference
    first = commits[-1] if commits else None  # oldest first in typical log (newest first)
    last = commits[0] if commits else None    # most recent

    # Look for hotfix / revert signals
    stress_commits = [
        c for c in commits
        if any(kw in c.get("message", "").lower()
               for kw in ["hotfix", "fix", "revert", "emergency", "urgent", "please"])
    ]

    authors = list({c.get("author", "Unknown") for c in commits})
    author_note = (
        f"The work spans contributions from {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}."
        if len(authors) > 1
        else f"This is largely the work of one developer, {authors[0] if authors else 'unknown'}."
    )

    stress_note = ""
    if stress_commits:
        stress_note = (
            f" The commit '{stress_commits[0]['message']}' by {stress_commits[0].get('author', 'someone')} "
            f"stands out as a moment of pressure — the kind of commit that gets written when "
            f"something important is at stake."
        )

    time_note = ""
    if first and last and first.get("date") and last.get("date"):
        time_note = f" The project spans from {first['date']} to {last['date']}."

    return (
        f"{opening} {archetype}. "
        f"{author_note}"
        f"{time_note}"
        f"{stress_note} "
        f"Looking at these {n} commit{'s' if n != 1 else ''} in sequence, "
        f"you can see a team (or a person) learning what they were building "
        f"by the act of building it — which is the only honest way to make software."
    )


def empathetic_blame(file_path: str, blame_lines: list[dict]) -> str:
    """Produce an empathetic blame analysis for a file.

    Each blame_line dict should have: author, date, content.
    """
    rng = _rng()

    if not blame_lines:
        return (
            f"The file '{file_path}' has no blame data to analyze. "
            "It may be new, untracked, or simply beyond judgment."
        )

    # Find unique authors
    authors = list({line.get("author", "Unknown") for line in blame_lines})
    primary_author = rng.choice(authors)

    opening_template = rng.choice(_BLAME_OPENINGS)
    opening = opening_template.replace("{author}", primary_author)
    context = rng.choice(_BLAME_CONTEXTS)
    closing = rng.choice(_BLAME_CLOSINGS)

    # Find an interesting line to call out
    interesting_lines = [
        l for l in blame_lines
        if any(kw in l.get("content", "").lower()
               for kw in ["todo", "fixme", "hack", "temporary", "temp", "#", "//"])
    ]
    specific_note = ""
    if interesting_lines:
        il = rng.choice(interesting_lines)
        specific_note = (
            f" The line '{il['content'].strip()}' in particular "
            f"carries the weight of a decision that probably had more context at the time."
        )

    author_summary = (
        f"This file has been touched by {len(authors)} developer{'s' if len(authors) != 1 else ''}: "
        f"{', '.join(authors[:4])}{'...' if len(authors) > 4 else ''}. "
        if len(authors) > 1
        else f"This file belongs primarily to {authors[0]}. "
    )

    return (
        f"{opening} {context}.{specific_note} "
        f"{author_summary}"
        f"{closing}"
    )


def push_question(branch: str, n_commits: int, remote: str) -> str:
    """Generate an existential push confirmation question."""
    rng = _rng()
    template = rng.choice(_PUSH_QUESTIONS)
    return template.replace("{n}", str(n_commits)).replace("{branch}", branch).replace("{remote}", remote)
