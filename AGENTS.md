## Learned User Preferences

- Prefers a purple Frutiger Aero visual design with whimsical fey-magic motion across menus and workflows (respect `prefers-reduced-motion`).
- On Windows, prefer Command Prompt over PowerShell for Docker commands when PowerShell cannot run Docker.
- For larger features, prefer plan-first then implement the attached plan without editing the plan file.
- Search and filters (e.g. faction) should match partial/substring input, not only exact strings.
- When overhauling the backend, prefer a fresh cutover (new schema, wipe/recreate data) over preserving Django admin or migrating legacy data.
- Character relationship webs should be interactive visuals, support multiple named webs per campaign, directed and easy bidirectional relations, a synthetic Party node, and optional PC sub-nodes under Party for one-off PC–NPC ties.
- Campaign sessions should auto-assign the next number; story beats are DM-orderable branching paths; clues and secrets are line items; overall notes are free text.
- Campaign encounters are reusable, cloneable set-pieces (title, short description, enemy quantities/types, battlefield text, objects/interaction points, loot line items, further notes) with soft NPC links; sessions can soft-link encounters without owning them.
- Campaign locations are reusable place notes (title, description, optional image, loot line items, POIs/interactables) with soft NPC links; NPCs can optionally pick a catalog location via `location_id` while keeping free-text location notes; location detail shows Residents (FK) and Linked NPCs (soft); sessions can soft-link locations.

## Learned Workspace Facts

- Stack is Angular (standalone) frontend, FastAPI + SQLAlchemy + Alembic backend, SQLite on a Docker volume (`npc_data`); single shared login via `AUTH_USERNAME` / `AUTH_PASSWORD` in `.env` (HttpOnly session cookie gates `/api` and `/media`).
- `docker compose up --build` serves the app at http://localhost:0314; data and uploaded images (campaigns, NPCs, locations) live under `/data` in the backend volume.
- Backend was migrated from Django to FastAPI with a wipe/recreate cutover; Django admin is not part of the stack.
- FastAPI route dependencies use Annotated style (`DbSession = Annotated[Session, Depends(get_db)]` in `deps.py`); avoid `Depends()` / `Form()` / `File()` / `Query()` in parameter defaults.
- Frontend nginx CSP must allow Angular’s production CSS preload `onload="this.media='all'"` via `script-src-attr 'unsafe-hashes'` and the matching sha256 hash, or styles stay stuck on `media=print`.
- NPCs are campaign-scoped with core fields (name, aliases, role, alignment, location free-text, optional catalog location, faction, attitude, party relationship, tags) plus optional image and optional DM detail sections (appearance, voice, personality, motivation, secrets, knowledge, inventory, notes, session history).
- Campaign sessions are a per-campaign numbered notes feature (story beats/paths, linked NPCs, notes, clues, secrets, optional linked encounters and locations).
- Campaign encounters are reusable combat/set-piece notes (enemies, battlefield, objects, loot, linked NPCs) that can be cloned; not owned by sessions.
- Character graphs (relationship webs) are campaign-scoped; relation types are an editable set list; graph UI uses Cytoscape.

## Cursor Cloud specific instructions

Standard commands live in `README.md` (Docker + split dev) and `CONTRIBUTING.md`; this section only covers non-obvious dev/run caveats. The startup update script already installs deps: it creates a Python venv at `backend/.venv` (from `backend/requirements.txt`) and runs `npm install` in `frontend/`.

- Run in split dev mode (not Docker) for development. Backend: from `backend/`, run `.venv/bin/alembic upgrade head` once, then `.venv/bin/uvicorn app.main:app --reload --port 8000`. Frontend: from `frontend/`, run `npm start` (serves on `:4200` and proxies `/api` + `/media` to `:8000` via `proxy.conf.json`). Start the backend first.
- `alembic upgrade head` is NOT part of the update script — run it manually before serving; it creates/updates `backend/db.sqlite3` (relative to `backend/`). SQLite is an embedded file, not a separate service.
- Config (`app/config.py`) reads `.env` relative to the current working directory, so backend commands must be run from `backend/`. Defaults already give `DEBUG=true` and login `admin`/`admin`, so the backend runs with no `.env` present; a `.env` is only required for the Docker path.
- Login is a shared `AUTH_USERNAME`/`AUTH_PASSWORD` (default `admin`/`admin`) that sets an HttpOnly cookie gating `/api` and `/media`. A `401` on `/api` before login is expected; authenticate first (UI login page, or `POST /api/auth/login/` with a saved cookie jar). With `DEBUG=false` the backend refuses to start on the example creds.
- Gotcha when testing forms: NPC and Campaign create/edit forms have required fields validated client-side (NPC requires name, role/occupation, alignment [defaults to Neutral], attitude, and relationship to party). If a required field is empty, the submit button silently does nothing and sends no network request — this is expected validation, not a bug. Fill all required fields.
- Tests/lint: the frontend has no unit tests and no lint script (`package.json` scripts are `start`/`build`/`watch`/`test`; `ng test` finds no specs). Backend tests are `backend/smoke_test.py http://127.0.0.1:8000/api` (needs the backend running) and `backend/test_hardening.py` (standalone; run with the venv python). Build check: `npm run build` in `frontend/`.
- Docker/nginx path (`docker compose up --build`, host port `31402`) is the production/port-forward setup with CSP + login rate-limiting; not needed for local dev, where `ng serve` bypasses nginx entirely.
