"""Generate conversation TestPlans from nlp2dsl export_trace payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from testql.ir import Capture, ConversationTurnStep, Nlp2DslStep, ScenarioMetadata, TestPlan


@dataclass
class ConversationGenerator:
    """Build a declarative TestPlan from a runtime conversation trace."""

    def from_trace(self, trace: dict[str, Any], *, name: str = "generated-conversation") -> TestPlan:
        plan = TestPlan(
            metadata=ScenarioMetadata(name=name, type="conversation"),
            config={"nlp2dsl_base_url": trace.get("baseUrl", "${NLP2DSL_URL:-http://localhost:8080}")},
        )
        plan.steps.append(Nlp2DslStep(
            endpoint="chatstart",
            payload={"userId": trace.get("userId", "test-user")},
            captures=[Capture(var_name="conversationId", from_path="conversationId")],
            name="NLP_DSL",
        ))

        for turn in trace.get("turns") or []:
            endpoint = str(turn.get("endpoint", "chatmessage"))
            body = dict(turn.get("body") or {})
            if endpoint == "chatmessage" and body.get("text"):
                plan.steps.append(ConversationTurnStep(
                    role=str(body.get("role", "user")),
                    message=str(body.get("text", "")),
                    expect_status=body.get("expect_status") or turn.get("expect_status"),
                    name="CONVERSATION",
                ))
            plan.steps.append(Nlp2DslStep(
                endpoint=endpoint,
                payload=body,
                name="NLP_DSL",
            ))

        if trace.get("dsl"):
            plan.steps.append(Nlp2DslStep(
                endpoint="runworkflow",
                payload={"conversationId": trace.get("conversationId", "${conversationId}"), "dsl": trace["dsl"]},
                name="NLP_DSL",
            ))
        return plan

    def render_toon(self, plan: TestPlan) -> str:
        from testql.adapters.testtoon_adapter import TestToonAdapter
        return TestToonAdapter().render(plan)


def trace_from_export(export: dict[str, Any]) -> dict[str, Any]:
    """Normalise ``ConversationTestClient.export_trace()`` output for generation."""
    turns = []
    for item in export.get("turns") or []:
        turns.append({
            "endpoint": item.get("endpoint", "chatmessage"),
            "body": item.get("body") or {},
        })
    return {
        "conversationId": export.get("conversationId"),
        "userId": export.get("userId", "test-user"),
        "dsl": export.get("dsl"),
        "turns": turns,
    }
