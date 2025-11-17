"""
Shared helpers for AWS export date filtering.
"""

from datetime import datetime
from typing import Iterable, List, Optional, Tuple, Dict, Any
from rich.console import Console

console = Console()


def _parse_date_value(value: Any) -> Optional[datetime]:
    """Best-effort parsing of date/datetime values."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        # Try ISO first
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
        # Fall back to common formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


def resolve_date_range(
    filter_by_date: bool,
    start_date: Optional[str],
    end_date: Optional[str],
    audit_period: Optional[str] = None
) -> Tuple[Optional[datetime], Optional[datetime], Optional[str]]:
    """
    Normalize date inputs. Returns (start_dt, end_dt, label).
    """
    if not filter_by_date:
        return None, None, None
    
    if not (start_date and end_date):
        console.print("[yellow]⚠️  Date filtering requested but start/end dates were not provided.[/yellow]")
        return None, None, None
    
    start_dt = _parse_date_value(start_date)
    end_dt = _parse_date_value(end_date)
    if not start_dt or not end_dt:
        console.print("[yellow]⚠️  Unable to parse start/end dates for filtering.[/yellow]")
        return None, None, None
    
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    
    label = audit_period or f"{start_dt.date()} to {end_dt.date()}"
    return start_dt, end_dt, label


def filter_records_by_date(
    records: List[Dict[str, Any]],
    date_field: str,
    start_dt: datetime,
    end_dt: datetime
) -> List[Dict[str, Any]]:
    """
    Filters list of dicts so only records whose `date_field` falls within start/end remain.
    """
    if not records or not date_field or not start_dt or not end_dt:
        return records
    
    filtered = []
    for record in records:
        value = record.get(date_field)
        parsed = _parse_date_value(value)
        if parsed and start_dt <= parsed <= end_dt:
            filtered.append(record)
    console.print(
        f"[cyan]🗂️  Date filter '{date_field}' kept {len(filtered)}/{len(records)} records "
        f"({start_dt.date()} → {end_dt.date()}).[/cyan]"
    )
    return filtered

