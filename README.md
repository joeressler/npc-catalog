# NPC Catalog

A purple Frutiger Aero D&D NPC catalog for Dungeon Masters. Create campaigns, catalog NPCs as you invent them, and retrieve them quickly at the table.

## Quick start

```bash
docker compose up --build
```

Open **http://localhost:0314**

Data persists in the `npc_data` Docker volume (SQLite database + campaign images).

### Fresh cutover (wipe existing data)

When migrating from the old Django backend, resetting all data, or after breaking API contract changes (e.g. session/encounter `npc_ids`):

```bash
docker compose down -v
docker compose up --build
```

## Architecture

| Layer | Location |
|-------|----------|
| Angular pages + `ApiService` | `frontend/src/app/` |
| FastAPI app | `backend/app/` (`routers/` → `services/` → `models/` / `schemas/` / `mappers.py`) |
| Migrations | `backend/alembic/versions/` |
| SQLite + media | Docker volume `npc_data` → `/data` |
| South Side CR dashboard | `trains/` (served at `/trains/` via nginx → trains container) |

**Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md) for layout, request shapes, and how to add a feature.

### Request shapes

- **Campaigns & NPCs:** `multipart/form-data` (supports image upload).
- **Sessions, encounters, graphs, relation types, nodes, edges:** JSON bodies.

Copy **encounters/sessions** when adding typical JSON CRUD—not campaigns/NPCs—unless you need uploads.

## Development

Copy environment defaults (required for Docker Compose — the backend loads auth secrets via `env_file: .env`):

```bash
cp .env.example .env
```

Edit `.env` and set `AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_PLAYER_USERNAME`, `AUTH_PLAYER_PASSWORD`, and `AUTH_SECRET`. Compose injects that file into the backend container; `SQLITE_PATH` / `MEDIA_ROOT` in Compose still point at the `/data` volume.

Default local logins: DM `admin`/`admin`, player `player`/`test` (readonly; only sees items marked **Visible to players**). Sessions and encounters are never player-visible.

### Backend only

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Interactive OpenAPI docs: **http://127.0.0.1:8000/docs** (requires a valid session cookie after login).

### Frontend only

```bash
cd frontend
npm install
npm start
```

The dev server proxies `/api`, `/media`, and `/trains` when configured in `proxy.conf.json`. See [frontend/README.md](frontend/README.md).

### South Side trains dashboard

Requires the backend (for the shared login cookie). In a third terminal:

```bash
cd trains
npm install
npm run build
BACKEND_URL=http://127.0.0.1:8000 npm start
```

Open **http://localhost:3000/trains/** (or **http://localhost:4200/trains/** via the frontend proxy) after signing in. Schedules refresh every 5 minutes from the MBTA V3 API (optional `MBTA_API_KEY` in `.env`).

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login/` | Sign in (sets session cookie) |
| POST | `/api/auth/logout/` | Clear session cookie |
| GET | `/api/auth/me/` | Current session user (`username`, `role`: `dm` \| `player`) |
| GET/POST | `/api/campaigns/` | List / create campaigns |
| GET/PATCH/DELETE | `/api/campaigns/{id}/` | Campaign detail |
| GET/POST | `/api/campaigns/{id}/npcs/` | NPCs in campaign |
| GET/PATCH/DELETE | `/api/npcs/{id}/` | NPC detail |
| GET | `/api/tags/` | All tags |
| GET | `/api/npcs/?q=&alignment=&tag=&location=&faction=` | Filter NPCs |
| GET/POST | `/api/campaigns/{id}/graphs/` | List / create relationship webs |
| GET/PATCH/DELETE | `/api/graphs/{id}/` | Graph detail (nodes + edges) |
| GET/POST | `/api/campaigns/{id}/sessions/` | List / create session notes |
| GET/PATCH/DELETE | `/api/sessions/{id}/` | Session detail |
| GET/POST | `/api/campaigns/{id}/encounters/` | List / create encounters |
| GET/PATCH/DELETE | `/api/encounters/{id}/` | Encounter detail |
| POST | `/api/encounters/{id}/clone/` | Clone an encounter |
| GET/POST | `/api/campaigns/{id}/relation-types/` | List / add relation types |
| PATCH/DELETE | `/api/relation-types/{id}/` | Update / delete relation type |
| POST | `/api/graphs/{id}/nodes/` | Add NPC, Party, or PC node |
| PATCH/DELETE | `/api/graph-nodes/{id}/` | Update position / remove node |
| POST | `/api/graphs/{id}/edges/` | Add directed relation (`from_node_id` / `to_node_id`, optional `bidirectional`) |
| PATCH/DELETE | `/api/graph-edges/{id}/` | Update / remove relation |
| GET | `/api/ai/status/` | Whether ComfyUI image generation is available |
| POST | `/api/ai/generate-image/` | Generate NPC portrait or location landscape (returns base64 PNG) |

## Stack

- **Frontend:** Angular (standalone), SCSS
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** SQLite on Docker volume
- **Auth:** Single shared username/password from `.env`; HttpOnly session cookie gates `/api`, `/media`, and `/trains`
- **AI images (Docker):** ComfyUI + SDXL on an NVIDIA GPU (internal service; not published)
- **Trains:** Node service at `/trains/` — South Side Commuter Rail shapes + schedule dashboard (MBTA V3)

## Production / port-forward

This stack is a single-user DM tool. If you expose host port **0314** (router NAT, LAN, or tunnel):

1. Copy `.env.example` → `.env` and set **strong unique** `AUTH_USERNAME`, `AUTH_PASSWORD`, `AUTH_PLAYER_USERNAME`, `AUTH_PLAYER_PASSWORD`, and `AUTH_SECRET` (not the example `admin` / `player` / `test` / `dev-secret-change-me` values).
2. Set `DEBUG=false`. With debug off, the backend **refuses to start** on empty or example credentials, and OpenAPI `/docs` is disabled.
3. Forward **only** `0314` (frontend nginx). Do **not** publish backend `8000` or ComfyUI `8188`.
4. Prefer a VPN, Tailscale, or SSH tunnel over an open WAN port when you can.
5. Cookie Secure flag:
   - Plain HTTP port-forward → keep `AUTH_COOKIE_SECURE=false` (required for cookies to work).
   - HTTPS terminator in front (Caddy, Cloudflare Tunnel, etc.) → set `AUTH_COOKIE_SECURE=true`.
   - Do **not** enable HSTS while serving plain HTTP.
6. Login is rate-limited (nginx + in-process lockout). Changing `AUTH_SECRET` invalidates all sessions — restart and sign in again.
7. Backup the `npc_data` volume periodically (`/data/db.sqlite3` and `/data/media`), e.g. `docker compose cp backend:/data ./backup-data`.
8. **ComfyUI / AI portraits:** requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the host. First boot downloads SDXL base into the `comfyui_models` volume (~6GB+). NPC and location forms show **Generate portrait** / **Generate landscape** when ComfyUI is healthy; images are previewed then saved through the normal form upload path.

Health probe (also used by Compose healthchecks): `GET http://localhost:0314/health`.
