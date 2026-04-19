"""Report Generator for TestQL - Generates HTML reports from test data."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class TestResult:
    """Single test result."""
    name: str
    status: str  # passed, failed, skipped
    duration_ms: int
    assertions: int
    failures: list[str]


@dataclass
class TestSuiteReport:
    """Test suite report data."""
    suite_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    tests: list[TestResult]


class ReportDataParser:
    """Parse test results into structured data.json format."""

    def parse_testql_results(self, results_file: Path) -> TestSuiteReport:
        """Parse testql run results from log/json file."""
        # Placeholder - actual parsing from testql output
        return TestSuiteReport(
            suite_name="default",
            total=0, passed=0, failed=0, skipped=0, duration_ms=0, tests=[]
        )

    def to_json(self, report: TestSuiteReport) -> str:
        """Convert report to JSON string."""
        return json.dumps(asdict(report), indent=2)


class HTMLReportGenerator:
    """Generate HTML reports from test data."""

    def __init__(self, template_dir: Path | None = None):
        self.template_dir = template_dir or Path(__file__).parent / "templates"

    def generate(self, report: TestSuiteReport, output: Path) -> Path:
        """Generate HTML report file."""
        html = self._render_html(report)
        output.write_text(html, encoding="utf-8")
        return output

    def _render_html(self, report: TestSuiteReport) -> str:
        """Render HTML report content."""
        success_rate = (report.passed / report.total * 100) if report.total else 0

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TestQL Report: {report.suite_name}</title>
    <style>
        :root {{
            --color-pass: #28a745;
            --color-fail: #dc3545;
            --color-skip: #ffc107;
            --color-bg: #f8f9fa;
            --color-text: #212529;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 2rem;
            background: var(--color-bg);
            color: var(--color-text);
        }}
        .header {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        .stat-box {{
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .passed {{ color: var(--color-pass); }}
        .failed {{ color: var(--color-fail); }}
        .skipped {{ color: var(--color-skip); }}
        .test-list {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .test-item {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-item:last-child {{ border-bottom: none; }}
        .status-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }}
        .badge-pass {{ background: #d4edda; color: #155724; }}
        .badge-fail {{ background: #f8d7da; color: #721c24; }}
        .badge-skip {{ background: #fff3cd; color: #856404; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TestQL Report: {report.suite_name}</h1>
        <div class="summary">
            <div class="stat-box">
                <div class="stat-value">{report.total}</div>
                <div>Total</div>
            </div>
            <div class="stat-box">
                <div class="stat-value passed">{report.passed}</div>
                <div>Passed</div>
            </div>
            <div class="stat-box">
                <div class="stat-value failed">{report.failed}</div>
                <div>Failed</div>
            </div>
            <div class="stat-box">
                <div class="stat-value skipped">{report.skipped}</div>
                <div>Skipped</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{success_rate:.1f}%</div>
                <div>Success Rate</div>
            </div>
        </div>
    </div>
    <div class="test-list">
        {''.join(self._render_test_row(t) for t in report.tests)}
    </div>
</body>
</html>"""

    def _render_test_row(self, test: TestResult) -> str:
        badge_class = {
            'passed': 'badge-pass',
            'failed': 'badge-fail',
            'skipped': 'badge-skip'
        }.get(test.status, 'badge-skip')

        failures = ''
        if test.failures:
            failures = f'<div style="color: #dc3545; font-size: 0.875rem; margin-top: 0.5rem;">{"<br>".join(test.failures)}</div>'

        return f"""
        <div class="test-item">
            <div>
                <div style="font-weight: 500;">{test.name}</div>
                <div style="font-size: 0.875rem; color: #6c757d;">{test.duration_ms}ms • {test.assertions} assertions</div>
                {failures}
            </div>
            <span class="status-badge {badge_class}">{test.status.upper()}</span>
        </div>
        """


def _adapt_test_entry(t: dict) -> TestResult:
    """Adapt a test entry to TestResult, supporting both pytest-json-report and native testql formats."""
    # pytest-json-report format: nodeid, outcome, call.duration
    if "nodeid" in t:
        name = t["nodeid"].split("::")[-1]
        status = t.get("outcome", "unknown")
        duration_ms = round((t.get("call", {}) or {}).get("duration", 0) * 1000)
        failures = []
        call = t.get("call") or {}
        if call.get("longrepr"):
            failures = [str(call["longrepr"])[:200]]
        return TestResult(name=name, status=status, duration_ms=duration_ms, assertions=0, failures=failures)
    # Native testql format
    return TestResult(**t)


def generate_report(data_json: Path, output_html: Path) -> Path:
    """Generate HTML report from data.json file."""
    # Load and parse data.json
    data = json.loads(data_json.read_text())

    # Support pytest-json-report top-level format
    summary = data.get("summary", {})
    duration_ms = round(data.get("duration", 0) * 1000)

    report = TestSuiteReport(
        suite_name=data.get("suite_name", "Test Suite"),
        total=summary.get("total", data.get("total", 0)),
        passed=summary.get("passed", data.get("passed", 0)),
        failed=summary.get("failed", data.get("failed", 0)),
        skipped=summary.get("skipped", data.get("skipped", 0)),
        duration_ms=duration_ms or data.get("duration_ms", 0),
        tests=[_adapt_test_entry(t) for t in data.get("tests", [])]
    )

    generator = HTMLReportGenerator()
    return generator.generate(report, output_html)


if __name__ == "__main__":
    # Example usage
    example_data = {
        "suite_name": "API Tests",
        "total": 3,
        "passed": 2,
        "failed": 1,
        "skipped": 0,
        "duration_ms": 1250,
        "tests": [
            {"name": "test_health_endpoint", "status": "passed", "duration_ms": 120, "assertions": 2, "failures": []},
            {"name": "test_user_create", "status": "passed", "duration_ms": 450, "assertions": 5, "failures": []},
            {"name": "test_auth_login", "status": "failed", "duration_ms": 680, "assertions": 3, "failures": ["Expected 200, got 401"]},
        ]
    }

    data_file = Path("example_data.json")
    data_file.write_text(json.dumps(example_data))
    output = generate_report(data_file, Path("report.html"))
    print(f"Report generated: {output}")
