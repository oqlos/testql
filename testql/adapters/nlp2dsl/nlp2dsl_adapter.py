"""Nlp2DslAdapter — parse/validate conversation TestPlans for nlp2dsl integration."""

from __future__ import annotations

from dataclasses import dataclass, field

from testql.adapters.base import BaseDSLAdapter, DSLDetectionResult, SourceLike, ValidationIssue, read_source
from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.ir import (
    ArtifactAssertStep,
    ConversationTurnStep,
    Nlp2DslStep,
    TestPlan,
)

_CONVERSATION_TYPES = frozenset({"conversation", "nlp2dsl", "dialog"})
_NLP2DSL_ENDPOINTS = frozenset({
    "chatstart",
    "chatmessage",
    "workflowfrom-text",
    "runworkflow",
    "systemexecute",
})


@dataclass
class Nlp2DslAdapter(BaseDSLAdapter):
    """Wraps TestTOON parsing and adds conversation/nlp2dsl validation."""

    name: str = "nlp2dsl"
    file_extensions: tuple[str, ...] = field(
        default_factory=lambda: (".conversation.testql.toon.yaml",)
    )
    _toon: TestToonAdapter = field(default_factory=TestToonAdapter, repr=False)

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, _ = read_source(source)
        if "# TYPE: conversation" in text or "# TYPE: nlp2dsl" in text:
            return DSLDetectionResult(matches=True, confidence=0.95, reason="conversation metadata")
        base = self._toon.detect(source)
        if not base.matches:
            return base
        plan = self._toon.parse(text)
        if plan.metadata.type.lower() in _CONVERSATION_TYPES:
            return DSLDetectionResult(matches=True, confidence=0.9, reason="conversation type")
        has_nlp = any(isinstance(s, (Nlp2DslStep, ConversationTurnStep, ArtifactAssertStep)) for s in plan.steps)
        if has_nlp:
            return DSLDetectionResult(matches=True, confidence=0.85, reason="nlp2dsl steps present")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="not a conversation scenario")

    def parse(self, source: SourceLike) -> TestPlan:
        plan = self._toon.parse(source)
        plan.config.setdefault("layers", {})
        layers = plan.config["layers"]
        if isinstance(layers, dict):
            layers.setdefault("conversation", plan.metadata.type.lower() in _CONVERSATION_TYPES)
            layers.setdefault("tooling", any(isinstance(s, Nlp2DslStep) for s in plan.steps))
            layers.setdefault("artifacts", any(isinstance(s, ArtifactAssertStep) for s in plan.steps))
        return plan

    def render(self, plan: TestPlan) -> str:
        return self._toon.render(plan)

    def validate(self, plan: TestPlan) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for idx, step in enumerate(plan.steps):
            if isinstance(step, Nlp2DslStep) and step.endpoint not in _NLP2DSL_ENDPOINTS:
                issues.append(ValidationIssue(
                    severity="error",
                    message=f"unknown nlp2dsl endpoint: {step.endpoint}",
                    location=f"steps[{idx}]",
                    code="nlp2dsl.unknown_endpoint",
                ))
            if isinstance(step, ConversationTurnStep) and step.role not in {"user", "assistant", "system"}:
                issues.append(ValidationIssue(
                    severity="warning",
                    message=f"unexpected conversation role: {step.role}",
                    location=f"steps[{idx}]",
                    code="conversation.unknown_role",
                ))
        return issues
