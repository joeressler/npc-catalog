# NPC Catalog

A purple Frutiger Aero D&D NPC catalog for Dungeon Masters. Create campaigns, catalog NPCs as you invent them, and retrieve them quickly at the table.

## Quick start

```bash
docker compose up --build
```

Open **http://localhost:0314**

Data persists in the `npc_data` Docker volume (SQLite database + campaign images).

### Fresh cutover (wipe existing data)

When migrating from the old Django backend or resetting all data:

```bash
docker compose down -v
docker compose up --build
```

## Development

Copy environment defaults:

```bash
cp .env.example .env
```

### Backend only

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend only

```bash
cd frontend
npm install
npm start
```

The dev server proxies `/api` and `/media` to the backend when configured in `proxy.conf.json`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/api/campaigns/` | List / create campaigns |
| GET/PATCH/DELETE | `/api/campaigns/{id}/` | Campaign detail |
| GET/POST | `/api/campaigns/{id}/npcs/` | NPCs in campaign |
| GET/PATCH/DELETE | `/api/npcs/{id}/` | NPC detail |
| GET | `/api/tags/` | All tags |
| GET | `/api/npcs/?q=&alignment=&tag=&location=&faction=` | Filter NPCs |
| GET/POST | `/api/campaigns/{id}/graphs/` | List / create relationship webs |
| GET/PATCH/DELETE | `/api/graphs/{id}/` | Graph detail (nodes + edges) |
| GET/POST | `/api/campaigns/{id}/relation-types/` | List / add relation types |
| PATCH/DELETE | `/api/relation-types/{id}/` | Update / delete relation type |
| POST | `/api/graphs/{id}/nodes/` | Add NPC, Party, or PC node |
| PATCH/DELETE | `/api/graph-nodes/{id}/` | Update position / remove node |
| POST | `/api/graphs/{id}/edges/` | Add directed relation (`from_node_id` / `to_node_id`, optional `bidirectional`) |
| PATCH/DELETE | `/api/graph-edges/{id}/` | Update / remove relation |

## Stack

- **Frontend:** Angular (standalone), SCSS
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Database:** SQLite on Docker volume
- **Auth:** None (single-user local tool)
