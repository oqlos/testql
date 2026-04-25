from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ResultStatus = Literal["passed", "failed", "partial", "blocked"]
CheckStatus = Literal["passed", "failed", "warning", "skipped"]
Severity = Literal["low", "medium", "high", "critical"]


@dataclass
class CheckResult:
    id: str
    status: CheckStatus
    summary: str
    node_id: str | None = None
    edge_id: str | None = None
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "status": self.status,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }
        if self.node_id:
            data["node_id"] = self.node_id
        if self.edge_id:
            data["edge_id"] = self.edge_id
        return data


@dataclass
class FailureFinding:
    id: str
    severity: Severity
    summary: str
    node_id: str | None = None
    edge_id: str | None = None
    likely_cause: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "severity": self.severity,
            "summary": self.summary,
            "likely_cause": self.likely_cause,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }
        if self.node_id:
            data["node_id"] = self.node_id
        if self.edge_id:
            data["edge_id"] = self.edge_id
        return data


@dataclass
class SuggestedAction:
    id: str
    type: str
    summary: str
    target: str | None = None
    priority: Severity = "medium"
    evidence_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "type": self.type,
            "summary": self.summary,
            "priority": self.priority,
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }
        if self.target:
            data["target"] = self.target
        return data


@dataclass
class TestResultEnvelope:
    topology_id: str
    run_id: str
    status: ResultStatus
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[FailureFinding] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)
    suggested_actions: list[SuggestedAction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "topology_id": self.topology_id,
            "run_id": self.run_id,
            "status": self.status,
            "metadata": dict(self.metadata),
            "checks": [item.to_dict() for item in self.checks],
            "failures": [item.to_dict() for item in self.failures],
            "traces": [dict(item) for item in self.traces],
            "suggested_actions": [item.to_dict() for item in self.suggested_actions],
        }


@dataclass
class RefactorPlan:
    id: str
    source_run_id: str
    status: str
    findings: list[FailureFinding] = field(default_factory=list)
    actions: list[SuggestedAction] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_envelope(cls, envelope: TestResultEnvelope) -> "RefactorPlan":
        status = "ready" if envelope.failures or envelope.suggested_actions else "no_action_required"
        return cls(
            id=f"refactor.{envelope.run_id}",
            source_run_id=envelope.run_id,
            status=status,
            findings=list(envelope.failures),
            actions=list(envelope.suggested_actions),
            metadata={"topology_id": envelope.topology_id, "source_status": envelope.status},
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_run_id": self.source_run_id,
            "status": self.status,
            "metadata": dict(self.metadata),
            "findings": [item.to_dict() for item in self.findings],
            "actions": [item.to_dict() for item in self.actions],
        }
