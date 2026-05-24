#!/usr/bin/env python3
"""Stop hook: interactive Claude cannot end its turn until the code actually works.

Runs the FAST verification tier (scripts/verify.py). On failure it blocks the stop
and hands the failing output back to Claude, framed as an automated gate so the
model doesn't mistake it for a user denial and go idle.

Install location matters: this lives under .claude/hooks/ (committed), NOT in a
plugin package -- plugin-installed Stop hooks halt instead of forcing continuation
(GitHub issue #10412).
"""
import json
import os
import subprocess
import sys

# .claude/hooks/stop-gate.py -> repo root is three directories up.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    # Canonical infinite-loop guard: on the second pass, let Claude stop.
    if data.get("stop_hook_active"):
        return 0

    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "verify.py")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        tail = (result.stdout + "\n" + result.stderr).strip()[-3000:]
        print(json.dumps({
            "decision": "block",
            "reason": (
                "<claude-directive>This is an AUTOMATED QUALITY GATE, not a user "
                "denial. verify.py failed, which means the code is not actually "
                "working yet -- do NOT claim the task is done. Fix every failure "
                "below, then stop. Do not ask for permission to continue.\n\n"
                + tail +
                "</claude-directive>"
            ),
        }))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
