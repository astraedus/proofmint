"""
ProofMint — AI Agent Proof-of-Work NFT Certificates on Hedera

FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.certificates import router as certificates_router
from backend.api.health import router as health_router
from backend.api.tasks import router as tasks_router
from backend.db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("ProofMint started")
    yield
    logger.info("ProofMint shutting down")


app = FastAPI(
    title="ProofMint",
    description="AI Agent Proof-of-Work NFT Certificates on Hedera",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(certificates_router)
app.include_router(tasks_router)


if __name__ == "__main__":
    import uvicorn
    from backend.config import settings
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
