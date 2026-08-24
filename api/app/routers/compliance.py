from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.compliance import run_compliance_check, get_compliance_standards

router = APIRouter()


class ComplianceRequest(BaseModel):
    financial_data: dict  # {revenue, net_income, total_assets, etc.}


@router.post("/check")
async def run_check(request: ComplianceRequest):
    """Run compliance checks against Iranian standards and IFRS."""
    result = run_compliance_check(request.financial_data)
    return result


@router.get("/standards")
async def list_standards():
    """List all compliance standards checked."""
    return {"standards": get_compliance_standards()}
