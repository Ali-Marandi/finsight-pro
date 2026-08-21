"""License validation middleware for protected endpoints.

In production, this middleware will validate the license key from the
Authorization header against LemonSqueezy's API.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)


FREE_ENDPOINTS = {
    "/api/v1/health",
    "/api/v1/license/validate",
}


async def require_license(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """Validate license for protected endpoints."""
    path = request.url.path
    
    # Allow free endpoints
    if path in FREE_ENDPOINTS or path.startswith("/api/v1/analysis/upload"):
        return None
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={"code": "MISSING_LICENSE", "message": "License key required. Please activate your copy of FinSight Pro."},
        )
    
    # In production: validate against LemonSqueezy
    # For MVP: accept any Bearer token
    token = credentials.credentials
    if not token or len(token) < 5:
        raise HTTPException(status_code=401, detail="Invalid license key")
    
    return None
