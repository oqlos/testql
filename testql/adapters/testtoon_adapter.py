"""TestToonAdapter — wraps the existing TestTOON parser into the IR.

Phase 0 strategy: do **not** move parser logic. The current
`testql.interpreter._testtoon_parser` is already low-CC and fully tested; we
treat it as the source of truth and translate its `ToonScript` output into a
Unified `TestPlan` IR. This keeps backward compatibility absolute.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testql.interpreter._testtoon_parser import (
    ToonScript,
    ToonSection,
    parse_testtoon as _parse_testtoon,
    testtoon_to_iql,
)
from testql.ir import (
    ApiStep,
    Assertion,
    Capture,
    EncoderStep,
    GuiStep,
    NlStep,
    ScenarioMetadata,
    ShellStep,
    Step,
    TestPlan,
    UnitStep,
)

from .base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source


# ── Section → step translators ──────────────────────────────────────────────

def _config_to_dict(section: ToonSection) -> dict[str, Any]:
    return {row.get("key", ""): row.get("value") for row in section.rows if row.get("key")}


def _api_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        asserts: list[Assertion] = []
        status = row.get("status") or row.get("expect_status")
        if status is not None:
            asserts.append(Assertion(field="status", op="==", expected=status))
        ak, av = row.get("assert_key"), row.get("assert_value") or row.get("assert_val")
        if ak and av:
            asserts.append(Assertion(field=str(ak), op="==", expected=av))
        name = str(row.get("name", "")).strip() or None
        steps.append(ApiStep(
            name=name,
            method=str(row.get("method", "GET")).upper(),
            path=str(row.get("endpoint", "/")),
            expect_status=int(status) if isinstance(status, (int, str)) and str(status).isdigit() else None,
            asserts=asserts,
        ))
    return steps


def _navigate_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        wait_ms = row.get("wait_ms")
        steps.append(GuiStep(
            action="navigate",
            path=str(row.get("path", "/")),
            wait_ms=int(wait_ms) if wait_ms is not None else None,
        ))
    return steps


def _gui_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        wait_ms = row.get("wait_ms")
        action = str(row.get("action", "")).strip().lower() or "noop"
        selector = row.get("selector") or row.get("target")
        steps.append(GuiStep(
            action=action,
            selector=str(selector) if selector not in (None, "-") else None,
            value=row.get("value") if row.get("value") not in (None, "-") else None,
            wait_ms=int(wait_ms) if isinstance(wait_ms, int) else None,
        ))
    return steps


def _encoder_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        wait_ms = row.get("wait_ms")
        steps.append(EncoderStep(
            action=str(row.get("action", "")).lower(),
            target=row.get("target"),
            value=row.get("value"),
            wait_ms=int(wait_ms) if wait_ms is not None else None,
        ))
    return steps


def _assert_section_to_steps(section: ToonSection) -> list[Step]:
    """ASSERT section becomes a single synthetic step that carries the asserts."""
    asserts = [
        Assertion(
            field=str(row.get("field", "")),
            op=str(row.get("op", "==")),
            expected=row.get("expected"),
        )
        for row in section.rows
    ]
    if not asserts:
        return []
    return [Step(kind="assert", name="ASSERT", asserts=asserts)]


def _capture_section_apply(section: ToonSection, plan: TestPlan) -> None:
    """`CAPTURE[N]{step, var, from}` rows attach `Capture`s to existing plan steps.

    `step` matches `Step.name` if non-numeric; otherwise it is treated as a
    1-based index into `plan.steps`. Unresolved references are silently dropped
    (mirrors the orphan-assert behaviour of `_assert_section_to_steps`).
    """
    by_name = {s.name: s for s in plan.steps if s.name}
    for row in section.rows:
        target = str(row.get("step", "")).strip()
        var_name = str(row.get("var", "")).strip()
        from_path = str(row.get("from", "")).strip()
        if not (target and var_name and from_path):
            continue
        owner = _resolve_capture_target(target, by_name, plan.steps)
        if owner is not None:
            owner.captures.append(Capture(var_name=var_name, from_path=from_path))


def _resolve_capture_target(target: str, by_name: dict[str, Step],
                            steps: list[Step]) -> Step | None:
    if target in by_name:
        return by_name[target]
    if target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(steps):
            return steps[idx]
    return None


def _generic_section_to_steps(section: ToonSection) -> list[Step]:
    """Fallback for section types we don't yet model in the IR (FLOW, OQL, ...)."""
    steps: list[Step] = []
    for row in section.rows:
        steps.append(Step(kind=section.type.lower(), name=section.type, extra=dict(row)))
    return steps


def _shell_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        command = str(row.get("command") or row.get("cmd") or "").strip()
        if not command:
            continue
        step = ShellStep(command=command, cwd=row.get("cwd"))
        exit_code = row.get("exit_code")
        if exit_code is None:
            exit_code = row.get("expect_exit_code")
        if isinstance(exit_code, int):
            step.expect_exit_code = exit_code
        elif isinstance(exit_code, str) and exit_code.strip().lstrip("-").isdigit():
            step.expect_exit_code = int(exit_code)
        steps.append(step)
    return steps


def _unit_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        target = str(row.get("target") or row.get("test") or "").strip()
        if target:
            steps.append(UnitStep(target=target))
    return steps


def _log_section_to_steps(section: ToonSection) -> list[Step]:
    steps: list[Step] = []
    for row in section.rows:
        message = row.get("message") or row.get("text")
        if message is None:
            continue
        steps.append(NlStep(text=str(message)))
    return steps


_SECTION_TRANSLATORS = {
    "API": _api_section_to_steps,
    "NAVIGATE": _navigate_section_to_steps,
    "GUI": _gui_section_to_steps,
    "ENCODER": _encoder_section_to_steps,
    "ASSERT": _assert_section_to_steps,
    "SHELL": _shell_section_to_steps,
    "UNIT": _unit_section_to_steps,
    "LOG": _log_section_to_steps,
}


def _translate_section(section: ToonSection) -> tuple[list[Step], dict[str, Any]]:
    """Return (steps, config_delta) for a single ToonSection."""
    if section.type == "CONFIG":
        return [], _config_to_dict(section)
    translator = _SECTION_TRANSLATORS.get(section.type, _generic_section_to_steps)
    return translator(section), {}


def _toon_to_plan(toon: ToonScript) -> TestPlan:
    """Convert a parsed `ToonScript` into a Unified IR `TestPlan`."""
    md = ScenarioMetadata(
        name=toon.meta.get("scenario", ""),
        type=toon.meta.get("type", ""),
        version=toon.meta.get("version"),
        lang=toon.meta.get("lang"),
        extra={k: v for k, v in toon.meta.items() if k not in {"scenario", "type", "version", "lang"}},
    )
    plan = TestPlan(metadata=md)
    capture_sections: list[ToonSection] = []
    for section in toon.sections:
        if section.type == "CAPTURE":
            capture_sections.append(section)  # apply after all steps are loaded
            continue
        steps, cfg = _translate_section(section)
        plan.steps.extend(steps)
        plan.config.update(cfg)
    for section in capture_sections:
        _capture_section_apply(section, plan)
    return plan


# ── Renderer (IR → TestTOON) ────────────────────────────────────────────────

def _render_meta(md: ScenarioMetadata) -> list[str]:
    out: list[str] = []
    if md.name:
        out.append(f"# SCENARIO: {md.name}")
    if md.type:
        out.append(f"# TYPE: {md.type}")
    if md.version:
        out.append(f"# VERSION: {md.version}")
    if md.lang:
        out.append(f"# LANG: {md.lang}")
    return out


def _render_config(config: dict[str, Any]) -> list[str]:
    if not config:
        return []
    lines = [f"CONFIG[{len(config)}]" + "{key, value}:"]
    for k, v in config.items():
        lines.append(f"  {k}, {v}")
    return lines


def _render_api_steps(steps: list[ApiStep]) -> list[str]:
    if not steps:
        return []
    lines = [f"API[{len(steps)}]" + "{method, endpoint, status}:"]
    for s in steps:
        status = s.expect_status if s.expect_status is not None else "-"
        lines.append(f"  {s.method}, {s.path}, {status}")
    return lines


def _render_navigate_steps(steps: list[GuiStep]) -> list[str]:
    nav = [s for s in steps if s.action == "navigate"]
    if not nav:
        return []
    lines = [f"NAVIGATE[{len(nav)}]" + "{path, wait_ms}:"]
    for s in nav:
        wait = s.wait_ms if s.wait_ms is not None else "-"
        lines.append(f"  {s.path}, {wait}")
    return lines


def _render_encoder_steps(steps: list[EncoderStep]) -> list[str]:
    if not steps:
        return []
    lines = [f"ENCODER[{len(steps)}]" + "{action, target, value, wait_ms}:"]
    for s in steps:
        lines.append(
            f"  {s.action}, {s.target or '-'}, "
            f"{s.value if s.value is not None else '-'}, "
            f"{s.wait_ms if s.wait_ms is not None else '-'}"
        )
    return lines


_GUI_ACTION_COMMANDS = {
    "click": "GUI_CLICK",
    "input": "GUI_INPUT",
    "type": "GUI_INPUT",
    "assert_visible": "GUI_ASSERT_VISIBLE",
    "visible": "GUI_ASSERT_VISIBLE",
    "wait": "WAIT",
    "select": "GUI_SELECT",
    "hover": "GUI_HOVER",
    "scroll": "GUI_SCROLL",
}


def _toon_safe_selector(selector: str | None) -> str:
    """Render a CSS selector so the TOON parser treats it as a string.

    TOON (like YAML) parses bare ``[...]`` cell values as list literals, which
    mangles attribute selectors such as ``[data-testid='x']``. Prefixing the
    universal selector ``*`` is functionally equivalent but TOON-safe. Other
    forms (``#id``, ``.class``, ``tag[attr=...]``) are returned unchanged.
    """
    if selector is None:
        return "-"
    s = str(selector)
    if s.startswith("["):
        return "*" + s
    return s


def _render_gui_action_steps(steps: list[Step]) -> list[str]:
    """Render non-navigate GuiSteps as a FLOW section.

    Earlier versions emitted ``GUI[N]{...}`` which had no parser-side expander
    and surfaced as ``Unknown command: GUI`` at runtime. The TestTOON parser's
    ``_expand_flow`` is the canonical pathway for one-line GUI commands, so we
    use ``FLOW[N]{command, target, value}``.
    """
    actions = [s for s in steps if isinstance(s, GuiStep) and s.action != "navigate"]
    if not actions:
        return []
    lines = [f"FLOW[{len(actions)}]" + "{command, target, value}:"]
    for s in actions:
        action = (s.action or "").lower()
        cmd = _GUI_ACTION_COMMANDS.get(action, action.upper() or "GUI_NOOP")
        target = _toon_safe_selector(s.selector)
        value = s.value if s.value is not None else "-"
        lines.append(f"  {cmd}, {target}, {value}")
    return lines


def _render_shell_steps(steps: list[Step]) -> list[str]:
    shells = [s for s in steps if isinstance(s, ShellStep)]
    if not shells:
        return []
    lines = [f"SHELL[{len(shells)}]" + "{command, exit_code}:"]
    for s in shells:
        ec = s.expect_exit_code if s.expect_exit_code is not None else "-"
        lines.append(f"  {s.command}, {ec}")
    return lines


def _render_unit_steps(steps: list[Step]) -> list[str]:
    units = [s for s in steps if isinstance(s, UnitStep)]
    if not units:
        return []
    lines = [f"UNIT[{len(units)}]" + "{target}:"]
    for s in units:
        lines.append(f"  {s.target}")
    return lines


def _render_log_steps(steps: list[Step]) -> list[str]:
    logs = [s for s in steps if isinstance(s, NlStep)]
    if not logs:
        return []
    lines = [f"LOG[{len(logs)}]" + "{message}:"]
    for s in logs:
        text = s.text.replace("\n", " ").strip()
        lines.append(f"  {text}")
    return lines


def _render_assertions(steps: list[Step]) -> list[str]:
    asserts = [a for s in steps for a in s.asserts if s.kind == "assert"]
    if not asserts:
        return []
    lines = [f"ASSERT[{len(asserts)}]" + "{field, op, expected}:"]
    for a in asserts:
        lines.append(f"  {a.field}, {a.op}, {a.expected}")
    return lines


def _render_captures(steps: list[Step]) -> list[str]:
    """Emit a `CAPTURE[N]{step, var, from}` section for any step with captures.

    Uses the 1-based step index so round-trip is lossless even when the API
    renderer (which has fixed columns) doesn't emit step names.
    """
    rows: list[tuple[str, str, str]] = []
    for idx, step in enumerate(steps, start=1):
        for c in step.captures:
            rows.append((str(idx), c.var_name, c.from_path))
    if not rows:
        return []
    lines = [f"CAPTURE[{len(rows)}]" + "{step, var, from}:"]
    for step_ref, var, frm in rows:
        lines.append(f"  {step_ref}, {var}, {frm}")
    return lines


def _render_plan(plan: TestPlan) -> str:
    """Lossy renderer covering CONFIG / API / NAVIGATE / ENCODER / ASSERT.

    Phase 0 keeps this minimal — adapters that need richer round-trip can
    extend later phases. The current renderer is good enough for symmetric
    IR → TestTOON of the four canonical sections used in test fixtures.
    """
    parts: list[str] = []
    parts.extend(_render_meta(plan.metadata))
    if parts:
        parts.append("")
    parts.extend(_render_config(plan.config))
    api_steps = [s for s in plan.steps if isinstance(s, ApiStep)]
    parts.extend(_render_api_steps(api_steps))
    gui_steps = [s for s in plan.steps if isinstance(s, GuiStep)]
    parts.extend(_render_navigate_steps(gui_steps))
    parts.extend(_render_gui_action_steps(plan.steps))
    encoder_steps = [s for s in plan.steps if isinstance(s, EncoderStep)]
    parts.extend(_render_encoder_steps(encoder_steps))
    parts.extend(_render_shell_steps(plan.steps))
    parts.extend(_render_unit_steps(plan.steps))
    parts.extend(_render_log_steps(plan.steps))
    parts.extend(_render_assertions(plan.steps))
    parts.extend(_render_captures(plan.steps))
    return "\n".join(parts) + ("\n" if parts else "")


# ── Adapter ─────────────────────────────────────────────────────────────────

@dataclass
class TestToonAdapter(BaseDSLAdapter):
    """Adapter for the legacy `*.testql.toon.yaml` format (TestTOON)."""

    __test__ = False  # Not a pytest test class

    name: str = "testtoon"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".testql.toon.yaml",
        ".testql.toon.yml",
    ))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.95, reason=f"extension {ext}")
        # Heuristic: TestTOON sections look like `NAME[n]{cols}:`
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# SCENARIO:") or stripped.startswith("# TYPE:"):
                return DSLDetectionResult(matches=True, confidence=0.7, reason="metadata header")
            if "{" in stripped and stripped.endswith(":") and "}:" in stripped:
                return DSLDetectionResult(matches=True, confidence=0.6, reason="section header")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no TestTOON markers")

    def parse(self, source: SourceLike) -> TestPlan:
        text, filename = read_source(source)
        toon = _parse_testtoon(text, filename=filename)
        return _toon_to_plan(toon)

    def render(self, plan: TestPlan) -> str:
        return _render_plan(plan)


# Convenience module-level functions — useful for tests and ad-hoc callers.

def parse(source: SourceLike) -> TestPlan:
    return TestToonAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return TestToonAdapter().render(plan)


__all__ = [
    "TestToonAdapter",
    "parse",
    "render",
    # Re-exports of the underlying parser primitives, for backward-compat callers
    # that imported them from this module after the migration.
    "ToonScript",
    "ToonSection",
    "testtoon_to_iql",
]
