"""Utility dataclasses for orchestrator execution plans.

These lightweight models give the LLM-directed orchestrator a structured
representation of the plan it generated.  They track execution status,
timestamps, and any validation or remediation notes so downstream logic can
reason about progress without manually mutating nested dictionaries.

The module intentionally keeps the API small so it can be imported in tooling
or test harnesses without pulling the heavier orchestrator module.  The
orchestrator converts between these dataclasses and JSON payloads that are
shared with the LLM or persisted to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


def _utc_iso() -> str:
    """Return a UTC timestamp in ISO-8601 format."""

    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


@dataclass
class PlanStep:
    """Represents a single orchestrator step.

    Attributes mirror what the LLM returns but add execution bookkeeping.  The
    orchestrator can mark progress through helper methods rather than mutating
    dicts in multiple places.
    """

    step: int
    tool: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    validation: str = ""
    depends_on: List[int] = field(default_factory=list)
    if_fails: Optional[str] = None
    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_summary: Optional[str] = None
    validation_notes: Optional[str] = None

    def mark_in_progress(self) -> None:
        """Mark the step as running."""

        if self.status not in {"completed", "failed", "invalid_output"}:
            self.status = "in_progress"
            if not self.started_at:
                self.started_at = _utc_iso()

    def mark_completed(self, output_summary: Optional[str] = None,
                       validation_notes: Optional[str] = None) -> None:
        """Mark the step as successfully completed."""

        self.status = "completed"
        self.completed_at = _utc_iso()
        if output_summary:
            self.output_summary = output_summary
        if validation_notes:
            self.validation_notes = validation_notes

    def mark_invalid(self, reason: str) -> None:
        """Mark the step as completed but failing validation criteria."""

        self.status = "invalid_output"
        self.completed_at = _utc_iso()
        self.validation_notes = reason

    def mark_failed(self, reason: str) -> None:
        """Mark the step as failed."""

        self.status = "failed"
        self.completed_at = _utc_iso()
        self.validation_notes = reason

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the step for JSON responses."""

        return {
            "step": self.step,
            "tool": self.tool,
            "description": self.description,
            "parameters": self.parameters,
            "validation": self.validation,
            "depends_on": self.depends_on,
            "if_fails": self.if_fails,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "output_summary": self.output_summary,
            "validation_notes": self.validation_notes,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "PlanStep":
        """Create a :class:`PlanStep` from serialized data."""

        return cls(
            step=int(payload.get("step", 0)),
            tool=payload.get("tool", ""),
            description=payload.get("description", ""),
            parameters=payload.get("parameters", {}) or {},
            validation=payload.get("validation", ""),
            depends_on=list(payload.get("depends_on", []) or []),
            if_fails=payload.get("if_fails"),
            status=payload.get("status", "pending"),
            started_at=payload.get("started_at"),
            completed_at=payload.get("completed_at"),
            output_summary=payload.get("output_summary"),
            validation_notes=payload.get("validation_notes"),
        )


@dataclass
class ExecutionPlan:
    """Container for the orchestrator execution plan."""

    rfi_code: str
    evidence_type: str = ""
    collection_strategy: str = ""
    success_criteria: List[str] = field(default_factory=list)
    estimated_time_minutes: Optional[int] = None
    steps: List[PlanStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step(self, step_number: int) -> Optional[PlanStep]:
        """Return the step with the supplied number."""

        for step in self.steps:
            if step.step == step_number:
                return step
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the plan."""

        payload = {
            "rfi_code": self.rfi_code,
            "evidence_type": self.evidence_type,
            "collection_strategy": self.collection_strategy,
            "execution_plan": [step.to_dict() for step in self.steps],
            "success_criteria": self.success_criteria,
            "estimated_time_minutes": self.estimated_time_minutes,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    def summarise_progress(self) -> Dict[str, Any]:
        """Produce a small progress summary useful for chat context."""

        totals = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "invalid_output": 0,
        }
        for step in self.steps:
            totals[step.status] = totals.get(step.status, 0) + 1

        return {
            "rfi_code": self.rfi_code,
            "steps_total": len(self.steps),
            "status_breakdown": totals,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ExecutionPlan":
        """Create an :class:`ExecutionPlan` from JSON-style data."""

        steps_payload = payload.get("execution_plan", []) or []
        steps = [PlanStep.from_dict(step) for step in steps_payload]
        return cls(
            rfi_code=payload.get("rfi_code", ""),
            evidence_type=payload.get("evidence_type", ""),
            collection_strategy=payload.get("collection_strategy", ""),
            success_criteria=list(payload.get("success_criteria", []) or []),
            estimated_time_minutes=payload.get("estimated_time_minutes"),
            steps=steps,
            metadata=payload.get("metadata", {}) or {},
        )

