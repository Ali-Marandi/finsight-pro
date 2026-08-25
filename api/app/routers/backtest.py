from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.backtest import backtest_strategy, portfolio_backtest, backtest_demo

router = APIRouter()


class SingleBacktestRequest(BaseModel):
    prices: list[float]
    signals: list[int] | None = None
    initial_capital: float = 1_000_000
    commission: float = 0.001
    slippage: float = 0.0005
    benchmark_prices: list[float] | None = None
    strategy_name: str = "Strategy"


class PortfolioBacktestRequest(BaseModel):
    asset_prices: list[list[float]]
    weights: list[float] | None = None
    rebalance_days: int = 21
    initial_capital: float = 10_000_000
    benchmark_prices: list[float] | None = None
    asset_names: list[str] | None = None


@router.post("/strategy")
async def strategy_backtest_endpoint(req: SingleBacktestRequest):
    """Run a single-asset strategy backtest."""
    return backtest_strategy(
        prices=req.prices,
        signals=req.signals,
        initial_capital=req.initial_capital,
        commission=req.commission,
        slippage=req.slippage,
        benchmark_prices=req.benchmark_prices,
        strategy_name=req.strategy_name,
    )


@router.post("/portfolio")
async def portfolio_backtest_endpoint(req: PortfolioBacktestRequest):
    """Run a portfolio backtest with rebalancing."""
    return portfolio_backtest(
        asset_prices=req.asset_prices,
        weights=req.weights,
        rebalance_days=req.rebalance_days,
        initial_capital=req.initial_capital,
        benchmark_prices=req.benchmark_prices,
        asset_names=req.asset_names,
    )


@router.get("/demo")
async def demo_endpoint():
    """Get demo backtest results with synthetic TSE data."""
    return backtest_demo()
