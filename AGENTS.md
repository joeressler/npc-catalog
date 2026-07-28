## Learned User Preferences

- Prefers a purple Frutiger Aero visual design for the NPC Catalog UI.
- On Windows, prefer Command Prompt over PowerShell for Docker commands when PowerShell cannot run Docker.
- For larger features, prefer plan-first then implement the attached plan without editing the plan file.
- Search and filters (e.g. faction) should match partial/substring input, not only exact strings.
- When overhauling the backend, prefer a fresh cutover (new schema, wipe/recreate data) over preserving Django admin or migrating legacy data.
- Character relationship webs should be interactive visuals, support multiple named webs per campaign, directed and easy bidirectional relations, a synthetic Party node, and optional PC sub-nodes under Party for one-off PC–NPC ties.
- Campaign sessions should auto-assign the next number; story beats are DM-orderable branching paths; clues and secrets are line items; overall notes are free text.
- Campaign encounters are reusable, cloneable set-pieces (title, short description, enemy quantities/types, battlefield text, objects/interaction points, loot line items, further notes) with soft NPC links; sessions can soft-link encounters without owning them.
- Campaign locations are reusable place notes (title, description, optional image, loot line items, POIs/interactables) with soft NPC links; NPCs can optionally pick a catalog location via `location_id` while keeping free-text location notes; location detail shows Residents (FK) and Linked NPCs (soft); sessions can soft-link locations.

## Learned Workspace Facts

- Stack is Angular (standalone) frontend, FastAPI + SQLAlchemy + Alembic backend, SQLite on a Docker volume (`npc_data`); no auth (single-user local tool).
- `docker compose up --build` serves the app at http://localhost:0314; data and uploaded images (campaigns, NPCs, locations) live under `/data` in the backend volume.
- Backend was migrated from Django to FastAPI with a wipe/recreate cutover; Django admin is not part of the stack.
- NPCs are campaign-scoped with core fields (name, aliases, role, alignment, location free-text, optional catalog location, faction, attitude, party relationship, tags) plus optional image and optional DM detail sections (appearance, voice, personality, motivation, secrets, knowledge, inventory, notes, session history).
- Campaign sessions are a per-campaign numbered notes feature (story beats/paths, linked NPCs, notes, clues, secrets, optional linked encounters and locations).
- Campaign encounters are reusable combat/set-piece notes (enemies, battlefield, objects, loot, linked NPCs) that can be cloned; not owned by sessions.
- Character graphs (relationship webs) are campaign-scoped; relation types are an editable set list; graph UI uses Cytoscape.
