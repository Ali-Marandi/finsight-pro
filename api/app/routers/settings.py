from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import PreferencesSchema
import json
from datetime import datetime

router = APIRouter()


@router.get("/preferences")
async def get_preferences(db: Session = Depends(get_db)):
    """Get user preferences."""
    from app.models.models import SettingsModel
    
    settings = db.query(SettingsModel).all()
    prefs = {}
    for s in settings:
        try:
            prefs[s.key] = json.loads(s.value)
        except (json.JSONDecodeError, TypeError):
            prefs[s.key] = s.value
    
    return PreferencesSchema(
        default_language=prefs.get("default_language", "en"),
        chart_theme=prefs.get("chart_theme", "light"),
        decimal_places=prefs.get("decimal_places", 2),
        auto_save=prefs.get("auto_save", True),
    )


@router.put("/preferences")
async def update_preferences(
    prefs: PreferencesSchema,
    db: Session = Depends(get_db),
):
    """Update user preferences."""
    from app.models.models import SettingsModel
    
    data = prefs.model_dump()
    
    for key, value in data.items():
        existing = db.query(SettingsModel).filter(SettingsModel.key == key).first()
        if existing:
            existing.value = json.dumps(value)
            existing.updated_at = datetime.now()
        else:
            db.add(SettingsModel(key=key, value=json.dumps(value)))
    
    db.commit()
    return prefs
