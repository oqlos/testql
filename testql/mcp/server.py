"""FastMCP server wrapper for TestQL core workflows.

This module intentionally keeps tool surface minimal and deterministic:
- list available IR sources/targets
- generate scenarios from source artifacts
- run scenarios from file/dir/glob
- build topology in json/yaml/toon
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _require_fastmcp():
    try:
        from mcp.server.fastmcp import FastMCP
        return FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "MCP support requires optional dependency 'mcp'. "
            "Install with: pip install mcp"
        ) from exc


def _normalize_run_payload(results: list[tuple[Path, Any]]) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    passed_files = 0
    failed_files = 0

    for path, result in results:
        ok = bool(result.ok)
        if ok:
            passed_files += 1
        else:
            failed_files += 1
        runs.append(
            {
                "file": str(path),
                "source": result.source,
                "ok": ok,
                "passed": result.passed,
                "failed": result.failed,
                "steps": len(result.steps),
                "duration_ms": round(result.duration_ms, 1),
                "errors": result.errors,
                "warnings": result.warnings,
            }
        )

    payload: dict[str, Any] = {
        "ok": failed_files == 0,
        "files": len(results),
        "passed_files": passed_files,
        "failed_files": failed_files,
        "runs": runs,
    }

    if len(results) == 1:
        only = runs[0]
        payload.update(
            {
                "source": only["source"],
                "passed": only["passed"],
                "failed": only["failed"],
                "steps": only["steps"],
                "duration_ms": only["duration_ms"],
                "errors": only["errors"],
                "warnings": only["warnings"],
            }
        )

    return payload


@dataclass
class TestQLMCPServer:
    """Thin wrapper exposing selected TestQL actions as FastMCP tools."""

    name: str = "testql"

    def __post_init__(self) -> None:
        FastMCP = _require_fastmcp()
        self.app = FastMCP(self.name)
        self._register_tools()

    def _register_tools(self) -> None:
        from testql.commands.run_cmd import _resolve_input_paths, _run_single
        from testql.generators import pipeline
        from testql.generators.sources import available_sources
        from testql.generators.targets import available_targets
        from testql.topology import build_topology, render_topology

        @self.app.tool()
        def list_sources() -> list[str]:
            """List available source adapters for generate-ir."""
            return available_sources()

        @self.app.tool()
        def list_targets() -> list[str]:
            """List available generation targets."""
            return available_targets()

        @self.app.tool()
        def generate_ir(source: str, artifact: str, target: str = "testtoon", out: str | None = None) -> dict[str, Any]:
            """Generate scenario from source artifact via IR pipeline."""
            result = pipeline.run(source=source, target=target, artifact=artifact)
            payload: dict[str, Any] = {
                "source": result.source_name,
                "target": result.target_name,
                "plan": result.plan.metadata.to_dict(),
                "output": result.output,
            }
            if out:
                written = pipeline.write(result, out)
                payload["written"] = str(written)
            return payload

        @self.app.tool()
        def run_scenarios(
            file_spec: str,
            url: str = "http://localhost:8101",
            dry_run: bool = True,
            quiet: bool = True,
            timeout: int | None = None,
        ) -> dict[str, Any]:
            """Run one or many scenarios from file/dir/glob spec."""
            paths = _resolve_input_paths(file_spec)
            results = [(p, _run_single(p, url, dry_run, quiet, timeout)) for p in paths]
            return _normalize_run_payload(results)

        @self.app.tool()
        def build_topology_manifest(
            source: str = ".",
            fmt: str = "json",
            include_manifest: bool = False,
            scan_network: bool = False,
        ) -> str:
            """Build topology and return serialized graph as string."""
            graph = build_topology(source, scan_network=scan_network)
            return render_topology(graph, fmt, include_manifest=include_manifest)

    def run(self) -> None:
        """Run MCP stdio server."""
        self.app.run()


def create_server(name: str = "testql") -> TestQLMCPServer:
    return TestQLMCPServer(name=name)


def run_server() -> None:
    create_server().run()


if __name__ == "__main__":
    run_server()
