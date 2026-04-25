"""Step nodes for the Unified IR.

Hierarchy:
    Step (base)
    ├── ApiStep      — HTTP API calls
    ├── GuiStep      — browser/UI interactions (navigate, click, input, ...)
    ├── EncoderStep  — hardware encoder commands (on/off/click/scroll/...)
    ├── ShellStep    — shell command execution
    ├── UnitStep     — unit-test invocation
    ├── NlStep       — raw natural-language line (pre-resolution)
    ├── SqlStep      — SQL DDL/DML execution
    ├── ProtoStep    — protobuf message round-trip / validation
    └── GraphqlStep  — GraphQL query/mutation/subscription
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .assertions import Assertion
from .captures import Capture


@dataclass
class Step:
    """Base step. Subclasses add typed fields; `kind` discriminator makes the
    intent unambiguous when serialised.
    """

    kind: str = "generic"
    name: Optional[str] = None
    asserts: list[Assertion] = field(default_factory=list)
    captures: list[Capture] = field(default_factory=list)
    wait_ms: Optional[int] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out: dict = {"kind": self.kind}
        if self.name is not None:
            out["name"] = self.name
        if self.asserts:
            out["asserts"] = [a.to_dict() for a in self.asserts]
        if self.captures:
            out["captures"] = [c.to_dict() for c in self.captures]
        if self.wait_ms is not None:
            out["wait_ms"] = self.wait_ms
        if self.extra:
            out["extra"] = dict(self.extra)
        return out


@dataclass
class ApiStep(Step):
    method: str = "GET"
    path: str = "/"
    body: Optional[Any] = None
    headers: dict[str, str] = field(default_factory=dict)
    expect_status: Optional[int] = None

    def __post_init__(self) -> None:
        self.kind = "api"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({"method": self.method, "path": self.path})
        if self.body is not None:
            out["body"] = self.body
        if self.headers:
            out["headers"] = dict(self.headers)
        if self.expect_status is not None:
            out["expect_status"] = self.expect_status
        return out


@dataclass
class GuiStep(Step):
    action: str = "navigate"  # navigate | click | input | wait | assert_visible | ...
    selector: Optional[str] = None
    path: Optional[str] = None
    value: Optional[Any] = None

    def __post_init__(self) -> None:
        self.kind = "gui"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["action"] = self.action
        if self.selector is not None:
            out["selector"] = self.selector
        if self.path is not None:
            out["path"] = self.path
        if self.value is not None:
            out["value"] = self.value
        return out


@dataclass
class EncoderStep(Step):
    action: str = "on"  # on | off | click | dblclick | status | page_next | page_prev | scroll | focus
    target: Optional[str] = None
    value: Optional[Any] = None

    def __post_init__(self) -> None:
        self.kind = "encoder"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["action"] = self.action
        if self.target is not None:
            out["target"] = self.target
        if self.value is not None:
            out["value"] = self.value
        return out


@dataclass
class ShellStep(Step):
    command: str = ""
    cwd: Optional[str] = None
    expect_exit_code: Optional[int] = None

    def __post_init__(self) -> None:
        self.kind = "shell"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["command"] = self.command
        if self.cwd is not None:
            out["cwd"] = self.cwd
        if self.expect_exit_code is not None:
            out["expect_exit_code"] = self.expect_exit_code
        return out


@dataclass
class UnitStep(Step):
    target: str = ""  # module::function or pytest node id
    args: list[Any] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.kind = "unit"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["target"] = self.target
        if self.args:
            out["args"] = list(self.args)
        if self.kwargs:
            out["kwargs"] = dict(self.kwargs)
        return out


@dataclass
class NlStep(Step):
    """Raw natural-language line that has not yet been resolved to a typed step."""

    text: str = ""
    lang: Optional[str] = None

    def __post_init__(self) -> None:
        self.kind = "nl"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["text"] = self.text
        if self.lang is not None:
            out["lang"] = self.lang
        return out


@dataclass
class SqlStep(Step):
    query: str = ""
    dialect: Optional[str] = None
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.kind = "sql"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out["query"] = self.query
        if self.dialect is not None:
            out["dialect"] = self.dialect
        if self.params:
            out["params"] = dict(self.params)
        return out


@dataclass
class ProtoStep(Step):
    schema_file: str = ""
    message: str = ""
    fields: dict[str, Any] = field(default_factory=dict)
    check: str = "round_trip_equal"

    def __post_init__(self) -> None:
        self.kind = "proto"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({
            "schema_file": self.schema_file,
            "message": self.message,
            "check": self.check,
        })
        if self.fields:
            out["fields"] = dict(self.fields)
        return out


@dataclass
class GraphqlStep(Step):
    operation: str = "query"  # query | mutation | subscription
    body: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    endpoint: Optional[str] = None

    def __post_init__(self) -> None:
        self.kind = "graphql"

    def to_dict(self) -> dict:
        out = super().to_dict()
        out.update({"operation": self.operation, "body": self.body})
        if self.variables:
            out["variables"] = dict(self.variables)
        if self.endpoint is not None:
            out["endpoint"] = self.endpoint
        return out
