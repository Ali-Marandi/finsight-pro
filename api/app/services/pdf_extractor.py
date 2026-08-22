"""
PDF Financial Statement Extractor.
Extracts tabular data from PDF financial statements using multiple strategies:
1. pdfplumber for text-based PDFs (most common)
2. Table detection with heuristic column mapping
3. Fallback to raw text extraction

This service enables users to upload PDF balance sheets and income statements
directly, without manual data entry.
"""

import io
import re
from typing import Optional


def extract_tables_from_pdf(pdf_bytes: bytes) -> list[list[str]]:
    """
    Extract all tables from a PDF file.
    Returns a list of tables, where each table is a list of rows,
    and each row is a list of cell strings.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for PDF extraction. "
            "Install it with: pip install pdfplumber"
        )
    
    all_tables = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Clean table data
                cleaned = []
                for row in table:
                    cleaned_row = []
                    for cell in row:
                        if cell is None:
                            cleaned_row.append('')
                        else:
                            # Strip whitespace and normalize
                            cleaned_row.append(str(cell).strip())
                    # Skip empty rows
                    if any(cell for cell in cleaned_row):
                        cleaned.append(cleaned_row)
                if cleaned:
                    all_tables.append(cleaned)
    
    return all_tables


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract raw text from a PDF file.
    Used as fallback when table extraction fails.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required for PDF extraction.")
    
    text_parts = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    
    return '\n'.join(text_parts)


# Mapping of common financial terms to our standard field names
FIELD_ALIASES = {
    'revenue': ['revenue', 'sales', 'net sales', 'total revenue', 'net revenue', 'turnover',
               'فروش', 'درآمد', 'فروش خالص', 'درآمد عملیاتی'],
    'cost_of_goods_sold': ['cost of goods sold', 'cogs', 'cost of revenue', 'cost of sales',
                         'بهای تمام شده', 'هزینه فروش', 'بهای تمام شده کالا'],
    'gross_profit': ['gross profit', 'gross margin', 'gross income',
                    'سود ناخالص', 'سود ناخالص عملیاتی'],
    'operating_income': ['operating income', 'operating profit', 'ebit', 'income from operations',
                       'سود عملیاتی', 'درآمد عملیاتی'],
    'net_income': ['net income', 'net profit', 'net earnings', 'profit after tax', 'bottom line',
                 'سود خالص', 'سود پس از مالیات', 'سود ویژه سهامداران'],
    'total_assets': ['total assets', 'assets', 'total current and non-current assets',
                 'جمع دارایی‌ها', 'دارایی کل', 'جمع دارایی'],
    'current_assets': ['current assets', 'total current assets',
                    'دارایی جاری', 'دارایی‌های جاری', 'جمع دارایی جاری'],
    'cash': ['cash', 'cash and cash equivalents', 'cash & equivalents',
           'وجه نقد', 'نقد و معادل نقد', 'موجودی نقد'],
    'accounts_receivable': ['accounts receivable', 'receivables', 'trade receivables',
                        'حساب‌های دریافتنی', 'اسناد دریافتنی', 'طلبکاران'],
    'inventory': ['inventory', 'inventories', 'stock',
               'موجودی کالا', 'موجودی‌ها', 'ذخایر'],
    'total_liabilities': ['total liabilities', 'liabilities', 'total current and non-current liabilities',
                      'جمع بدهی‌ها', 'بدهی کل', 'جمع بدهی'],
    'current_liabilities': ['current liabilities', 'total current liabilities',
                        'بدهی جاری', 'بدهی‌های جاری', 'جمع بدهی جاری'],
    'total_equity': ['total equity', 'shareholders equity', 'stockholders equity', 'owners equity',
                 'total shareholders\' equity', 'net assets',
                 'حقوق صاحبان سهام', 'سرمایه سهامداران', 'جمع حقوق صاحبان سهام'],
    'interest_expense': ['interest expense', 'interest paid', 'interest and finance costs',
                     'هزینه بهره', 'بهره پرداختی', 'هزینه مالی'],
    'tax_expense': ['income tax expense', 'tax expense', 'provision for tax',
                'مالیات بر درآمد', 'هزینه مالیات', 'مالیات'],
    'retained_earnings': ['retained earnings', 'accumulated earnings', 'retained profit',
                      'سود انباشته', 'سود لحظه ای'],
    'ebit': ['ebit', 'operating income', 'operating profit', 'earnings before interest and taxes'],
}


def _parse_number(text: str) -> Optional[float]:
    """
    Parse a financial number from text.
    Handles: 1,234.56 | 1234.56 | (1,234.56) | -1,234.56 | 1.23M | 1.23B
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Handle parentheses as negative (accounting format)
    if text.startswith('(') and text.endswith(')'):
        text = '-' + text[1:-1]
    
    # Remove currency symbols and whitespace
    text = re.sub(r'[$€£¥\u0631\u062a\u0627\u0644\u0627\u0633]\s*', '', text)
    text = re.sub(r'\s+', '', text)
    
    # Handle millions/billions
    multipliers = {'M': 1_000_000, 'B': 1_000_000_000, 'K': 1_000,
                   'm': 1_000_000, 'b': 1_000_000_000, 'k': 1_000}
    multiplier = 1.0
    for suffix, mult in multipliers.items():
        if text.upper().endswith(suffix):
            multiplier = mult
            text = text[:-1]
            break
    
    # Remove commas
    text = text.replace(',', '')
    
    # Try to parse
    try:
        value = float(text) * multiplier
        return value
    except ValueError:
        return None


def _match_field(label: str) -> Optional[str]:
    """
    Match a table header/label to a standard field name.
    Returns the standard field name or None.
    """
    label_lower = label.strip().lower()
    
    for field_name, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in label_lower or label_lower in alias:
                return field_name
    
    return None


def extract_financial_data_from_pdf(pdf_bytes: bytes) -> dict:
    """
    Main extraction function.
    Extracts financial figures from a PDF and returns a structured dict
    compatible with the analyzer service.
    
    Returns:
        dict with extracted financial figures, or raises ValueError if extraction fails.
    """
    # Strategy 1: Extract tables
    tables = extract_tables_from_pdf(pdf_bytes)
    
    extracted = {}
    
    if tables:
        # Process each table to find financial figures
        for table in tables:
            if len(table) < 2:
                continue
            
            # Try to identify if this is a key-value table or a matrix table
            for row_idx, row in enumerate(table):
                for col_idx, cell in enumerate(row):
                    field = _match_field(cell)
                    if field:
                        # Look for the value in the same row (next column) or next row
                        value = None
                        
                        # Try same row, next columns
                        for next_col in range(col_idx + 1, len(row)):
                            v = _parse_number(row[next_col])
                            if v is not None:
                                value = v
                                break
                        
                        # Try next row, same or next column
                        if value is None and row_idx + 1 < len(table):
                            next_row = table[row_idx + 1]
                            for next_col in range(col_idx, len(next_row)):
                                v = _parse_number(next_row[next_col])
                                if v is not None:
                                    value = v
                                    break
                        
                        if value is not None and field not in extracted:
                            extracted[field] = value
    
    # Strategy 2: If table extraction didn't find enough, try text extraction
    if len(extracted) < 5:
        text = extract_text_from_pdf(pdf_bytes)
        
        # Find "label: value" or "label  value" patterns
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Try various patterns
            patterns = [
                r'^([A-Za-z\s]+?)\s*[:\-=]\s*([\(\)\-\$\d,\.]+)',
                r'^([A-Za-z][A-Za-z\s]+?)\s{2,}([\(\)\-\$\d,\.]+)',
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    label = match.group(1).strip()
                    value_str = match.group(2).strip()
                    field = _match_field(label)
                    if field and field not in extracted:
                        value = _parse_number(value_str)
                        if value is not None:
                            extracted[field] = value
    
    if len(extracted) < 3:
        raise ValueError(
            f"Could not extract enough financial data from PDF. "
            f"Found {len(extracted)} fields: {list(extracted.keys())}. "
            f"Please ensure the PDF contains a financial statement with recognizable labels."
        )
    
    # Normalize extracted data to match analyzer expectations
    result = {
        'revenue': extracted.get('revenue', 0),
        'cogs': extracted.get('cost_of_goods_sold', 0),
        'gross_profit': extracted.get('gross_profit', 0),
        'net_income': extracted.get('net_income', 0),
        'ebit': extracted.get('ebit', extracted.get('operating_income', 0)),
        'interest_expense': extracted.get('interest_expense', 0),
        'tax_expense': extracted.get('tax_expense', 0),
        'total_assets': extracted.get('total_assets', 0),
        'current_assets': extracted.get('current_assets', 0),
        'cash': extracted.get('cash', 0),
        'accounts_receivable': extracted.get('accounts_receivable', 0),
        'inventory': extracted.get('inventory', 0),
        'total_liabilities': extracted.get('total_liabilities', 0),
        'current_liabilities': extracted.get('current_liabilities', 0),
        'total_equity': extracted.get('total_equity', 0),
        'retained_earnings': extracted.get('retained_earnings', None),
    }
    
    # Compute derived values
    if result['gross_profit'] == 0 and result['revenue'] > 0 and result['cogs'] > 0:
        result['gross_profit'] = result['revenue'] - result['cogs']
    
    if result['total_liabilities'] == 0 and result['total_assets'] > 0 and result['total_equity'] > 0:
        result['total_liabilities'] = result['total_assets'] - result['total_equity']
    
    return {
        'extracted_fields': list(extracted.keys()),
        'field_count': len(extracted),
        'financial_data': result,
    }
