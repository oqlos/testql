"""Tests for conversation / nlp2dsl integration."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.nlp2dsl import Nlp2DslAdapter, Nlp2DslClient, Nlp2DslResponse
from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.artifacts.file_checker import FileArtifactChecker
from testql.conversation import ConversationRunner
from testql.generators.conversation_generator import ConversationGenerator, trace_from_export
from testql.generators.sources.conversation import ConversationTestSource
from testql.ir import ArtifactAssertStep, Capture, ConversationTurnStep, Nlp2DslStep, TestPlan
from testql.ir_runner.executors import assert_json as assert_json_executor
from testql.ir_runner.context import ExecutionContext
from testql.base import VariableStore
from testql.ir import Assertion, Step


CONVERSATION_SAMPLE = """\
# SCENARIO: send-invoice-with-attachment
# TYPE: conversation

CONFIG[2]{key, value}:
  nlp2dsl_base_url, http://localhost:8080
  mock_smtp_dir, testql-scenarios/artifacts/mock-inbox

CONTEXT[2]{key, value}:
  invoice_path, testql-scenarios/artifacts/user-files/faktura.pdf
  recipient, klient@example.com

NLP_DSL[2]{endpoint, payload, use_mock_llm}:
  chatstart, {}, false
  chatmessage, {"text": "Wyślij fakturę", "conversationId": "${conversationId}"}, true

CAPTURE[1]{step, var, from}:
  1, conversationId, conversationId

CONVERSATION[1]{role, message, expect_status}:
  user, Wyślij fakturę, incomplete

VALIDATE[1]{type, target, criteria}:
  email, testql-scenarios/artifacts/mock-inbox, count>=1
"""


ASSERT_JSON_SAMPLE = """\
# SCENARIO: assert-json-sample
# TYPE: conversation

NLP_DSL[1]{endpoint, payload}:
  chatstart, {}

ASSERT_JSON[1]{step, path, op, expected}:
  1, conversationId, ==, conv-1
"""


class TestAssertJsonSection:
    def test_assert_json_attached_to_step(self):
        plan = TestToonAdapter().parse(ASSERT_JSON_SAMPLE)
        nlp = [s for s in plan.steps if isinstance(s, Nlp2DslStep)]
        assert len(nlp) == 1
        assert nlp[0].asserts[0].field == "data.conversationId"
        assert nlp[0].asserts[0].expected == "conv-1"

    def test_assert_json_executor_uses_last_response(self):
        ctx = ExecutionContext(vars=VariableStore(), last_status=200, last_response={"status": "incomplete"})
        step = Step(kind="assert_json", name="ASSERT_JSON", asserts=[Assertion(field="data.status", op="==", expected="incomplete")])
        result = assert_json_executor.execute(step, ctx)
        assert result.status.value == "passed" or str(result.status) == "passed"


class TestConversationGenerator:
    def test_from_trace_builds_plan(self):
        trace = trace_from_export({
            "conversationId": "c1",
            "turns": [{"endpoint": "chatmessage", "body": {"text": "hello", "role": "user"}}],
            "dsl": {"steps": []},
        })
        plan = ConversationGenerator().from_trace(trace, name="from-history")
        assert plan.metadata.name == "from-history"
        assert any(isinstance(s, Nlp2DslStep) for s in plan.steps)
        assert any(isinstance(s, ConversationTurnStep) for s in plan.steps)


class TestConversationIRParse:
    def test_parse_conversation_sections(self):
        plan = TestToonAdapter().parse(CONVERSATION_SAMPLE)
        assert plan.metadata.type == "conversation"
        assert plan.config["context"]["recipient"] == "klient@example.com"
        nlp = [s for s in plan.steps if isinstance(s, Nlp2DslStep)]
        assert len(nlp) == 2
        assert nlp[0].endpoint == "chatstart"
        turns = [s for s in plan.steps if isinstance(s, ConversationTurnStep)]
        assert turns[0].expect_status == "incomplete"
        artifacts = [s for s in plan.steps if isinstance(s, ArtifactAssertStep)]
        assert artifacts[0].artifact_type == "email"

    def test_nlp2dsl_adapter_detects_conversation(self):
        result = Nlp2DslAdapter().detect(CONVERSATION_SAMPLE)
        assert result.matches

    def test_conversation_source_loads(self):
        plan = ConversationTestSource().load(CONVERSATION_SAMPLE)
        assert plan.config["layers"]["conversation"] is True


class TestConversationRunner:
    def test_dry_run_skips_http(self):
        plan = TestToonAdapter().parse(CONVERSATION_SAMPLE)
        result = ConversationRunner(dry_run=True).run(plan)
        assert result.passed is True
        assert all(t.status == "skipped" for t in result.turns if t.kind == "nlp2dsl")


class TestArtifactChecker:
    def test_file_hash(self, tmp_path: Path):
        target = tmp_path / "x.txt"
        target.write_text("hello", encoding="utf-8")
        import hashlib
        digest = hashlib.sha256(b"hello").hexdigest()
        step = ArtifactAssertStep(
            artifact_type="file",
            target=str(target),
            criteria={"sha256": digest},
        )
        result = FileArtifactChecker().check(step)
        assert result.passed is True


class FakeClient(Nlp2DslClient):
    def chatstart(self, payload=None):
        return Nlp2DslResponse(200, {"conversationId": "conv-1"})

    def chatmessage(self, payload):
        if payload.get("llmContext"):
            return Nlp2DslResponse(200, {"status": "complete", "dsl": {"steps": []}})
        return Nlp2DslResponse(200, {"status": "incomplete", "missing": ["attachment"]})


def test_runner_with_fake_client():
    from testql.ir import Capture, Nlp2DslStep, TestPlan

    plan = TestPlan(steps=[
        Nlp2DslStep(
            endpoint="chatstart",
            payload={},
            captures=[Capture(var_name="conversationId", from_path="conversationId")],
        ),
    ])
    runner = ConversationRunner(client=FakeClient())
    result = runner.run(plan)
    assert result.passed is True
    assert runner.variables.get("conversationId") == "conv-1"
