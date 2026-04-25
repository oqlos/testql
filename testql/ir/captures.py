"""Capture — extract a value from a step's payload into a variable.

Attached to a `Step` via its `captures` list. After the step's executor runs
and produces a result payload, the runner walks each `Capture`, navigates the
dotted `from_path` inside that payload, and stores the resolved value into
the execution context's `VariableStore` under `var_name`.

Subsequent steps can reference the captured value via `${var_name}` in any of
their string-shaped fields (path, body, headers, query, etc.).

Example IR:

    ApiStep(
        method="POST", path="/devices",
        body={"name": "Test"},
        captures=[Capture(var_name="device_id", from_path="data.id")],
    )
    ApiStep(method="GET", path="/devices/${device_id}")
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Capture:
    """Bind a value at `from_path` inside a step's payload to `var_name`."""

    var_name: str
    from_path: str

    def to_dict(self) -> dict:
        return {"var_name": self.var_name, "from_path": self.from_path}


__all__ = ["Capture"]
