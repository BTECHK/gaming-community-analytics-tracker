# CommunityPulse

## Project facts

- Stack: SvelteKit + Vite frontend (`frontend/`), FastAPI + SQLAlchemy + Alembic
  backend (`backend/`), Postgres, Docker Compose. Long-running feature work can be
  driven by an autonomous coding-agent loop.
- Verification (single source of truth): `python scripts/verify.py` (fast: svelte-check
  + vitest + pytest) and `python scripts/verify.py --full` (adds the Playwright
  UI->API->DB smoke against a live stack).
- Frontend commands run in `frontend/`: `npm run check`, `npm run test:run`,
  `npm run test:e2e`. Backend tests: `python -m pytest` in `backend/`.

## Verification is enforced, not requested

These gates are deterministic and you cannot route around them. Don't try; just
make them pass:

- A **Stop hook** runs `verify.py` (fast) and blocks the end of your turn until it
  exits 0. Do not claim a task is done while it is red.
- An **autonomous-agent done-gate** runs `verify.py --full` whenever the agent's
  progress log is marked `PASSED`, and blocks if the slice isn't actually wired and passing.
- **Lefthook** blocks commits (fast) and pushes (full) on failure.

"200/200 passing" is meaningless unless `verify.py` agrees. If you can't verify it,
it isn't done.

## IMPORTANT: Slicing rule (load-bearing)

When implementing a feature, build ONE end-to-end vertical slice first:

1. DB migration / schema change
2. A single API endpoint
3. A single UI element that calls that endpoint
4. A Playwright smoke test proving the click reaches the real backend/DB

Only after that slice is green do you expand sideways. Never build a horizontal
layer (e.g. "all the endpoints") before the first vertical slice is wired. The
recurring failure here is a UI element that exists but is never connected (a dead
button) while "done" gets claimed anyway.

## IMPORTANT: No assumptions

When a file path, DB schema, or library version is unclear, read the file or grep
first. Never guess and run along with a wrong assumption. If a smoke test uses
`if (await el.isVisible())` around its only assertion, it proves nothing — assert
the real network call succeeded and real data rendered.
