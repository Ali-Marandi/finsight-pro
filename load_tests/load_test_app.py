"""Minimal API surface for repeatable Cloud Sync load tests.

It intentionally exercises the production Cloud Sync router and database models
while excluding unrelated product modules from performance measurements.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.models.database import init_db
from app.routers.cloud_sync import router as cloud_sync_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="FinSight Cloud Sync Load Test", lifespan=lifespan)
app.include_router(cloud_sync_router, prefix="/api/v1/cloud-sync", tags=["Cloud Sync"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "service": "cloud-sync-load-test"}
