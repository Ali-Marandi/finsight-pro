from fastapi import APIRouter, HTTPException
from app.models.schemas import LicenseValidateRequest, LicenseInfo

router = APIRouter()


@router.post("/validate", response_model=LicenseInfo)
async def validate_license(request: LicenseValidateRequest):
    """Validate a license key and return license info."""
    # In production, this would call LemonSqueezy API or a license server
    # For MVP, we validate format and return a demo response
    
    key = request.key.strip()
    
    if not key or len(key) < 10:
        return LicenseInfo(valid=False, tier="free", features=[])
    
    # Demo: accept keys starting with "FSP-PRO-" as Pro
    if key.startswith("FSP-PRO-"):
        return LicenseInfo(
            valid=True,
            tier="pro",
            expires_at="2026-12-31",
            features=[
                "all_ratios",
                "pdf_reports",
                "xlsx_export",
                "batch_processing",
                "industry_benchmarks",
                "interactive_charts",
            ],
        )
    
    # Demo: accept keys starting with "FSP-ENT-" as Enterprise
    if key.startswith("FSP-ENT-"):
        return LicenseInfo(
            valid=True,
            tier="enterprise",
            expires_at="2026-12-31",
            features=[
                "all_ratios",
                "pdf_reports",
                "xlsx_export",
                "batch_processing",
                "industry_benchmarks",
                "interactive_charts",
                "custom_ratios",
                "api_access",
                "custom_branding",
                "priority_support",
            ],
        )
    
    return LicenseInfo(valid=False, tier="free", features=[])
