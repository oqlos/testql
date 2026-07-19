"""Strict ``testql:assertion-suite/v1`` parser and evaluator.

This profile is intentionally small.  It is used for policy and continuity
checks that evaluate a supplied JSON context; it must never fall through to
the semantic-event interpreter because doing so would turn unknown assertions
into false-positive test passes.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

from testql.base import ScriptResult, StepResult, StepStatus


PROFILE = "testql:assertion-suite/v1"


@dataclass(frozen=True)
class Assertion:
    expression: str
    line: int
    message: str = ""


@dataclass
class AssertionTest:
    name: str
    line: int
    assertions: list[Assertion] = field(default_factory=list)


@dataclass
class AssertionSuite:
    version: int
    name: str
    filename: str
    suite_type: str | None = None
    tests: list[AssertionTest] = field(default_factory=list)

    @property
    def assertion_count(self) -> int:
        return sum(len(test.assertions) for test in self.tests)


_TOKEN = re.compile(
    r"\s*(?:(?P<operator>==|!=|>=|<=|>|<)|"
    r"(?P<lparen>\()|(?P<rparen>\))|"
    r"(?P<string>\"(?:\\.|[^\"\\])*\")|"
    r"(?P<number>-?\d+(?:\.\d+)?)|"
    r"(?P<word>[A-Za-z_][A-Za-z0-9_.-]*))"
)


class AssertionSuiteSyntaxError(ValueError):
    """Source error with a stable code and line number."""

    def __init__(self, code: str, line: int, detail: str = "") -> None:
        suffix = f":{detail}" if detail else ""
        super().__init__(f"{code}:line={line}{suffix}")
        self.code = code
        self.line = line


def is_assertion_suite(source: str, filename: str = "") -> bool:
    """Detect the explicit assertion-suite profile without claiming GUI/OQL files."""
    if not filename.endswith(".testql"):
        return False
    return bool(
        re.search(r"^\s*(?:TESTQL_VERSION\s+\d+|VERSION:\s*\d+)\s*$", source, re.MULTILINE | re.IGNORECASE)
        and re.search(r"^\s*SUITE\s+.+:\s*$", source, re.MULTILINE | re.IGNORECASE)
        and re.search(r"^\s*EXPECT\s+.+$", source, re.MULTILINE | re.IGNORECASE)
    )


def parse_assertion_suite(source: str, filename: str = "<string>") -> AssertionSuite:
    """Parse the complete profile and reject every unknown instruction."""
    version: int | None = None
    suite: AssertionSuite | None = None
    current_test: AssertionTest | None = None
    last_assertion: Assertion | None = None

    for number, raw in enumerate(source.replace("\r\n", "\n").split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        match = re.fullmatch(r"(?:TESTQL_VERSION\s+|VERSION:\s*)(\d+)", line, re.IGNORECASE)
        if match:
            if version is not None:
                raise AssertionSuiteSyntaxError("duplicate_testql_version", number)
            version = int(match.group(1))
            if version != 1:
                raise AssertionSuiteSyntaxError("unsupported_testql_version", number, str(version))
            continue

        match = re.fullmatch(r"SUITE\s+(.+?)(?:\s+TYPE\s+([A-Za-z0-9_.-]+))?:", line, re.IGNORECASE)
        if match:
            if version is None:
                raise AssertionSuiteSyntaxError("testql_version_required_before_suite", number)
            if suite is not None:
                raise AssertionSuiteSyntaxError("duplicate_testql_suite", number)
            suite = AssertionSuite(
                version=version,
                name=match.group(1).strip(),
                suite_type=match.group(2),
                filename=filename,
            )
            continue

        match = re.fullmatch(r"TEST\s+(.+):", line, re.IGNORECASE)
        if match:
            if suite is None:
                raise AssertionSuiteSyntaxError("testql_suite_required_before_test", number)
            current_test = AssertionTest(name=match.group(1).strip(), line=number)
            suite.tests.append(current_test)
            last_assertion = None
            continue

        match = re.fullmatch(r"EXPECT\s+(.+)", line, re.IGNORECASE)
        if match:
            if current_test is None:
                raise AssertionSuiteSyntaxError("testql_test_required_before_expect", number)
            expression = match.group(1).strip()
            parse_expression(expression, number)
            last_assertion = Assertion(expression=expression, line=number)
            current_test.assertions.append(last_assertion)
            continue

        match = re.fullmatch(r"MESSAGE\s+\"((?:\\.|[^\"\\])*)\"", line, re.IGNORECASE)
        if match:
            if current_test is None or last_assertion is None:
                raise AssertionSuiteSyntaxError("testql_expect_required_before_message", number)
            message = json.loads(f'"{match.group(1)}"')
            current_test.assertions[-1] = Assertion(
                expression=last_assertion.expression,
                line=last_assertion.line,
                message=message,
            )
            last_assertion = current_test.assertions[-1]
            continue

        raise AssertionSuiteSyntaxError("unknown_testql_instruction", number, line[:120])

    if version is None:
        raise AssertionSuiteSyntaxError("testql_version_missing", 1)
    if suite is None:
        raise AssertionSuiteSyntaxError("testql_suite_missing", 1)
    if not suite.tests:
        raise AssertionSuiteSyntaxError("testql_tests_missing", 1)
    for test in suite.tests:
        if not test.assertions:
            raise AssertionSuiteSyntaxError("testql_assertions_missing", test.line, test.name)
    return suite


def _tokens(expression: str, line: int) -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    position = 0
    while position < len(expression):
        match = _TOKEN.match(expression, position)
        if not match:
            raise AssertionSuiteSyntaxError("unsupported_testql_token", line, expression[position : position + 32])
        position = match.end()
        kind = match.lastgroup or ""
        raw = match.group(kind)
        if kind == "string":
            value: Any = json.loads(raw)
            result.append(("literal", value))
        elif kind == "number":
            result.append(("literal", float(raw) if "." in raw else int(raw)))
        elif kind == "word":
            lowered = raw.lower()
            if lowered in {"true", "false", "null"}:
                result.append(("literal", {"true": True, "false": False, "null": None}[lowered]))
            elif lowered in {"and", "or", "implies", "contains", "exists"}:
                result.append((lowered, lowered))
            else:
                result.append(("path", raw))
        else:
            result.append((kind, raw))
    return result


def parse_expression(expression: str, line: int = 1) -> Any:
    """Return a small AST with ``and`` > ``or`` > ``implies`` precedence."""
    tokens = _tokens(expression, line)
    position = 0

    def peek() -> tuple[str, Any] | None:
        return tokens[position] if position < len(tokens) else None

    def take(kind: str | None = None) -> tuple[str, Any]:
        nonlocal position
        token = peek()
        if token is None or (kind is not None and token[0] != kind):
            actual = token[0] if token else "eof"
            raise AssertionSuiteSyntaxError("unexpected_testql_token", line, f"expected={kind},actual={actual}")
        position += 1
        return token

    def operand() -> Any:
        token = peek()
        if token is None or token[0] not in {"path", "literal"}:
            raise AssertionSuiteSyntaxError("testql_operand_expected", line)
        take()
        return {"kind": token[0], "value": token[1]}

    def primary() -> Any:
        if peek() and peek()[0] == "lparen":
            take("lparen")
            node = implies()
            take("rparen")
            return node
        left = operand()
        operator = take()
        if operator[0] == "exists":
            if peek() and peek()[0] == "literal" and isinstance(peek()[1], bool):
                expected = take("literal")[1]
            else:
                expected = True
            return {"kind": "exists", "left": left, "expected": expected}
        if operator[0] not in {"operator", "contains"}:
            raise AssertionSuiteSyntaxError("testql_operator_expected", line, str(operator[1]))
        return {"kind": "comparison", "operator": operator[1], "left": left, "right": operand()}

    def conjunction() -> Any:
        node = primary()
        while peek() and peek()[0] == "and":
            take("and")
            node = {"kind": "and", "left": node, "right": primary()}
        return node

    def disjunction() -> Any:
        node = conjunction()
        while peek() and peek()[0] == "or":
            take("or")
            node = {"kind": "or", "left": node, "right": conjunction()}
        return node

    def implies() -> Any:
        node = disjunction()
        if peek() and peek()[0] == "implies":
            take("implies")
            node = {"kind": "implies", "left": node, "right": implies()}
        return node

    tree = implies()
    if position != len(tokens):
        raise AssertionSuiteSyntaxError("unexpected_testql_token", line, str(peek()[1] if peek() else "eof"))
    return tree


def _path(context: dict[str, Any], name: str) -> Any:
    value: Any = context
    for part in name.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def _value(node: Any, context: dict[str, Any]) -> Any:
    return _path(context, node["value"]) if node["kind"] == "path" else node["value"]


def evaluate_expression(tree: Any, context: dict[str, Any]) -> bool:
    kind = tree["kind"]
    if kind == "and":
        return evaluate_expression(tree["left"], context) and evaluate_expression(tree["right"], context)
    if kind == "or":
        return evaluate_expression(tree["left"], context) or evaluate_expression(tree["right"], context)
    if kind == "implies":
        return not evaluate_expression(tree["left"], context) or evaluate_expression(tree["right"], context)
    if kind == "exists":
        present = _value(tree["left"], context) is not None
        return present is tree["expected"]
    if kind != "comparison":
        raise ValueError(f"unsupported_testql_ast:{kind}")
    left = _value(tree["left"], context)
    right = _value(tree["right"], context)
    operator = tree["operator"]
    if operator == "contains":
        if isinstance(left, (list, tuple, set)):
            return right in left
        if isinstance(left, dict):
            return right in left
        return str(right) in str(left or "")
    if left is None:
        return False
    try:
        return {
            "==": lambda: left == right,
            "!=": lambda: left != right,
            ">=": lambda: left >= right,
            "<=": lambda: left <= right,
            ">": lambda: left > right,
            "<": lambda: left < right,
        }[operator]()
    except (KeyError, TypeError):
        return False


def run_assertion_suite(
    suite_or_source: AssertionSuite | str,
    context: dict[str, Any] | None = None,
    *,
    filename: str = "<string>",
    dry_run: bool = False,
) -> ScriptResult:
    suite = parse_assertion_suite(suite_or_source, filename) if isinstance(suite_or_source, str) else suite_or_source
    started = time.monotonic()
    steps: list[StepResult] = []
    errors: list[str] = []
    supplied_context = context or {}

    for test in suite.tests:
        for assertion in test.assertions:
            name = f"{test.name}: {assertion.expression}"
            details = {"profile": PROFILE, "line": assertion.line, "test": test.name}
            if dry_run:
                steps.append(StepResult(name=name, status=StepStatus.SKIPPED, message="validated_only", details=details))
                continue
            tree = parse_expression(assertion.expression, assertion.line)
            passed = evaluate_expression(tree, supplied_context)
            message = "" if passed else (assertion.message or f"assertion failed at line {assertion.line}")
            status = StepStatus.PASSED if passed else StepStatus.FAILED
            steps.append(StepResult(name=name, status=status, message=message, details=details))
            if not passed:
                errors.append(f"L{assertion.line}: {message}")

    result = ScriptResult(
        source=suite.filename,
        ok=not errors,
        steps=steps,
        variables={},
        errors=errors,
        warnings=[],
        duration_ms=(time.monotonic() - started) * 1000,
    )
    result.profile = PROFILE
    result.validated = len(steps) if dry_run else 0
    result.executed = 0 if dry_run else len(steps)
    result.skipped = sum(1 for step in steps if step.status == StepStatus.SKIPPED)
    return result

