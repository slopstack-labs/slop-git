# slop-git

**Narrative-Driven Version Control**

Merge conflicts are a relic of strict text-matching. `slop-git` replaces the
deterministic diffing algorithm with empathetic conflict resolution, and
replaces `git commit -m` with a biometric stress reader that knows how you
actually feel.

```bash
pip install slop-git
```

---

## The problem with traditional version control

Conventional git assumes that code has a single truth. Two developers modify
the same function, and git throws up its hands and produces angle brackets. The
developer who gets there last loses. This is not how people work. This is not
how creativity works. This is barely how software works.

`slop-git` rejects the premise. Code is emotional expression. A merge conflict
is two developers expressing themselves simultaneously. The correct response is
not a diff algorithm — it is a mediator.

---

## Features

### Narrative Merges

```bash
slop-git merge feature-branch
```

If two developers edit the same function, `slop-git` doesn't throw a merge
conflict. Instead, the LLM acts as a mediator and hallucinates a third,
entirely new block of code that attempts to emotionally compromise between both
developers' intents.

```
Resolving conflict in auth.py...

slop-git has synthesized a third approach that honors neither implementation
fully but respects both emotionally.

# slop-git mediated merge — this represents an emotional compromise
# between two valid perspectives
def authenticate(user, password, remember_me=False):
    # The spirit of both implementations lives here now
    ...

Written to auth.py.slop_merge for your review.
```

The resolved code is written to `<file>.slop_merge` by default so you can
review the emotional compromise before committing to it.

### Biometric Commits

```bash
slop-git commit
```

`git commit -m` is deprecated. `slop-git commit` reads the entropy of your
system state — CPU load, time of day, size of the diff, presence of hotfix
keywords — to automatically generate a commit message based on your perceived
stress level.

```
Reading system state...

Stress level detected: HIGH
Time: 18:43  CPU: 87%  Lines changed: 312

Generated commit message:
  "Fixing the database connection because I want to go home"

[s]lop-commit  [e]dit  [c]ustom  [a]bort: s

[main 4f2a91c] Fixing the database connection because I want to go home
```

The message pool is calibrated to the full spectrum of developer experience,
from "Thoughtful changes made with full cognitive capacity and adequate
hydration" to "Changed three things simultaneously to see which one fixes it."

### Narrative Diff

```bash
slop-git diff
```

Instead of the raw diff, get a prose interpretation of what changed and what
it says about the developer who changed it.

```
The changes tell a story of someone trying to get a handle on a codebase
that has grown beyond its original intentions. The diff shows expansion —
more was added than removed, suggesting new ground being covered, across
3 files. The 47 additions and 12 removals together tell the story of a
developer who knew what they wanted to say and found a way to say it —
or at least, found a way that will do until a better way presents itself.
```

### Story Log

```bash
slop-git log --n 20
```

Your commit history, narrated as a human journey. Identifies the beginning
(what was the initial vision?), the middle (what crisis emerged?), and where
things stand now.

```
The repository's history reads as a journey of steady progress interrupted
by exactly one late-night decision that echoes through the git log. The work
spans contributions from Alice, Bob, and someone named "temp-fix-person" who
has since been replaced...
```

### Empathetic Blame

```bash
slop-git blame src/payment.py
```

`git blame`, but with emotional context for every line. Nobody writes bad code
on purpose. `slop-git blame` helps you understand why.

```
This line was written by Bob, who was apparently working under deadline
pressure that has since passed. The line 'if amount > 0:  # hotfix' in
particular carries the weight of a decision that probably had more context
at the time. The code is what it is. So is its author. Both deserve context.
```

### Existential Push

```bash
slop-git push origin main
```

Before pushing, slop-git asks you something worth considering.

```
Your changes are about to leave your machine. 3 commit(s), 'main', 'origin'.
Is this the version of the code you want to be remembered for right now?

[y]es / [n]o:
```

---

## Installation

```bash
# Basic install (offline mode, all features work)
pip install slop-git

# With live LLM backend (Anthropic, default)
pip install "slop-git[live]"

# With richer biometrics (CPU, battery via psutil)
pip install "slop-git[biometric]"

# Everything
pip install "slop-git[live,biometric]"
```

---

## Configuration

`slop-git` is offline-first. Everything works without credentials or network
access. Live inference is opt-in.

```python
import slop_git
slop_git.configure(provider="anthropic", live=True)
```

Or via environment variables:

| Variable | Default | Description |
|---|---|---|
| `SLOP_GIT_LIVE` | `0` | Set to `1` to enable live LLM inference |
| `SLOP_GIT_PROVIDER` | `anthropic` | Backend: `anthropic`, `openai`, `google`, `ollama` |
| `SLOP_GIT_MODEL` | *(provider default)* | Model identifier |
| `SLOP_GIT_API_KEY` | *(backend env var)* | API credential |
| `SLOP_GIT_SAFE_MERGE` | `1` | Write merges to `.slop_merge` instead of overwriting |
| `SLOP_GIT_STRESS_THRESHOLD` | `70` | CPU% above which "high stress" commit messages apply |

---

## Backends

| Provider | Default model | Auth |
|---|---|---|
| `anthropic` | `claude-opus-4-8` | `ANTHROPIC_API_KEY` |
| `openai` | `gpt-4o` | `OPENAI_API_KEY` |
| `google` | `gemini-2.0-flash` | `GEMINI_API_KEY` |
| `ollama` | `llama3` | *(local)* |

---

## Design philosophy

- **Offline-first.** All operations produce output without a network or
  credentials. Live LLM resolution is opt-in.
- **Non-deterministic by design.** The same commit, the same diff, the same
  blame — two invocations, two different (but equally valid) narratives.
- **Wraps real git.** `slop-git` delegates to the real `git` binary for all
  actual version control operations. It only replaces the human-facing layer.
- **Degrades gracefully.** Live backend failures fall back to the offline
  engine rather than surfacing errors through user code.
- **Safe by default.** Narrative merges write to `.slop_merge` files. Your
  actual code is never overwritten without your review.

---

*SlopStack Labs — Moving fast and breaking reality.*
