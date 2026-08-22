"""
Document Intelligence Service — OCR-based financial document extraction.
Supports PDF (native + scanned), Excel, CSV, and image-based statements.
Extracts financial data using a combination of pdfplumber, pytesseract, and regex parsing.
"""

import re
import io
import pandas as pd
from typing import Optional
from PIL import Image


# Persian number mapping
PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'
DIGIT_MAP = {**{ord(c): str(i) for i, c in enumerate(PERSIAN_DIGITS)},
             **{ord(c): str(i) for i, c in enumerate(ARABIC_DIGITS)}}

# Persian/English financial term mappings
FINANCIAL_TERMS_FA = {
    'درآمد': 'revenue', 'فروش': 'revenue', 'درآمد عملیاتی': 'revenue',
    'بهای تمام شده': 'cogs', 'هزینه خرید': 'cogs', 'هزینه تولید': 'cogs',
    'سود ناخالص': 'gross_profit', 'سود عملیاتی': 'ebit',
    'سود خالص': 'net_income', 'سود پس از مالیات': 'net_income',
    'هزینه بهره': 'interest_expense', 'بهره': 'interest_expense',
    'مالیات': 'tax_expense', 'هزینه مالیاتی': 'tax_expense',
    'جمع دارایی': 'total_assets', 'دارایی کل': 'total_assets', 'دارایی‌ها': 'total_assets',
    'جمع حقوق صاحبان سهام': 'total_equity', 'حقوق صاحبان سهام': 'total_equity',
    'سرمایه': 'total_equity', 'ذخیره': 'retained_earnings',
    'جمع بدهی': 'total_liabilities', 'بدهی کل': 'total_liabilities', 'بدهی‌ها': 'total_liabilities',
    'دارایی جاری': 'current_assets', 'دارایی‌های جاری': 'current_assets',
    'بدهی جاری': 'current_liabilities', 'بدهی‌های جاری': 'current_liabilities',
    'موجودی کالا': 'inventory', 'انبار': 'inventory', 'موجودی': 'inventory',
    'نقد و بانک': 'cash', 'وجه نقد': 'cash', 'پول نقد': 'cash',
    'حساب‌های دریافتنی': 'accounts_receivable', 'طلبکاری': 'accounts_receivable',
    'فروش خالص': 'revenue', 'هزینه‌های عملیاتی': 'operating_expenses',
    'دارایی ثابت': 'fixed_assets', 'اموال و ماشین‌آلات': 'fixed_assets',
    'بدهی بلندمدت': 'long_term_debt', 'وام': 'long_term_debt',
    'جمع دارایی ثابت': 'net_fixed_assets', 'استهلاک': 'depreciation',
    'سود قبل از مالیات': 'ebt', 'سود قبل از بهره و مالیات': 'ebit',
    'درآمد سایر': 'other_income', 'هزینه‌های اداری': 'admin_expenses',
    'هزینه‌های فروش': 'selling_expenses',
}

FINANCIAL_TERMS_EN = {
    'revenue': 'revenue', 'net revenue': 'revenue', 'sales': 'revenue', 'net sales': 'revenue',
    'total revenue': 'revenue', 'cost of goods sold': 'cogs', 'cogs': 'cogs',
    'cost of revenue': 'cogs', 'gross profit': 'gross_profit',
    'operating income': 'ebit', 'operating profit': 'ebit', 'ebit': 'ebit',
    'net income': 'net_income', 'net profit': 'net_income', 'net earnings': 'net_income',
    'interest expense': 'interest_expense', 'interest': 'interest_expense',
    'tax expense': 'tax_expense', 'income tax': 'tax_expense',
    'total assets': 'total_assets', 'assets': 'total_assets',
    'total equity': 'total_equity', 'shareholders equity': 'total_equity',
    'stockholders equity': 'total_equity', 'total liabilities': 'total_liabilities',
    'current assets': 'current_assets', 'current liabilities': 'current_liabilities',
    'inventory': 'inventory', 'inventories': 'inventory',
    'cash': 'cash', 'cash and equivalents': 'cash', 'cash & equivalents': 'cash',
    'accounts receivable': 'accounts_receivable', 'receivables': 'accounts_receivable',
    'retained earnings': 'retained_earnings', 'depreciation': 'depreciation',
    'fixed assets': 'fixed_assets', 'long term debt': 'long_term_debt',
    'working capital': 'working_capital', 'ebt': 'ebt',
}


def _normalize_persian_numbers(text: str) -> str:
    """Convert Persian and Arabic digits to Latin digits."""
    return text.translate(DIGIT_MAP)


def _extract_number(text: str) -> Optional[float]:
    """Extract a number from text, handling commas, parentheses (negative), and Persian digits."""
    text = _normalize_persian_numbers(text.strip())
    # Remove common currency/unit suffixes
    text = re.sub(r'(ریال|تومان|IR|Rial|Toman|USD|\$|€)', '', text, flags=re.IGNORECASE).strip()
    # Handle parentheses for negative numbers
    if re.match(r'^\([\d,.]+\)$', text):
        text = '-' + text.strip('()')
    # Remove commas and spaces within numbers
    text = re.sub(r'[\s,]', '', text)
    # Extract first number
    match = re.search(r'-?[\d]+(?:\.\d+)?', text)
    return float(match.group()) if match else None


def _parse_line_items(text: str) -> dict:
    """Parse key-value pairs from OCR text lines."""
    results = {}
    lines = text.split('\n')
    
    all_terms = {**FINANCIAL_TERMS_FA, **FINANCIAL_TERMS_EN}
    
    for line in lines:
        line_stripped = _normalize_persian_numbers(line.strip())
        if not line_stripped:
            continue
        
        for term, key in all_terms.items():
            # Check if the line contains this financial term
            normalized_term = _normalize_persian_numbers(term)
            if normalized_term.lower() in line_stripped.lower():
                # Try to extract the number from the line
                # Strategy: find the last number on the line (usually the value)
                numbers = re.findall(r'-?[\d,]+(?:\.\d+)?', line_stripped)
                if numbers:
                    value_str = numbers[-1].replace(',', '')
                    try:
                        value = float(value_str)
                        if key not in results:  # First match wins
                            results[key] = value
                    except ValueError:
                        pass
                break
    
    return results


def extract_from_text(text: str) -> dict:
    """Extract financial data from raw text (OCR output or pasted text)."""
    data = _parse_line_items(text)
    
    # Apply basic validation and derived calculations
    if 'gross_profit' not in data and 'revenue' in data and 'cogs' in data:
        data['gross_profit'] = data['revenue'] - data['cogs']
    if 'total_liabilities' not in data and 'total_assets' in data and 'total_equity' in data:
        data['total_liabilities'] = data['total_assets'] - data['total_equity']
    if 'ebit' not in data and 'net_income' in data and 'tax_expense' in data and 'interest_expense' in data:
        data['ebit'] = data['net_income'] + data['tax_expense'] + data['interest_expense']
    
    return data


def extract_from_pdf(file_content: bytes, use_ocr: bool = False) -> dict:
    """Extract financial data from PDF.
    
    Args:
        file_content: Raw PDF bytes
        use_ocr: Force OCR mode (for scanned PDFs)
    
    Returns:
        dict with 'financial_data', 'extraction_method', 'confidence', 'raw_text'
    """
    import pdfplumber
    
    pdf_file = io.BytesIO(file_content)
    
    # Try native PDF text extraction first
    financial_data = {}
    raw_text = ''
    extraction_method = 'native'
    confidence = 0.9
    
    if not use_ocr:
        try:
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ''
                    raw_text += text + '\n'
                    
                    # Try table extraction
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if row:
                                row_text = ' | '.join(str(cell or '') for cell in row)
                                raw_text += row_text + '\n'
                    
                    financial_data.update(_parse_line_items(text))
        except Exception:
            pass
    
    # If native extraction yielded little data, try OCR
    if len(financial_data) < 3 or use_ocr:
        try:
            ocr_data, ocr_text = _ocr_extract(file_content)
            if len(ocr_data) > len(financial_data):
                financial_data = ocr_data
                raw_text = ocr_text
                extraction_method = 'ocr'
                confidence = 0.7
        except Exception:
            if not financial_data:
                extraction_method = 'failed'
                confidence = 0.0
    
    return {
        'financial_data': financial_data,
        'extraction_method': extraction_method,
        'confidence': confidence,
        'fields_found': len(financial_data),
        'raw_text': raw_text[:5000],  # Limit raw text
    }


def _ocr_extract(file_content: bytes) -> tuple[dict, str]:
    """OCR extraction from PDF pages."""
    import pytesseract
    from pdf2image import convert_from_bytes
    
    images = convert_from_bytes(file_content, dpi=300)
    all_text = ''
    
    for img in images:
        # Persian + English OCR
        text = pytesseract.image_to_string(
            img,
            lang='eng+fas',
            config='--psm 6'
        )
        all_text += text + '\n'
    
    financial_data = _parse_line_items(all_text)
    return financial_data, all_text


def extract_from_image(file_content: bytes) -> dict:
    """Extract financial data from an image file (PNG, JPG, etc.)."""
    import pytesseract
    
    img = Image.open(io.BytesIO(file_content))
    
    # Try Persian + English
    text = pytesseract.image_to_string(img, lang='eng+fas', config='--psm 6')
    
    financial_data = _parse_line_items(text)
    
    return {
        'financial_data': financial_data,
        'extraction_method': 'ocr',
        'confidence': 0.65,
        'fields_found': len(financial_data),
        'raw_text': text[:5000],
    }


def extract_from_excel(file_content: bytes, filename: str) -> dict:
    """Smart extraction from Excel with multi-sheet support and header detection."""
    financial_data = {}
    raw_text = ''
    
    try:
        xls = pd.ExcelFile(io.BytesIO(file_content))
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            raw_text += f"--- Sheet: {sheet_name} ---\n"
            
            for _, row in df.iterrows():
                row_text = ' | '.join(str(v) for v in row if pd.notna(v))
                raw_text += row_text + '\n'
                financial_data.update(_parse_line_items(row_text))
    except Exception:
        pass
    
    # Derived calculations
    if 'gross_profit' not in financial_data and 'revenue' in financial_data and 'cogs' in financial_data:
        financial_data['gross_profit'] = financial_data['revenue'] - financial_data['cogs']
    if 'total_liabilities' not in financial_data and 'total_assets' in financial_data and 'total_equity' in financial_data:
        financial_data['total_liabilities'] = financial_data['total_assets'] - financial_data['total_equity']
    
    return {
        'financial_data': financial_data,
        'extraction_method': 'structured',
        'confidence': 0.95,
        'fields_found': len(financial_data),
        'raw_text': raw_text[:5000],
    }


def detect_document_type(text: str) -> str:
    """Detect the type of financial document from extracted text."""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ['balance sheet', 'ترازنامه', 'position statement']):
        return 'balance_sheet'
    if any(w in text_lower for w in ['income statement', 'صورت سود و زیان', 'profit and loss']):
        return 'income_statement'
    if any(w in text_lower for w in ['cash flow', 'جریان نقد', 'cashflow']):
        return 'cash_flow'
    if any(w in text_lower for w in ['stockholders', 'equity', 'حقوق صاحبان']):
        return 'equity_statement'
    
    return 'mixed'


def analyze_extraction_quality(financial_data: dict) -> dict:
    """Analyze the quality of extracted data and suggest improvements."""
    critical_fields = ['revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity']
    found = [f for f in critical_fields if f in financial_data]
    missing = [f for f in critical_fields if f not in financial_data]
    
    completeness = len(found) / len(critical_fields)
    
    # Check for reasonable ranges
    warnings = []
    for key, value in financial_data.items():
        if key in ('revenue', 'total_assets', 'total_liabilities', 'total_equity'):
            if value < 0:
                warnings.append(f"{key} is negative ({value}), please verify")
            elif value == 0:
                warnings.append(f"{key} is zero, may indicate extraction error")
        if key == 'net_income' and abs(value) > (financial_data.get('revenue', 0) * 2):
            warnings.append("net_income exceeds 2x revenue, please verify")
    
    # Balance sheet check
    if all(k in financial_data for k in ['total_assets', 'total_liabilities', 'total_equity']):
        expected = financial_data['total_liabilities'] + financial_data['total_equity']
        actual = financial_data['total_assets']
        diff_pct = abs(expected - actual) / max(abs(expected), 1) * 100
        if diff_pct > 5:
            warnings.append(f"Balance sheet doesn't balance: Assets={actual}, L+E={expected} ({diff_pct:.1f}% diff)")
    
    return {
        'completeness': round(completeness, 2),
        'fields_found': len(financial_data),
        'critical_found': len(found),
        'critical_missing': missing,
        'warnings': warnings,
        'quality_score': round(completeness * 100 - len(warnings) * 10, 1),
    }
