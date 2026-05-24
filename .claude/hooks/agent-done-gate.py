#!/usr/bin/env python3
"""Autonomous-agent done-gate: a task cannot be recorded PASSED over phantom code.

When an autonomous coding loop marks a unit of work "done" by writing a PASSED
marker to its progress log, this PostToolUse hook runs the FULL verification tier
(scripts/verify.py --full: unit + svelte-check + Playwright UI->API->DB smoke).
If that fails, it blocks (exit 2) and tells the agent to fix the slice before
marking it done -- the principle being: run the probe yourself, don't trust the
self-reported PASS marker.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _payload_text(tool_input: dict) -> str:
    """Text introduced by this Write/Edit, where a status change would appear."""
    parts = [
        tool_input.get("content", ""),
        tool_input.get("new_string", ""),
    ]
    for edit in tool_input.get("edits", []) or []:
        parts.append(edit.get("new_string", ""))
    return "\n".join(p for p in parts if p)


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool_input = data.get("tool_input", {}) or {}
    path = (tool_input.get("file_path") or "").replace("\\", "/").lower()
    # Match the agent's progress log wherever it lives (project dir or a tool cache).
    if not path.endswith("progress.txt"):
        return 0

    # Only gate when a unit of work is being marked done.
    if "PASSED" not in _payload_text(tool_input).upper():
        return 0

    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "verify.py"), "--full"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = (result.stdout + "\n" + result.stderr).strip()[-3000:]
        sys.stderr.write(
            "AUTOMATED QUALITY GATE (not a user denial): the progress log was "
            "updated to PASSED, but verify.py --full failed. A task cannot be "
            "marked done over phantom or unwired code -- the UI->API->DB smoke or a "
            "test did not pass. Revert the PASSED marker, fix the failures below, "
            "and only mark done once verify.py --full exits 0.\n\n" + tail
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
