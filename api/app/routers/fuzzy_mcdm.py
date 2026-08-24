from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.fuzzy_mcdm import fuzzy_ahp, fuzzy_topsis, stock_ranking


router = APIRouter()


class AHPRequest(BaseModel):
    criteria_matrix: list[list[float]]
    criteria_names: list[str]


class TOPSISRequest(BaseModel):
    decision_matrix: list[list[float]]
    criteria_names: list[str]
    alternative_names: list[str]
    criteria_weights: list[float]
    benefit_criteria: list[bool] | None = None


class StockRankingRequest(BaseModel):
    stocks: list[dict]
    criteria: list[str] | None = None


@router.post("/ahp")
async def ahp_endpoint(req: AHPRequest):
    """Run Fuzzy AHP analysis to derive criteria weights."""
    return fuzzy_ahp(req.criteria_matrix, req.criteria_names)


@router.post("/topsis")
async def topsis_endpoint(req: TOPSISRequest):
    """Run Fuzzy TOPSIS to rank alternatives."""
    return fuzzy_topsis(
        req.decision_matrix,
        req.criteria_names,
        req.alternative_names,
        req.criteria_weights,
        req.benefit_criteria,
    )


@router.post("/stock-ranking")
async def stock_ranking_endpoint(req: StockRankingRequest):
    """Run combined AHP-TOPSIS pipeline to rank stocks."""
    return stock_ranking(req.stocks, req.criteria)


@router.get("/demo")
async def demo_endpoint():
    """Get demo data for Fuzzy MCDM."""
    demo_stocks = [
        {"name": "Persian Gulf Petro", "pe": 8.5, "roe": 0.22, "debt_ratio": 0.35, "revenue_growth": 0.18},
        {"name": "Melli Bank", "pe": 6.2, "roe": 0.14, "debt_ratio": 0.82, "revenue_growth": 0.05},
        {"name": "Mobarakeh Steel", "pe": 7.1, "roe": 0.19, "debt_ratio": 0.45, "revenue_growth": 0.12},
        {"name": "Iran Khodro", "pe": 11.0, "roe": 0.08, "debt_ratio": 0.70, "revenue_growth": -0.03},
        {"name": "Telecom Iran", "pe": 9.3, "roe": 0.25, "debt_ratio": 0.28, "revenue_growth": 0.15},
        {"name": "National Copper", "pe": 5.8, "roe": 0.30, "debt_ratio": 0.40, "revenue_growth": 0.22},
    ]
    result = stock_ranking(demo_stocks)
    return {"demo_stocks": demo_stocks, "analysis": result}
