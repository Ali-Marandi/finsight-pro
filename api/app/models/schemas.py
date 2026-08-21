from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class RatioCategory(str, Enum):
    profitability = "profitability"
    liquidity = "liquidity"
    leverage = "leverage"
    efficiency = "efficiency"


class RatioStatus(str, Enum):
    good = "good"
    warning = "warning"
    critical = "critical"


class RatioResultSchema(BaseModel):
    category: RatioCategory
    ratio_name: str
    value: float
    unit: str
    benchmark: Optional[float] = None
    status: RatioStatus


class AnalysisResponse(BaseModel):
    analysis_id: str
    company_name: str
    period: str
    file_name: str
    created_at: datetime
    ratios: list[RatioResultSchema]


class AnalysisSummarySchema(BaseModel):
    profitability: float
    liquidity: float
    leverage: float
    efficiency: float


class AnalysisHistoryItem(BaseModel):
    analysis_id: str
    company_name: str
    period: str
    file_name: str
    created_at: datetime
    summary: AnalysisSummarySchema


class LicenseValidateRequest(BaseModel):
    key: str
    machine_id: Optional[str] = None


class LicenseInfo(BaseModel):
    valid: bool
    tier: str = "free"
    expires_at: Optional[str] = None
    features: list[str] = []


class PreferencesSchema(BaseModel):
    default_language: str = "en"
    chart_theme: str = "light"
    decimal_places: int = 2
    auto_save: bool = True


class ReportGenerateRequest(BaseModel):
    analysis_id: str
    template: str = "professional"
    language: str = "en"
    include_charts: bool = True


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
