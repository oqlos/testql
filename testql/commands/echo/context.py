"""Context generation for echo command."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .parsers.doql import parse_doql_less
from .parsers.toon import parse_toon_scenarios


def _find_doql_file(path: Path) -> Path | None:
    """Find DOQL file in project (prefer .less over .css)."""
    doql_files = list(path.rglob("*.doql.less")) + list(path.rglob("app.doql.css"))
    if not doql_files:
        return None
    # Prefer .less over .css
    return next((f for f in doql_files if f.suffix == ".less"), doql_files[0])


def _find_toon_path(path: Path) -> Path:
    """Find TOON scenarios path."""
    scenarios_path = path / "testql-scenarios"
    if scenarios_path.exists():
        return scenarios_path
    return path


def generate_context(
    path: Path,
    include_toon: bool = True,
    include_doql: bool = True
) -> dict[str, Any]:
    """Generate unified project context from DOQL and TOON sources."""
    context = {
        "project": {
            "path": str(path),
            "name": path.name,
        },
        "generated_at": None,
    }

    # Parse doql
    if include_doql:
        doql_file = _find_doql_file(path)
        if doql_file:
            context["system_model"] = parse_doql_less(doql_file)

    # Parse toon
    if include_toon:
        toon_path = _find_toon_path(path)
        context["api_contracts"] = parse_toon_scenarios(toon_path)

    return context
