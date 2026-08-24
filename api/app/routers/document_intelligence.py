"""Document Intelligence Router — Endpoints for OCR-based document extraction."""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.document_intelligence import (
    extract_from_pdf, extract_from_image, extract_from_excel,
    extract_from_text, detect_document_type, analyze_extraction_quality,
)

router = APIRouter()


class TextInput(BaseModel):
    text: str


class ExtractResponse(BaseModel):
    financial_data: dict
    extraction_method: str
    confidence: float
    fields_found: int
    raw_text: Optional[str] = None


@router.post("/extract-pdf")
async def extract_pdf(file: UploadFile = File(...), force_ocr: bool = Form(False)):
    """Extract financial data from a PDF file."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    content = await file.read()
    if len(content) < 100:
        raise HTTPException(400, "File too small to be a valid PDF")
    result = extract_from_pdf(content, use_ocr=force_ocr)
    quality = analyze_extraction_quality(result["financial_data"])
    return {**result, "filename": file.filename, "quality": quality}


@router.post("/extract-image")
async def extract_image_endpoint(file: UploadFile = File(...)):
    """Extract financial data from an image (PNG, JPG, etc.)."""
    allowed = {"png", "jpg", "jpeg", "bmp", "tiff", "tif", "webp"}
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported image format: .{ext}. Allowed: {', '.join(allowed)}")
    content = await file.read()
    result = extract_from_image(content)
    quality = analyze_extraction_quality(result["financial_data"])
    return {**result, "filename": file.filename, "quality": quality}


@router.post("/extract-excel")
async def extract_excel_endpoint(file: UploadFile = File(...)):
    """Smart extract financial data from Excel with multi-sheet support."""
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    content = await file.read()
    result = extract_from_excel(content, file.filename)
    quality = analyze_extraction_quality(result["financial_data"])
    return {**result, "filename": file.filename, "quality": quality}


@router.post("/extract-text")
async def extract_text_endpoint(body: TextInput):
    """Extract financial data from pasted/OCR text."""
    if not body.text.strip():
        raise HTTPException(400, "Text is empty")
    financial_data = extract_from_text(body.text)
    doc_type = detect_document_type(body.text)
    quality = analyze_extraction_quality(financial_data)
    return {
        "financial_data": financial_data,
        "extraction_method": "text_parse",
        "confidence": 0.6,
        "fields_found": len(financial_data),
        "document_type": doc_type,
        "quality": quality,
    }


@router.post("/detect-type")
async def detect_type(body: TextInput):
    """Detect the type of financial document from text."""
    doc_type = detect_document_type(body.text)
    return {"document_type": doc_type, "confidence": 0.7}


@router.get("/quality-check")
async def quality_check(financial_data: str):
    """Analyze extraction quality of provided financial data (JSON string)."""
    import json
    try:
        data = json.loads(financial_data)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")
    return analyze_extraction_quality(data)
