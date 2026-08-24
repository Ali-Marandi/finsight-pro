from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal

from app.services.black_litterman import black_litterman, black_litterman_demo


router = APIRouter()


class View(BaseModel):
    assets: list[int]
    value: float
    confidence: float = 1.0


class BlackLittermanRequest(BaseModel):
    market_cap_weights: list[float]
    covariance_matrix: list[list[float]]
    risk_aversion: float = 2.5
    tau: float = 0.05
    views: list[View] | None = None
    risk_free_rate: float = 0.0


@router.post("/optimize")
async def optimize_endpoint(req: BlackLittermanRequest):
    """Run Black-Litterman portfolio optimization."""
    views_dicts = None
    if req.views:
        views_dicts = [v.model_dump() for v in req.views]
    return black_litterman(
        req.market_cap_weights,
        req.covariance_matrix,
        req.risk_aversion,
        req.tau,
        views_dicts,
        req.risk_free_rate,
    )


@router.get("/demo")
async def demo_endpoint():
    """Get a demo Black-Litterman analysis with 5 assets."""
    return black_litterman_demo()
