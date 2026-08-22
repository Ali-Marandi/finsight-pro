from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from app.services.ai_copilot import chat_with_ai
from app.models.database import get_db
from sqlalchemy.orm import Session


router = APIRouter()


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    analysis_id: Optional[str] = None
    conversation_history: List[ChatMessage] = Field(default_factory=list)


class AIConfigRequest(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_endpoint: str = Field(default="https://api.openai.com/v1")
    model: str = Field(default="gpt-4o-mini")


@router.post("/chat")
async def copilot_chat(request: ChatRequest, db: Session = None):
    """Chat with the AI Financial Copilot."""
    analysis_data = None
    prediction_data = None
    
    # Load analysis data if analysis_id is provided
    if request.analysis_id:
        try:
            from app.models.models import AnalysisModel, RatioResultModel
            if db is None:
                from app.models.database import SessionLocal
                db = SessionLocal()
                close_db = True
            else:
                close_db = False
            
            analysis = db.query(AnalysisModel).filter(
                AnalysisModel.id == request.analysis_id
            ).first()
            
            if analysis:
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
                
                # Also run prediction if we have the data
                try:
                    from app.services.predictor import predict_from_analysis
                    prediction_data = predict_from_analysis(analysis_data)
                except Exception:
                    pass  # Prediction is optional
            
            if close_db:
                db.close()
        except Exception:
            pass  # Continue without analysis data
    
    # Load AI config from settings
    api_key = None
    api_endpoint = None
    model = "gpt-4o-mini"
    try:
        from app.models.database import SessionLocal
        from app.models.models import SettingsModel
        tmp_db = SessionLocal()
        settings = tmp_db.query(SettingsModel).first()
        if settings:
            import json
            config = json.loads(settings.ai_config) if settings.ai_config else {}
            api_key = config.get("api_key")
            api_endpoint = config.get("api_endpoint")
            model = config.get("model", "gpt-4o-mini")
        tmp_db.close()
    except Exception:
        pass
    
    result = await chat_with_ai(
        message=request.message,
        analysis_data=analysis_data,
        prediction_data=prediction_data,
        conversation_history=[msg.dict() for msg in request.conversation_history],
        api_key=api_key,
        api_endpoint=api_endpoint,
        model=model,
    )
    
    return result


@router.post("/configure")
async def configure_ai(config: AIConfigRequest, db: Session = None):
    """Configure the AI Copilot API settings."""
    try:
        from app.models.database import SessionLocal
        from app.models.models import SettingsModel
        import json
        
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        settings = db.query(SettingsModel).first()
        if not settings:
            settings = SettingsModel()
            db.add(settings)
        
        settings.ai_config = json.dumps({
            "api_key": config.api_key,
            "api_endpoint": config.api_endpoint,
            "model": config.model,
        })
        db.commit()
        
        if close_db:
            db.close()
        
        return {"status": "configured", "model": config.model, "endpoint": config.api_endpoint}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configure")
async def get_ai_config(db: Session = None):
    """Get current AI configuration (without API key)."""
    try:
        from app.models.database import SessionLocal
        from app.models.models import SettingsModel
        import json
        
        if db is None:
            db = SessionLocal()
            close_db = True
        else:
            close_db = False
        
        settings = db.query(SettingsModel).first()
        result = {"configured": False, "model": "", "endpoint": ""}
        
        if settings and settings.ai_config:
            config = json.loads(settings.ai_config)
            result = {
                "configured": bool(config.get("api_key")),
                "model": config.get("model", ""),
                "endpoint": config.get("api_endpoint", ""),
            }
        
        if close_db:
            db.close()
        
        return result
    except Exception:
        return {"configured": False, "model": "", "endpoint": ""}
