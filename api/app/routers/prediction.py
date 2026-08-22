from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models.database import get_db
from app.services.predictor import BankruptcyPredictor, predict_from_analysis


router = APIRouter()


class PredictionFromAnalysisRequest(BaseModel):
    analysis_id: str


class ManualPredictionRequest(BaseModel):
    total_assets: float
    total_liabilities: float
    total_equity: float
    net_income: float
    revenue: float
    ebit: float
    current_assets: float
    current_liabilities: float
    interest_expense: float = 0.0
    retained_earnings: Optional[float] = None
    market_value_equity: Optional[float] = None


@router.post("/from-analysis")
async def predict_from_existing_analysis(
    request: PredictionFromAnalysisRequest,
    db: Session = Depends(get_db),
):
    """Run bankruptcy prediction using an existing analysis's data."""
    from app.models.models import AnalysisModel, RatioResultModel
    
    analysis = db.query(AnalysisModel).filter(
        AnalysisModel.id == request.analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    ratios = db.query(RatioResultModel).filter(
        RatioResultModel.analysis_id == request.analysis_id
    ).all()
    
    analysis_data = {
        "company_name": analysis.company_name,
        "period": analysis.period,
        "ratios": [
            {
                "category": r.category,
                "ratio_name": r.ratio_name,
                "value": r.value,
                "unit": r.unit,
                "benchmark": r.benchmark,
                "status": r.status,
            }
            for r in ratios
        ],
    }
    
    try:
        result = predict_from_analysis(analysis_data)
        result["company_name"] = analysis.company_name
        result["period"] = analysis.period
        result["analysis_id"] = request.analysis_id
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/manual")
async def predict_manual(request: ManualPredictionRequest):
    """Run bankruptcy prediction with manually provided financial figures."""
    predictor = BankruptcyPredictor()
    try:
        result = predictor.predict_all(
            total_assets=request.total_assets,
            total_liabilities=request.total_liabilities,
            total_equity=request.total_equity,
            net_income=request.net_income,
            revenue=request.revenue,
            ebit=request.ebit,
            current_assets=request.current_assets,
            current_liabilities=request.current_liabilities,
            interest_expense=request.interest_expense,
            retained_earnings=request.retained_earnings,
            market_value_equity=request.market_value_equity,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")