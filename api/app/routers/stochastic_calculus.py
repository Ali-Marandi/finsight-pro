from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.stochastic_calculus import (
    ito_simulation,
    heston_model,
    option_greeks_surface,
    barrier_option_pricing,
    jump_diffusion_model,
    stochastic_calculus_demo,
)

router = APIRouter()


class ItoRequest(BaseModel):
    s0: float = 1000.0
    mu: float = 0.15
    sigma: float = 0.25
    days: int = 252
    n_paths: int = 1000
    dt: Optional[float] = None


class HestonRequest(BaseModel):
    s0: float = 1000.0
    v0: float = 0.04
    kappa: float = 2.0
    theta: float = 0.04
    xi: float = 0.3
    rho: float = -0.7
    days: int = 252
    n_paths: int = 1000


class GreeksRequest(BaseModel):
    s_min: float = 500.0
    s_max: float = 1500.0
    n_spot_points: int = 20
    t_min: float = 0.02
    t_max: float = 1.0
    n_time_points: int = 15
    strike: float = 1000.0
    rate: float = 0.05
    vol: float = 0.25


class BarrierRequest(BaseModel):
    s0: float = 1000.0
    strike: float = 1000.0
    barrier: float = 1200.0
    barrier_type: str = "up-and-out"
    option_type: str = "call"
    days: int = 252
    n_sims: int = 50000
    mu: float = 0.15
    sigma: float = 0.25
    rate: float = 0.05


class JumpDiffusionRequest(BaseModel):
    s0: float = 1000.0
    mu: float = 0.15
    sigma: float = 0.20
    days: int = 252
    n_paths: int = 1000
    jump_lambda: float = 0.1
    jump_mu: float = -0.02
    jump_sigma: float = 0.05


@router.post("/ito")
async def ito_endpoint(req: ItoRequest):
    """Simulate GBM paths using Itô's Lemma."""
    return ito_simulation(
        s0=req.s0,
        mu=req.mu,
        sigma=req.sigma,
        days=req.days,
        n_paths=req.n_paths,
        dt=req.dt,
    )


@router.post("/heston")
async def heston_endpoint(req: HestonRequest):
    """Run Heston stochastic volatility simulation."""
    return heston_model(
        s0=req.s0,
        v0=req.v0,
        kappa=req.kappa,
        theta=req.theta,
        xi=req.xi,
        rho=req.rho,
        days=req.days,
        n_paths=req.n_paths,
    )


@router.post("/greeks")
async def greeks_endpoint(req: GreeksRequest):
    """Compute Black-Scholes Greeks surfaces over spot/time grid."""
    return option_greeks_surface(
        s_min=req.s_min,
        s_max=req.s_max,
        n_spot_points=req.n_spot_points,
        t_min=req.t_min,
        t_max=req.t_max,
        n_time_points=req.n_time_points,
        strike=req.strike,
        rate=req.rate,
        vol=req.vol,
    )


@router.post("/barrier")
async def barrier_endpoint(req: BarrierRequest):
    """Price barrier options via Monte Carlo simulation."""
    return barrier_option_pricing(
        s0=req.s0,
        strike=req.strike,
        barrier=req.barrier,
        barrier_type=req.barrier_type,
        option_type=req.option_type,
        days=req.days,
        n_sims=req.n_sims,
        mu=req.mu,
        sigma=req.sigma,
        rate=req.rate,
    )


@router.post("/jump-diffusion")
async def jump_diffusion_endpoint(req: JumpDiffusionRequest):
    """Run Merton jump-diffusion simulation."""
    return jump_diffusion_model(
        s0=req.s0,
        mu=req.mu,
        sigma=req.sigma,
        days=req.days,
        n_paths=req.n_paths,
        jump_lambda=req.jump_lambda,
        jump_mu=req.jump_mu,
        jump_sigma=req.jump_sigma,
    )


@router.get("/demo")
async def demo_endpoint():
    """Get comprehensive stochastic calculus demo with TSE parameters."""
    return stochastic_calculus_demo()
