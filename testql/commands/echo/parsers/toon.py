"""TestTOON scenario file parser for echo command."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# HTTP methods recognized in TOON scenarios
_HTTP_METHODS = frozenset({"GET", "POST", "PUT", "DELETE", "PATCH"})


def _extract_endpoint(method: str, value: Any) -> dict:
    """Extract endpoint from HTTP method key."""
    if isinstance(value, dict):
        return {
            "method": method.upper(),
            "path": value.get("url", ""),
            "status": value.get("status"),
        }
    return {
        "method": method.upper(),
        "path": str(value),
        "status": None,
    }


def _extract_assert(key: str, value: Any) -> dict:
    """Extract assert from ASSERT* key."""
    return {
        "type": key,
        "condition": value,
    }


def _parse_scenario(content: dict, file: Path, base_path: Path) -> dict:
    """Parse single scenario content into contract."""
    contract = {
        "file": str(file.relative_to(base_path)),
        "name": content.get("meta", {}).get("name", file.stem),
        "type": content.get("meta", {}).get("type", "api"),
        "tags": content.get("meta", {}).get("tags", []),
        "endpoints": [],
        "asserts": [],
    }

    for key, value in content.items():
        if key in ("meta", "config", "variables"):
            continue

        # Detect HTTP methods
        if key.upper() in _HTTP_METHODS:
            contract["endpoints"].append(_extract_endpoint(key, value))

        # Detect asserts
        if key.startswith("ASSERT"):
            contract["asserts"].append(_extract_assert(key, value))

    return contract


def parse_toon_scenarios(path: Path) -> list[dict[str, Any]]:
    """Parse .testql.toon.yaml files into API contract structure."""
    contracts = []

    for file in path.rglob("*.testql.toon.yaml"):
        content = yaml.safe_load(file.read_text())
        if not content:
            continue

        contract = _parse_scenario(content, file, path)
        contracts.append(contract)

    return contracts
