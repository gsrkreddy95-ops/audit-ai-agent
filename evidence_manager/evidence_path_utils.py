"""
Utility helpers for determining the local evidence directory.

All evidence should live under ~/Documents/audit-evidence/<FiscalYear>/...
This module centralizes that logic so every integration uses the same path.
"""

import os
from pathlib import Path
from typing import Optional

DEFAULT_BASE_ENV = "LOCAL_EVIDENCE_PATH"
DEFAULT_YEAR_ENV = "SHAREPOINT_CURRENT_YEAR"
DEFAULT_YEAR = "FY2025"


def _get_base_dir() -> Path:
    """Return the root evidence directory (~/Documents/audit-evidence by default)."""
    base_env = os.getenv(DEFAULT_BASE_ENV)
    if base_env:
        base_path = Path(base_env).expanduser()
    else:
        base_path = Path.home() / "Documents" / "audit-evidence"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def get_year_dir() -> Path:
    """Return the fiscal-year evidence directory (creates if needed)."""
    fiscal_year = os.getenv(DEFAULT_YEAR_ENV, DEFAULT_YEAR)
    year_dir = _get_base_dir() / fiscal_year
    year_dir.mkdir(parents=True, exist_ok=True)
    return year_dir


def ensure_evidence_subdir(subdir: Optional[str]) -> Path:
    """
    Return a writable evidence subdirectory under the fiscal year folder.

    Args:
        subdir: Optional folder name (e.g., RFI code). If None, uses 'GENERAL'.
    """
    folder_name = subdir or "GENERAL"
    target_dir = get_year_dir() / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir

