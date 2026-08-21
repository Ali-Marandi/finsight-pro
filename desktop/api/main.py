from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import sys
from pathlib import Path

# Add the CLI engine to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from finsight.io import load_statement
from finsight.ratios import calculate_ratios, RATIO_LABELS
from finsight.charts import create_dashboard
from finsight.report import create_html_report

app = FastAPI(title="FinSight Pro API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisResponse(BaseModel):
    periods: list[str]
    ratios: list[dict[str, Optional[float]]]
    labels: dict[str, str]
    chart_path: Optional[str] = None
    report_path: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile):
    """Analyze an uploaded financial statement file."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xlsm"}:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use .csv, .xlsx, or .xlsm")

    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = Path(tmp_dir) / file.filename
        content = await file.read()
        with open(input_path, "wb") as f:
            f.write(content)

        try:
            statement = load_statement(str(input_path))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")

        ratios_df = calculate_ratios(statement)

        chart_path = Path(tmp_dir) / "dashboard.png"
        create_dashboard(statement, ratios_df, str(chart_path))

        report_path = Path(tmp_dir) / "report.html"
        create_html_report(ratios_df, str(chart_path), str(report_path))

        periods = ratios_df["period"].tolist()
        ratio_dicts = ratios_df.drop(columns=["period"]).to_dict(orient="records")
        for row in ratio_dicts:
            for k, v in row.items():
                if v is not None:
                    try:
                        row[k] = round(float(v), 6)
                    except (TypeError, ValueError):
                        pass

        return AnalysisResponse(
            periods=periods,
            ratios=ratio_dicts,
            labels=RATIO_LABELS,
            chart_path=str(chart_path),
            report_path=str(report_path),
        )


@app.get("/schema")
async def get_schema():
    """Return the required input data schema."""
    from finsight.io import REQUIRED_COLUMNS
    return {
        "required_columns": sorted(REQUIRED_COLUMNS),
        "categories": {
            "identity": ["period"],
            "income_statement": ["revenue", "gross_profit", "operating_income", "net_income", "cost_of_goods_sold"],
            "balance_sheet": ["total_assets", "current_assets", "inventory", "cash", "accounts_receivable", "total_liabilities", "current_liabilities", "equity"],
            "cash_flow": ["operating_cash_flow", "interest_expense"],
        },
    }


@app.get("/labels")
async def get_labels():
    """Return ratio labels for display."""
    return RATIO_LABELS
