"""Tests for nlp2env TestTOON adapter and scenario runner."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from testql.adapters.nlp2env import Nlp2EnvAdapter
from testql.base import StepStatus
from testql.nlp2env.mcp_client import mcp_available
from testql.nlp2env.runner import Nlp2EnvRunner
from testql.nlp2env.scenarios import load_scenarios, scenario_count


INLINE_SAMPLE = """\
# SCENARIO: smtp-inline-fixture
# TYPE: nlp2env
# VERSION: 1.0

CONFIG[1]{key, value}:
  password_env, SMTP_PASSWORD

PROMPTS[2]{id, lang, source, nl, tool, after, assert_configured}:
  gmail-basic, -, inline, Gmail SMTP setup, nlp2env_set_email, -, false
  status-check, -, inline, Check SMTP status, nlp2env_email_status, gmail-basic, true

PROMPT_FIELDS[5]{prompt_id, key, value}:
  gmail-basic, host, smtp.gmail.com
  gmail-basic, user, jan@firma.pl
  gmail-basic, port, 587
  gmail-basic, from_addr, jan@firma.pl
  gmail-basic, password_env, SMTP_PASSWORD

ASSERT_ENV[4]{prompt_id, expect}:
  gmail-basic, SMTP_HOST=smtp.gmail.com
  gmail-basic, SMTP_USER=jan@firma.pl
  status-check, SMTP_HOST=smtp.gmail.com
  status-check, SMTP_USER=jan@firma.pl
"""


class TestNlp2EnvAdapter:
    def test_detect_by_type_header(self):
        result = Nlp2EnvAdapter().detect(INLINE_SAMPLE)
        assert result.matches
        assert result.confidence >= 0.9

    def test_detect_by_sections(self):
        text = "PROMPTS[1]{id}:\n  x\nASSERT_ENV[1]{prompt_id, expect}:\n  x, SMTP_HOST=1\n"
        result = Nlp2EnvAdapter().detect(text)
        assert result.matches

    def test_parse_sets_config(self):
        plan = Nlp2EnvAdapter().parse(INLINE_SAMPLE)
        assert plan.metadata.type == "nlp2env"
        assert plan.config["nlp2env"]["scenario_count"] == 2
        assert plan.config["layers"]["nlp2env"] is True

    def test_validate_requires_prompts(self):
        plan = Nlp2EnvAdapter().parse("# SCENARIO: x\n# TYPE: nlp2env\n")
        issues = [i for i in Nlp2EnvAdapter().validate(plan) if i.severity == "error"]
        assert issues
        assert issues[0].code == "nlp2env.missing_prompts"

    def test_load_scenarios(self):
        scenarios = load_scenarios(INLINE_SAMPLE)
        assert [s.prompt_id for s in scenarios] == ["gmail-basic", "status-check"]
        assert scenarios[0].inline_arguments()["host"] == "smtp.gmail.com"
        assert scenarios[1].after == "gmail-basic"
        assert scenarios[1].assert_configured is True

    def test_scenario_count(self):
        assert scenario_count(INLINE_SAMPLE) == 2
        assert scenario_count("# TYPE: nlp2env\n") == 0


class TestNlp2EnvRunner:
    def test_dry_run(self, tmp_path: Path):
        scenario = tmp_path / "inline.testql.toon.yaml"
        scenario.write_text(INLINE_SAMPLE, encoding="utf-8")
        (tmp_path / ".env.example").write_text("SMTP_PASSWORD=e2e-test-secret-42\n", encoding="utf-8")

        result = Nlp2EnvRunner(example_dir=tmp_path, dry_run=True).run_file(scenario)
        assert result.ok
        assert len(result.steps) == 2
        assert all(s.status == StepStatus.PASSED for s in result.steps)

    @pytest.mark.skipif(not mcp_available(), reason="nlp2env-mcp not installed")
    def test_inline_mcp_e2e(self, tmp_path: Path, monkeypatch):
        scenario = tmp_path / "inline.testql.toon.yaml"
        scenario.write_text(INLINE_SAMPLE, encoding="utf-8")
        (tmp_path / ".env.example").write_text("SMTP_PASSWORD=e2e-test-secret-42\n", encoding="utf-8")
        monkeypatch.setenv("SMTP_PASSWORD", "e2e-test-secret-42")

        result = Nlp2EnvRunner(
            example_dir=tmp_path,
            workdir=tmp_path / "work",
            skip_llm=True,
        ).run_file(scenario)
        assert result.ok, result.errors
        assert result.passed == 2


@pytest.mark.skipif(
    not Path(os.getenv("NLP2ENV_INLINE_SCENARIO", "/home/tom/github/semcod/nlp2env/examples/write/smtp-email/smtp-email-inline.testql.toon.yaml")).is_file(),
    reason="nlp2env inline scenario file not found",
)
def test_real_inline_scenario_dry_run():
    path = Path(os.getenv(
        "NLP2ENV_INLINE_SCENARIO",
        "/home/tom/github/semcod/nlp2env/examples/write/smtp-email/smtp-email-inline.testql.toon.yaml",
    ))
    result = Nlp2EnvRunner(example_dir=path.parent, dry_run=True).run_file(path)
    assert result.ok
    assert len(result.steps) == 5
