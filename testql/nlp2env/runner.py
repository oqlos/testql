"""Run nlp2env TestTOON scenarios via MCP (+ optional LLM)."""

from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from testql.base import ScriptResult, StepResult, StepStatus
from testql.nlp2env.llm import resolve_llm_backend, translate_nl_to_mcp
from testql.nlp2env.mcp_client import assert_ok, mcp_call
from testql.nlp2env.scenarios import PromptScenario, load_scenarios_file


@dataclass
class Nlp2EnvRunner:
    workdir: Path | None = None
    example_dir: Path | None = None
    dry_run: bool = False
    skip_llm: bool = False
    only_llm: bool = False
    force_ollama: bool = False

    def run_file(self, path: Path | str) -> ScriptResult:
        from testql.adapters.nlp2env import Nlp2EnvAdapter

        started = time.perf_counter()
        scenario_path = Path(path).resolve()
        source = scenario_path.name
        adapter = Nlp2EnvAdapter()
        plan = adapter.parse(scenario_path)
        issues = [i for i in adapter.validate(plan) if i.severity == "error"]
        if issues:
            return ScriptResult(
                source=source,
                ok=False,
                errors=[i.message for i in issues],
                duration_ms=(time.perf_counter() - started) * 1000,
            )

        example = self.example_dir or scenario_path.parent
        work_root = self.workdir or (example / "workdir-testql")
        scenarios = load_scenarios_file(scenario_path)
        scenarios = self._filter_scenarios(scenarios)

        if self.dry_run:
            steps = [
                StepResult(
                    name=s.prompt_id,
                    status=StepStatus.PASSED,
                    message=f"dry-run source={s.source}",
                )
                for s in scenarios
            ]
            return ScriptResult(
                source=source,
                ok=True,
                steps=steps,
                duration_ms=(time.perf_counter() - started) * 1000,
            )

        backend, model = resolve_llm_backend()
        if self.force_ollama and backend == "ollama":
            pass
        elif self.force_ollama and backend != "ollama":
            return ScriptResult(
                source=source,
                ok=False,
                errors=["NLP2ENV_FORCE_OLLAMA=1 ale Ollama niedostępna"],
                duration_ms=(time.perf_counter() - started) * 1000,
            )

        env_by_id: dict[str, Path] = {}
        steps: list[StepResult] = []
        errors: list[str] = []

        for scenario in scenarios:
            step_started = time.perf_counter()
            try:
                reuse = env_by_id.get(scenario.after) if scenario.after else None
                env_file = self._prepare_env(work_root, example, scenario.prompt_id, reuse)
                detail = self._run_scenario(scenario, env_file=env_file, backend=backend, model=model)
                env_by_id[scenario.prompt_id] = env_file
                steps.append(StepResult(
                    name=scenario.prompt_id,
                    status=StepStatus.PASSED,
                    message=detail,
                    duration_ms=(time.perf_counter() - step_started) * 1000,
                ))
            except Exception as exc:
                msg = str(exc)
                errors.append(f"[{scenario.prompt_id}] {msg}")
                steps.append(StepResult(
                    name=scenario.prompt_id,
                    status=StepStatus.FAILED,
                    message=msg,
                    duration_ms=(time.perf_counter() - step_started) * 1000,
                ))

        ok = not errors and all(s.status == StepStatus.PASSED for s in steps)
        return ScriptResult(
            source=source,
            ok=ok,
            steps=steps,
            errors=errors,
            duration_ms=(time.perf_counter() - started) * 1000,
        )

    def _filter_scenarios(self, scenarios: list[PromptScenario]) -> list[PromptScenario]:
        out: list[PromptScenario] = []
        for scenario in scenarios:
            if self.skip_llm and scenario.source == "llm":
                continue
            if self.only_llm and scenario.source != "llm":
                continue
            out.append(scenario)
        return out

    def _prepare_env(
        self,
        workdir: Path,
        example: Path,
        prompt_id: str,
        reuse: Path | None,
    ) -> Path:
        target = workdir / prompt_id
        target.mkdir(parents=True, exist_ok=True)
        env_file = target / ".env"
        if reuse and reuse.is_file():
            shutil.copy2(reuse, env_file)
            return env_file
        template = example / ".env.example"
        if template.is_file():
            shutil.copy2(template, env_file)
        else:
            env_file.write_text("", encoding="utf-8")
        return env_file

    def _verify_env(self, env_file: Path, scenario: PromptScenario) -> None:
        text = env_file.read_text(encoding="utf-8")
        missing = [needle for needle in scenario.expects if needle not in text]
        if missing:
            raise AssertionError(f"brak w .env: {missing}")
        if scenario.assert_configured:
            status = assert_ok(
                mcp_call("nlp2env_email_status", env_file=str(env_file)),
                "email_status",
            )
            if not status["email_status"]["configured"]:
                raise AssertionError(f"email_status not configured: {status['email_status']}")

    def _run_scenario(
        self,
        scenario: PromptScenario,
        *,
        env_file: Path,
        backend: str,
        model: str,
    ) -> str:
        if scenario.source == "llm":
            if backend == "none":
                raise RuntimeError("source=llm ale brak OpenRouter/Ollama")
            tool, args = translate_nl_to_mcp(scenario.nl, backend, model)
        else:
            tool = scenario.tool
            args = scenario.inline_arguments()
            if not tool or tool == "-":
                raise RuntimeError("brak tool= dla source=inline")

        if tool == "nlp2env_set_email":
            out = assert_ok(mcp_call(tool, args, env_file=str(env_file)), tool)
            if not out.get("email_status", {}).get("configured"):
                raise AssertionError("set_email OK ale profile incomplete")
        elif tool == "nlp2env_email_status":
            out = assert_ok(mcp_call(tool, args, env_file=str(env_file)), tool)
            if scenario.assert_configured and not out["email_status"]["configured"]:
                raise AssertionError("email_status configured=false")
        elif tool == "nlp2env_list":
            assert_ok(mcp_call(tool, args, env_file=str(env_file)), tool)
        else:
            assert_ok(mcp_call(tool, args, env_file=str(env_file)), tool)

        self._verify_env(env_file, scenario)
        return f"verified {len(scenario.expects)} expect lines"


def run_nlp2env_file(path: Path | str, **kwargs) -> ScriptResult:
    return Nlp2EnvRunner(**kwargs).run_file(path)


def is_nlp2env_scenario_text(text: str) -> bool:
    from testql.adapters.nlp2env import Nlp2EnvAdapter

    return Nlp2EnvAdapter().detect(text).matches
