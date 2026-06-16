"""slop-git vibes layer demo — no git installation required."""

from slop_git import vibes

print("=== Commit Message Generator ===")
for level in ("low", "medium", "high", "late_night", "early_morning"):
    msg = vibes.commit_message(level, hour=14, diff_lines=42)
    print(f"  [{level:14s}] {msg}")

print("\n=== Narrative Diff ===")
fake_diff = """diff --git a/auth.py b/auth.py
+++ b/auth.py
-def login(user, password):
+def login(user, password, remember_me=False):
+    # TODO: implement remember_me
     return check_credentials(user, password)"""
print(vibes.narrative_diff(fake_diff))

print("\n=== Story Log ===")
commits = [
    {"hash": "a1b2c3d4", "author": "Alice", "date": "2026-01-01", "message": "Initial commit"},
    {"hash": "e5f6g7h8", "author": "Bob",   "date": "2026-01-05", "message": "Add authentication"},
    {"hash": "i9j0k1l2", "author": "Alice", "date": "2026-01-08", "message": "Fix the auth bug"},
    {"hash": "m3n4o5p6", "author": "Bob",   "date": "2026-01-09", "message": "hotfix: emergency patch"},
    {"hash": "q7r8s9t0", "author": "Alice", "date": "2026-01-10", "message": "Revert hotfix"},
]
print(vibes.story_log(commits))

print("\n=== Empathetic Blame ===")
blame_lines = [
    {"author": "Alice", "date": "2026-01-01", "content": "def process_payment(amount):"},
    {"author": "Bob",   "date": "2026-01-09", "content": "    if amount > 0:  # hotfix"},
    {"author": "Alice", "date": "2026-01-10", "content": "        return charge(amount)"},
]
print(vibes.empathetic_blame("payment.py", blame_lines))

print("\n=== Push Confirmation ===")
print(vibes.push_question("main", 3, "origin"))

print("\n=== Narrative Merge ===")
ours = "def greet(name):\n    return f'Hello, {name}!'"
theirs = "def greet(name, formal=False):\n    prefix = 'Dear' if formal else 'Hey'\n    return f'{prefix} {name}'"
merged, description = vibes.narrative_merge("greet.py", ours, theirs)
print(f"Description: {description}")
print(f"Merged:\n{merged}")
