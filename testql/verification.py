"""Public, versioned batch-verification contract for TestQL scenarios."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

VERIFICATION_REQUEST_V1 = "testql.verification-request.v1"
VERIFICATION_RESULT_V1 = "testql.verification-result.v1"

_SCHEMA_FILES = {
    VERIFICATION_REQUEST_V1: "verification-request-v1.schema.json",
    VERIFICATION_RESULT_V1: "verification-result-v1.schema.json",
}
_REQUEST_FIELDS = {
    "schema",
    "file_specs",
    "project_dir",
    "url",
    "dry_run",
    "quiet",
    "timeout",
    "context",
    "allow_semantic_events",
    "request_hash",
}


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _payload_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode()).hexdigest()


def verification_contract_schema(schema_id: str) -> dict[str, Any]:
    """Load a packaged verification JSON Schema by contract identifier."""
    try:
        filename = _SCHEMA_FILES[schema_id]
    except KeyError as exc:
        raise KeyError(f"unknown TestQL verification contract {schema_id!r}") from exc
    path = resources.files("testql.data").joinpath(filename)
    return json.loads(path.read_text(encoding="utf-8"))


class VerificationRequestError(ValueError):
    """Raised when a verification request cannot be normalized safely."""


@dataclass(frozen=True)
class VerificationRequest:
    """Canonical input for one deterministic TestQL verification batch."""

    file_specs: tuple[str, ...]
    project_dir: str | Path = "."
    url: str = "http://localhost:8101"
    dry_run: bool = True
    quiet: bool = True
    timeout: int | None = None
    context: Mapping[str, object] | None = None
    allow_semantic_events: bool = False

    def __post_init__(self) -> None:
        raw_specs = (
            (self.file_specs,) if isinstance(self.file_specs, str) else self.file_specs
        )
        specs = tuple(
            sorted({str(spec).strip() for spec in raw_specs if str(spec).strip()})
        )
        if not specs:
            raise VerificationRequestError(
                "file_specs must contain at least one path or glob"
            )
        if not isinstance(self.dry_run, bool) or not isinstance(self.quiet, bool):
            raise VerificationRequestError("dry_run and quiet must be booleans")
        if not isinstance(self.allow_semantic_events, bool):
            raise VerificationRequestError("allow_semantic_events must be a boolean")
        if self.timeout is not None and (
            isinstance(self.timeout, bool)
            or not isinstance(self.timeout, int)
            or self.timeout < 0
        ):
            raise VerificationRequestError(
                "timeout must be a non-negative integer or null"
            )
        if self.context is not None and not isinstance(self.context, Mapping):
            raise VerificationRequestError("context must be an object or null")
        object.__setattr__(self, "file_specs", specs)
        object.__setattr__(self, "project_dir", str(Path(self.project_dir).resolve()))
        try:
            _canonical_json(self.canonical_dict())
        except (TypeError, ValueError) as exc:
            raise VerificationRequestError(
                f"request is not canonical JSON: {exc}"
            ) from exc

    @property
    def schema(self) -> str:
        return VERIFICATION_REQUEST_V1

    @property
    def normalized_project_dir(self) -> str:
        return str(Path(self.project_dir).resolve())

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "file_specs": list(self.file_specs),
            "project_dir": self.normalized_project_dir,
            "url": self.url,
            "dry_run": self.dry_run,
            "quiet": self.quiet,
            "timeout": self.timeout,
            "context": dict(self.context) if self.context is not None else None,
            "allow_semantic_events": self.allow_semantic_events,
        }

    @property
    def request_hash(self) -> str:
        return _payload_hash(self.canonical_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "request_hash": self.request_hash}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> VerificationRequest:
        unknown = sorted(set(payload) - _REQUEST_FIELDS)
        if unknown:
            raise VerificationRequestError(
                f"unknown verification request fields: {unknown}"
            )
        schema = payload.get("schema")
        if schema not in {None, VERIFICATION_REQUEST_V1}:
            raise VerificationRequestError(
                f"unsupported verification request schema {schema!r}"
            )
        file_specs = payload.get("file_specs")
        if not isinstance(file_specs, (list, tuple)) or not all(
            isinstance(spec, str) for spec in file_specs
        ):
            raise VerificationRequestError("file_specs must be an array of strings")
        request = cls(
            file_specs=tuple(file_specs),
            project_dir=str(payload.get("project_dir") or "."),
            url=str(payload.get("url") or "http://localhost:8101"),
            dry_run=payload.get("dry_run", True),
            quiet=payload.get("quiet", True),
            timeout=payload.get("timeout"),
            context=payload.get("context"),
            allow_semantic_events=payload.get("allow_semantic_events", False),
        )
        supplied_hash = payload.get("request_hash")
        if supplied_hash is not None and supplied_hash != request.request_hash:
            raise VerificationRequestError(
                "verification request_hash does not match payload"
            )
        return request


@dataclass(frozen=True)
class VerificationRun:
    file: str
    source: str
    ok: bool
    passed: int
    failed: int
    steps: int
    skipped: int
    validated: int
    executed: int
    profile: str | None
    duration_ms: float
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    failures: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "source": self.source,
            "ok": self.ok,
            "passed": self.passed,
            "failed": self.failed,
            "steps": self.steps,
            "skipped": self.skipped,
            "validated": self.validated,
            "executed": self.executed,
            "profile": self.profile,
            "duration_ms": self.duration_ms,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "failures": list(self.failures),
        }


@dataclass(frozen=True)
class VerificationResult:
    runs: tuple[VerificationRun, ...]
    dry_run: bool
    request_hash: str

    @property
    def schema(self) -> str:
        return VERIFICATION_RESULT_V1

    def canonical_dict(self) -> dict[str, Any]:
        failed_files = sum(not run.ok for run in self.runs)
        return {
            "schema": self.schema,
            "ok": failed_files == 0,
            "files": len(self.runs),
            "passed_files": len(self.runs) - failed_files,
            "failed_files": failed_files,
            "runs": [run.to_dict() for run in self.runs],
            "dry_run": self.dry_run,
            "request_hash": self.request_hash,
        }

    @property
    def result_hash(self) -> str:
        return _payload_hash(self.canonical_dict())

    def to_dict(self) -> dict[str, Any]:
        return {**self.canonical_dict(), "result_hash": self.result_hash}


def _resolved_paths(request: VerificationRequest) -> list[Path]:
    from click import ClickException

    from testql.commands.run_cmd import _resolve_input_paths

    root = Path(request.normalized_project_dir)
    paths_by_key: dict[str, Path] = {}
    try:
        for raw_spec in request.file_specs:
            spec = Path(raw_spec)
            resolved_spec = str(spec if spec.is_absolute() else root / raw_spec)
            for path in _resolve_input_paths(resolved_spec):
                paths_by_key[str(path.resolve())] = path
    except ClickException as exc:
        raise VerificationRequestError(exc.format_message()) from exc
    return [paths_by_key[key] for key in sorted(paths_by_key)]


def run_verification(
    request: VerificationRequest | Mapping[str, Any],
) -> VerificationResult:
    """Resolve and run a batch without exposing CLI/private runner details."""
    if not isinstance(request, VerificationRequest):
        request = VerificationRequest.from_dict(request)

    from testql.commands.run_cmd import _failure_details, _run_single

    runs: list[VerificationRun] = []
    for path in _resolved_paths(request):
        result = _run_single(
            path,
            request.url,
            request.dry_run,
            request.quiet,
            request.timeout,
            dict(request.context or {}),
            request.allow_semantic_events,
        )
        steps = list(result.steps)
        profile = getattr(result, "profile", None)
        runs.append(
            VerificationRun(
                file=str(path),
                source=str(getattr(result, "source", path.name)),
                ok=bool(result.ok),
                passed=int(result.passed),
                failed=int(result.failed),
                steps=len(steps),
                skipped=int(getattr(result, "skipped", 0)),
                validated=int(getattr(result, "validated", 0)),
                executed=int(getattr(result, "executed", len(steps))),
                profile=str(profile) if profile is not None else None,
                duration_ms=round(float(result.duration_ms), 1),
                errors=tuple(str(error) for error in result.errors),
                warnings=tuple(str(warning) for warning in result.warnings),
                failures=tuple(_failure_details(result)),
            )
        )
    return VerificationResult(tuple(runs), request.dry_run, request.request_hash)


__all__ = [
    "VERIFICATION_REQUEST_V1",
    "VERIFICATION_RESULT_V1",
    "VerificationRequest",
    "VerificationRequestError",
    "VerificationResult",
    "VerificationRun",
    "run_verification",
    "verification_contract_schema",
]
