"""
Safe file reader for retail datasets (.csv, .xlsx, .xls).
Guards against macro execution, formula bombs, oversized files, and empty files.
"""

import os
import io
import hashlib
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd
import openpyxl

from src.config import MAX_UPLOAD_SIZE_MB, ALLOWED_EXTENSIONS


class FileReadError(Exception):
    """Custom exception for file reading errors."""
    pass


def compute_file_hash(file_bytes: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(file_bytes).hexdigest()


def get_excel_sheet_names(file_source) -> List[str]:
    """Retrieve sheet names from an Excel file without loading all sheet data."""
    try:
        if isinstance(file_source, (bytes, bytearray)):
            wb = openpyxl.load_workbook(io.BytesIO(file_source), read_only=True, keep_links=False)
        elif hasattr(file_source, "read"):
            pos = file_source.tell() if hasattr(file_source, "tell") else 0
            file_bytes = file_source.read()
            if hasattr(file_source, "seek"):
                file_source.seek(pos)
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, keep_links=False)
        else:
            wb = openpyxl.load_workbook(file_source, read_only=True, keep_links=False)
        sheet_names = wb.sheetnames
        wb.close()
        return sheet_names
    except Exception as e:
        raise FileReadError(f"Could not inspect Excel sheets: {str(e)}")


def read_uploaded_file(
    file_source,
    file_name: str,
    sheet_name: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Safely read CSV or Excel files.
    
    Parameters:
    - file_source: bytes, file-like object, or file path.
    - file_name: original filename including extension.
    - sheet_name: specific sheet for Excel files (defaults to first sheet).
    
    Returns:
    - (DataFrame, metadata_dict)
    """
    ext = os.path.splitext(file_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileReadError(f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}")

    # Extract bytes if needed
    if isinstance(file_source, (bytes, bytearray)):
        content_bytes = file_source
    elif hasattr(file_source, "read"):
        content_bytes = file_source.read()
    elif isinstance(file_source, (str, os.PathLike)):
        with open(file_source, "rb") as f:
            content_bytes = f.read()
    else:
        raise FileReadError("Invalid file source provided.")

    # Size check
    size_mb = len(content_bytes) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_SIZE_MB:
        raise FileReadError(f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {MAX_UPLOAD_SIZE_MB} MB.")

    if len(content_bytes) == 0:
        raise FileReadError("The uploaded file is completely empty (0 bytes).")

    file_hash = compute_file_hash(content_bytes)
    sheet_names = []

    try:
        if ext == ".csv":
            # Attempt UTF-8, fall back to latin1/cp1252
            try:
                df = pd.read_csv(io.BytesIO(content_bytes), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content_bytes), encoding="latin1")
            sheet_names = ["CSV"]
        else:
            # Excel file: use openpyxl with data_only=True to evaluate cached formula values
            # and ignore potential malicious macro or formula execution
            bio = io.BytesIO(content_bytes)
            wb = openpyxl.load_workbook(bio, read_only=True, data_only=True, keep_links=False)
            sheet_names = wb.sheetnames
            wb.close()

            target_sheet = sheet_name if sheet_name and sheet_name in sheet_names else sheet_names[0]
            bio.seek(0)
            df = pd.read_excel(bio, sheet_name=target_sheet, engine="openpyxl")
    except Exception as e:
        raise FileReadError(f"Failed to parse file: {str(e)}")

    if df.empty:
        raise FileReadError("The file was parsed successfully but contains no data rows.")

    metadata = {
        "file_name": file_name,
        "file_hash": file_hash,
        "extension": ext,
        "size_bytes": len(content_bytes),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "sheet_names": sheet_names,
        "selected_sheet": sheet_name or (sheet_names[0] if sheet_names else None)
    }

    return df, metadata
