"""Validated CSV/XLSX financial statement ingestion."""



from __future__ import annotations



from pathlib import Path



import pandas as pd



REQUIRED_COLUMNS = {
    
    "period",
    
    "revenue",
    
    "gross_profit",
    
    "operating_income",
    
    "net_income",
    
    "total_assets",
    
    "current_assets",
    
    "inventory",
    
    "cash",
    
    "total_liabilities",
    
    "current_liabilities",
    
    "equity",
    
    "operating_cash_flow",
    
    "interest_expense",
    
    "cost_of_goods_sold",
    
    "accounts_receivable",
    
}

NUMERIC_COLUMNS = REQUIRED_COLUMNS - {"period"}





def load_statement(path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    
    """Load and validate a normalized financial statement.
    


    Input columns use snake_case canonical names. Period is retained as text,
    
    while all financial values are coercively parsed as numbers.
    
    """
    


    source = Path(path)
    
    if not source.exists():
        
        raise FileNotFoundError(source)
        
    suffix = source.suffix.lower()
    
    if suffix == ".csv":
        
        frame = pd.read_csv(source)
        
    elif suffix in {".xlsx", ".xlsm"}:
        
        frame = pd.read_excel(source, sheet_name=sheet_name, engine="openpyxl")
        
    else:
        
        raise ValueError("supported formats are .csv, .xlsx and .xlsm")
        


    frame.columns = [str(column).strip().lower() for column in frame.columns]
    
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    
    if missing:
        
        raise ValueError(f"missing required columns: {', '.join(missing)}")
        


    frame = frame.loc[:, sorted(REQUIRED_COLUMNS)].copy()
    
    for column in NUMERIC_COLUMNS:
        
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        
    invalid = frame[list(NUMERIC_COLUMNS)].isna()
    
    if invalid.any().any():
        
        locations = [
            
            f"row {row + 2}, {column}"
            
            for row, column in zip(*invalid.to_numpy().nonzero())
            
        ]
        
        raise ValueError(f"non-numeric or empty financial values: {', '.join(locations[:8])}")
        
    if frame["period"].duplicated().any():
        
        raise ValueError("period values must be unique")
        
    return frame.reset_index(drop=True)
    

















































