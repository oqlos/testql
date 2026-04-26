"""End-to-end tests for ``testql generate-from-page`` and ``testql heal-scenario``.

These tests use the ``--from-elements`` flag to bypass Playwright entirely,
keeping CI hermetic. The Playwright path itself is exercised manually.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from testql.commands.generate_from_page_cmd import generate_from_page
from testql.commands.heal_scenario_cmd import heal_scenario


# Realistic descriptor list mirroring what the JS extractor in
# ``page_source._EXTRACT_JS`` produces for a tiny login page.
_LOGIN_ELEMENTS: list[dict] = [
    {
        "tag": "h1", "role": None, "name": "Sign in", "id": "title",
        "data_testid": None, "data_test": None, "name_attr": None,
        "input_type": None, "aria_label": None, "placeholder": None,
        "href": None, "text": "Sign in", "classes": ["page-title-real"],
        "disabled": False, "visible": True,
    },
    {
        "tag": "input", "role": None, "name": "Email",
        "id": "email", "data_testid": "login-email", "data_test": None,
        "name_attr": "email", "input_type": "email", "aria_label": None,
        "placeholder": "Email address", "href": None, "text": "",
        "classes": ["form-input-real"], "disabled": False, "visible": True,
    },
    {
        "tag": "input", "role": None, "name": "Password",
        "id": "password", "data_testid": None, "data_test": None,
        "name_attr": "password", "input_type": "password", "aria_label": None,
        "placeholder": "Hasło", "href": None, "text": "",
        "classes": ["form-input-real"], "disabled": False, "visible": True,
    },
    {
        "tag": "button", "role": "button", "name": "Submit",
        "id": "btn-login", "data_testid": "login-submit", "data_test": None,
        "name_attr": None, "input_type": "submit", "aria_label": None,
        "placeholder": None, "href": None, "text": "Submit",
        "classes": ["btn", "btn-primary"], "disabled": False, "visible": True,
    },
]


def _write_elements(tmp_path: Path) -> Path:
    p = tmp_path / "elements.json"
    p.write_text(json.dumps(_LOGIN_ELEMENTS), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# generate-from-page
# ---------------------------------------------------------------------------

class TestGenerateFromPageCli:
    def test_writes_scenario_with_expected_steps(self, tmp_path: Path):
        elements_path = _write_elements(tmp_path)
        out = tmp_path / "login.testql.toon.yaml"
        runner = CliRunner()
        result = runner.invoke(generate_from_page, [
            "http://localhost:8100/login",
            "--output", str(out),
            "--from-elements", str(elements_path),
        ])
        assert result.exit_code == 0, result.output
        content = out.read_text(encoding="utf-8")
        # Header / config
        assert "# TYPE: gui" in content
        assert "base_url, http://localhost:8100" in content
        # NAVIGATE step
        assert "NAVIGATE[" in content and "/login" in content
        # The login button selected via data-testid (most stable). The
        # renderer prefixes a universal selector so TOON doesn't parse the
        # bracket cell as a list literal — `*[data-testid='X']` is the
        # TOON-safe form that still resolves to the same DOM element.
        assert "*[data-testid='login-submit']" in content
        # email input via name_attr (more specific than input_type='email')
        assert "*[data-testid='login-email']" in content or "input[name='email']" in content
        # The password input received the Polish-aware default
        assert "Password123!" in content

    def test_print_only_does_not_write_file(self, tmp_path: Path):
        elements_path = _write_elements(tmp_path)
        runner = CliRunner()
        result = runner.invoke(generate_from_page, [
            "http://localhost:8100/login",
            "--from-elements", str(elements_path),
            "--print",
        ])
        assert result.exit_code == 0, result.output
        assert "# TYPE: gui" in result.output
        assert not (tmp_path / "generated-page-login.testql.toon.yaml").exists()

    def test_max_steps_caps_output(self, tmp_path: Path):
        # 30 buttons; cap to 5 steps including NAVIGATE.
        elements = [
            {
                "tag": "button", "role": "button", "name": f"B{i}",
                "id": f"btn-{i}", "data_testid": None, "data_test": None,
                "name_attr": None, "input_type": None, "aria_label": None,
                "placeholder": None, "href": None, "text": f"B{i}",
                "classes": [], "disabled": False, "visible": True,
            }
            for i in range(30)
        ]
        elements_path = tmp_path / "many.json"
        elements_path.write_text(json.dumps(elements), encoding="utf-8")
        out = tmp_path / "many.testql.toon.yaml"
        runner = CliRunner()
        result = runner.invoke(generate_from_page, [
            "http://x/y",
            "--output", str(out),
            "--from-elements", str(elements_path),
            "--max-steps", "5",
        ])
        assert result.exit_code == 0
        content = out.read_text(encoding="utf-8")
        # NAVIGATE always present, then up to (max_steps - 1) clicks.
        click_count = content.count("\n  click,")
        assert click_count <= 4


# ---------------------------------------------------------------------------
# heal-scenario
# ---------------------------------------------------------------------------

class TestHealScenarioCli:
    def _scenario_with_broken_selectors(self) -> str:
        # A tiny scenario that uses selectors which won't appear in
        # _LOGIN_ELEMENTS (so heal must replace them).
        return (
            "# SCENARIO: legacy-login\n"
            "# TYPE: gui\n"
            "\n"
            "FLOW[1]{command, target, value}:\n"
            "  input, .email-old, hello@example.com\n"
            "\n"
            "FLOW[1]{command, target, meta}:\n"
            "  click, #login-submit, -\n"
        )

    def test_heals_class_selector_via_fuzzy_match(self, tmp_path: Path):
        scenario = tmp_path / "legacy.testql.toon.yaml"
        scenario.write_text(self._scenario_with_broken_selectors(), encoding="utf-8")
        elements_path = _write_elements(tmp_path)

        runner = CliRunner()
        result = runner.invoke(heal_scenario, [
            str(scenario),
            "--url", "http://localhost:8100/login",
            "--from-elements", str(elements_path),
        ])
        assert result.exit_code == 0, result.output

        healed = scenario.with_suffix(".healed.testql.toon.yaml")
        assert healed.exists(), result.output
        text = healed.read_text(encoding="utf-8")
        # `.email-old` → `[data-testid='login-email']` (fuzzy-matched on "email" token).
        # Heal writes the *raw* pick_selector output (no `*` prefix) — the prefix
        # is only added by the renderer when a TestPlan is rendered fresh.
        assert ".email-old" not in text
        assert "[data-testid='login-email']" in text
        # `#login-submit` → `[data-testid='login-submit']`
        assert "#login-submit" not in text
        assert "[data-testid='login-submit']" in text

    def test_write_in_place(self, tmp_path: Path):
        scenario = tmp_path / "legacy.testql.toon.yaml"
        scenario.write_text(self._scenario_with_broken_selectors(), encoding="utf-8")
        elements_path = _write_elements(tmp_path)
        runner = CliRunner()
        result = runner.invoke(heal_scenario, [
            str(scenario),
            "--url", "http://localhost:8100/login",
            "--from-elements", str(elements_path),
            "--write",
        ])
        assert result.exit_code == 0, result.output
        text = scenario.read_text(encoding="utf-8")
        assert "[data-testid='login-submit']" in text
        # No .healed file when --write
        assert not scenario.with_suffix(".healed.testql.toon.yaml").exists()

    def test_unhealable_selector_reported(self, tmp_path: Path):
        scenario = tmp_path / "weird.testql.toon.yaml"
        scenario.write_text(
            "# SCENARIO: weird\n"
            "# TYPE: gui\n"
            "\n"
            "FLOW[1]{command, target, meta}:\n"
            "  click, .completely-unrelated-zzz, -\n",
            encoding="utf-8",
        )
        elements_path = _write_elements(tmp_path)
        report_path = tmp_path / "report.json"
        runner = CliRunner()
        result = runner.invoke(heal_scenario, [
            str(scenario),
            "--url", "http://localhost:8100/login",
            "--from-elements", str(elements_path),
            "--report", str(report_path),
        ])
        assert result.exit_code == 0, result.output
        assert "Unhealable" in result.output
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["healed"] == 0
        assert any(
            entry["selector"] == ".completely-unrelated-zzz"
            for entry in report["unhealable"]
        )
