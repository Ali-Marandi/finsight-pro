from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.advanced_optimization import (
    socp_portfolio,
    robust_optimization,
    hierarchical_risk_parity,
    multi_objective_optimization,
    advanced_optimization_demo,
)


router = APIRouter()


class SOCPRequest(BaseModel):
    expected_returns: list[float]
    cov_matrix: list[list[float]]
    constraints: dict | None = None
    risk_free_rate: float = 0.0
    current_weights: list[float] | None = None


class RobustRequest(BaseModel):
    expected_returns: list[float]
    cov_matrix: list[list[float]]
    uncertainty_budget: float = 0.1
    delta: float = 0.95
    risk_free_rate: float = 0.0


class HRPRequest(BaseModel):
    returns_matrix: list[list[float]]
    asset_names: list[str] | None = None
    risk_free_rate: float = 0.0


class ParetoRequest(BaseModel):
    expected_returns: list[float]
    cov_matrix: list[list[float]]
    n_points: int = 50
    risk_free_rate: float | None = None


@router.post("/socp")
async def socp_endpoint(req: SOCPRequest):
    """SOCP portfolio optimization with real-world constraints."""
    return socp_portfolio(
        req.expected_returns,
        req.cov_matrix,
        req.constraints,
        req.risk_free_rate,
        req.current_weights,
    )


@router.post("/robust")
async def robust_endpoint(req: RobustRequest):
    """Robust portfolio optimization under uncertainty."""
    return robust_optimization(
        req.expected_returns,
        req.cov_matrix,
        req.uncertainty_budget,
        req.delta,
        req.risk_free_rate,
    )


@router.post("/hrp")
async def hrp_endpoint(req: HRPRequest):
    """Hierarchical Risk Parity allocation."""
    return hierarchical_risk_parity(
        req.returns_matrix,
        req.asset_names,
        req.risk_free_rate,
    )


@router.post("/pareto")
async def pareto_endpoint(req: ParetoRequest):
    """Multi-objective Pareto frontier for return vs risk."""
    return multi_objective_optimization(
        req.expected_returns,
        req.cov_matrix,
        req.n_points,
        req.risk_free_rate,
    )


@router.get("/demo")
async def demo_endpoint():
    """Full demo with 8 TSE stocks across 4 sectors."""
    return advanced_optimization_demo()
