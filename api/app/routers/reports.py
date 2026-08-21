from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.schemas import ReportGenerateRequest
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate a report in the specified format."""
    from app.models.models import AnalysisModel, RatioResultModel, ReportModel
    from app.services.report_generator import create_report
    
    # Verify analysis exists
    analysis = db.query(AnalysisModel).filter(
        AnalysisModel.id == request.analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    ratios = db.query(RatioResultModel).filter(
        RatioResultModel.analysis_id == request.analysis_id
    ).all()
    
    if not ratios:
        raise HTTPException(status_code=404, detail="No ratio data found for this analysis")
    
    ratio_data = [
        {
            "category": r.category,
            "ratio_name": r.ratio_name,
            "value": r.value,
            "unit": r.unit,
            "benchmark": r.benchmark,
            "status": r.status,
        }
        for r in ratios
    ]
    
    try:
        file_path = create_report(
            analysis_id=request.analysis_id,
            company_name=analysis.company_name or "Untitled",
            period=analysis.period or "N/A",
            ratios=ratio_data,
            template=request.template,
            language=request.language,
            include_charts=request.include_charts,
        )
        
        # Record the report
        import os
        report = ReportModel(
            analysis_id=request.analysis_id,
            format="pdf",
            file_path=file_path,
            size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        )
        db.add(report)
        db.commit()
        
        return {"file_path": file_path, "format": "pdf"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.post("/export/xlsx")
async def export_xlsx(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
):
    """Export analysis results to Excel."""
    from app.models.models import AnalysisModel, RatioResultModel
    
    analysis = db.query(AnalysisModel).filter(
        AnalysisModel.id == request.analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    ratios = db.query(RatioResultModel).filter(
        RatioResultModel.analysis_id == request.analysis_id
    ).all()
    
    try:
        import pandas as pd
        import os
        
        data = [
            {
                "Category": r.category,
                "Ratio": r.ratio_name.replace("_", " ").title(),
                "Value": r.value,
                "Unit": r.unit,
                "Benchmark": r.benchmark if r.benchmark else "N/A",
                "Status": r.status,
            }
            for r in ratios
        ]
        
        df = pd.DataFrame(data)
        output_dir = os.path.join(os.path.expanduser("~"), ".finsight-pro", "exports")
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"analysis_{request.analysis_id[:8]}.xlsx")
        df.to_excel(file_path, index=False, sheet_name="Financial Ratios")
        
        return {"file_path": file_path, "format": "xlsx"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")
