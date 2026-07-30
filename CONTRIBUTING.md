# Contributing

NPC Catalog is a single-user local DM tool: Angular frontend + FastAPI backend + SQLite. Access is gated by a shared username/password from `.env` (session cookie).

## Layout

```
backend/app/          # The only backend package — start here
  main.py             # App factory, router mounts, /media, /health
  models/             # SQLAlchemy ORM (campaign, npc, session, encounter, graph)
  schemas/            # Pydantic request/response shapes (same domains)
  mappers.py          # ORM → response DTO mapping (not Django REST serializers)
  routers/            # HTTP endpoints (graphs/ is a subpackage)
  services/           # Queries, validation, 404 helpers (may raise HTTPException)
  media.py            # Image storage under MEDIA_ROOT
frontend/src/app/
  pages/              # One folder per screen (lazy-loaded routes)
  services/api.service.ts
  models/domain.models.ts  # Domain TypeScript types (all entities)
```

Alembic migrations live under `backend/alembic/versions/`. There is no Django app package.

## Request shapes

| Domains | Body style |
|---------|------------|
| Campaigns, NPCs | `multipart/form-data` (JSON payload field and/or file upload) |
| Sessions, encounters, graphs, relation types, nodes, edges | JSON (`application/json`) |

When adding CRUD, **copy encounters or sessions** as the template. Do not copy campaigns/NPCs unless you need image upload.

## Add a domain feature

1. Add SQLAlchemy models under `backend/app/models/` and re-export from `__init__.py`.
2. Add an Alembic revision under `backend/alembic/versions/` and run `alembic upgrade head`.
3. Add Pydantic Write / Read / WritePartial schemas under `backend/app/schemas/` and re-export.
4. Add `serialize_*` helpers in `backend/app/mappers.py`.
5. Put queries and validation in `backend/app/services/<domain>.py` (services may raise `HTTPException`).
6. Add routers under `backend/app/routers/` (usually a campaign-nested list/create router plus an entity detail router).
7. Mount routers in `backend/app/main.py` with `prefix="/api"`.
8. Add TypeScript types in `frontend/src/app/models/domain.models.ts`.
9. Add methods on `frontend/src/app/services/api.service.ts`.
10. Add pages under `frontend/src/app/pages/` and routes in `frontend/src/app/app.routes.ts` (campaign param is always `:campaignId`).
11. Extend `backend/smoke_test.py` when the HTTP contract grows.

Prefer FastAPI `/docs` (when the API is running) plus the smoke test as living contracts.

## Frontend patterns

- Routes are lazy `loadComponent` entries in `app.routes.ts`; page folders mirror the URL.
- Reuse global Frutiger Aero utilities from `frontend/src/styles.scss` (see the file header) instead of inventing new panel/button styles.
- List/form screens for sessions and encounters are the best clones for new JSON CRUD UIs.
- Relationship webs (`/graphs/`) are the densest feature (Cytoscape); budget extra time there.

## Local development

See the root [README.md](README.md) for Docker and split frontend/backend commands.

```bash
# Full stack
docker compose up --build
# http://localhost:0314

# API smoke (backend must be running)
cd backend && python smoke_test.py http://127.0.0.1:8000/api
```

## Naming notes

- ORM model `GameSession` maps to table/API `sessions` (avoids clashing with SQLAlchemy `Session`).
- Session/encounter payloads use `npc_ids` (write) and `npcs` (read) for linked NPCs. Association tables in the DB remain `session_npcs` / `encounter_npcs`.
- Product language for graphs is “relationship webs”; URL paths stay `/graphs/`.
