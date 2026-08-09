from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # 👈 Import CORS

from app.config import settings
from app.graph.neo4j_client import neo4j_client
from app.api.graph_router import router as graph_router
from app.api.routes.repositories import router as repository_router
from app.risk.route_change_coupling import (
    router as change_coupling_router,
)
from app.rag.route_rag import router as rag_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    neo4j_client.connect()
    logger.info("Connected to Neo4j")

    yield

    # Shutdown
    neo4j_client.close()
    logger.info("Disconnected from Neo4j")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# 👈 Add CORS Middleware so Vite frontend (http://localhost:5173) can communicate safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(repository_router)
app.include_router(graph_router)
app.include_router(change_coupling_router)
app.include_router(rag_router)

@app.get("/")
async def root():
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy" if neo4j_client.is_connected() else "unhealthy",
        "neo4j": "connected" if neo4j_client.is_connected() else "disconnected",
    }