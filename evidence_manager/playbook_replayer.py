"""
Evidence Playbook Replayer
Executes stored playbooks to re-collect audit evidence and produces reports.
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from evidence_manager.playbook_builder import EvidencePlaybookBuilder
from evidence_manager.playbook_schema import Playbook, PlaybookTask


class EvidencePlaybookReplayer:
    def __init__(
        self,
        tool_executor,
        builder: Optional[EvidencePlaybookBuilder] = None,
        report_dir: Optional[Path] = None
    ) -> None:
        self.tool_executor = tool_executor
        self.builder = builder or EvidencePlaybookBuilder()
        self.report_dir = Path(report_dir or (self.builder.output_dir.parent / "playbook_reports"))
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def replay(
        self,
        fiscal_year: str,
        rfi_code: str,
        user_request: str,
        overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        playbook = self.builder.load_playbook(fiscal_year, rfi_code)
        if not playbook:
            return {
                "status": "error",
                "error": f"No playbook found for FY {fiscal_year} / RFI {rfi_code}"
            }

        if hasattr(self.tool_executor, "set_current_request"):
            self.tool_executor.set_current_request(user_request)

        results = []
        overrides = overrides or {}

        for task in playbook.tasks:
            params = self._prepare_params(task, overrides)
            result = self.tool_executor.execute_tool(task.tool, params)
            results.append(self._build_task_result(task, result))

        summary = self._build_summary(playbook, results)
        report_path = self._write_report(playbook, summary)

        return {
            "status": "success",
            "result": {
                "playbook": {
                    "fiscal_year": playbook.fiscal_year,
                    "rfi": playbook.rfi,
                    "task_count": len(playbook.tasks)
                },
                "summary": summary,
                "report_path": str(report_path)
            }
        }

    def _prepare_params(self, task: PlaybookTask, overrides: Dict[str, str]) -> Dict[str, str]:
        params = dict(task.params)
        if overrides.get("aws_account"):
            params["aws_account"] = overrides["aws_account"]
        if overrides.get("aws_region"):
            params["aws_region"] = overrides["aws_region"]
        if overrides.get("audit_period"):
            params["audit_period"] = overrides["audit_period"]
            params.setdefault("filter_by_date", True)
        if overrides.get("filter_by_date"):
            params.setdefault("filter_by_date", True)
        if overrides.get("start_date") and overrides.get("end_date"):
            params["start_date"] = overrides["start_date"]
            params["end_date"] = overrides["end_date"]
            params.setdefault("filter_by_date", True)
        if overrides.get("date_field"):
            params["date_field"] = overrides["date_field"]
        if task.metadata.get("date_field"):
            params.setdefault("date_field", task.metadata["date_field"])
        if task.date_filters:
            if task.date_filters.get("start_date") and task.date_filters.get("end_date"):
                params.setdefault("start_date", task.date_filters["start_date"])
                params.setdefault("end_date", task.date_filters["end_date"])
                params.setdefault("filter_by_date", True)
            if task.date_filters.get("audit_period"):
                params.setdefault("audit_period", task.date_filters["audit_period"])
                params.setdefault("filter_by_date", True)
            if task.date_filters.get("date_field"):
                params.setdefault("date_field", task.date_filters["date_field"])
        return params

    def _build_task_result(self, task: PlaybookTask, tool_result: Dict[str, any]) -> Dict[str, any]:
        status = tool_result.get("status", "unknown")
        result_payload = tool_result.get("result")
        evidence_path = ""
        if isinstance(result_payload, dict):
            evidence_path = result_payload.get("output_path") or result_payload.get("export_path", "")
        return {
            "task": task.title,
            "tool": task.tool,
            "service": task.service,
            "account": task.account,
            "region": task.region,
            "status": status,
            "evidence_path": evidence_path,
            "raw_result": result_payload,
            "error": tool_result.get("error")
        }

    def _build_summary(self, playbook: Playbook, results: List[Dict[str, any]]) -> Dict[str, any]:
        counts = {"success": 0, "error": 0, "other": 0}
        for result in results:
            status = result["status"]
            if status == "success":
                counts["success"] += 1
            elif status == "error":
                counts["error"] += 1
            else:
                counts["other"] += 1

        previous_report = self._load_previous_report(playbook)
        changes = self._calculate_delta(previous_report, results) if previous_report else []

        return {
            "generated_at": datetime.now().isoformat(),
            "task_totals": counts,
            "results": results,
            "changes_since_last_run": changes,
            "previous_report": previous_report
        }

    def _calculate_delta(
        self,
        previous_report: Dict[str, any],
        current_results: List[Dict[str, any]]
    ) -> List[Dict[str, str]]:
        delta = []
        previous_map = {entry["task"]: entry for entry in previous_report.get("results", [])}
        for result in current_results:
            previous_entry = previous_map.get(result["task"])
            if not previous_entry:
                delta.append({
                    "task": result["task"],
                    "change": "new_task_or_renamed"
                })
                continue
            if previous_entry.get("status") != result["status"]:
                delta.append({
                    "task": result["task"],
                    "change": f"status changed ({previous_entry.get('status')} -> {result['status']})"
                })
            elif previous_entry.get("evidence_path") != result.get("evidence_path"):
                delta.append({
                    "task": result["task"],
                    "change": "evidence_path_changed"
                })
        return delta

    def _write_report(self, playbook: Playbook, summary: Dict[str, any]) -> Path:
        report_dir = self.report_dir / playbook.fiscal_year
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / f"{playbook.rfi}_summary.json"
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2, default=str)
        return path

    def _load_previous_report(self, playbook: Playbook) -> Optional[Dict[str, any]]:
        path = self.report_dir / playbook.fiscal_year / f"{playbook.rfi}_summary.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

