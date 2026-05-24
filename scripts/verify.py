#!/usr/bin/env python3
"""Single source of truth for "is this code actually working?".

Called from every chokepoint where a false "done" claim can originate:
  - the interactive Claude Stop hook        (.claude/hooks/stop-gate.py)
  - the autonomous-agent done-gate          (.claude/hooks/agent-done-gate.py)
  - Lefthook pre-commit / pre-push          (lefthook.yml)

Two tiers:
  fast (default) : frontend svelte-check + vitest, backend pytest   (~<60s)
  full (--full)  : fast tier + Playwright UI->API->DB smoke against a live stack

Exit 0 only if every check passes; otherwise exit 1 with the failing output.
Cross-platform (Windows/PowerShell + polyglot Python/SvelteKit repo).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(ROOT, "frontend")
BACKEND = os.path.join(ROOT, "backend")

# Backend health endpoint polled before the smoke test runs (see --full).
HEALTH_URL = os.environ.get("COMMUNITYPULSE_HEALTH_URL", "http://localhost:8000/api/health")
HEALTH_TIMEOUT_S = int(os.environ.get("COMMUNITYPULSE_HEALTH_TIMEOUT", "90"))

MAX_OUTPUT_CHARS = 2000  # tail of failing output handed back to the agent


def _resolve(cmd: str) -> str:
    """Resolve an executable (npm -> npm.cmd on Windows) to a full path."""
    found = shutil.which(cmd)
    if not found:
        raise FileNotFoundError(
            f"'{cmd}' not found on PATH. Install it before running verify.py."
        )
    return found


class Check:
    def __init__(self, name: str, args: list[str], cwd: str, timeout: int = 300):
        self.name = name
        self.args = args
        self.cwd = cwd
        self.timeout = timeout

    def run(self) -> tuple[bool, str]:
        start = time.time()
        try:
            proc = subprocess.run(
                self.args,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"TIMEOUT after {self.timeout}s"
        except FileNotFoundError as exc:
            return False, str(exc)
        secs = time.time() - start
        ok = proc.returncode == 0
        if ok:
            return True, f"{secs:.1f}s"
        tail = (proc.stdout + "\n" + proc.stderr).strip()[-MAX_OUTPUT_CHARS:]
        return False, f"exit {proc.returncode} after {secs:.1f}s\n{tail}"


def fast_checks() -> list[Check]:
    npm = _resolve("npm")
    return [
        Check("frontend:check", [npm, "run", "check"], FRONTEND),
        Check("frontend:unit", [npm, "run", "test:run"], FRONTEND),
        Check("backend:pytest", [sys.executable, "-m", "pytest", "-q"], BACKEND),
    ]


def wait_for_backend() -> tuple[bool, str]:
    """Poll the backend health endpoint so the smoke test isn't itself a phantom.

    A "passing" Playwright run against a dead backend proves nothing -- exactly
    the failure mode we are eliminating -- so the smoke tier refuses to run until
    the real stack answers.
    """
    deadline = time.time() + HEALTH_TIMEOUT_S
    last_err = "no attempt made"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=5) as resp:
                if 200 <= resp.status < 300:
                    return True, f"backend healthy at {HEALTH_URL}"
                last_err = f"status {resp.status}"
        except (urllib.error.URLError, OSError) as exc:
            last_err = str(exc)
        time.sleep(3)
    return False, (
        f"backend health check FAILED ({HEALTH_URL}): {last_err}.\n"
        f"Bring the stack up first: `docker compose up -d` (and wait for it)."
    )


def ensure_stack_up() -> tuple[bool, str]:
    """Best-effort `docker compose up -d`, then block on the health endpoint."""
    docker = shutil.which("docker")
    if docker:
        subprocess.run(
            [docker, "compose", "up", "-d"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
    return wait_for_backend()


def full_checks() -> list[Check]:
    npm = _resolve("npm")
    return [Check("frontend:e2e", [npm, "run", "test:e2e"], FRONTEND, timeout=600)]


def main() -> int:
    parser = argparse.ArgumentParser(description="CommunityPulse verification gate")
    parser.add_argument(
        "--full",
        action="store_true",
        help="also run the Playwright UI->API->DB smoke test against a live stack",
    )
    args = parser.parse_args()

    print(f"== verify.py ({'full' if args.full else 'fast'} tier) ==", flush=True)
    failures: list[str] = []

    for check in fast_checks():
        print(f"-> {check.name} ...", flush=True)
        ok, detail = check.run()
        print(f"   {'PASS' if ok else 'FAIL'} {check.name} ({detail.splitlines()[0]})", flush=True)
        if not ok:
            failures.append(f"[{check.name}] {detail}")

    if args.full and failures:
        print("-> skipping smoke test: fast checks already failed (no point spinning up the stack)", flush=True)
    elif args.full:
        print("-> ensuring stack is up for smoke test ...", flush=True)
        up_ok, up_detail = ensure_stack_up()
        print(f"   {'READY' if up_ok else 'FAIL'} {up_detail.splitlines()[0]}", flush=True)
        if not up_ok:
            failures.append(f"[stack] {up_detail}")
        else:
            for check in full_checks():
                print(f"-> {check.name} ...", flush=True)
                ok, detail = check.run()
                print(f"   {'PASS' if ok else 'FAIL'} {check.name} ({detail.splitlines()[0]})", flush=True)
                if not ok:
                    failures.append(f"[{check.name}] {detail}")

    print("=" * 40, flush=True)
    if failures:
        print(f"VERIFY FAILED ({len(failures)} check(s)):\n", flush=True)
        for f in failures:
            print(f, flush=True)
            print("-" * 40, flush=True)
        return 1
    print("VERIFY PASSED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
