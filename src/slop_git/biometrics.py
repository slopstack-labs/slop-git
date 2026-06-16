"""System state reader for biometric commit message generation.

Reads available system metrics to estimate the developer's current state.
Gracefully degrades when psutil is not available — falls back to time-based
heuristics and /proc/loadavg on Linux. The goal is not accuracy, it's
plausibility.
"""

from __future__ import annotations

import time
import os


def read_system_state() -> dict:
    """Read available system metrics. Returns what it can, gracefully degrades.

    Returns a dict with:
        hour: int           — current hour (0-23)
        cpu_percent: float  — estimated CPU usage (0-100)
        battery_percent: float | None — battery level if available
        uptime_hours: float | None    — system uptime in hours if available
    """
    state: dict = {
        "hour": time.localtime().tm_hour,
        "cpu_percent": 50.0,  # default: medium stress assumption
        "battery_percent": None,
        "uptime_hours": None,
    }

    # Try psutil for richer biometrics
    try:
        import psutil
        state["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        battery = psutil.sensors_battery()
        if battery:
            state["battery_percent"] = battery.percent
        boot_time = psutil.boot_time()
        state["uptime_hours"] = (time.time() - boot_time) / 3600
    except ImportError:
        # Fall back to /proc/loadavg on Linux or just time-based heuristics
        try:
            with open("/proc/loadavg") as f:
                load = float(f.read().split()[0])
                # Rough CPU% from load average (not accurate but evocative)
                state["cpu_percent"] = min(100.0, load * 25.0)
        except (OSError, ValueError):
            pass

    return state


def diff_keywords(diff_text: str) -> dict:
    """Extract stress signals from the diff text.

    Returns a dict with:
        has_hotfix: bool     — diff mentions hotfix / urgent / emergency
        has_revert: bool     — diff contains a revert
        n_files: int         — number of files changed
        n_lines_changed: int — rough count of changed lines
        has_todo: bool       — diff contains TODO / FIXME / HACK
        has_debug: bool      — diff contains debug statements
    """
    text = diff_text.lower()
    return {
        "has_hotfix": any(
            kw in text for kw in ["hotfix", "urgent", "emergency", "critical", "fix"]
        ),
        "has_revert": "revert" in text,
        "n_files": diff_text.count("\ndiff --git") + (
            1 if diff_text.startswith("diff --git") else 0
        ),
        "n_lines_changed": diff_text.count("\n+") + diff_text.count("\n-"),
        "has_todo": "todo" in text or "fixme" in text or "hack" in text,
        "has_debug": any(
            kw in text
            for kw in ["console.log", "print(", "debugger", "breakpoint", "pdb", "binding.pry"]
        ),
    }
