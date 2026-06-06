"""Optional live-LLM conversation tests (skipped unless TESTQL_LIVE_LLM=1)."""

from __future__ import annotations

import os

import httpx
import pytest

from testql.adapters.nlp2dsl import LiveLLMProvider, live_llm_enabled, resolve_llm_provider
from testql.adapters.nlp2dsl.mock_llm import MockLLMProvider
from testql.conversation import ConversationRunner


pytestmark = pytest.mark.live_llm


class TestLLMProviderResolution:
    def test_defaults_to_mock(self, monkeypatch):
        monkeypatch.delenv("TESTQL_LIVE_LLM", raising=False)
        provider = resolve_llm_provider(live=False)
        assert isinstance(provider, MockLLMProvider)

    def test_live_flag_selects_live_provider(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        provider = resolve_llm_provider(live=True)
        assert isinstance(provider, LiveLLMProvider)

    def test_live_without_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            resolve_llm_provider(live=True)


class TestLiveLLMParsing:
    def test_parse_json_object_strips_fence(self):
        raw = '```json\n{"attachmentPath": "/tmp/x.pdf"}\n```'
        parsed = LiveLLMProvider._parse_json_object(raw)
        assert parsed["attachmentPath"] == "/tmp/x.pdf"


@pytest.mark.live_llm
def test_live_llm_reply_for_real_api():
    if not os.environ.get("OPENROUTER_API_KEY") and not os.environ.get("LLM_API_KEY"):
        pytest.skip("no LLM API key")
    provider = LiveLLMProvider.from_env()
    reply = provider.reply_for(
        "conv-live-1",
        missing=["attachment"],
        context={"recipient": "test@example.com", "files": ["faktura.pdf"]},
    )
    assert isinstance(reply, dict)
    assert reply


@pytest.mark.live_llm
def test_conversation_runner_with_live_llm_smoke():
    nlp2dsl_url = os.environ.get("NLP2DSL_URL", "http://localhost:8080")
    try:
        httpx.get(f"{nlp2dsl_url.rstrip('/')}/health", timeout=2.0)
    except Exception:
        pytest.skip(f"nlp2dsl not reachable at {nlp2dsl_url}")

    if not live_llm_enabled():
        pytest.skip("TESTQL_LIVE_LLM not enabled")

    from testql.ir import Capture, Nlp2DslStep, TestPlan

    plan = TestPlan(steps=[
        Nlp2DslStep(endpoint="chatstart", payload={"userId": "live-test"}, captures=[
            Capture(var_name="conversationId", from_path="conversationId"),
        ]),
        Nlp2DslStep(
            endpoint="chatmessage",
            payload={"conversationId": "${conversationId}", "text": "ping"},
            mock_llm={},
        ),
    ])
    runner = ConversationRunner(api_url=nlp2dsl_url, live_llm=True)
    result = runner.run(plan)
    assert any(t.kind == "nlp2dsl" for t in result.turns)
