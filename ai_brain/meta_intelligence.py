"""
Meta-Intelligence Layer: Self-Evolving Multi-Dimensional Agent
===============================================================

This is the highest intelligence layer that enables the agent to:
1. Analyze its own capabilities and limitations
2. Automatically enhance tooling when encountering complex scenarios
3. Generate new tools on-the-fly when needed
4. Learn from failures and adapt
5. Operate across multiple dimensions (AWS, Jira, Confluence, GitHub, SharePoint)
6. Self-diagnose and self-heal

Architecture:
- AIOrchestrator: Plans and directs tools
- UniversalIntelligence: Tools query for guidance
- MetaIntelligence: Monitors everything, enhances when needed

This creates a truly autonomous, self-improving agent.
"""

import os
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import re

from ai_brain.enhancement_manager import EnhancementManager

console = Console()


@dataclass
class ToolContract:
    """Structured contract Claude produces for each tool execution."""
    tool: str
    intent: str
    inputs: Dict[str, Any]
    success_criteria: List[str]
    preconditions: List[str] = field(default_factory=list)
    post_validations: List[str] = field(default_factory=list)
    fallback_plan: List[str] = field(default_factory=list)
    execution_constraints: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)

    def required_fields(self) -> List[str]:
        required = self.inputs.get("required", [])
        normalized = []
        for item in required:
            if isinstance(item, dict):
                normalized.append(item.get("name"))
            else:
                normalized.append(item)
        return [field for field in normalized if field]

    def get_final_payload(self, original_params: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(original_params or {})
        final_payload = self.inputs.get("final_payload")
        if isinstance(final_payload, dict):
            for key, value in final_payload.items():
                if value is None:
                    continue
                if key not in payload or self._is_missing(payload[key]):
                    payload[key] = value
        return payload

    @staticmethod
    def _is_missing(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, tuple, set, dict)) and not value:
            return True
        return False


@dataclass
class TelemetryRecord:
    """Telemetry snapshot for a single tool attempt."""
    timestamp: str
    tool: str
    attempt: int
    duration: float
    status: str
    error: Optional[str]
    payload_size: int


class MetaIntelligence:
    """
    Meta-Intelligence Layer - The Self-Evolving Brain
    
    Capabilities:
    1. **Capability Analysis**: Understands what the agent can and cannot do
    2. **Gap Detection**: Identifies missing functionality for complex tasks
    3. **Auto-Enhancement**: Generates code to fill capability gaps
    4. **Learning**: Learns from failures and successes
    5. **Multi-Dimensional**: Operates across all integrated platforms
    6. **Self-Healing**: Fixes broken tools automatically
    """
    
    def __init__(self, llm, tool_executor, orchestrator):
        """
        Initialize Meta-Intelligence
        
        Args:
            llm: LLM instance (Claude/Bedrock)
            tool_executor: Tool executor with all tools
            orchestrator: AI Orchestrator for planning
        """
        self.llm = llm
        self.tool_executor = tool_executor
        self.orchestrator = orchestrator
        self.capability_map = self._build_capability_map()
        self.enhancement_history = []
        self.failure_patterns = []
        self.contract_history: List[Dict[str, Any]] = []
        self.telemetry_log: List[TelemetryRecord] = []
        self.request_memory: List[Dict[str, Any]] = []
        self.proactive_recommendations: List[Dict[str, Any]] = []
        self.guardrails = {
            "max_attempts": 3,
            "max_duration_seconds": 240,
            "max_payload_chars": 12000
        }
        self.ground_truth_validators = self._build_ground_truth_validators()
        self.enhancement_manager = EnhancementManager()
        
        # Initialize Auto-Fix Engine
        from ai_brain.knowledge_manager import get_knowledge_manager
        from ai_brain.auto_fix_engine import AutoFixEngine
        self.auto_fix = AutoFixEngine(self.enhancement_manager, get_knowledge_manager())
        
        console.print("\n[bold magenta]🧩 Meta-Intelligence Layer Activated[/bold magenta]")
        console.print("[dim]  Self-evolving multi-dimensional agent ready[/dim]")
        console.print(f"[dim]  Auto-fix: {'ENABLED' if self.auto_fix.enabled else 'DISABLED'}[/dim]\n")
    
    def _build_capability_map(self) -> Dict[str, Dict]:
        """
        Build comprehensive capability map of what agent can do
        
        Returns:
            Dict mapping domains to capabilities
        """
        return {
            "aws": {
                "services": ["ec2", "s3", "rds", "lambda", "iam", "vpc", "kms", "etc"],
                "actions": ["list", "describe", "export_csv", "export_json", "screenshot", "navigate"],
                "limitations": ["No write operations", "Requires authentication"],
                "tools": ["aws_console_action", "aws_list_resources", "aws_export_data", "aws_collect_comprehensive_audit_evidence"]
            },
            "jira": {
                "services": ["tickets", "sprints", "boards", "projects"],
                "actions": ["search_jql", "list_tickets", "get_ticket", "export", "filter_by_board"],
                "limitations": ["Read-only", "Pagination at 100 per page"],
                "tools": ["jira_search_jql", "jira_list_tickets", "jira_get_ticket"]
            },
            "confluence": {
                "services": ["pages", "spaces", "content"],
                "actions": ["search", "get_page", "list_space", "export"],
                "limitations": ["Read-only"],
                "tools": ["confluence_search", "confluence_get_page", "confluence_list_space"]
            },
            "github": {
                "services": ["repos", "prs", "commits", "releases"],
                "actions": ["list_prs", "get_pr", "list_commits", "search"],
                "limitations": ["Rate limits", "Authentication required"],
                "tools": ["github_list_prs", "github_get_pr", "github_list_commits"]
            },
            "sharepoint": {
                "services": ["folders", "files", "evidence"],
                "actions": ["review_evidence", "upload", "analyze"],
                "limitations": ["Browser-based", "Manual authentication"],
                "tools": ["sharepoint_review_evidence", "upload_to_sharepoint"]
            },
            "general": {
                "services": ["file_operations", "data_processing", "validation"],
                "actions": ["read", "write", "validate", "analyze"],
                "limitations": ["File system access only"],
                "tools": ["show_local_evidence"]
            }
        }
    
    def _build_ground_truth_validators(self) -> Dict[str, Any]:
        """Register lightweight validators that confirm tool output before returning to the user."""
        def validate_aws_export(result: Dict[str, Any]) -> List[str]:
            errors = []
            if not isinstance(result, dict):
                return ["AWS export result payload missing or invalid"]
            exports = result.get("exports") or []
            failures = result.get("failures", [])
            successful_entries = 0
            for entry in exports:
                region = entry.get("region", "unknown")
                files = entry.get("files") or []
                zero_records = entry.get("zero_records", False)
                if files:
                    missing_files = [path for path in files if path and not Path(path).exists()]
                    if missing_files:
                        errors.append(f"Missing export file(s) for region {region}: {', '.join(missing_files)}")
                    else:
                        successful_entries += 1
                elif zero_records:
                    successful_entries += 1
                else:
                    errors.append(f"Region {region} reported success but no files or zero-record indicator")
            if not exports:
                errors.append("AWS export returned no successful exports")
            elif successful_entries == 0:
                errors.append("AWS export did not produce files or zero-record confirmations")
            for failure in failures:
                errors.append(f"Region {failure.get('region')}: {failure.get('error')}")
            if not result.get("service"):
                errors.append("Export result missing service metadata")
            return errors
        
        def validate_jira_search(result: Dict[str, Any]) -> List[str]:
            errors = []
            if not isinstance(result, dict):
                return ["Jira result payload missing or invalid"]
            tickets = result.get("tickets")
            if tickets is None:
                errors.append("Jira result missing 'tickets' collection")
            count = result.get("count")
            truncated = result.get("truncated")
            total = result.get("total_tickets")
            if tickets is not None and count is not None:
                actual = len(tickets)
                if truncated and total is not None and count == total:
                    # acceptable: count reflects total, tickets list is truncated sample
                    pass
                elif count != actual:
                    errors.append(f"Jira result count mismatch (metadata={count}, actual={actual})")
            return errors
        
        return {
            "aws_export_data": validate_aws_export,
            "jira_search_jql": validate_jira_search
        }
    
    @staticmethod
    def _extract_json_block(content: str) -> str:
        """Extract JSON payload from LLM response (handles fenced blocks)."""
        if not content:
            return ""
        if "```json" in content:
            try:
                return content.split("```json", 1)[1].split("```", 1)[0].strip()
            except Exception:
                pass
        if "```" in content:
            try:
                return content.split("```", 1)[1].split("```", 1)[0].strip()
            except Exception:
                pass
        return content.strip()
    
    @staticmethod
    def _safe_json_load(payload: str) -> Optional[Dict[str, Any]]:
        """Parse JSON while tolerating minor formatting issues."""
        if not payload:
            return None
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            try:
                return json.loads(payload, strict=False)
            except json.JSONDecodeError:
                return None
    
    def _get_recent_memory_for_prompt(self, limit: int = 3) -> str:
        """Return compact JSON summary of recent executions for prompting."""
        if not self.request_memory:
            return "[]"
        recent = self.request_memory[-limit:]
        try:
            return json.dumps(recent, indent=2, default=str)
        except Exception:
            # Fallback if non-serializable entries exist
            sanitized = [
                {
                    "timestamp": entry.get("timestamp"),
                    "request": entry.get("request"),
                    "tool": entry.get("tool"),
                    "status": entry.get("status"),
                    "notes": entry.get("notes")
                }
                for entry in recent
            ]
            return json.dumps(sanitized, indent=2, default=str)
    
    def _record_memory_snapshot(
        self,
        user_request: str,
        tool_name: str,
        success: bool,
        result_summary: str,
        contract: ToolContract,
        telemetry_summary: Dict[str, Any]
    ) -> None:
        """Persist lightweight execution memory for adaptive planning."""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "request": user_request,
            "tool": tool_name,
            "status": "success" if success else "error",
            "result": result_summary[:500],
            "intent": contract.intent,
            "attempts": telemetry_summary.get("attempts"),
            "duration": telemetry_summary.get("total_duration"),
            "notes": telemetry_summary.get("notes")
        }
        self.request_memory.append(snapshot)
        self.request_memory = self.request_memory[-25:]
    
    def _record_telemetry(
        self,
        tool_name: str,
        attempt: int,
        duration: float,
        status: str,
        error: Optional[str],
        payload: Dict[str, Any]
    ) -> TelemetryRecord:
        payload_size = len(json.dumps(payload, default=str)) if payload else 0
        record = TelemetryRecord(
            timestamp=datetime.now().isoformat(),
            tool=tool_name,
            attempt=attempt + 1,
            duration=duration,
            status=status,
            error=error,
            payload_size=payload_size
        )
        self.telemetry_log.append(record)
        self.telemetry_log = self.telemetry_log[-200:]
        return record
    
    def _summarize_telemetry(self, records: List[TelemetryRecord]) -> Dict[str, Any]:
        if not records:
            return {"attempts": 0, "total_duration": 0, "errors": 0}
        total_duration = sum(r.duration for r in records)
        error_count = sum(1 for r in records if r.status != "success")
        return {
            "attempts": len(records),
            "total_duration": total_duration,
            "errors": error_count,
            "notes": f"{error_count} error attempt(s)" if error_count else "clean run"
        }
    
    def _validate_contract_schema(self, contract_dict: Dict[str, Any]) -> None:
        required_keys = ["tool", "intent", "inputs", "success_criteria"]
        for key in required_keys:
            if key not in contract_dict:
                raise ValueError(f"Contract missing required key: {key}")
        if not isinstance(contract_dict["inputs"], dict):
            raise ValueError("Contract 'inputs' must be an object")
        if not isinstance(contract_dict["success_criteria"], list):
            raise ValueError("Contract 'success_criteria' must be a list")
    
    def _fallback_contract(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        reason: str
    ) -> ToolContract:
        console.print(f"[yellow]⚠️  Falling back to default contract: {reason}[/yellow]")
        contract_dict = {
            "tool": tool_name,
            "intent": f"Execute {tool_name} safely with provided parameters",
            "inputs": {
                "required": list(tool_params.keys()),
                "final_payload": tool_params
            },
            "success_criteria": [
                "Tool returns status=success",
                "Result payload is not empty"
            ],
            "preconditions": [],
            "post_validations": [],
            "fallback_plan": [],
            "execution_constraints": {},
        }
        return ToolContract(
            tool=contract_dict["tool"],
            intent=contract_dict["intent"],
            inputs=contract_dict["inputs"],
            success_criteria=contract_dict["success_criteria"],
            preconditions=contract_dict["preconditions"],
            post_validations=contract_dict["post_validations"],
            fallback_plan=contract_dict["fallback_plan"],
            execution_constraints=contract_dict["execution_constraints"],
            raw=contract_dict
        )
    
    def _build_tool_contract(
        self,
        user_request: str,
        tool_name: str,
        tool_params: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> ToolContract:
        """Ask Claude to build a structured execution contract for the tool."""
        recent_memory = self._get_recent_memory_for_prompt()
        prompt = f"""You are the Meta-Intelligence planning brain.
Create a JSON contract describing how to call the tool below.

User request: {user_request}
Tool: {tool_name}
Tool parameters provided: {json.dumps(tool_params, indent=2, default=str)}
Request analysis: {json.dumps(analysis, indent=2)}
Recent execution memory: {recent_memory}

Return JSON with the following shape:
{{
  "tool": "{tool_name}",
  "intent": "short sentence",
  "inputs": {{
    "required": [{{"name": "aws_account", "description": "..."}}, "..."],
    "optional": ["..."],
    "final_payload": {{... merged params ready for execution ...}}
  }},
  "preconditions": ["checks before running"],
  "success_criteria": ["observable conditions to consider result valid"],
  "post_validations": ["lightweight assertions to confirm data is real"],
  "fallback_plan": ["steps if success criteria fail"],
  "execution_constraints": {{
        "max_attempts": 3,
        "max_duration_seconds": 240
  }}
}}
Only return JSON."""
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            contract_json = self._extract_json_block(content)
            contract_dict = self._safe_json_load(contract_json)
            if not contract_dict:
                raise ValueError("LLM did not return valid JSON contract")
            self._validate_contract_schema(contract_dict)
            contract = ToolContract(
                tool=contract_dict["tool"],
                intent=contract_dict["intent"],
                inputs=contract_dict["inputs"],
                success_criteria=contract_dict["success_criteria"],
                preconditions=contract_dict.get("preconditions", []),
                post_validations=contract_dict.get("post_validations", []),
                fallback_plan=contract_dict.get("fallback_plan", []),
                execution_constraints=contract_dict.get("execution_constraints", {}),
                raw=contract_dict
            )
            self.contract_history.append({
                "timestamp": datetime.now().isoformat(),
                "tool": tool_name,
                "request": user_request,
                "contract": contract_dict
            })
            self.contract_history = self.contract_history[-50:]
            return contract
        except Exception as exc:
            return self._fallback_contract(tool_name, tool_params, str(exc))
    
    def _validate_payload_against_contract(
        self,
        contract: ToolContract,
        payload: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        errors = []
        for field in contract.required_fields():
            if payload.get(field) in (None, "", []):
                errors.append(f"Missing required input '{field}' per contract")
        return len(errors) == 0, errors
    
    def _run_ground_truth_validators(
        self,
        tool_name: str,
        result_payload: Any
    ) -> List[str]:
        validator = self.ground_truth_validators.get(tool_name)
        if not validator or result_payload is None:
            return []
        try:
            return validator(result_payload) or []
        except Exception as exc:
            return [f"Validator error: {exc}"]
    
    def _derive_guardrails(self, contract: ToolContract) -> Dict[str, Any]:
        guardrails = dict(self.guardrails)
        for key, value in (contract.execution_constraints or {}).items():
            if key in guardrails and isinstance(value, (int, float)) and value > 0:
                guardrails[key] = value
        return guardrails
    
    def _maybe_schedule_proactive_enhancement(
        self,
        user_request: str,
        analysis: Dict[str, Any],
        telemetry_summary: Dict[str, Any],
        trigger_reason: str
    ) -> None:
        """Ask Claude to propose future enhancements when we hit repeated pain."""
        try:
            prompt = f"""The agent needs to become more autonomous.
Suggest a future capability enhancement when the following conditions were observed:

User request: {user_request}
Analysis: {json.dumps(analysis, indent=2)}
Telemetry summary: {json.dumps(telemetry_summary, indent=2)}
Trigger reason: {trigger_reason}

Return JSON with:
{{
  "summary": "short description",
  "benefit": "expected benefit",
  "suggested_changes": ["code area or tool to update", "..."],
  "priority": "low|medium|high"
}}"""
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            idea_json = self._extract_json_block(content)
            idea = self._safe_json_load(idea_json)
            if idea:
                idea["timestamp"] = datetime.now().isoformat()
                idea["reason"] = trigger_reason
                self.proactive_recommendations.append(idea)
                self.proactive_recommendations = self.proactive_recommendations[-20:]
                self._persist_proactive_recommendation(idea)
        except Exception:
            # Silent failure – proactive ideas are nice-to-have
            pass
    
    def _persist_proactive_recommendation(self, idea: Dict[str, Any]) -> None:
        """Persist proactive recommendation for later review."""
        enhancement_dir = Path("/Users/krishna/Documents/audit-ai-agent/ai_brain/enhancements")
        enhancement_dir.mkdir(exist_ok=True)
        filename = enhancement_dir / f"proactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, "w", encoding="utf-8") as handle:
                json.dump(idea, handle, indent=2)
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Enhancement generation & approval helpers
    # ------------------------------------------------------------------ #
    def _generate_structured_patch(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Ask Claude to produce a JSON patch plan that can be auto-applied after approval.
        """
        prompt = f"""You are a senior engineer generating a SAFE PATCH PLAN based on this context:

Context:
{json.dumps(context, indent=2, default=str)}

Return STRICT JSON (no markdown) using this schema:
{{
  "summary": "Short title of the fix",
  "reason": "Why this fix is needed",
  "files": [
    {{
      "path": "relative/path.py",
      "operation": "replace|create|append",
      "description": "What this change does",
      "search": "exact text to replace (for replace ops)",
      "replace": "new text (for replace ops)",
      "content": "full file contents (for create/append ops)"
    }}
  ],
  "test_plan": "How to verify the fix"
}}

Rules:
- Use repository-relative paths (e.g., "tools/aws_export_tool.py").
- For replace operations include BOTH `search` and `replace`.
- For create/append operations include `content`.
- Keep search blocks small (20-40 lines max) and copy exact text from repo.
- Escape newlines properly. No comments, no additional text outside JSON.
"""
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            patch_json = self._extract_json_block(content)
            patch = self._safe_json_load(patch_json)
            if not patch or "files" not in patch:
                raise ValueError("Patch plan missing required fields")
            return patch
        except Exception as exc:
            console.print(f"[red]❌ Unable to generate structured patch: {exc}[/red]")
            return None

    def _register_pending_enhancement(
        self,
        trigger: str,
        user_request: str,
        analysis: Dict[str, Any],
        patch_plan: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not patch_plan:
            return None
        # Add confidence scoring to the proposal
        confidence = self._calculate_fix_confidence(patch_plan, analysis, telemetry_summary)
        risk_level = self._assess_risk_level(patch_plan)
        
        record = self.enhancement_manager.register_proposal({
            "trigger": trigger,
            "user_request": user_request,
            "analysis": analysis,
            "summary": patch_plan.get("summary", "Untitled Enhancement"),
            "reason": patch_plan.get("reason"),
            "files": patch_plan.get("files"),
            "test_plan": patch_plan.get("test_plan"),
            "metadata": metadata,
            "confidence": confidence,
            "risk_level": risk_level,
            "error_pattern": analysis.get("error")
        })
        
        # Try auto-apply if confidence is high enough
        if self.auto_fix.should_auto_apply(record):
            console.print(f"[bold green]🤖 Auto-applying fix (confidence: {confidence*100:.0f}%)[/bold green]")
            apply_result = self.auto_fix.apply_fix(record)
            if apply_result.get("applied"):
                record["status"] = "auto_applied"
                record["auto_applied_at"] = datetime.now().isoformat()
                console.print("[green]✅ Fix applied automatically[/green]")
        
        return record

    def _calculate_fix_confidence(
        self,
        patch_plan: Dict[str, Any],
        analysis: Dict[str, Any],
        telemetry: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for a fix (0.0-1.0).
        
        Factors:
        - Error is common/well-known: +0.3
        - Fix is simple (import, typo, etc.): +0.3
        - Similar fix succeeded before: +0.2
        - Multiple attempts failed same way: +0.1
        - Telemetry shows consistent pattern: +0.1
        """
        confidence = 0.5  # Base confidence
        
        error = analysis.get("error", "").lower()
        summary = patch_plan.get("summary", "").lower()
        
        # Common errors get higher confidence
        common_errors = ["import", "attribute", "typeerror", "keyerror", "missing"]
        if any(err in error for err in common_errors):
            confidence += 0.2
        
        # Simple fixes get higher confidence
        simple_fixes = ["add import", "fix typo", "update parameter", "add missing"]
        if any(fix in summary for fix in simple_fixes):
            confidence += 0.3
        
        # Recurring errors (multiple attempts) increase confidence
        attempts = telemetry.get("attempts", 1)
        if attempts >= 3:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _assess_risk_level(self, patch_plan: Dict[str, Any]) -> str:
        """
        Assess risk level of applying a fix.
        
        Returns:
            "low"|"medium"|"high"
        """
        files = patch_plan.get("files", [])
        
        # Count operations
        replace_count = sum(1 for f in files if f.get("operation") == "replace")
        create_count = sum(1 for f in files if f.get("operation") == "create")
        
        # Multiple file changes = higher risk
        if len(files) > 3:
            return "high"
        
        # Creating new files is lower risk than modifying
        if create_count > 0 and replace_count == 0:
            return "low"
        
        # Check if modifying core files
        core_files = ["intelligent_agent.py", "tool_executor.py", "orchestrator.py"]
        for file_info in files:
            path = file_info.get("path", "")
            if any(core in path for core in core_files):
                return "high"
        
        # Simple import fixes or small changes
        for file_info in files:
            search = file_info.get("search", "")
            if "import" in search and len(search) < 100:
                return "low"
        
        return "medium"
    
    def _serialize_proposal_for_response(self, record: Dict[str, Any]) -> Dict[str, Any]:
        files = record.get("files") or []
        file_summaries = [
            {
                "path": f.get("path"),
                "operation": f.get("operation"),
                "description": f.get("description")
            }
            for f in files
        ]
        return {
            "id": record.get("id"),
            "summary": record.get("summary"),
            "reason": record.get("reason"),
            "files": file_summaries,
            "test_plan": record.get("test_plan"),
            "apply_tool": "apply_pending_enhancement",
            "list_tool": "list_pending_enhancements"
        }

    def _build_pending_response(
        self,
        record: Dict[str, Any],
        reason: str,
        meta_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        pending_payload = self._serialize_proposal_for_response(record)
        pending_payload["pending_reason"] = reason
        return {
            "status": "pending_approval",
            "meta_analysis": meta_analysis,
            "pending_approval": pending_payload,
            "message": (
                f"Enhancement '{record.get('summary')}' is ready for review. "
                "Call 'apply_pending_enhancement' with the proposal_id after approval."
            )
        }

    def _queue_fix_proposal(
        self,
        trigger: str,
        user_request: str,
        analysis: Dict[str, Any],
        tool_name: str,
        error: str,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        patch_plan = self._generate_structured_patch({
            "trigger": trigger,
            "user_request": user_request,
            "tool": tool_name,
            "error": error,
            "context": context
        })
        if not patch_plan:
            return None
        record = self._register_pending_enhancement(
            trigger=trigger,
            user_request=user_request,
            analysis=analysis,
            patch_plan=patch_plan,
            metadata={
                "tool": tool_name,
                "error": error,
                "context": context
            }
        )
        return record
    
    def analyze_request_complexity(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze user request to determine complexity and required capabilities
        
        Args:
            user_request: The user's natural language request
        
        Returns:
            Dict with complexity analysis
        """
        prompt = f"""Analyze this user request and determine:
1. Required domains (AWS, Jira, Confluence, GitHub, SharePoint, etc.)
2. Required actions in each domain
3. Complexity level (simple, moderate, complex, very complex)
4. Whether current capabilities are sufficient
5. What new capabilities might be needed if any

Current agent capabilities:
{json.dumps(self.capability_map, indent=2)}

User request: "{user_request}"

Return JSON:
{{
    "complexity": "simple|moderate|complex|very_complex",
    "required_domains": ["domain1", "domain2"],
    "required_actions": {{
        "domain1": ["action1", "action2"],
        "domain2": ["action3"]
    }},
    "capabilities_sufficient": true/false,
    "missing_capabilities": ["capability1", "capability2"],
    "reasoning": "explanation of analysis"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            json_str = self._extract_json_block(content)
            analysis = self._safe_json_load(json_str)
            if not analysis:
                raise ValueError("LLM did not return valid JSON")
            
            console.print(f"\n[cyan]📊 Request Complexity Analysis:[/cyan]")
            console.print(f"  Complexity: [yellow]{analysis['complexity']}[/yellow]")
            console.print(f"  Domains: {', '.join(analysis['required_domains'])}")
            console.print(f"  Sufficient: [{'green' if analysis['capabilities_sufficient'] else 'red'}]{'✓' if analysis['capabilities_sufficient'] else '✗'}[/{'green' if analysis['capabilities_sufficient'] else 'red'}]")
            
            return analysis
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Complexity analysis fallback: {e}[/yellow]")
            return {
                "complexity": "unknown",
                "required_domains": [],
                "required_actions": {},
                "capabilities_sufficient": True,
                "missing_capabilities": [],
                "reasoning": f"Analysis failed: {e}"
            }
    
    def detect_capability_gaps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect specific capability gaps from analysis
        
        Args:
            analysis: Result from analyze_request_complexity
        
        Returns:
            List of capability gaps with details
        """
        if analysis["capabilities_sufficient"]:
            return []
        
        gaps = []
        for domain, actions in analysis["required_actions"].items():
            if domain not in self.capability_map:
                gaps.append({
                    "type": "missing_domain",
                    "domain": domain,
                    "actions": actions,
                    "severity": "high"
                })
                continue
            
            domain_caps = self.capability_map[domain]
            for action in actions:
                if action not in domain_caps["actions"]:
                    gaps.append({
                        "type": "missing_action",
                        "domain": domain,
                        "action": action,
                        "severity": "medium"
                    })
        
        return gaps
    
    
    def enhance_agent_realtime(
        self,
        user_request: str,
        analysis: Dict[str, Any],
        gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enhance agent in real-time by generating a structured patch and queueing it for approval.
        """
        if not gaps:
            return {"status": "noop", "message": "No enhancements needed"}
        
        console.print(Panel(
            f"[yellow]🚀 Auto-Enhancement Mode Activated[/yellow]\n\n"
            f"Detected {len(gaps)} capability gap(s)\n"
            f"Generating solution...",
            title="Meta-Intelligence"
        ))
        
        patch_plan = self._generate_structured_patch({
            "trigger": "capability_gap",
            "user_request": user_request,
            "analysis": analysis,
            "gaps": gaps
        })
        if not patch_plan:
            return {"status": "error", "error": "Failed to generate enhancement patch"}
        
        record = self._register_pending_enhancement(
            trigger="capability_gap",
            user_request=user_request,
            analysis=analysis,
            patch_plan=patch_plan,
            metadata={"gaps": gaps}
        )
        if not record:
            return {"status": "error", "error": "Failed to register enhancement proposal"}
        
        enhancement_history_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "analysis": analysis,
            "gaps": gaps,
            "proposal_id": record.get("id"),
            "status": "pending"
        }
        self.enhancement_history.append(enhancement_history_entry)
        
        return self._build_pending_response(
            record,
            reason="capability gap detected",
            meta_analysis=analysis
        )
    
    def learn_from_failure(self, tool_name: str, error: str, context: Dict) -> Dict[str, Any]:
        """
        Learn from tool failures and generate fixes
        
        Args:
            tool_name: Name of failed tool
            error: Error message
            context: Execution context
        
        Returns:
            Dict with learning insights and fix suggestions
        """
        console.print(f"\n[yellow]🧠 Learning from failure: {tool_name}[/yellow]")
        
        # Record failure pattern
        failure_pattern = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "error": error,
            "context": context,
            "recurrence_count": 1
        }
        
        # Check if this is a recurring pattern
        similar_failures = [
            f for f in self.failure_patterns
            if f["tool"] == tool_name and f["error"] == error
        ]
        
        if similar_failures:
            failure_pattern["recurrence_count"] = len(similar_failures) + 1
            console.print(f"[red]⚠️  Recurring failure detected ({failure_pattern['recurrence_count']} times)[/red]")
        
        self.failure_patterns.append(failure_pattern)
        
        # Generate fix suggestion
        prompt = f"""Analyze this tool failure and suggest a fix:

Tool: {tool_name}
Error: {error}
Context: {json.dumps(context, indent=2)}
Recurrence: {failure_pattern['recurrence_count']} time(s)

Provide:
1. Root cause analysis
2. Suggested fix (code or configuration)
3. Prevention strategy

Return JSON:
{{
    "root_cause": "explanation",
    "fix_type": "code|config|documentation",
    "suggested_fix": "detailed fix description or code",
    "prevention": "how to prevent this in future"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            # Robust JSON extraction with fallback
            json_str = self._extract_json_block(content)
            if not json_str or json_str.strip() == "":
                # Empty response, return graceful fallback
                console.print(f"[yellow]⚠️  Empty LLM response for learning analysis[/yellow]")
                return {
                    "root_cause": "Unable to analyze (empty LLM response)",
                    "fix_type": "unknown",
                    "suggested_fix": f"Check parameters: {context}",
                    "prevention": "Review tool parameter requirements"
                }
            
            learning = self._safe_json_load(json_str)
            if not learning:
                # JSON parsing failed, return graceful fallback
                console.print(f"[yellow]⚠️  Failed to parse learning analysis JSON[/yellow]")
                return {
                    "root_cause": "Unable to analyze (invalid JSON)",
                    "fix_type": "unknown",
                    "suggested_fix": f"Error: {error}. Check parameters.",
                    "prevention": "Review tool parameter requirements"
                }
            
            console.print(f"\n[cyan]📚 Learning Analysis:[/cyan]")
            console.print(f"  Root Cause: {learning.get('root_cause', 'Unknown')}")
            console.print(f"  Fix Type: {learning.get('fix_type', 'unknown')}")
            console.print(f"  Prevention: {learning.get('prevention', 'Monitor')}")
            
            return learning
            
        except Exception as e:
            console.print(f"[red]❌ Error in learning analysis: {e}[/red]")
            return {
                "root_cause": f"Analysis failed: {str(e)}",
                "fix_type": "unknown",
                "suggested_fix": f"Error: {error}. Manual investigation required.",
                "prevention": "Monitor for recurrence"
            }
    
    def suggest_alternative_approach(
        self,
        original_request: str,
        failed_approach: str,
        error: str
    ) -> Optional[str]:
        """
        When an approach fails, suggest alternative ways to accomplish the goal
        
        Args:
            original_request: User's original request
            failed_approach: The approach that failed
            error: Error message
        
        Returns:
            Alternative approach suggestion
        """
        prompt = f"""A tool execution failed. Suggest alternative approaches:

Original Request: {original_request}
Failed Approach: {failed_approach}
Error: {error}

Available capabilities:
{json.dumps(self.capability_map, indent=2)}

Suggest 2-3 alternative approaches that could achieve the same goal using:
1. Different tools
2. Different API methods
3. Different data sources
4. Workarounds

Return as clear, actionable steps."""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            console.print(Panel(
                content,
                title="[yellow]🔄 Alternative Approaches[/yellow]",
                border_style="yellow"
            ))
            
            return content
            
        except Exception as e:
            console.print(f"[red]❌ Error generating alternatives: {e}[/red]")
            return None
    
    def execute_with_meta_intelligence(
        self,
        user_request: str,
        tool_name: str,
        tool_params: Dict,
        execute_callback=None
    ) -> Dict[str, Any]:
        """
        Execute a tool with meta-intelligence monitoring
        
        This wraps tool execution with:
        - Pre-execution validation
        - Real-time monitoring
        - Post-execution analysis
        - Automatic retry with fixes
        - Learning from failures
        
        Args:
            user_request: Original user request
            tool_name: Tool to execute
            tool_params: Tool parameters
        
        Returns:
            Execution result with meta-intelligence enhancements
        """
        console.print(f"\n[bold cyan]🧩 Meta-Intelligence Execution: {tool_name}[/bold cyan]")
        
        # Default execution callback falls back to tool executor's direct method
        if execute_callback is None:
            if hasattr(self.tool_executor, "_execute_tool_direct"):
                execute_callback = self.tool_executor._execute_tool_direct  # type: ignore[attr-defined]
            else:
                execute_callback = self.tool_executor.execute_tool
        
        # Pre-execution: Analyze complexity
        analysis = self.analyze_request_complexity(user_request)
        
        # Check for capability gaps
        gaps = self.detect_capability_gaps(analysis)
        if gaps:
            console.print(f"[yellow]⚠️  Detected {len(gaps)} capability gap(s)[/yellow]")
            gap_response = self.enhance_agent_realtime(user_request, analysis, gaps)
            if gap_response.get("status") != "noop":
                gap_response.setdefault("meta_analysis", analysis)
                gap_response.setdefault("gaps", gaps)
                return gap_response
        
        # Build structured contract & guardrails
        contract = self._build_tool_contract(user_request, tool_name, tool_params, analysis)
        guardrails = self._derive_guardrails(contract)
        tool_payload = contract.get_final_payload(tool_params)
        payload_valid, payload_errors = self._validate_payload_against_contract(contract, tool_payload)
        if not payload_valid:
            return {
                "status": "error",
                "error": "; ".join(payload_errors),
                "meta_analysis": analysis,
                "contract": contract.raw
            }
        
        if contract.preconditions:
            console.print("[dim]Preconditions:[/dim] " + " | ".join(contract.preconditions))
        
        console.print(f"[cyan]▶️  Executing {tool_name} with structured plan...[/cyan]")
        
        execution_telemetry: List[TelemetryRecord] = []
        max_retries = guardrails.get("max_attempts", 3) or 3
        total_start = time.time()
        guardrail_reason = None
        
        region_status: Dict[str, Dict[str, Any]] = {}
        for attempt in range(max_retries):
            attempt_start = time.time()
            try:
                result = execute_callback(tool_name, tool_payload)
                duration = time.time() - attempt_start
                telemetry = self._record_telemetry(
                    tool_name,
                    attempt,
                    duration,
                    result.get("status", "unknown"),
                    result.get("error"),
                    tool_payload
                )
                execution_telemetry.append(telemetry)
                
                if telemetry.payload_size > guardrails.get("max_payload_chars", float("inf")):
                    guardrail_reason = (
                        f"Payload size guardrail exceeded ({telemetry.payload_size} chars)"
                    )
                    console.print(f"[yellow]⚠️  {guardrail_reason}[/yellow]")
                    break
                
                if tool_name == "aws_export_data":
                    for entry in result.get("result", {}).get("exports", []):
                        region_status[entry.get("region")] = {"status": "success", "error": None}
                    for failure in result.get("result", {}).get("failures", []):
                        region_status[failure.get("region")] = {"status": "error", "error": failure.get("error")}

                if result.get("status") == "success":
                    validation_errors = self._run_ground_truth_validators(tool_name, result.get("result"))
                    if validation_errors:
                        console.print(f"[yellow]⚠️  Validator detected issues: {'; '.join(validation_errors)}[/yellow]")
                        result = {
                            "status": "error",
                            "error": "; ".join(validation_errors)
                        }
                    else:
                        telemetry_summary = self._summarize_telemetry(execution_telemetry)
                        result_summary = json.dumps(result.get("result"), default=str)[:500]
                        self._record_memory_snapshot(
                            user_request,
                            tool_name,
                            True,
                            result_summary,
                            contract,
                            telemetry_summary
                        )
                        if (
                            telemetry_summary["total_duration"] > guardrails.get("max_duration_seconds", 240) * 0.8
                            or analysis.get("complexity") in ("complex", "very_complex")
                        ):
                            self._maybe_schedule_proactive_enhancement(
                                user_request,
                                analysis,
                                telemetry_summary,
                                "high complexity or duration"
                            )
                        console.print(f"[green]✅ Execution successful[/green]")
                        return {
                            "status": "success",
                            "result": result.get("result"),
                            "meta_analysis": analysis,
                            "contract": contract.raw,
                            "telemetry": telemetry_summary,
                            "attempts": attempt + 1
                        }
                
                error = result.get("error", "Unknown error")
                if tool_name == "aws_export_data":
                    region_status.setdefault("unknown", {"status": "error", "error": error})
                console.print(f"[yellow]⚠️  Attempt {attempt + 1} failed: {error}[/yellow]")
                
                learning = self.learn_from_failure(
                    tool_name,
                    error,
                    {"params": tool_payload, "attempt": attempt + 1}
                )
                
                if learning.get("fix_type") == "config" and attempt < max_retries - 1:
                    console.print(f"[cyan]🔧 Applying suggested config fix before retry...[/cyan]")
                    continue
                
                if attempt == max_retries - 1:
                    self.suggest_alternative_approach(
                        user_request,
                        f"{tool_name} with {tool_payload}",
                        error
                    )
            
            except Exception as e:
                duration = time.time() - attempt_start
                telemetry = self._record_telemetry(
                    tool_name,
                    attempt,
                    duration,
                    "exception",
                    str(e),
                    tool_payload
                )
                execution_telemetry.append(telemetry)
                error_str = str(e)
                console.print(f"[red]❌ Execution exception: {error_str}[/red]")
                
                if attempt < max_retries - 1:
                    console.print(f"[yellow]🔄 Retrying ({attempt + 2}/{max_retries})...[/yellow]")
                    continue
                
                telemetry_summary = self._summarize_telemetry(execution_telemetry)
                self._record_memory_snapshot(
                    user_request,
                    tool_name,
                    False,
                    error_str,
                    contract,
                    telemetry_summary
                )
                self._maybe_schedule_proactive_enhancement(
                    user_request,
                    analysis,
                    telemetry_summary,
                    "exception raised during execution"
                )
                pending_fix = self._queue_fix_proposal(
                    trigger="runtime_error",
                    user_request=user_request,
                    analysis=analysis,
                    tool_name=tool_name,
                    error=error_str,
                    context={"params": tool_payload, "attempt": attempt + 1, "exception": True}
                )
                if pending_fix:
                    return self._build_pending_response(
                        pending_fix,
                        reason=error_str,
                        meta_analysis=analysis
                    )
                return {
                    "status": "error",
                    "error": error_str,
                    "meta_analysis": analysis,
                    "contract": contract.raw,
                    "telemetry": telemetry_summary,
                    "attempts": attempt + 1,
                    "region_status": region_status,
                    "learning": self.learn_from_failure(tool_name, error_str, {"params": tool_payload})
                }
            
            elapsed_total = time.time() - total_start
            if elapsed_total > guardrails.get("max_duration_seconds", float("inf")):
                guardrail_reason = f"Exceeded duration guardrail ({elapsed_total:.1f}s)"
                console.print(f"[yellow]⚠️  {guardrail_reason}[/yellow]")
                break
        
        telemetry_summary = self._summarize_telemetry(execution_telemetry)
        summary_error = guardrail_reason or "Max retries exceeded"
        self._record_memory_snapshot(
            user_request,
            tool_name,
            False,
            summary_error,
            contract,
            telemetry_summary
        )
        self._maybe_schedule_proactive_enhancement(
            user_request,
            analysis,
            telemetry_summary,
            guardrail_reason or "max retries exceeded"
        )
        pending_fix = self._queue_fix_proposal(
            trigger="runtime_error",
            user_request=user_request,
            analysis=analysis,
            tool_name=tool_name,
            error=summary_error,
            context={"params": tool_payload, "telemetry": telemetry_summary}
        )
        if pending_fix:
            return self._build_pending_response(
                pending_fix,
                reason=summary_error,
                meta_analysis=analysis
            )
        return {
            "status": "error",
            "error": summary_error,
            "meta_analysis": analysis,
            "contract": contract.raw,
            "telemetry": telemetry_summary,
            "attempts": len(execution_telemetry),
            "region_status": region_status
        }
    
    def generate_capability_report(self) -> str:
        """
        Generate comprehensive capability report
        
        Returns:
            Markdown report of agent capabilities
        """
        report = "# Agent Capability Report\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        report += "## Current Capabilities\n\n"
        for domain, caps in self.capability_map.items():
            report += f"### {domain.upper()}\n\n"
            report += f"**Services**: {', '.join(caps['services'])}\n\n"
            report += f"**Actions**: {', '.join(caps['actions'])}\n\n"
            report += f"**Tools**: {', '.join(caps['tools'])}\n\n"
            report += f"**Limitations**: {', '.join(caps['limitations'])}\n\n"
        
        report += "## Enhancement History\n\n"
        if self.enhancement_history:
            for i, enh in enumerate(self.enhancement_history, 1):
                report += f"### Enhancement #{i}\n"
                report += f"- **Timestamp**: {enh['timestamp']}\n"
                report += f"- **Request**: {enh['user_request']}\n"
                report += f"- **Gaps**: {len(enh['gaps'])}\n"
                report += f"- **Applied**: {enh['applied']}\n\n"
        else:
            report += "No enhancements yet.\n\n"
        
        report += "## Failure Patterns\n\n"
        if self.failure_patterns:
            # Group by tool
            by_tool = {}
            for failure in self.failure_patterns:
                tool = failure["tool"]
                if tool not in by_tool:
                    by_tool[tool] = []
                by_tool[tool].append(failure)
            
            for tool, failures in by_tool.items():
                report += f"### {tool}\n"
                report += f"- **Total Failures**: {len(failures)}\n"
                unique_errors = set(f["error"] for f in failures)
                report += f"- **Unique Errors**: {len(unique_errors)}\n\n"
        else:
            report += "No failures recorded.\n\n"
        
        return report


class MultiDimensionalCoordinator:
    """
    Coordinates operations across multiple platforms simultaneously
    
    Example: "Compare Jira tickets with AWS resources and update Confluence"
    requires coordinating Jira, AWS, and Confluence tools in sequence
    """
    
    def __init__(self, meta_intelligence: MetaIntelligence):
        self.meta = meta_intelligence
        self.active_dimensions = set()
    
    def execute_cross_platform_task(
        self,
        task_description: str,
        dimensions: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a task that spans multiple platforms
        
        Args:
            task_description: Natural language task description
            dimensions: List of platforms involved (e.g., ["jira", "aws", "confluence"])
        
        Returns:
            Combined results from all dimensions
        """
        console.print(f"\n[bold magenta]🌐 Multi-Dimensional Task Execution[/bold magenta]")
        console.print(f"[cyan]Dimensions: {', '.join(dimensions)}[/cyan]")
        console.print(f"[cyan]Task: {task_description}[/cyan]\n")
        
        self.active_dimensions.update(dimensions)
        
        # Use meta-intelligence to break down the task
        prompt = f"""Break down this cross-platform task into sequential steps:

Task: {task_description}
Platforms: {', '.join(dimensions)}

Available capabilities per platform:
{json.dumps({d: self.meta.capability_map.get(d, {}) for d in dimensions}, indent=2)}

Return JSON array of steps:
[
    {{
        "step": 1,
        "platform": "jira",
        "action": "search_tickets",
        "params": {{}},
        "output_to": "jira_results"
    }},
    {{
        "step": 2,
        "platform": "aws",
        "action": "list_resources",
        "params": {{}},
        "depends_on": ["jira_results"]
    }}
]"""
        
        try:
            response = self.meta.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            steps = json.loads(json_str)
            
            # Execute steps in sequence
            results = {}
            for step in steps:
                step_num = step["step"]
                platform = step["platform"]
                action = step["action"]
                params = step.get("params", {})
                
                console.print(f"\n[cyan]Step {step_num}: {platform}.{action}[/cyan]")
                
                # Build tool name (platform_action)
                tool_name = f"{platform}_{action}"
                
                # Execute with meta-intelligence
                result = self.meta.execute_with_meta_intelligence(
                    task_description,
                    tool_name,
                    params
                )
                
                # Store result
                output_key = step.get("output_to", f"step_{step_num}_result")
                results[output_key] = result
            
            return {
                "status": "success",
                "dimensions": list(self.active_dimensions),
                "steps_executed": len(steps),
                "results": results
            }
            
        except Exception as e:
            console.print(f"[red]❌ Multi-dimensional execution failed: {e}[/red]")
            return {
                "status": "error",
                "error": str(e),
                "dimensions": list(self.active_dimensions)
            }

