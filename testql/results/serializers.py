from __future__ import annotations

import json
from typing import Any, Literal

import yaml

from testql.results.models import RefactorPlan, TestResultEnvelope
from testql.topology import TopologyManifest

InspectionFormat = Literal["json", "yaml", "toon", "nlp"]


def render_result_envelope(envelope: TestResultEnvelope, fmt: InspectionFormat = "toon") -> str:
    return _render_data({"result": envelope.to_dict()}, fmt)


def render_refactor_plan(plan: RefactorPlan, fmt: InspectionFormat = "toon") -> str:
    return _render_data({"refactor_plan": plan.to_dict()}, fmt)


def render_inspection(topology: TopologyManifest, envelope: TestResultEnvelope, plan: RefactorPlan, fmt: InspectionFormat = "toon") -> str:
    data = {
        "inspection": {
            "topology": topology.to_dict(),
            "result": envelope.to_dict(),
            "refactor_plan": plan.to_dict(),
        }
    }
    if fmt == "nlp":
        return _render_nlp(envelope, plan)
    return _render_data(data, fmt)


def _render_data(data: dict[str, Any], fmt: InspectionFormat) -> str:
    if fmt == "json":
        return json.dumps(data, indent=2, sort_keys=True) + "\n"
    if fmt == "yaml":
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if fmt == "toon":
        return _render_toon(data)
    if fmt == "nlp":
        result = data.get("result") or data.get("inspection", {}).get("result", {})
        plan = data.get("refactor_plan") or data.get("inspection", {}).get("refactor_plan", {})
        return _render_nlp_dict(result, plan)
    raise ValueError(f"unsupported inspection format: {fmt}")


def _render_toon(data: dict[str, Any]) -> str:
    inspection = data.get("inspection")
    if inspection:
        result = inspection["result"]
        plan = inspection["refactor_plan"]
        topology = inspection["topology"]
    else:
        result = data.get("result", {})
        plan = data.get("refactor_plan", {})
        topology = {}
    lines = ["INSPECTION{key, value}:"]
    if topology:
        lines.append(f"  topology_id, {result.get('topology_id', '')}")
        lines.append(f"  topology_nodes, {len(topology.get('nodes', []))}")
        lines.append(f"  topology_edges, {len(topology.get('edges', []))}")
    lines.append(f"  run_id, {result.get('run_id', '')}")
    lines.append(f"  status, {result.get('status', '')}")
    lines.append(f"  checks, {len(result.get('checks', []))}")
    lines.append(f"  failures, {len(result.get('failures', []))}")
    lines.append(f"  actions, {len(result.get('suggested_actions', []))}")
    lines.append("")
    checks = result.get("checks", [])
    lines.append(f"CHECKS[{len(checks)}]{{id, status, summary}}:")
    for check in checks:
        lines.append(f"  {check['id']}, {check['status']}, {_clean(check['summary'])}")
    failures = result.get("failures", [])
    lines.append("")
    lines.append(f"FINDINGS[{len(failures)}]{{id, severity, node_id, summary}}:")
    for finding in failures:
        lines.append(f"  {finding['id']}, {finding['severity']}, {finding.get('node_id', '')}, {_clean(finding['summary'])}")
    actions = plan.get("actions", result.get("suggested_actions", []))
    lines.append("")
    lines.append(f"ACTIONS[{len(actions)}]{{id, type, target, summary}}:")
    for action in actions:
        lines.append(f"  {action['id']}, {action['type']}, {action.get('target', '')}, {_clean(action['summary'])}")
    return "\n".join(lines) + "\n"


def _render_nlp(envelope: TestResultEnvelope, plan: RefactorPlan) -> str:
    return _render_nlp_dict(envelope.to_dict(), plan.to_dict())


def _render_nlp_dict(result: dict[str, Any], plan: dict[str, Any]) -> str:
    status = result.get("status", "unknown")
    checks = result.get("checks", [])
    failures = result.get("failures", [])
    actions = plan.get("actions", result.get("suggested_actions", []))
    lines = [f"Inspection status: {status}."]
    lines.append(f"Executed {len(checks)} structural checks; found {len(failures)} findings.")
    if failures:
        lines.append("Key findings:")
        for finding in failures[:5]:
            lines.append(f"- {finding['severity']}: {finding['summary']}")
    else:
        lines.append("No refactor-blocking findings were detected in the current topology snapshot.")
    if actions:
        lines.append("Recommended actions:")
        for action in actions[:5]:
            lines.append(f"- {action['summary']}")
    return "\n".join(lines) + "\n"


def _clean(value: str) -> str:
    return " ".join(str(value).split())
