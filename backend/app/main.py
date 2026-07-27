from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.media import ensure_media_root
from app.routers import campaigns, encounters, graphs, npcs, sessions, tags


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_media_root()
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="NPC Catalog API", lifespan=lifespan)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(settings.media_root)), name="media")

app.include_router(campaigns.router, prefix="/api")
app.include_router(graphs.campaign_graphs_router, prefix="/api")
app.include_router(graphs.campaign_relation_types_router, prefix="/api")
app.include_router(graphs.router, prefix="/api")
app.include_router(graphs.relation_types_router, prefix="/api")
app.include_router(graphs.graph_nodes_router, prefix="/api")
app.include_router(graphs.graph_edges_router, prefix="/api")
app.include_router(sessions.campaign_sessions_router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(encounters.campaign_encounters_router, prefix="/api")
app.include_router(encounters.router, prefix="/api")
app.include_router(npcs.campaign_npcs_router, prefix="/api")
app.include_router(npcs.router, prefix="/api")
app.include_router(tags.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
