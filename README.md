# NPC Catalog

A purple Frutiger Aero D&D NPC catalog for Dungeon Masters. Create campaigns, catalog NPCs as you invent them, and retrieve them quickly at the table.

## Quick start

```bash
docker compose up --build
```

Open **http://localhost:8080**

Data persists in the `npc_data` Docker volume (SQLite database + campaign images).

## Development

Copy environment defaults:

```bash
cp .env.example .env
```

### Backend only

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
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

## Stack

- **Frontend:** Angular (standalone), SCSS
- **Backend:** Django + Django REST Framework
- **Database:** SQLite on Docker volume
- **Auth:** None (single-user local tool)
