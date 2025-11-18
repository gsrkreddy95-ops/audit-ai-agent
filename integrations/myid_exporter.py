"""
MyID Access Exporter

Allows the agent to pull access provisioning records from MyID (or any compatible
access management API) and store the results under the audit-evidence tree.
"""

import os
import csv
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from rich.console import Console
from evidence_manager.evidence_path_utils import ensure_evidence_subdir

console = Console()


class MyIDExporter:
    """
    Export access records from MyID.

    Requires MYID_API_TOKEN in the environment. Optional overrides:
    - MYID_BASE_URL (default https://myid.cisco.com/api)
    - MYID_DEFAULT_GROUP
    """

    def __init__(self, base_url: Optional[str] = None, api_token: Optional[str] = None):
        from dotenv import load_dotenv
        load_dotenv()

        self.base_url = (base_url or os.getenv("MYID_BASE_URL") or "https://myid.cisco.com/api").rstrip("/")
        self.api_token = api_token or os.getenv("MYID_API_TOKEN")
        self.default_group = os.getenv("MYID_DEFAULT_GROUP")

        if not self.api_token:
            console.print("[yellow]⚠️  MYID_API_TOKEN not set. MyID exporter will be disabled.[/yellow]")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_token)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json"
        }

    def _get(self, path: str, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        url = f"{self.base_url}{path}"
        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "items" in data:
                return data["items"]
            if isinstance(data, list):
                return data
            console.print(f"[yellow]⚠️  Unexpected MyID response format: {type(data)}[/yellow]")
            return []
        except Exception as error:
            console.print(f"[red]❌ MyID API request failed: {error}[/red]")
            return None

    def export_access_records(
        self,
        environment: Optional[str] = None,
        groups: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        include_fields: Optional[List[str]] = None,
        output_format: str = "csv",
        rfi_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export access records from MyID.

        Args:
            environment: Filter by environment (e.g., 'non-prod', 'prod')
            groups: List of MyID group names
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            include_fields: Additional fields to include
            output_format: 'csv' or 'json'
            rfi_code: Optional folder name under audit evidence
        """
        if not self.is_configured:
            return {"success": False, "error": "MYID_API_TOKEN not configured"}

        params: Dict[str, Any] = {}
        if environment:
            params["environment"] = environment
        if groups:
            params["groups"] = ",".join(groups)
        elif self.default_group:
            params["groups"] = self.default_group
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if include_fields:
            params["fields"] = ",".join(include_fields)

        console.print("[cyan]🔐 Querying MyID access records...[/cyan]")
        records = self._get("/v1/access-records", params=params)
        if records is None:
            return {"success": False, "error": "MyID API request failed"}

        console.print(f"[green]✅ Retrieved {len(records)} records from MyID[/green]")

        target_dir = ensure_evidence_subdir(rfi_code or "MYID-EXPORTS")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"myid_access_{timestamp}.{output_format}"
        output_path = target_dir / output_name

        try:
            if output_format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=2, ensure_ascii=False)
            elif output_format == "csv":
                if not records:
                    console.print("[yellow]⚠️  No records to export[/yellow]")
                with open(output_path, "w", newline="", encoding="utf-8") as f:
                    if records:
                        fieldnames = list(records[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in records:
                            writer.writerow(row)
            else:
                return {"success": False, "error": f"Unsupported format: {output_format}"}
        except Exception as error:
            console.print(f"[red]❌ Failed to save MyID export: {error}[/red]")
            return {"success": False, "error": str(error)}

        console.print(f"[green]📁 MyID export saved to {output_path}[/green]")
        return {
            "success": True,
            "count": len(records),
            "export_path": str(output_path),
            "environment": environment,
            "groups": groups or ([self.default_group] if self.default_group else []),
        }

