from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.analyzer import analyze_financial_statement
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/upload")
async def upload_and_analyze(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a CSV/XLSX financial statement and run full analysis."""
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or XLSX.",
            error_code="INVALID_FILE_FORMAT",
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Run analysis
        result = analyze_financial_statement(
            file_content=content,
            filename=file.filename,
            extension=ext,
        )
        
        # Store in database
        from app.models.models import AnalysisModel, RatioResultModel
        
        analysis_id = str(uuid.uuid4())
        analysis = AnalysisModel(
            id=analysis_id,
            company_name=result.get("company_name"),
            period=result.get("period"),
            file_name=file.filename,
        )
        db.add(analysis)
        
        for ratio in result.get("ratios", []):
            ratio_record = RatioResultModel(
                analysis_id=analysis_id,
                category=ratio["category"],
                ratio_name=ratio["ratio_name"],
                value=ratio["value"],
                unit=ratio["unit"],
                benchmark=ratio.get("benchmark"),
                status=ratio["status"],
            )
            db.add(ratio_record)
        
        db.commit()
        db.refresh(analysis)
        
        return {
            "analysis_id": analysis_id,
            "company_name": analysis.company_name,
            "period": analysis.period,
            "file_name": file.filename,
            "created_at": datetime.now().isoformat(),
            "ratios": result.get("ratios", []),
        }
    
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/history")
async def get_history(
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    """Get paginated analysis history."""
    from app.models.models import AnalysisModel, RatioResultModel
    from sqlalchemy import func
    
    offset = (page - 1) * per_page
    analyses = db.query(AnalysisModel).order_by(AnalysisModel.created_at.desc()).offset(offset).limit(per_page).all()
    
    items = []
    for a in analyses:
        ratios = db.query(RatioResultModel).filter(RatioResultModel.analysis_id == a.id).all()
        
        category_scores = {}
        for r in ratios:
            if r.category not in category_scores:
                category_scores[r.category] = []
            category_scores[r.category].append(r.value)
        
        summary = {}
        for cat, values in category_scores.items():
            summary[cat] = sum(values) / len(values) if values else 0
        
        items.append({
            "analysis_id": a.id,
            "company_name": a.company_name,
            "period": a.period,
            "file_name": a.file_name,
            "created_at": a.created_at.isoformat(),
            "summary": summary,
        })
    
    return items


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Get a specific analysis by ID."""
    from app.models.models import AnalysisModel, RatioResultModel
    
    analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    ratios = db.query(RatioResultModel).filter(RatioResultModel.analysis_id == analysis_id).all()
    
    return {
        "analysis_id": analysis.id,
        "company_name": analysis.company_name,
        "period": analysis.period,
        "file_name": analysis.file_name,
        "created_at": analysis.created_at.isoformat(),
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
