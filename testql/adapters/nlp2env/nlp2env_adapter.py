"""Nlp2EnvAdapter — parse/validate TYPE: nlp2env TestTOON scenarios."""

from __future__ import annotations

from dataclasses import dataclass, field

from testql.adapters.base import BaseDSLAdapter, DSLDetectionResult, SourceLike, ValidationIssue, read_source
from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.ir import TestPlan
from testql.nlp2env.scenarios import load_scenarios, scenario_count


_NLP2ENV_TYPES = frozenset({"nlp2env", "env", "dotenv"})


@dataclass
class Nlp2EnvAdapter(BaseDSLAdapter):
    """Wraps TestTOON parsing for nlp2env prompt → .env e2e scenarios."""

    name: str = "nlp2env"
    file_extensions: tuple[str, ...] = field(
        default_factory=lambda: (".nlp2env.testql.toon.yaml",)
    )
    _toon: TestToonAdapter = field(default_factory=TestToonAdapter, repr=False)

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        if any(filename.lower().endswith(ext) for ext in self.file_extensions):
            return DSLDetectionResult(matches=True, confidence=0.95, reason="nlp2env extension")
        if "# TYPE: nlp2env" in text:
            return DSLDetectionResult(matches=True, confidence=0.95, reason="nlp2env metadata")
        plan = self._toon.parse(text)
        if plan.metadata.type.lower() in _NLP2ENV_TYPES:
            return DSLDetectionResult(matches=True, confidence=0.9, reason="nlp2env type")
        if "PROMPTS[" in text and "ASSERT_ENV[" in text:
            return DSLDetectionResult(matches=True, confidence=0.75, reason="nlp2env sections")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="not an nlp2env scenario")

    def parse(self, source: SourceLike) -> TestPlan:
        plan = self._toon.parse(source)
        text, filename = read_source(source)
        try:
            scenarios = load_scenarios(text, source_name=filename)
        except ValueError:
            scenarios = []
        plan.config["nlp2env"] = {
            "scenario_count": len(scenarios),
            "prompt_ids": [s.prompt_id for s in scenarios],
        }
        plan.config.setdefault("layers", {})
        if isinstance(plan.config["layers"], dict):
            plan.config["layers"]["nlp2env"] = True
        return plan

    def render(self, plan: TestPlan) -> str:
        return self._toon.render(plan)

    def validate(self, plan: TestPlan) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        count = plan.config.get("nlp2env", {}).get("scenario_count", 0)
        if count == 0:
            issues.append(ValidationIssue(
                severity="error",
                message="brak sekcji PROMPTS w scenariuszu nlp2env",
                location="PROMPTS",
                code="nlp2env.missing_prompts",
            ))
        return issues


def scenario_count_from_source(source: SourceLike) -> int:
    text, filename = read_source(source)
    return scenario_count(text, source_name=filename)
