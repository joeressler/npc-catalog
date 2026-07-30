from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, validate_production_secrets
from app.media import ensure_media_root
from app.middleware_auth import AuthMiddleware
from app.routers import auth, campaigns, encounters, graphs, locations, npcs, sessions, tags


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production_secrets()
    ensure_media_root()
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    yield


_docs = "/docs" if settings.debug else None
_redoc = "/redoc" if settings.debug else None
_openapi = "/openapi.json" if settings.debug else None

app = FastAPI(
    title="NPC Catalog API",
    lifespan=lifespan,
    docs_url=_docs,
    redoc_url=_redoc,
    openapi_url=_openapi,
)

# Auth runs outermost so /api and /media are gated before route handlers.
app.add_middleware(AuthMiddleware)

if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:0314"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(settings.media_root)), name="media")

app.include_router(auth.router, prefix="/api")
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
app.include_router(locations.campaign_locations_router, prefix="/api")
app.include_router(locations.router, prefix="/api")
app.include_router(npcs.campaign_npcs_router, prefix="/api")
app.include_router(npcs.router, prefix="/api")
app.include_router(tags.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
