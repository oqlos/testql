"""Contract coverage analysis: how well does a `TestPlan` cover a contract?

Three contract types are supported:

    * OpenAPI — every `paths.<path>.<method>` operation should have an
      `ApiStep` in the plan.
    * SQL DDL — every declared table should appear in at least one `SqlStep`.
    * Protobuf — every `MessageDef` should have a `ProtoStep`.

Each analyser returns a `CoverageReport` with `covered`, `total`,
`missing` and `percent`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Union

import yaml

from testql.adapters.proto.descriptor_loader import ProtoFile, parse_proto
from testql.adapters.sql.ddl_parser import ParsedDDL, parse_ddl
from testql.ir import ApiStep, ProtoStep, SqlStep, TestPlan

_HTTP_METHODS = ("get", "post", "put", "delete", "patch", "head", "options")


@dataclass
class CoverageReport:
    contract: str = ""           # "openapi" | "sql" | "proto"
    total: int = 0
    covered: int = 0
    missing: list[str] = field(default_factory=list)

    @property
    def percent(self) -> float:
        return (self.covered / self.total * 100.0) if self.total else 100.0

    def to_dict(self) -> dict:
        return {
            "contract": self.contract,
            "total": self.total,
            "covered": self.covered,
            "percent": round(self.percent, 1),
            "missing": list(self.missing),
        }


# ── Helpers ────────────────────────────────────────────────────────────────


def _load_text(source: Union[str, Path]) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if "\n" not in source and Path(source).is_file():
        return Path(source).read_text(encoding="utf-8")
    return source


def _load_yaml(source: Union[str, Path, dict]) -> dict:
    if isinstance(source, dict):
        return source
    return yaml.safe_load(_load_text(source)) or {}


def _build_report(contract: str, declared: Iterable[str], covered: Iterable[str]) -> CoverageReport:
    declared_set, covered_set = set(declared), set(covered)
    return CoverageReport(
        contract=contract,
        total=len(declared_set),
        covered=len(declared_set & covered_set),
        missing=sorted(declared_set - covered_set),
    )


# ── OpenAPI ────────────────────────────────────────────────────────────────


def _openapi_endpoints(spec: dict) -> set[str]:
    out: set[str] = set()
    for path, item in (spec.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in item:
            if method.lower() in _HTTP_METHODS:
                out.add(f"{method.upper()} {path}")
    return out


def _plan_endpoints(plan: TestPlan) -> set[str]:
    return {f"{s.method} {s.path}" for s in plan.steps if isinstance(s, ApiStep)}


def coverage_vs_openapi(plan: TestPlan, spec: Union[str, Path, dict]) -> CoverageReport:
    return _build_report("openapi", _openapi_endpoints(_load_yaml(spec)), _plan_endpoints(plan))


# ── SQL ────────────────────────────────────────────────────────────────────


def _sql_tables(ddl: ParsedDDL) -> set[str]:
    return {t.name.lower() for t in ddl.tables}


def _plan_sql_tables(plan: TestPlan) -> set[str]:
    """Naïve: any SqlStep query containing `from <name>` covers `<name>`."""
    out: set[str] = set()
    for step in plan.steps:
        if not isinstance(step, SqlStep):
            continue
        out.update(_extract_table_names(step.query))
    return out


_FROM_RE = None  # lazily compiled — coverage_analyzer is also imported at light usage


def _extract_table_names(sql: str) -> set[str]:
    import re
    global _FROM_RE
    if _FROM_RE is None:
        _FROM_RE = re.compile(r"\bfrom\s+([A-Za-z_][\w.]*)", re.IGNORECASE)
    return {m.group(1).lower() for m in _FROM_RE.finditer(sql)}


def coverage_vs_sql(plan: TestPlan, ddl_source: Union[str, Path]) -> CoverageReport:
    return _build_report("sql", _sql_tables(parse_ddl(_load_text(ddl_source))),
                         _plan_sql_tables(plan))


# ── Protobuf ───────────────────────────────────────────────────────────────


def _proto_messages(proto: ProtoFile) -> set[str]:
    return {m.name for m in proto.messages}


def _plan_proto_messages(plan: TestPlan) -> set[str]:
    return {s.message for s in plan.steps if isinstance(s, ProtoStep) and s.message}


def coverage_vs_proto(plan: TestPlan, proto_source: Union[str, Path]) -> CoverageReport:
    return _build_report("proto", _proto_messages(parse_proto(_load_text(proto_source))),
                         _plan_proto_messages(plan))


# ── Convenience ────────────────────────────────────────────────────────────


def analyze(plan: TestPlan, contract: str,
            source: Union[str, Path, dict]) -> CoverageReport:
    """Dispatch by contract name (`openapi` | `sql` | `proto`)."""
    fn = _DISPATCH.get(contract.lower())
    if fn is None:
        raise ValueError(f"unknown contract {contract!r}; expected openapi/sql/proto")
    return fn(plan, source)


_DISPATCH = {
    "openapi": coverage_vs_openapi,
    "sql": coverage_vs_sql,
    "proto": coverage_vs_proto,
}


__all__ = [
    "CoverageReport",
    "coverage_vs_openapi",
    "coverage_vs_sql",
    "coverage_vs_proto",
    "analyze",
]
