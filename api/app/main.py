from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.models.database import engine, Base, init_db
from app.routers import (
    analysis, evidence, reports, license as license_router, settings,
    ai_copilot, prediction,
    document_intelligence, benchmarking, compliance as compliance_router,
    consolidation, tsetmc, cloud_sync,
    time_series, financial_engineering,
    fuzzy_mcdm, black_litterman, factor_analysis,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown
    engine.dispose()


app = FastAPI(
    title="FinSight Pro API",
    description="Backend API for FinSight Pro Desktop — AI-Powered Financial Analysis",
    version="0.3.0",
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
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["Evidence Review"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(license_router.router, prefix="/api/v1/license", tags=["License"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(ai_copilot.router, prefix="/api/v1/ai", tags=["AI Copilot"])
app.include_router(prediction.router, prefix="/api/v1/prediction", tags=["Prediction"])
app.include_router(document_intelligence.router, prefix="/api/v1/document-intelligence", tags=["Document Intelligence"])
app.include_router(benchmarking.router, prefix="/api/v1/benchmarking", tags=["Benchmarking"])
app.include_router(compliance_router.router, prefix="/api/v1/compliance", tags=["Compliance"])
app.include_router(consolidation.router, prefix="/api/v1/consolidation", tags=["Consolidation"])
app.include_router(tsetmc.router, prefix="/api/v1/tsetmc", tags=["TSETMC"])
app.include_router(cloud_sync.router, prefix="/api/v1/cloud-sync", tags=["Cloud Sync"])
app.include_router(time_series.router, prefix="/api/v1/time-series", tags=["Time Series"])
app.include_router(financial_engineering.router, prefix="/api/v1/financial-engineering", tags=["Financial Engineering"])
app.include_router(fuzzy_mcdm.router, prefix="/api/v1/fuzzy-mcdm", tags=["Fuzzy MCDM"])
app.include_router(black_litterman.router, prefix="/api/v1/black-litterman", tags=["Black-Litterman"])
app.include_router(factor_analysis.router, prefix="/api/v1/factor-analysis", tags=["Factor Analysis"])


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": "0.6.0"}
