"""Contract tests for the public TestQL verification runner."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from testql.verification import (
    VERIFICATION_REQUEST_V1,
    VERIFICATION_RESULT_V1,
    VerificationRequest,
    VerificationRequestError,
    run_verification,
    verification_contract_schema,
)


@dataclass
class _FakeResult:
    source: str
    ok: bool = True
    passed: int = 1
    failed: int = 0
    steps: list[object] = field(default_factory=lambda: [object()])
    duration_ms: float = 1.25
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class _FakeInterpreter:
    def __init__(self, **_: object) -> None:
        pass

    def run(self, _source: str, filename: str) -> _FakeResult:
        return _FakeResult(source=filename)


def _install_fake_interpreter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "testql.interpreter",
        SimpleNamespace(OqlInterpreter=_FakeInterpreter),
    )


def _scenario(path: Path) -> None:
    path.write_text("# SCENARIO: public verification contract\n", encoding="utf-8")


def test_request_is_canonical_and_rejects_tampering(tmp_path: Path) -> None:
    first = VerificationRequest(
        file_specs=("b.testql.toon.yaml", "a.testql.toon.yaml"),
        project_dir=tmp_path,
    )
    second = VerificationRequest(
        file_specs=("a.testql.toon.yaml", "b.testql.toon.yaml"),
        project_dir=tmp_path,
    )

    assert first.to_dict() == second.to_dict()
    assert len(first.request_hash) == 64
    assert VerificationRequest.from_dict(first.to_dict()) == first

    tampered = {**first.to_dict(), "dry_run": False}
    with pytest.raises(VerificationRequestError, match="request_hash"):
        VerificationRequest.from_dict(tampered)

    with pytest.raises(VerificationRequestError, match="unknown"):
        VerificationRequest.from_dict({**first.to_dict(), "surprise": True})


def test_public_runner_resolves_batch_and_emits_hashed_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_interpreter(monkeypatch)
    _scenario(tmp_path / "b.testql.toon.yaml")
    _scenario(tmp_path / "a.testql.toon.yaml")
    request = VerificationRequest(
        file_specs=("*.testql.toon.yaml",), project_dir=tmp_path
    )

    payload = run_verification(request).to_dict()

    assert payload["schema"] == VERIFICATION_RESULT_V1
    assert payload["ok"] is True
    assert payload["files"] == 2
    assert payload["passed_files"] == 2
    assert [Path(run["file"]).name for run in payload["runs"]] == [
        "a.testql.toon.yaml",
        "b.testql.toon.yaml",
    ]
    assert payload["request_hash"] == request.request_hash
    assert len(payload["result_hash"]) == 64


def test_public_runner_reports_actionable_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailedInterpreter(_FakeInterpreter):
        def run(self, _source: str, filename: str) -> _FakeResult:
            step = SimpleNamespace(
                status="failed", name="GUI_ASSERT_TEXT", message="missing"
            )
            return _FakeResult(
                source=filename,
                ok=False,
                passed=0,
                failed=1,
                steps=[step],
            )

    monkeypatch.setitem(
        sys.modules,
        "testql.interpreter",
        SimpleNamespace(OqlInterpreter=FailedInterpreter),
    )
    _scenario(tmp_path / "failed.testql.toon.yaml")

    payload = run_verification(
        VerificationRequest(
            file_specs=("failed.testql.toon.yaml",), project_dir=tmp_path
        )
    ).to_dict()

    assert payload["ok"] is False
    assert payload["failed_files"] == 1
    assert payload["runs"][0]["failures"] == [
        {"name": "GUI_ASSERT_TEXT", "status": "failed", "message": "missing"}
    ]


def test_public_runner_uses_typed_input_error(tmp_path: Path) -> None:
    request = VerificationRequest(
        file_specs=("missing*.testql.toon.yaml",), project_dir=tmp_path
    )
    with pytest.raises(VerificationRequestError, match="existing file"):
        run_verification(request)


def test_packaged_contract_schemas_validate_payloads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_interpreter(monkeypatch)
    _scenario(tmp_path / "schema.testql.toon.yaml")
    request = VerificationRequest(
        file_specs=("schema.testql.toon.yaml",), project_dir=tmp_path
    )
    result = run_verification(request)

    request_schema = verification_contract_schema(VERIFICATION_REQUEST_V1)
    result_schema = verification_contract_schema(VERIFICATION_RESULT_V1)
    Draft202012Validator.check_schema(request_schema)
    Draft202012Validator.check_schema(result_schema)
    assert (
        list(Draft202012Validator(request_schema).iter_errors(request.to_dict())) == []
    )
    assert list(Draft202012Validator(result_schema).iter_errors(result.to_dict())) == []
