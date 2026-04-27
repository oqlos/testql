from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from testql.ir import (
    ApiStep,
    Assertion,
    Capture,
    EncoderStep,
    GraphqlStep,
    GuiStep,
    NlStep,
    ScenarioMetadata,
    ShellStep,
    SqlStep,
    Step,
    TestPlan,
    UnitStep,
)

from .base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source


_OPERATOR_ALIASES = {
    "eq": "==",
    "equals": "==",
    "is": "==",
    "ne": "!=",
    "not": "!=",
    "not_equals": "!=",
    "lt": "<",
    "lte": "<=",
    "le": "<=",
    "gt": ">",
    "gte": ">=",
    "ge": ">=",
    "contains": "contains",
    "matches": "matches",
    "in": "in",
    "not in": "not in",
}

_FIELD_ALIASES = {
    "exit_code": "returncode",
    "status_code": "status",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _parse_wait_ms(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text.endswith("ms"):
        return int(float(text[:-2].strip()))
    if text.endswith("s"):
        return int(float(text[:-1].strip()) * 1000)
    return int(float(text))


def _split_request(value: Any) -> tuple[str, str]:
    if isinstance(value, str):
        parts = value.strip().split(maxsplit=1)
        if len(parts) == 2 and parts[0].upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            return parts[0].upper(), parts[1]
        return "GET", value.strip()
    data = _as_dict(value)
    method = str(data.get("method", "GET")).upper()
    path = data.get("path") or data.get("url") or data.get("endpoint") or "/"
    return method, str(path)


def _normalise_capture_path(path: Any) -> str:
    text = str(path).strip()
    return text.removeprefix("response.").removeprefix("payload.")


def _captures_from(value: Any) -> list[Capture]:
    data = _as_dict(value)
    return [Capture(var_name=str(var), from_path=_normalise_capture_path(path)) for var, path in data.items()]


def _assertion_from_field(field: str, value: Any) -> list[Assertion]:
    field = _FIELD_ALIASES.get(field, field)
    if isinstance(value, dict):
        assertions: list[Assertion] = []
        for op, expected in value.items():
            op_text = _OPERATOR_ALIASES.get(str(op).strip(), str(op).strip())
            assertions.append(Assertion(field=field, op=op_text, expected=expected))
        return assertions
    return [Assertion(field=field, op="==", expected=value)]


def _assertions_from_expect(expect: Any) -> list[Assertion]:
    if expect is None:
        return []
    if isinstance(expect, list):
        assertions: list[Assertion] = []
        for item in expect:
            assertions.extend(_assertions_from_expect(item))
        return assertions
    if not isinstance(expect, dict):
        return []
    assertions: list[Assertion] = []
    for field, value in expect.items():
        if field == "json" and isinstance(value, dict):
            for path, expected in value.items():
                assertions.extend(_assertion_from_field(str(path), expected))
            continue
        assertions.extend(_assertion_from_field(str(field), value))
    return assertions


def _step_common(step: Step, data: dict[str, Any]) -> Step:
    if "name" in data:
        step.name = str(data["name"])
    step.asserts.extend(_assertions_from_expect(data.get("expect")))
    step.captures.extend(_captures_from(data.get("capture")))
    if "wait" in data:
        step.wait_ms = _parse_wait_ms(data.get("wait"))
    using = data.get("using")
    if using is not None:
        step.extra["using"] = using
    for key in ("retry", "timeout", "continue_on_error", "background"):
        if key in data:
            step.extra[key] = data[key]
    return step


def _api_step(data: dict[str, Any]) -> ApiStep:
    method, path = _split_request(data.get("request"))
    request_data = _as_dict(data.get("request"))
    step = ApiStep(
        method=method,
        path=path,
        body=request_data.get("body") or data.get("body"),
        headers=request_data.get("headers") or data.get("headers") or {},
    )
    status = request_data.get("status") or request_data.get("expected_status")
    if status is None:
        expect = _as_dict(data.get("expect"))
        status = expect.get("status")
    if isinstance(status, int) or (isinstance(status, str) and status.isdigit()):
        step.expect_status = int(status)
    return _step_common(step, data)


def _gui_step(data: dict[str, Any]) -> GuiStep:
    if "open" in data:
        step = GuiStep(action="navigate", path=str(data["open"]))
    elif "click" in data:
        step = GuiStep(action="click", selector=str(data["click"]))
    elif "input" in data:
        step = GuiStep(action="input", selector=str(data["input"]), value=data.get("value"))
    elif "select" in data:
        step = GuiStep(action="select", selector=str(data["select"]), value=data.get("value"))
    elif "screenshot" in data:
        step = GuiStep(action="screenshot", path=str(data["screenshot"]))
    else:
        expect = _as_dict(data.get("expect"))
        if "visible" in expect:
            step = GuiStep(action="assert_visible", selector=str(expect["visible"]))
        elif "text" in expect and isinstance(expect["text"], dict):
            text = expect["text"]
            step = GuiStep(action="assert_text", selector=str(text.get("selector", "")), value=text.get("equals"))
        else:
            step = GuiStep(action="noop")
    return _step_common(step, data)


def _encoder_step(data: dict[str, Any]) -> EncoderStep:
    if "encoder" in data and isinstance(data["encoder"], dict):
        enc = data["encoder"]
        raw_action = enc.get("action") or enc.get("power") or enc.get("status") or "status"
        # YAML converts 'on' to True boolean - convert back to "on"
        if isinstance(raw_action, bool):
            action = "on" if raw_action else "off"
        else:
            action = str(raw_action)
        return _step_common(EncoderStep(action=action, target=enc.get("target"), value=enc.get("value")), data)
    for key, action in (("power", None), ("focus", "focus"), ("scroll", "scroll"), ("status", "status")):
        if key in data:
            value = data[key]
            return _step_common(EncoderStep(action=str(value) if action is None else action, target=str(value) if key == "focus" else None, value=value if key == "scroll" else None), data)
    return _step_common(EncoderStep(action="click", target=data.get("click")), data)


def _shell_step(data: dict[str, Any]) -> ShellStep:
    expect = _as_dict(data.get("expect"))
    exit_code = expect.get("exit_code", expect.get("returncode"))
    step = ShellStep(command=str(data.get("run") or data.get("shell") or ""), cwd=data.get("cwd"))
    if isinstance(exit_code, int) or (isinstance(exit_code, str) and exit_code.isdigit()):
        step.expect_exit_code = int(exit_code)
    return _step_common(step, data)


def _unit_step(data: dict[str, Any]) -> UnitStep:
    value = data.get("unit") or data.get("test") or data.get("call") or data.get("import") or data.get("eval") or ""
    return _step_common(UnitStep(target=str(value)), data)


def _typed_step(item: Any) -> Step:
    if isinstance(item, str):
        return NlStep(text=item, name=item[:80])
    data = _as_dict(item)
    
    step_type = _detect_step_type(data)
    return _create_step_by_type(step_type, data)


def _detect_step_type(data: dict[str, Any]) -> str:
    """Detect the type of step from data keys."""
    if "request" in data:
        return "api"
    if _is_gui_step(data):
        return "gui"
    if "run" in data or "shell" in data:
        return "shell"
    if _is_encoder_step(data):
        return "encoder"
    if _is_unit_step(data):
        return "unit"
    if "sql" in data or "query" in data:
        return "sql"
    if "graphql" in data:
        return "graphql"
    if "log" in data:
        return "nl"
    if "expect" in data:
        return "gui"
    return "generic"


def _is_gui_step(data: dict[str, Any]) -> bool:
    """Check if data represents a GUI step."""
    gui_keys = ("open", "input", "select", "screenshot")
    if any(key in data for key in gui_keys):
        return True
    if "click" in data and data.get("using") != "encoder":
        return True
    return False


def _is_encoder_step(data: dict[str, Any]) -> bool:
    """Check if data represents an encoder step."""
    encoder_keys = ("encoder", "power", "focus", "scroll", "status")
    if any(key in data for key in encoder_keys):
        return True
    if data.get("using") == "encoder":
        return True
    return False


def _is_unit_step(data: dict[str, Any]) -> bool:
    """Check if data represents a unit step."""
    unit_keys = ("unit", "test", "call", "import", "eval")
    return any(key in data for key in unit_keys)


def _create_step_by_type(step_type: str, data: dict[str, Any]) -> Step:
    """Create a Step object based on detected type."""
    creators = {
        "api": _api_step,
        "gui": _gui_step,
        "shell": _shell_step,
        "encoder": _encoder_step,
        "unit": _unit_step,
        "sql": _create_sql_step,
        "graphql": _create_graphql_step,
        "nl": _create_nl_step,
        "generic": _create_generic_step,
    }
    creator = creators.get(step_type, _create_generic_step)
    return creator(data)


def _create_sql_step(data: dict[str, Any]) -> SqlStep:
    return _step_common(SqlStep(query=str(data.get("sql") or data.get("query") or ""), dialect=data.get("dialect")), data)


def _create_graphql_step(data: dict[str, Any]) -> GraphqlStep:
    graphql = _as_dict(data.get("graphql"))
    return _step_common(GraphqlStep(operation=str(graphql.get("operation", "query")), body=str(graphql.get("body", "")), variables=graphql.get("variables") or {}, endpoint=graphql.get("endpoint")), data)


def _create_nl_step(data: dict[str, Any]) -> NlStep:
    return NlStep(text=str(data["log"]), name=str(data["log"])[:80])


def _create_generic_step(data: dict[str, Any]) -> Step:
    return Step(kind="generic", name=str(data.get("name", "step")), extra=dict(data))


def _metadata_from(data: dict[str, Any]) -> ScenarioMetadata:
    return ScenarioMetadata(
        name=str(data.get("scenario") or data.get("name") or ""),
        type=str(data.get("type") or "mixed"),
        version=str(data["version"]) if data.get("version") is not None else None,
        lang=data.get("lang"),
        tags=[str(tag) for tag in _as_list(data.get("tags"))],
        extra={str(k): str(v) for k, v in _as_dict(data.get("metadata")).items()},
    )


def _config_from(data: dict[str, Any]) -> dict[str, Any]:
    config: dict[str, Any] = {}
    config.update(_as_dict(data.get("vars")))
    config.update(_as_dict(data.get("config")))
    targets = _as_dict(data.get("targets"))
    if targets:
        config["targets"] = targets
    for target_name, target_data in targets.items():
        if not isinstance(target_data, dict):
            continue
        for key, value in target_data.items():
            config[f"{target_name}.{key}"] = value
            if key == "base_url" and "base_url" not in config:
                config["base_url"] = value
    return config


def _plan_from_yaml(data: dict[str, Any]) -> TestPlan:
    plan = TestPlan(metadata=_metadata_from(data), config=_config_from(data))
    for phase in ("setup", "steps", "cleanup"):
        for item in _as_list(data.get(phase)):
            step = _typed_step(item)
            if phase != "steps":
                step.extra["phase"] = phase
            plan.steps.append(step)
    return plan


def _render_step(step: Step) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if step.name:
        data["name"] = step.name
    
    # Type-specific rendering
    if isinstance(step, ApiStep):
        data.update(_render_api_step(step))
    elif isinstance(step, GuiStep):
        data.update(_render_gui_step(step))
    elif isinstance(step, ShellStep):
        data.update(_render_shell_step(step))
    elif isinstance(step, EncoderStep):
        data.update(_render_encoder_step(step))
    elif isinstance(step, UnitStep):
        data.update(_render_unit_step(step))
    elif isinstance(step, SqlStep):
        data.update(_render_sql_step(step))
    elif isinstance(step, GraphqlStep):
        data.update(_render_graphql_step(step))
    elif isinstance(step, NlStep):
        data.update(_render_nl_step(step))
    else:
        data.update(step.extra)
    
    # Common step attributes
    _add_common_step_attributes(data, step)
    return data


def _render_api_step(step: ApiStep) -> dict[str, Any]:
    data = {"request": {"method": step.method, "path": step.path}}
    if step.body is not None:
        data["request"]["body"] = step.body
    if step.headers:
        data["request"]["headers"] = step.headers
    if step.expect_status is not None:
        data["expect"] = {"status": step.expect_status}
    return data


def _render_gui_step(step: GuiStep) -> dict[str, Any]:
    if step.action == "navigate":
        return {"open": step.path}
    elif step.action in {"click", "input", "select"}:
        data = {step.action: step.selector}
        if step.value is not None:
            data["value"] = step.value
        return data
    else:
        return {"gui": {"action": step.action, "selector": step.selector, "path": step.path, "value": step.value}}


def _render_shell_step(step: ShellStep) -> dict[str, Any]:
    data = {"run": step.command}
    if step.cwd:
        data["cwd"] = step.cwd
    if step.expect_exit_code is not None:
        data["expect"] = {"exit_code": step.expect_exit_code}
    return data


def _render_encoder_step(step: EncoderStep) -> dict[str, Any]:
    data = {"encoder": {"action": step.action}}
    if step.target is not None:
        data["encoder"]["target"] = step.target
    if step.value is not None:
        data["encoder"]["value"] = step.value
    return data


def _render_unit_step(step: UnitStep) -> dict[str, Any]:
    return {"unit": step.target}


def _render_sql_step(step: SqlStep) -> dict[str, Any]:
    return {"sql": step.query}


def _render_graphql_step(step: GraphqlStep) -> dict[str, Any]:
    return {"graphql": {"operation": step.operation, "body": step.body}}


def _render_nl_step(step: NlStep) -> dict[str, Any]:
    return {"log": step.text}


def _add_common_step_attributes(data: dict[str, Any], step: Step) -> None:
    """Add common step attributes like assertions, captures, wait."""
    if step.asserts and "expect" not in data:
        data["expect"] = {a.field: {_reverse_operator(a.op): a.expected} for a in step.asserts}
    if step.captures:
        data["capture"] = {c.var_name: c.from_path for c in step.captures}
    if step.wait_ms is not None:
        data["wait"] = f"{step.wait_ms}ms"


def _reverse_operator(op: str) -> str:
    return {"==": "equals", "!=": "not_equals", "<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}.get(op, op)


@dataclass
class ScenarioYamlAdapter(BaseDSLAdapter):
    name: str = "scenario_yaml"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".testql.yaml",
        ".testql.yml",
        ".scenario.yaml",
        ".scenario.yml",
    ))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.93, reason=f"extension {ext}")
        stripped = text.lstrip()
        if re.search(r"(?m)^(scenario|name):\s*.+", stripped) and re.search(r"(?m)^steps:\s*", stripped):
            return DSLDetectionResult(matches=True, confidence=0.75, reason="scenario yaml markers")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no scenario yaml markers")

    def parse(self, source: SourceLike) -> TestPlan:
        text, _ = read_source(source)
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            raise ValueError("scenario yaml root must be a mapping")
        return _plan_from_yaml(data)

    def render(self, plan: TestPlan) -> str:
        config = dict(plan.config)
        targets = config.pop("targets", None)
        for key in list(config.keys()):
            if "." in key:
                config.pop(key)
        data: dict[str, Any] = {
            "scenario": plan.metadata.name,
            "type": plan.metadata.type or "mixed",
        }
        if plan.metadata.version is not None:
            data["version"] = plan.metadata.version
        if plan.metadata.tags:
            data["tags"] = plan.metadata.tags
        if config:
            data["vars"] = config
        if targets:
            data["targets"] = targets
        data["steps"] = [_render_step(step) for step in plan.steps]
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def parse(source: SourceLike) -> TestPlan:
    return ScenarioYamlAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return ScenarioYamlAdapter().render(plan)


__all__ = ["ScenarioYamlAdapter", "parse", "render"]
