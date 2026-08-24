from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.factor_analysis import pca_analysis, fama_french, factor_analysis_demo


router = APIRouter()


class PCARequest(BaseModel):
    returns_matrix: list[list[float]]
    asset_names: list[str] | None = None
    n_components: int | None = None


class FamaFrenchRequest(BaseModel):
    returns_matrix: list[list[float]]
    market_returns: list[float]
    asset_names: list[str] | None = None
    market_cap: list[float] | None = None
    book_to_market: list[float] | None = None


@router.post("/pca")
async def pca_endpoint(req: PCARequest):
    """Run PCA factor analysis on asset returns."""
    return pca_analysis(req.returns_matrix, req.asset_names, req.n_components)


@router.post("/fama-french")
async def fama_french_endpoint(req: FamaFrenchRequest):
    """Run Fama-French 3-factor model estimation."""
    return fama_french(
        req.returns_matrix,
        req.market_returns,
        req.asset_names,
        req.market_cap,
        req.book_to_market,
    )


@router.get("/demo")
async def demo_endpoint():
    """Get a demo factor analysis with 10 TSE stocks."""
    return factor_analysis_demo()
