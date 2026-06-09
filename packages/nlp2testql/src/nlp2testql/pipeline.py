"""End-to-end NL → TestQL generation pipeline."""

from __future__ import annotations

import re
from pathlib import Path

from nlp2testql.models import GenerateResult, Plan
from nlp2testql.validate import validate_testql


def plan_with_rules(prompt: str) -> Plan:
    plan = Plan()
    name_match = re.search(r"(?:name|project|app)\s+(\w+)", prompt, re.IGNORECASE)
    if name_match:
        plan.project_name = name_match.group(1).lower()
    return plan


def generate_spec(
    prompt: str,
    *,
    out_path: str | Path | None = None,
    use_llm: bool = False,
    model: str = "openrouter/qwen/qwen3-coder-next",
    validate: bool = False,
) -> GenerateResult:
    """Plan and render TestQL LESS from natural language."""
    try:
        plan = plan_with_rules(prompt)
        testql_content = plan.to_testql_less()
    except Exception as exc:
        return GenerateResult(
            ok=False,
            testql="",
            plan=Plan(planner="failed"),
            error=str(exc),
        )

    validation = validate_testql(testql_content) if validate else None

    output_path = None
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(testql_content, encoding="utf-8")
        output_path = str(path.resolve())

    ok = True
    if validation is not None and not validation.get("ok", False):
        ok = False

    return GenerateResult(
        ok=ok,
        testql=testql_content,
        plan=plan,
        validation=validation,
        output_path=output_path,
    )
