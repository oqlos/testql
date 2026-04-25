from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

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
    summary.write_text(render_inspection(topology, envelope, plan, "nlp"))
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


def _metadata(topology: TopologyManifest, envelope: TestResultEnvelope, plan: RefactorPlan, written: list[Path]) -> dict:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
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
