from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.models.database import engine, Base, init_db
from app.routers import analysis, reports, license as license_router, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    engine.dispose()


app = FastAPI(
    title="FinSight Pro API",
    description="Backend API for FinSight Pro Desktop Application",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(license_router.router, prefix="/api/v1/license", tags=["License"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
