"""Unit tests for :mod:`testql.generators.page_analyzer`.

These exercise pure logic (selector picking, default values, plan construction,
heal-replacement lookup). No browser required.
"""

from __future__ import annotations

import pytest

from testql.generators.page_analyzer import (
    PageSnapshot,
    default_input_value,
    find_replacement,
    is_clickable,
    is_typed_input,
    pick_selector,
    snapshot_to_plan,
)
from testql.ir import GuiStep


# ---------------------------------------------------------------------------
# pick_selector
# ---------------------------------------------------------------------------

class TestPickSelector:
    def test_data_testid_wins(self):
        elem = {"tag": "button", "data_testid": "submit", "id": "btn", "classes": ["btn"]}
        assert pick_selector(elem) == "[data-testid='submit']"

    def test_data_test_fallback(self):
        elem = {"tag": "button", "data_test": "go"}
        assert pick_selector(elem) == "[data-test='go']"

    def test_id_when_stable(self):
        elem = {"tag": "button", "id": "btn-simulate-scan"}
        assert pick_selector(elem) == "#btn-simulate-scan"

    def test_id_skipped_when_unstable(self):
        elem = {"tag": "input", "id": "cdk-overlay-3", "name_attr": "email"}
        assert pick_selector(elem) == "input[name='email']"

    def test_id_skipped_for_uuid_like(self):
        elem = {"tag": "div", "id": "deadbeef1234abcd", "classes": ["card-real"]}
        assert pick_selector(elem) == "div.card-real"

    def test_form_field_name_attr(self):
        elem = {"tag": "input", "name_attr": "username", "input_type": "text"}
        assert pick_selector(elem) == "input[name='username']"

    def test_role_with_aria_label(self):
        elem = {"tag": "div", "role": "button", "aria_label": "Close dialog"}
        assert pick_selector(elem) == "[role='button'][aria-label='Close dialog']"

    def test_input_type_when_distinctive(self):
        elem = {"tag": "input", "input_type": "email"}
        assert pick_selector(elem) == "input[type='email']"

    def test_input_type_text_not_distinctive(self):
        elem = {"tag": "input", "input_type": "text", "classes": ["specific-field"]}
        assert pick_selector(elem) == "input.specific-field"

    def test_skips_generic_classes(self):
        elem = {"tag": "button", "classes": ["btn", "btn-primary", "active"]}
        assert pick_selector(elem) == "button.btn-primary"

    def test_returns_none_when_only_generic(self):
        elem = {"tag": "button", "classes": ["btn", "active", "primary"]}
        assert pick_selector(elem) is None

    def test_returns_none_when_nothing_stable(self):
        elem = {"tag": "div"}
        assert pick_selector(elem) is None

    def test_quote_escaping(self):
        elem = {"tag": "button", "data_testid": "it's me"}
        # Single quote inside attribute value — no double-quote replacement issue
        assert pick_selector(elem) == "[data-testid='it's me']"


# ---------------------------------------------------------------------------
# default_input_value
# ---------------------------------------------------------------------------

class TestDefaultInputValue:
    @pytest.mark.parametrize("input_type,expected", [
        ("email", "test@example.com"),
        ("password", "Password123!"),
        ("tel", "555-0100"),
        ("number", "1"),
        ("date", "2025-01-01"),
    ])
    def test_input_type_takes_precedence(self, input_type, expected):
        assert default_input_value({"input_type": input_type}) == expected

    def test_email_inferred_from_name(self):
        assert default_input_value({"name_attr": "email"}) == "test@example.com"

    def test_password_inferred_from_placeholder(self):
        assert default_input_value({"placeholder": "Hasło"}) == "Password123!"

    def test_search_inferred_from_aria_label(self):
        assert default_input_value({"aria_label": "Search products"}) == "test"

    def test_id_field_uses_id_default(self):
        assert default_input_value({"name_attr": "user_id"}) == "TEST123"

    def test_fallback(self):
        assert default_input_value({}) == "test value"


# ---------------------------------------------------------------------------
# is_typed_input / is_clickable
# ---------------------------------------------------------------------------

class TestClassification:
    def test_textarea_is_typed(self):
        assert is_typed_input({"tag": "textarea"})

    def test_input_email_is_typed(self):
        assert is_typed_input({"tag": "input", "input_type": "email"})

    def test_input_submit_is_not_typed(self):
        assert not is_typed_input({"tag": "input", "input_type": "submit"})

    def test_button_is_clickable(self):
        assert is_clickable({"tag": "button"})

    def test_link_is_clickable(self):
        assert is_clickable({"tag": "a"})

    def test_role_button_clickable(self):
        assert is_clickable({"tag": "div", "role": "button"})

    def test_disabled_not_clickable(self):
        assert not is_clickable({"tag": "button", "disabled": True})

    def test_input_submit_clickable(self):
        assert is_clickable({"tag": "input", "input_type": "submit"})


# ---------------------------------------------------------------------------
# snapshot_to_plan
# ---------------------------------------------------------------------------

class TestSnapshotToPlan:
    def _snap(self, elements):
        return PageSnapshot(url="http://localhost:8100/login", title="Login",
                            path="/login", elements=elements)

    def test_emits_navigate_first(self):
        plan = snapshot_to_plan(self._snap([]))
        gui_steps = [s for s in plan.steps if isinstance(s, GuiStep)]
        assert gui_steps, "expected at least one GuiStep"
        assert gui_steps[0].action == "navigate"
        assert gui_steps[0].path == "/login"

    def test_emits_input_with_default_value(self):
        plan = snapshot_to_plan(self._snap([
            {"tag": "input", "input_type": "email", "name_attr": "email", "visible": True},
        ]))
        inputs = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "input"]
        assert len(inputs) == 1
        # name_attr is more specific than input_type, so it wins
        assert inputs[0].selector == "input[name='email']"
        # value still derived from input_type=email
        assert inputs[0].value == "test@example.com"

    def test_emits_click_for_button(self):
        plan = snapshot_to_plan(self._snap([
            {"tag": "button", "id": "btn-go", "name": "Go", "visible": True},
        ]))
        clicks = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "click"]
        assert len(clicks) == 1
        assert clicks[0].selector == "#btn-go"

    def test_skips_invisible_and_unstable(self):
        plan = snapshot_to_plan(self._snap([
            {"tag": "button", "id": "ok", "visible": False},                     # hidden
            {"tag": "div", "classes": ["btn"]},                                   # only generic class
            {"tag": "button", "id": "btn-simulate-scan", "visible": True},        # kept
        ]))
        clicks = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "click"]
        assert [c.selector for c in clicks] == ["#btn-simulate-scan"]

    def test_dedup_same_selector(self):
        plan = snapshot_to_plan(self._snap([
            {"tag": "button", "id": "btn-go", "visible": True},
            {"tag": "button", "id": "btn-go", "visible": True},
        ]))
        clicks = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "click"]
        assert len(clicks) == 1

    def test_max_steps_respected(self):
        elems = [{"tag": "button", "id": f"btn-{i}", "visible": True} for i in range(20)]
        plan = snapshot_to_plan(self._snap(elems), max_steps=5)
        # NAVIGATE is step 1; the remaining 4 slots are clicks. The trailing
        # ASSERT step is added unconditionally after the cap.
        assert sum(1 for s in plan.steps if isinstance(s, GuiStep) and s.action == "click") == 4

    def test_metadata_records_source_url(self):
        plan = snapshot_to_plan(self._snap([]))
        assert plan.metadata.type == "gui"
        assert plan.metadata.extra["source"] == "page_analyzer"
        assert plan.metadata.extra["source_url"].endswith("/login")


# ---------------------------------------------------------------------------
# find_replacement (heal logic)
# ---------------------------------------------------------------------------

class TestFindReplacement:
    def test_replaces_broken_class_with_id_match(self):
        elements = [
            {"tag": "ul", "id": "user-list-real", "classes": ["users"]},
        ]
        # Old selector .user-list (no longer exists). Hint = "user-list".
        result = find_replacement(".user-list", elements)
        assert result == "#user-list-real"

    def test_exact_accessible_name_match_wins(self):
        elements = [
            {"tag": "button", "id": "x", "name": "Submit"},
            {"tag": "button", "id": "y", "name": "Submit form", "classes": ["submit-btn"]},
        ]
        # Broken selector hint = "submit"; first elem has exact name match.
        result = find_replacement("[data-testid='submit']", elements)
        assert result == "#x"

    def test_returns_none_when_no_match(self):
        elements = [
            {"tag": "div", "id": "totally-unrelated"},
        ]
        result = find_replacement(".qr-scanner-container", elements)
        assert result is None

    def test_token_match_picks_best(self):
        elements = [
            {"tag": "div", "id": "scanner-qr", "name": "QR Code Scanner",
             "classes": ["scanner-qr-real"]},
            {"tag": "div", "id": "user-input", "name": "User Input"},
        ]
        result = find_replacement(".qr-scanner-container", elements)
        assert result == "#scanner-qr"
