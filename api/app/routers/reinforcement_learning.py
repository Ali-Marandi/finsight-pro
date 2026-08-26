from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from app.services.reinforcement_learning import (
    q_learning_execution,
    twap_vwap_strategy,
    portfolio_rl_allocation,
    reinforcement_learning_demo,
)

router = APIRouter()


class ExecutionRequest(BaseModel):
    price_series: List[float]
    total_shares: int = 100000
    n_steps: int = 300
    learning_rate: float = 0.1
    discount_factor: float = 0.95
    episodes: int = 5000


class TwapVwapRequest(BaseModel):
    price_series: List[float]
    volumes: Optional[List[float]] = None
    total_shares: int = 100000
    n_steps: int = 300


class PortfolioAllocationRequest(BaseModel):
    returns_matrix: List[List[float]]
    n_assets: Optional[int] = None
    episodes: int = 3000


@router.post("/execution")
async def execution_endpoint(req: ExecutionRequest):
    """Run Q-Learning optimal order execution to minimize slippage."""
    return q_learning_execution(
        price_series=req.price_series,
        total_shares=req.total_shares,
        n_steps=req.n_steps,
        learning_rate=req.learning_rate,
        discount_factor=req.discount_factor,
        episodes=req.episodes,
    )


@router.post("/twap-vwap")
async def twap_vwap_endpoint(req: TwapVwapRequest):
    """Compute TWAP and VWAP execution benchmark strategies."""
    return twap_vwap_strategy(
        price_series=req.price_series,
        volumes=req.volumes,
        total_shares=req.total_shares,
        n_steps=req.n_steps,
    )


@router.post("/portfolio-allocation")
async def portfolio_allocation_endpoint(req: PortfolioAllocationRequest):
    """Run Q-Learning dynamic portfolio allocation across N assets."""
    return portfolio_rl_allocation(
        returns_matrix=req.returns_matrix,
        n_assets=req.n_assets,
        episodes=req.episodes,
    )


@router.get("/demo")
async def demo_endpoint():
    """Get comprehensive RL engine demo with TSE parameters."""
    return reinforcement_learning_demo()
