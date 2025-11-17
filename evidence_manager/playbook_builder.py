"""
Playbook Builder
Transforms analyzed SharePoint evidence into replayable tasks.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from evidence_manager.playbook_schema import Playbook, PlaybookTask


class EvidencePlaybookBuilder:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir or Path.cwd() / "evidence_playbooks")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build_playbook(
        self,
        fiscal_year: str,
        rfi_code: str,
        evidence_entries: List[Dict[str, any]],
        source_urls: List[str],
        notes: Optional[str] = None
    ) -> Playbook:
        tasks = []
        for entry in evidence_entries:
            task = self._build_task_from_entry(rfi_code, entry)
            if task:
                tasks.append(task)

        playbook = Playbook(
            fiscal_year=fiscal_year,
            rfi=rfi_code,
            tasks=tasks,
            source_urls=source_urls,
            notes=notes
        )
        self._write_playbook(playbook)
        return playbook

    def _build_task_from_entry(self, rfi_code: str, entry: Dict[str, any]) -> Optional[PlaybookTask]:
        extracted = entry.get("analysis", {})
        metadata = extracted.get("metadata", {})
        action = metadata.get("action") or extracted.get("suggested_action", "aws_console_action")
        service = metadata.get("service") or extracted.get("service", "unknown")
        evidence_type = metadata.get("evidence_type") or extracted.get("evidence_type", "screenshot")
        account = metadata.get("account") or entry.get("account", "unknown")
        region = metadata.get("region") or entry.get("region", "us-east-1")
        resource_name = metadata.get("resource_name") or extracted.get("resource_identifier", "")

        params = {
            "service": service,
            "aws_account": account,
            "aws_region": region,
            "rfi_code": rfi_code
        }
        params.update(metadata.get("params", {}))
        if resource_name and "resource_name" not in params:
            params["resource_name"] = resource_name

        date_filters = metadata.get("date_filters") or entry.get("date_filters") or {}

        return PlaybookTask(
            rfi=rfi_code,
            title=metadata.get("title") or entry.get("file_name", "Evidence Task"),
            service=service,
            account=account,
            region=region,
            evidence_type=evidence_type,
            tool=action,
            params=params,
            source_reference={
                "sharepoint_path": entry.get("sharepoint_path"),
                "local_path": entry.get("local_path")
            },
            metadata={
                "original_file": entry.get("file_name"),
                "summary": extracted.get("summary"),
                "instructions": extracted.get("instructions")
            },
            date_filters=date_filters
        )

    def _write_playbook(self, playbook: Playbook) -> Path:
        fy_dir = self.output_dir / playbook.fiscal_year / playbook.rfi
        fy_dir.mkdir(parents=True, exist_ok=True)
        path = fy_dir / "playbook.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(asdict(playbook), handle, indent=2)
        return path

    def load_playbook(self, fiscal_year: str, rfi_code: str) -> Optional[Playbook]:
        path = self.get_playbook_path(fiscal_year, rfi_code)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return Playbook.from_dict(data)

    def get_playbook_path(self, fiscal_year: str, rfi_code: str) -> Path:
        return self.output_dir / fiscal_year / rfi_code / "playbook.json"

