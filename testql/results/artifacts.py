from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from testql import __version__ as TESTQL_VERSION
from testql.results.models import RefactorPlan, TestResultEnvelope
from testql.results.serializers import render_inspection, render_refactor_plan, render_result_envelope
from testql.topology import TopologyManifest, render_topology


def write_inspection_artifacts(
    topology: TopologyManifest,
    envelope: TestResultEnvelope,
    plan: RefactorPlan,
    out_dir: str | Path = ".testql",
) -> list[Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    written.extend(_write_group(target, "topology", {
        "json": render_topology(topology, "json"),
        "yaml": render_topology(topology, "yaml"),
        "toon": render_topology(topology, "toon"),
    }))
    written.extend(_write_group(target, "result", {
        "json": render_result_envelope(envelope, "json"),
        "yaml": render_result_envelope(envelope, "yaml"),
        "toon": render_result_envelope(envelope, "toon"),
    }))
    written.extend(_write_group(target, "refactor-plan", {
        "json": render_refactor_plan(plan, "json"),
        "yaml": render_refactor_plan(plan, "yaml"),
        "toon": render_refactor_plan(plan, "toon"),
    }))
    written.extend(_write_group(target, "inspection", {
        "json": render_inspection(topology, envelope, plan, "json"),
        "yaml": render_inspection(topology, envelope, plan, "yaml"),
        "toon": render_inspection(topology, envelope, plan, "toon"),
    }))
    summary = target / "summary.md"
    summary.write_text(_render_summary_md(topology, envelope, plan, written))
    written.append(summary)
    metadata = target / "metadata.json"
    all_written = [*written, metadata]
    metadata.write_text(json.dumps(_metadata(topology, envelope, plan, all_written), indent=2, sort_keys=True) + "\n")
    return all_written


def _write_group(target: Path, prefix: str, contents: dict[str, str]) -> list[Path]:
    written = []
    suffixes = {"json": "json", "yaml": "yaml", "toon": "toon.yaml"}
    for fmt, content in contents.items():
        path = target / f"{prefix}.{suffixes[fmt]}"
        path.write_text(content)
        written.append(path)
    return written


def _render_summary_md(
    topology: TopologyManifest,
    envelope: TestResultEnvelope,
    plan: RefactorPlan,
    written: list[Path],
) -> str:
    """Generate markdown summary with links to all artifacts."""
    from testql.results.serializers import _render_nlp

    nlp_summary = _render_nlp(envelope, plan).strip()

    # Artifact descriptions mapping
    artifact_descs: dict[str, str] = {
        "inspection.yaml": "Full inspection report (YAML)",
        "inspection.json": "Full inspection report (JSON)",
        "inspection.toon.yaml": "Inspection report (TOON format)",
        "result.yaml": "Test execution results (YAML)",
        "result.json": "Test results (JSON)",
        "result.toon.yaml": "Test results (TOON format)",
        "topology.yaml": "Web topology graph (YAML)",
        "topology.json": "Topology (JSON)",
        "topology.toon.yaml": "Topology (TOON format)",
        "refactor-plan.yaml": "Refactoring recommendations (YAML)",
        "refactor-plan.json": "Refactor plan (JSON)",
        "refactor-plan.toon.yaml": "Refactor plan (TOON format)",
        "metadata.json": "Inspection metadata",
    }

    # Group artifacts by category
    groups: dict[str, list[tuple[str, str]]] = {
        "Inspection Reports": [],
        "Test Results": [],
        "Topology": [],
        "Refactor Plan": [],
        "Metadata": [],
    }

    for path in written:
        name = path.name
        desc = artifact_descs.get(name, name)
        link = f"[{name}]({name})"

        if name.startswith("inspection."):
            groups["Inspection Reports"].append((link, desc))
        elif name.startswith("result."):
            groups["Test Results"].append((link, desc))
        elif name.startswith("topology."):
            groups["Topology"].append((link, desc))
        elif name.startswith("refactor-plan."):
            groups["Refactor Plan"].append((link, desc))
        elif name == "metadata.json":
            groups["Metadata"].append((link, desc))

    lines = [nlp_summary, "", "## Generated Artifacts", ""]

    for group_name, items in groups.items():
        if items:
            lines.append(f"### {group_name}")
            for link, desc in items:
                lines.append(f"- {link} - {desc}")
            lines.append("")

    return "\n".join(lines)


def _metadata(topology: TopologyManifest, envelope: TestResultEnvelope, plan: RefactorPlan, written: list[Path]) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "testql_version": TESTQL_VERSION,
        "generator": "testql.inspect",
        "root": topology.root.to_dict(),
        "topology_id": envelope.topology_id,
        "run_id": envelope.run_id,
        "status": envelope.status,
        "refactor_plan_id": plan.id,
        "files": [path.name for path in written],
        "counts": {
            "nodes": len(topology.nodes),
            "edges": len(topology.edges),
            "checks": len(envelope.checks),
            "findings": len(envelope.failures),
            "actions": len(envelope.suggested_actions),
        },
    }
