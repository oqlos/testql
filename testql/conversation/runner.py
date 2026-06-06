"""Conversation test runner — multi-turn orchestration over Unified IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testql.adapters.nlp2dsl.client import Nlp2DslClient
from testql.adapters.nlp2dsl.llm_provider import LLMProvider, resolve_llm_provider
from testql.adapters.nlp2dsl.mock_llm import MockLLMProvider
from testql.artifacts.registry import get_artifact_registry
from testql.base import StepStatus, VariableStore
from testql.ir import (
    ApiStep,
    ArtifactAssertStep,
    ConversationTurnStep,
    Nlp2DslStep,
    Step,
    TestPlan,
)
from testql.ir_runner.context import ExecutionContext
from testql.ir_runner.engine import _run_step
from testql.ir_runner.executors.base import assemble_result


@dataclass
class TurnTrace:
    step_index: int
    kind: str
    status: str
    summary: str
    captures: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationRunResult:
    passed: bool
    turns: list[TurnTrace] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)

    def to_report_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "turns": [t.__dict__ for t in self.turns],
            "variables": dict(self.variables),
            "findings": list(self.findings),
        }


def _step_status_name(status: StepStatus) -> str:
    if status == StepStatus.PASSED:
        return "passed"
    if status == StepStatus.SKIPPED:
        return "skipped"
    if status == StepStatus.FAILED:
        return "failed"
    return "error"


class ConversationRunner:
    """Execute conversation-layer steps and collect trace for result.toon.yaml."""

    def __init__(
        self,
        client: Nlp2DslClient | None = None,
        mock_llm: LLMProvider | MockLLMProvider | None = None,
        llm_provider: LLMProvider | None = None,
        *,
        dry_run: bool = False,
        api_url: str = "http://localhost:8080",
        live_llm: bool | None = None,
        mock_replies: str | None = None,
    ) -> None:
        self.client = client or Nlp2DslClient(base_url=api_url)
        self.mock_llm = llm_provider or mock_llm or resolve_llm_provider(live=live_llm, mock_replies=mock_replies)
        self.dry_run = dry_run
        self.ctx = ExecutionContext(
            vars=VariableStore(),
            api_url=api_url.rstrip("/"),
            dry_run=dry_run,
        )
        self._artifact_registry = get_artifact_registry()

    @property
    def variables(self) -> dict[str, Any]:
        return self.ctx.vars.all()

    def run(self, plan: TestPlan) -> ConversationRunResult:
        self._apply_plan_config(plan)
        traces: list[TurnTrace] = []
        findings: list[str] = []
        passed = True

        for idx, step in enumerate(plan.steps):
            trace = self._run_step(idx, step)
            traces.append(trace)
            if trace.status not in {"passed", "skipped"}:
                passed = False
                findings.append(trace.summary)

        return ConversationRunResult(
            passed=passed,
            turns=traces,
            variables=dict(self.variables),
            findings=findings,
        )

    def _apply_plan_config(self, plan: TestPlan) -> None:
        for key, value in plan.config.items():
            if key == "context" and isinstance(value, dict):
                for ctx_key, ctx_val in value.items():
                    if not self.ctx.vars.has(ctx_key):
                        self.ctx.vars.set(ctx_key, ctx_val)
                continue
            if not self.ctx.vars.has(key):
                self.ctx.vars.set(key, value)
        base = plan.config.get("nlp2dsl_base_url") or plan.config.get("base_url")
        if base:
            self.ctx.api_url = str(base).rstrip("/")
            self.client.base_url = self.ctx.api_url

    def _run_step(self, idx: int, step: Step) -> TurnTrace:
        if isinstance(step, Nlp2DslStep):
            return self._run_nlp2dsl(idx, step)
        if isinstance(step, ConversationTurnStep):
            return self._run_turn(idx, step)
        if isinstance(step, ArtifactAssertStep):
            return self._run_artifact(idx, step)
        if isinstance(step, ApiStep) or step.kind in {"assert", "assert_json"}:
            return self._run_via_ir(idx, step)
        if self.dry_run:
            return TurnTrace(idx, step.kind, "skipped", f"dry-run: {step.kind}")
        return TurnTrace(idx, step.kind, "skipped", f"unsupported in conversation runner: {step.kind}")

    def _run_via_ir(self, idx: int, step: Step) -> TurnTrace:
        if self.dry_run:
            return TurnTrace(idx, step.kind, "skipped", f"dry-run: {step.kind}")
        result = _run_step(step, self.ctx)
        payload = (result.details or {}).get("payload", {})
        status = _step_status_name(result.status)
        return TurnTrace(
            idx,
            step.kind,
            status,
            result.message or result.name,
            captures={c.var_name: self.ctx.vars.get(c.var_name) for c in (step.captures or [])},
            payload=payload if isinstance(payload, dict) else {"value": payload},
        )

    def _dispatch_nlp2dsl_endpoint(self, endpoint: str, payload: dict[str, Any]) -> Any:
        """Dispatch to appropriate nlp2dsl client method; raises on unknown endpoint."""
        ep = endpoint.lower()
        if ep == "chatstart":
            return self.client.chatstart(payload)
        if ep == "chatmessage":
            return self.client.chatmessage(payload)
        if ep == "runworkflow":
            return self.client.runworkflow(payload)
        if ep in {"workflowfrom-text", "workflow_from_text"}:
            return self.client.workflow_from_text(
                str(payload.get("text", "")),
                execute=bool(payload.get("execute")),
            )
        raise ValueError(f"unknown endpoint: {endpoint}")

    def _apply_nlp2dsl_mock(self, step: Nlp2DslStep, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply mock LLM reply to payload if configured."""
        if step.mock_llm and self.mock_llm is not None:
            missing = payload.get("missing") or []
            reply = self.mock_llm.reply_for(
                str(payload.get("conversationId", "")),
                missing=list(missing),
                context=payload,
            )
            payload.setdefault("llmContext", reply)
        return payload

    def _determine_nlp2dsl_status(self, step: Nlp2DslStep, response: Any, ir_payload: dict) -> tuple[str, str]:
        """Determine status and summary for nlp2dsl response."""
        if step.asserts:
            assembled = assemble_result(step.endpoint, ir_payload, step.asserts, self.dry_run)
            return _step_status_name(assembled.status), assembled.message or f"{step.endpoint} → HTTP {response.status_code}"
        status = "passed" if response.ok else "failed"
        return status, f"{step.endpoint} → HTTP {response.status_code}"

    def _extract_captures(self, step: Step, body: dict[str, Any]) -> None:
        """Extract capture values from response body into context variables."""
        for capture in step.captures:
            value = _extract_path(body, capture.from_path)
            if value is not None:
                self.ctx.vars.set(capture.var_name, value)

    def _build_captures_dict(self, step: Step) -> dict[str, Any]:
        """Build captures dictionary from context variables."""
        return {c.var_name: self.ctx.vars.get(c.var_name) for c in step.captures}

    def _run_nlp2dsl(self, idx: int, step: Nlp2DslStep) -> TurnTrace:
        if self.dry_run:
            return TurnTrace(idx, step.kind, "skipped", f"dry-run: {step.endpoint}")

        payload = self._apply_nlp2dsl_mock(step, self._interpolate(step.payload))

        try:
            response = self._dispatch_nlp2dsl_endpoint(step.endpoint, payload)
        except ValueError as exc:
            return TurnTrace(idx, step.kind, "failed", str(exc))

        body = response.body
        self.ctx.last_status = response.status_code
        self.ctx.last_response = body
        ir_payload = {"status": response.status_code, "data": body, "headers": {}}

        status, summary = self._determine_nlp2dsl_status(step, response, ir_payload)
        self._extract_captures(step, body)

        return TurnTrace(
            idx,
            step.kind,
            status,
            summary,
            captures=self._build_captures_dict(step),
            payload=body,
        )

    def _run_turn(self, idx: int, step: ConversationTurnStep) -> TurnTrace:
        if self.dry_run:
            return TurnTrace(idx, step.kind, "skipped", f"dry-run: turn")
        payload = {"text": step.message, "role": step.role}
        payload.update(self.variables)
        response = self.client.chatmessage(payload)
        body = response.body
        self.ctx.last_status = response.status_code
        self.ctx.last_response = body
        dialog_status = str(body.get("status", ""))
        if step.expect_status and dialog_status != step.expect_status:
            return TurnTrace(
                idx,
                step.kind,
                "failed",
                f"expected status {step.expect_status}, got {dialog_status}",
                payload=body,
            )
        return TurnTrace(idx, step.kind, "passed", f"turn role={step.role}", payload=body)

    def _run_artifact(self, idx: int, step: ArtifactAssertStep) -> TurnTrace:
        if self.dry_run:
            return TurnTrace(idx, step.kind, "skipped", "dry-run: artifact")
        resolved = ArtifactAssertStep(
            artifact_type=step.artifact_type,
            target=self._interpolate_str(step.target),
            criteria={k: self._interpolate(v) for k, v in step.criteria.items()},
        )
        result = self._artifact_registry.check(resolved)
        return TurnTrace(
            idx,
            step.kind,
            "passed" if result.passed else "failed",
            result.summary,
            payload=result.details,
        )

    def _interpolate_str(self, value: str) -> str:
        out = value
        for key, val in self.variables.items():
            out = out.replace(f"${{{key}}}", str(val))
        return out

    def _interpolate(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._interpolate_str(value)
        if isinstance(value, dict):
            return {k: self._interpolate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._interpolate(v) for v in value]
        return value


def _extract_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.replace("body.", "", 1).split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current
