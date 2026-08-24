from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Literal

from app.services.financial_engineering import (
    calculate_var, monte_carlo_simulation, black_scholes, markowitz_optimize,
)

router = APIRouter()


class VaRRequest(BaseModel):
    prices: list[float]
    confidence: float = 0.95
    method: Literal["historical", "parametric", "cornish_fisher"] = "historical"
    position_value: float = 1_000_000


class MonteCarloRequest(BaseModel):
    s0: float
    mu: float
    sigma: float
    days: int = 252
    simulations: int = 10000
    position_value: float = 1_000_000


class BlackScholesRequest(BaseModel):
    spot: float
    strike: float
    time: float
    rate: float
    volatility: float
    option_type: Literal["call", "put"] = "call"


class MarkowitzRequest(BaseModel):
    expected_returns: list[float]
    cov_matrix: list[list[float]]
    risk_free_rate: float = 0.0


@router.post("/var")
async def var_endpoint(req: VaRRequest):
    """Calculate Value at Risk."""
    return calculate_var(req.prices, req.confidence, req.method, req.position_value)


@router.post("/monte-carlo")
async def monte_carlo_endpoint(req: MonteCarloRequest):
    """Run Monte Carlo price simulation."""
    return monte_carlo_simulation(req.s0, req.mu, req.sigma, req.days, req.simulations, req.position_value)


@router.post("/black-scholes")
async def black_scholes_endpoint(req: BlackScholesRequest):
    """Price an option using Black-Scholes model."""
    return black_scholes(req.spot, req.strike, req.time, req.rate, req.volatility, req.option_type)


@router.post("/portfolio-optimize")
async def portfolio_optimize_endpoint(req: MarkowitzRequest):
    """Run Markowitz mean-variance portfolio optimization."""
    return markowitz_optimize(req.expected_returns, req.cov_matrix, req.risk_free_rate)
