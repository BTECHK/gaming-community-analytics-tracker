# Decision: Anti-Phantom Verification Gates

**Status:** Accepted
**Date:** 2026-05-24

## Context

When you build with AI coding agents — interactive (Claude Code) or autonomous
(a self-driving build loop) — both will confidently claim work is "done and tested"
when it is not. The recurring failure is **phantom wiring**: points A, C, and D get
built, but B and E — often the *connection* between a UI element and its backing
endpoint/DB — never get built. Yet the agent reports "200/200 passing, everything
connected and verified."

A concrete example from this project: a "wire the new trend panel into the dashboard"
task where the component, the endpoint, and the API client all existed, but the actual
wiring was a dead button — and "done" still got claimed.

The root cause is not the model. Agents optimize for a finished-*looking* response,
not guaranteed task completion. Prompting cannot fix this. The fix is **deterministic,
non-LLM gates the agent cannot route around**, with at least one gate that runs the
*real wired-up path* (browser clicks button → API fires → DB row appears) rather than
compiling against mocks.

## Decision

Make a false "done" claim **structurally impossible to persist** at every chokepoint
where it can originate:

1. **Interactive turn** — a Stop hook.
2. **Autonomous agent marking work done** — a write-gate on the agent's progress log.
3. **Git commit / push** — Lefthook.

All three call **one** verification command (`scripts/verify.py`), so there is no
drift between "what the interactive agent runs," "what the autonomous loop runs," and
"what the commit runs."

## Core principle: one source of truth

`scripts/verify.py` is the keystone. Everything else is just a different chokepoint
calling it. Two speed tiers, because a per-turn gate must be fast and a smoke test is slow:

| Tier | Command | What it runs | Called by |
|------|---------|--------------|-----------|
| **fast** (<~60s) | `python scripts/verify.py` | frontend `npm run check` + `npm run test:run`; backend `pytest` | Stop hook (every interactive turn), Lefthook `pre-commit` |
| **full** | `python scripts/verify.py --full` | fast tier **+** Playwright smoke (`npm run test:e2e`) against the live stack | Lefthook `pre-push`, agent done-gate |

`verify.py` exits non-zero if **any** sub-check fails, and prints the failing tool's
last ~2000 chars of stderr so the agent gets an actionable error, not just "failed."

### Why Python (not bash/npm)

This is a Windows 11 / PowerShell, polyglot (Python + SvelteKit) repo. A single Python
orchestrator is cross-platform, can shell into both `npm` and `pytest`, and is the same
language as the hooks — one mental model.

## Components

### 1. `scripts/verify.py` — verification orchestrator

- Runs each check as a subprocess with a timeout; collects pass/fail.
- `--full` adds the Playwright smoke step **and ensures the full stack is up first**
  (without backend + DB running, the smoke test is itself a phantom).
- Exit 0 only if all checks pass; otherwise exit 1 with a structured failure report.

### 2. `.claude/hooks/stop-gate.py` — interactive turn gate

- Stop hook. Reads hook JSON from stdin; **first checks `stop_hook_active`** and
  exits 0 on the second pass (the canonical infinite-loop guard).
- Runs the **fast** tier. On failure, emits `{"decision":"block","reason": "..."}`
  with the failing output, wrapped in explicit phrasing:
  *"This is an AUTOMATED QUALITY GATE, not a user denial. Fix before stopping."*
  (Mitigates the known issue where a bare exit-2 makes the model go idle instead of retrying.)
- **Installed under `.claude/hooks/`, never via the plugin system** — plugin-installed
  Stop hooks halt instead of forcing continuation (GitHub issue #10412).

### 3. Playwright smoke test — the dead-button killer

- One e2e spec per vertical slice (see `frontend/e2e/wiring.smoke.spec.ts` for the
  canonical pattern).
- A smoke test must: drive the **real browser** against the running app, perform the
  user action, and assert the **real effect** — the network request to the real
  endpoint succeeded AND the rendered result reflects real backend/DB data (not a
  fixture). If the button isn't wired, the test fails.
- **Stack-up requirement (critical):** the Playwright `webServer` only starts the
  frontend dev server; the backend + DB are separate (`docker-compose`). `verify.py
  --full` therefore: (a) runs `docker compose up -d`, (b) polls the backend health
  endpoint until ready, (c) then runs `npm run test:e2e`. Without this, a "passing"
  smoke test against a dead backend is a new phantom — the exact thing we're eliminating.

### 4. Autonomous-agent done-gate — `.claude/hooks/agent-done-gate.py`

- **PostToolUse** hook matching `Write|Edit|MultiEdit` where the target is the agent's
  progress log.
- When the log is written with a `PASSED` marker, run the **full** tier. If red, block
  (exit 2) with a reason instructing the agent to fix the slice before recording it done.
  This makes it impossible for an autonomous loop to *persist* a "done" marker over
  phantom code — run the probe yourself, don't trust the reported PASS marker.

### 5. Lefthook — git-layer gate

- **Lefthook, not Husky** (Husky's `prepare` script overwrites committed hook files on
  every `npm install`; Lefthook doesn't).
- `pre-commit` → `verify.py` (fast); `pre-push` → `verify.py --full` (includes smoke).
- Same script as the hooks → zero drift between agent gates and git gates.

### 6. CLAUDE.md — the two load-bearing rules

- **Vertical-slice rule:** build ONE end-to-end slice first (DB → one endpoint → one UI
  element calling it → a smoke test proving the click reaches the DB). Expand sideways
  only once that slice is green.
- **No-assumptions rule:** when a path, schema, or library version is unclear, read the
  file or grep first — never guess.

These are *preferences* (CLAUDE.md). The *guarantees* live in the hooks.
("Use CLAUDE.md for preferences, hooks for guarantees.")

## Data flow

```
                      ┌─────────────────────────┐
  interactive turn ──▶│  Stop hook (fast tier)  │──▶ block until green
                      └───────────┬─────────────┘
  agent marks         ┌───────────▼─────────────┐
  work done ─────────▶│ done-gate (full tier)   │──▶ block until green
                      └───────────┬─────────────┘
  git commit ────────▶│ Lefthook pre-commit (fast)
  git push ──────────▶│ Lefthook pre-push (full) │
                      └───────────┬─────────────┘
                                  ▼
                        scripts/verify.py  ◀── single source of truth
                          ├─ npm run check        (svelte-check)
                          ├─ npm run test:run      (vitest)
                          ├─ pytest                (backend)
                          └─ [--full] docker up + health-wait + npm run test:e2e
```

## Out of scope (deliberately)

- **Contract tests (Pact)** — the E2E smoke proves integration more cheaply for a solo app.
- **CI runners (`act` / GitHub Actions)** — local gates catch it first; an easy later add.
- **Property-based tests** — nice-to-have, not core to phantom wiring.
- **ruff / mypy in `verify.py`** — add to the backend tier once installed.

## Testing the guards themselves

Each guard is proven by feeding it a deliberate failure (a broken test, an unwired
button) and confirming it *actually blocks* — not just by installing it. Installing a
gate and assuming it works would be... a phantom.
