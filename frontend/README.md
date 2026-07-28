# Frontend (NPC Catalog)

Angular 19 standalone app for the purple Frutiger Aero DM catalog UI.

## Dev server

With the backend on port **8000**:

```bash
npm install
npm start
```

Opens **http://localhost:4200/**. [`proxy.conf.json`](proxy.conf.json) forwards `/api` and `/media` to `http://127.0.0.1:8000`.

Full stack via Docker (nginx + API) is **http://localhost:0314** from the repo root (`docker compose up --build`).

## Layout

```
src/app/
  app.routes.ts          # Lazy routes; folders mirror URLs
  pages/<feature>/       # One screen per folder (ts/html/scss)
  services/api.service.ts
  models/npc.models.ts   # Domain types (campaigns, NPCs, sessions, …)
src/styles.scss          # Design tokens + shared utilities
```

Prefer cloning **session** or **encounter** list/form pages for new JSON CRUD screens. Relationship webs live under `pages/graph-*` (Cytoscape).

## Styling

Global Frutiger Aero tokens and utilities live in `src/styles.scss`. Prefer those classes (see the file header) over new one-off panel/button styles. Page SCSS should handle layout only.

## Scripts

| Command | Purpose |
|---------|---------|
| `npm start` | Dev server with API proxy |
| `npm run build` | Production build → `dist/` |
| `npm test` | Karma unit tests (few/no specs today; schematics use `skipTests`) |

Contributor workflow for backend + feature checklist: see the root [CONTRIBUTING.md](../CONTRIBUTING.md).
