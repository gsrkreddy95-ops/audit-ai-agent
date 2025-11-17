"""
Evidence Playbook Schema
Defines normalized structures for replaying prior audit evidence.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlaybookTask:
    rfi: str
    title: str
    service: str
    account: str
    region: str
    evidence_type: str
    tool: str
    params: Dict[str, str]
    source_reference: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    date_filters: Dict[str, str] = field(default_factory=dict)


@dataclass
class Playbook:
    fiscal_year: str
    rfi: str
    tasks: List[PlaybookTask] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Playbook":
        tasks = []
        for task_dict in data.get("tasks", []):
            tasks.append(PlaybookTask(**task_dict))
        return Playbook(
            fiscal_year=data.get("fiscal_year", ""),
            rfi=data.get("rfi", ""),
            tasks=tasks,
            source_urls=data.get("source_urls", []),
            notes=data.get("notes")
        )

