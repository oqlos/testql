"""Verb → JSON Schema registry."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

import jsonschema


@lru_cache(maxsize=1)
def _load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    pkg = resources.files("dsl2testql").joinpath("schema/commands")
    for path in pkg.iterdir():
        if path.name.endswith(".schema.json"):
            verb = path.name.replace(".schema.json", "").upper()
            schemas[verb] = json.loads(path.read_text(encoding="utf-8"))
    return schemas


def schema_for_verb(verb: str) -> dict[str, Any] | None:
    return _load_schemas().get(verb.upper())


def all_schemas() -> dict[str, dict[str, Any]]:
    return dict(_load_schemas())


def validate_command_dict(cmd: dict[str, Any]) -> list[str]:
    verb = str(cmd.get("verb", "")).upper()
    schema = schema_for_verb(verb)
    if schema is None:
        return []
    validator = jsonschema.Draft202012Validator(schema)
    return [e.message for e in sorted(validator.iter_errors(cmd), key=str)]


def validate_schema_registry() -> list[str]:
    errors: list[str] = []
    for verb, schema in _load_schemas().items():
        if schema.get("properties", {}).get("verb", {}).get("const") != verb:
            errors.append(f"{verb}: verb const mismatch")
    return errors
