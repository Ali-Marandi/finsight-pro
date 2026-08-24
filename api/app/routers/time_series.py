from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.time_series import (
    generate_sample_prices, time_series_summary, run_arima,
    run_garch, decompose_series, run_full_pipeline,
)

router = APIRouter()


class TimeSeriesRequest(BaseModel):
    prices: list[float]
    forecast_steps: int = 30


class GARCHRequest(BaseModel):
    prices: list[float]


class DecomposeRequest(BaseModel):
    prices: list[float]
    period: Optional[int] = None


@router.get("/summary")
async def summary(use_demo: bool = False):
    """Get time series summary statistics."""
    prices = generate_sample_prices() if use_demo else generate_sample_prices()
    return time_series_summary(prices)


@router.post("/arima")
async def arima_endpoint(req: TimeSeriesRequest):
    """Run ARIMA model on provided price series."""
    return run_arima(req.prices, req.forecast_steps)


@router.post("/garch")
async def garch_endpoint(req: GARCHRequest):
    """Run GARCH(1,1) volatility model."""
    return run_garch(req.prices)


@router.post("/decompose")
async def decompose_endpoint(req: DecomposeRequest):
    """Decompose time series into trend, seasonal, residual."""
    return decompose_series(req.prices, req.period)


@router.post("/full")
async def full_pipeline(req: TimeSeriesRequest):
    """Run complete time series analysis pipeline."""
    return run_full_pipeline(req.prices, req.forecast_steps)
