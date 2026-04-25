"""`${var}` / `$var` interpolation across step fields.

Walks strings, dicts, lists recursively so a step's `path`, `body`, `headers`,
`query` and `variables` (GraphQL) can all reference captured variables. Numbers,
booleans, None and other scalars pass through untouched.
"""

from __future__ import annotations

from typing import Any

from testql.base import VariableStore


def interp_value(value: Any, store: VariableStore) -> Any:
    """Interpolate `${var}` / `$var` references inside `value`.

    Recurses into dicts and lists. Non-string scalars are returned unchanged.
    """
    if isinstance(value, str):
        return store.interpolate(value)
    if isinstance(value, dict):
        return {k: interp_value(v, store) for k, v in value.items()}
    if isinstance(value, list):
        return [interp_value(item, store) for item in value]
    return value


__all__ = ["interp_value"]
