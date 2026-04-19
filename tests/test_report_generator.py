"""Tests for testql/report_generator.py"""
import json
from pathlib import Path
import pytest

from testql.report_generator import (
    TestResult,
    TestSuiteReport,
    ReportDataParser,
    HTMLReportGenerator,
)


def _make_report(**kwargs):
    defaults = dict(
        suite_name="my-suite",
        total=3,
        passed=2,
        failed=1,
        skipped=0,
        duration_ms=150,
        tests=[
            TestResult("test_a", "passed", 50, 2, []),
            TestResult("test_b", "passed", 60, 3, []),
            TestResult("test_c", "failed", 40, 1, ["expected 200 got 404"]),
        ],
    )
    defaults.update(kwargs)
    return TestSuiteReport(**defaults)


class TestTestResult:
    def test_create(self):
        r = TestResult("my_test", "passed", 100, 5, [])
        assert r.name == "my_test"
        assert r.status == "passed"
        assert r.duration_ms == 100
        assert r.assertions == 5
        assert r.failures == []

    def test_create_with_failures(self):
        r = TestResult("bad_test", "failed", 20, 1, ["err1", "err2"])
        assert r.failures == ["err1", "err2"]


class TestTestSuiteReport:
    def test_create(self):
        report = _make_report()
        assert report.suite_name == "my-suite"
        assert report.total == 3
        assert report.passed == 2
        assert report.failed == 1

    def test_zero_report(self):
        report = _make_report(total=0, passed=0, failed=0, skipped=0, tests=[])
        assert report.total == 0


class TestReportDataParser:
    def test_parse_testql_results_returns_report(self, tmp_path):
        parser = ReportDataParser()
        fake = tmp_path / "results.json"
        fake.write_text("{}")
        result = parser.parse_testql_results(fake)
        assert isinstance(result, TestSuiteReport)
        assert result.suite_name == "default"
        assert result.total == 0

    def test_to_json_is_valid_json(self):
        parser = ReportDataParser()
        report = _make_report()
        output = parser.to_json(report)
        data = json.loads(output)
        assert data["suite_name"] == "my-suite"
        assert data["total"] == 3

    def test_to_json_includes_tests(self):
        parser = ReportDataParser()
        report = _make_report()
        output = parser.to_json(report)
        data = json.loads(output)
        assert len(data["tests"]) == 3
        assert data["tests"][0]["name"] == "test_a"

    def test_to_json_empty_suite(self):
        parser = ReportDataParser()
        report = _make_report(total=0, passed=0, failed=0, tests=[])
        output = parser.to_json(report)
        data = json.loads(output)
        assert data["total"] == 0
        assert data["tests"] == []


class TestHTMLReportGenerator:
    def test_generate_creates_file(self, tmp_path):
        gen = HTMLReportGenerator()
        report = _make_report()
        out = tmp_path / "report.html"
        result = gen.generate(report, out)
        assert out.exists()
        assert result == out

    def test_html_contains_suite_name(self, tmp_path):
        gen = HTMLReportGenerator()
        report = _make_report(suite_name="alpha-suite")
        out = tmp_path / "report.html"
        gen.generate(report, out)
        html = out.read_text()
        assert "alpha-suite" in html

    def test_html_contains_stats(self, tmp_path):
        gen = HTMLReportGenerator()
        report = _make_report(total=5, passed=4, failed=1)
        out = tmp_path / "report.html"
        gen.generate(report, out)
        html = out.read_text()
        assert "5" in html
        assert "4" in html
        assert "1" in html

    def test_html_contains_test_names(self, tmp_path):
        gen = HTMLReportGenerator()
        report = _make_report()
        out = tmp_path / "report.html"
        gen.generate(report, out)
        html = out.read_text()
        assert "test_a" in html
        assert "test_c" in html

    def test_success_rate_zero_total(self, tmp_path):
        """Zero-total report should not crash."""
        gen = HTMLReportGenerator()
        report = _make_report(total=0, passed=0, failed=0, skipped=0, tests=[])
        out = tmp_path / "report.html"
        gen.generate(report, out)
        html = out.read_text()
        assert "0%" in html or "0.0" in html or len(html) > 100

    def test_html_is_valid_start(self, tmp_path):
        gen = HTMLReportGenerator()
        report = _make_report()
        out = tmp_path / "report.html"
        gen.generate(report, out)
        html = out.read_text()
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_custom_template_dir(self, tmp_path):
        gen = HTMLReportGenerator(template_dir=tmp_path)
        assert gen.template_dir == tmp_path

    def test_render_html_returns_string(self):
        gen = HTMLReportGenerator()
        report = _make_report()
        html = gen._render_html(report)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_html_failed_test_name(self):
        gen = HTMLReportGenerator()
        report = _make_report()
        html = gen._render_html(report)
        assert "test_c" in html

    def test_render_html_failure_message(self):
        gen = HTMLReportGenerator()
        report = _make_report()
        html = gen._render_html(report)
        assert "404" in html
