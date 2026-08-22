"""Evidence Review endpoints for pre-analysis financial data validation."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from finsight.evidence import inspect_statement  # noqa: E402

router = APIRouter()
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm"}


@router.post("/inspect")
async def inspect_evidence(
    file: UploadFile = File(...),
    mapping_overrides: str | None = Form(default=None),
):
    """Inspect a statement and return reviewable mappings and evidence-health results.

    Source content exists only in a temporary local file for the duration of the
    request. Suggested aliases remain blocking until the reviewer confirms them.
    """

    source_name = Path(file.filename or "statement.csv").name
    if Path(source_name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Use a CSV, XLSX, or XLSM financial statement.")

    overrides: dict[str, str | None] | None = None
    if mapping_overrides:
        try:
            parsed = json.loads(mapping_overrides)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="mapping_overrides must be valid JSON.") from exc
        if not isinstance(parsed, dict) or not all(value is None or isinstance(value, str) for value in parsed.values()):
            raise HTTPException(
                status_code=422,
                detail="mapping_overrides must map source-column names to a canonical concept or null.",
            )
        overrides = parsed

    with tempfile.TemporaryDirectory(prefix="finsight-evidence-") as temporary_directory:
        source_path = Path(temporary_directory) / source_name
        source_path.write_bytes(await file.read())
        try:
            result = inspect_statement(source_path, mapping_overrides=overrides)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return result.to_dict()
