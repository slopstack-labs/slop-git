#!/bin/bash
# slop-git demo — requires slop-git to be installed
# and must be run from inside a git repository.

echo "=== Narrative Diff ==="
# Shows a prose description of your staged changes instead of the raw diff
slop-git diff

echo ""
echo "=== Biometric Commit ==="
# Reads your system state and generates a commit message
# reflecting your apparent emotional/stress level
slop-git commit

echo ""
echo "=== Story Log ==="
# Your commit history, narrated as a human story
slop-git log --n 10

echo ""
echo "=== Empathetic Blame ==="
# git blame, but with emotional context for every line
# (Replace with an actual file in your repo)
# slop-git blame src/main.py
