from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.network_analysis import (
    correlation_network,
    minimum_spanning_tree,
    contagion_simulation,
    systemic_risk_metrics,
    network_analysis_demo,
)


router = APIRouter()


class CorrelationNetworkRequest(BaseModel):
    returns_matrix: list[list[float]]
    threshold: float = 0.3
    asset_names: list[str] | None = None


class MSTRequest(BaseModel):
    returns_matrix: list[list[float]]
    asset_names: list[str] | None = None


class ContagionRequest(BaseModel):
    adjacency_matrix: list[list[float]]
    initial_shocks: dict[str, float]
    transmission_rate: float = 0.4
    recovery_rate: float = 0.1
    n_rounds: int = 20
    asset_names: list[str] | None = None


class SystemicRiskRequest(BaseModel):
    returns_matrix: list[list[float]]
    asset_names: list[str] | None = None
    confidence_level: float = 0.95


@router.post("/correlation-network")
async def correlation_network_endpoint(req: CorrelationNetworkRequest):
    """Build a correlation network from asset returns."""
    return correlation_network(req.returns_matrix, req.threshold, req.asset_names)


@router.post("/mst")
async def mst_endpoint(req: MSTRequest):
    """Build minimum spanning tree from correlation distance matrix."""
    return minimum_spanning_tree(req.returns_matrix, req.asset_names)


@router.post("/contagion")
async def contagion_endpoint(req: ContagionRequest):
    """Simulate financial contagion on a network."""
    return contagion_simulation(
        req.adjacency_matrix,
        req.initial_shocks,
        req.transmission_rate,
        req.recovery_rate,
        req.n_rounds,
        req.asset_names,
    )


@router.post("/systemic-risk")
async def systemic_risk_endpoint(req: SystemicRiskRequest):
    """Compute systemic risk metrics for a portfolio."""
    return systemic_risk_metrics(req.returns_matrix, req.asset_names, req.confidence_level)


@router.get("/demo")
async def demo_endpoint():
    """Get a demo network analysis with 12 TSE stocks across 5 sectors."""
    return network_analysis_demo()
