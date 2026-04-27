"""Browser-agnostic page analysis helpers.

This module turns a list of element descriptors (plain ``dict``s — typically
extracted by Playwright in :mod:`testql.generators.sources.page_source`)
into a :class:`testql.ir.TestPlan` ready for rendering as TestTOON.

Pure logic, no I/O, no browser dependency — easy to unit-test without
spinning up Chromium.

Element descriptor shape (all keys optional except ``tag``)::

    {
        "tag": "button",                    # raw HTML tag (lower-case)
        "role": "button",                   # ARIA role (computed or explicit)
        "name": "Submit",                   # accessible name (label / aria-label / text)
        "id": "btn-submit",                 # element id (or None)
        "data_testid": "submit",            # data-testid value (or None)
        "data_test": None,                  # data-test value (or None)
        "name_attr": "email",               # form field name="" (or None)
        "input_type": "email",              # input[type] (or None)
        "aria_label": None,
        "placeholder": "Email address",
        "href": None,                       # for <a>
        "text": "Submit",                   # textContent (trimmed)
        "classes": ["btn", "btn-primary"],
        "disabled": False,
        "visible": True,
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from testql.ir import Assertion, GuiStep, ScenarioMetadata, Step, TestPlan


# ---------------------------------------------------------------------------
# Selector picking
# ---------------------------------------------------------------------------

# Regex matching id/class names that look auto-generated and therefore unstable.
_UNSTABLE_ID_PATTERNS = (
    re.compile(r"^[a-z]+-[a-z]+-\d+$", re.I),     # cdk-overlay-3, mat-input-12
    re.compile(r"^[a-z]+\d{3,}$", re.I),          # ember1234
    re.compile(r"^:.*:$"),                         # React's :r0:, :r1:
    re.compile(r"^[a-f0-9-]{8,}$", re.I),          # uuid-like
)

# Generic class names that don't uniquely identify an element.
_GENERIC_CLASSES = frozenset({
    "btn", "button", "icon", "input", "form", "label", "field",
    "container", "wrapper", "row", "col", "item", "active", "selected",
    "primary", "secondary", "success", "error", "warning", "info",
    "small", "medium", "large", "hidden", "visible", "block", "inline",
    "flex", "grid", "card", "modal", "panel", "header", "footer", "main",
    "nav", "menu", "list",
})


def _is_unstable(value: str) -> bool:
    return any(p.match(value) for p in _UNSTABLE_ID_PATTERNS)


def _css_escape(value: str) -> str:
    """Escape characters that are unsafe inside a CSS attribute selector value."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def pick_selector(elem: dict[str, Any]) -> Optional[str]:
    """Pick the most stable CSS selector for an element descriptor.

    Returns ``None`` when no reasonably stable selector can be derived; the
    caller should skip the element in that case (better than emitting a
    fragile selector that breaks on the next deploy).

    Priority (highest first):
        1. ``[data-testid='X']`` / ``[data-test='X']``
        2. ``#id``  (skipped when the id looks auto-generated)
        3. ``tag[name='X']``  (form fields)
        4. ``[role='X'][aria-label='Y']``
        5. ``tag[type='X']``  (e.g. ``input[type='email']``) — only when distinctive
        6. ``tag.classname``  (only for class names not in :data:`_GENERIC_CLASSES`)
    """
    strategies = [
        _try_testid_selector,
        _try_id_selector,
        _try_name_selector,
        _try_role_aria_selector,
        _try_input_type_selector,
        _try_class_selector,
    ]
    
    for strategy in strategies:
        selector = strategy(elem)
        if selector:
            return selector
    
    return None


def _try_testid_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build a data-testid/data-test selector."""
    testid = elem.get("data_testid") or elem.get("data_test")
    if testid:
        attr = "data-testid" if elem.get("data_testid") else "data-test"
        return f"[{attr}='{_css_escape(str(testid))}']"
    return None


def _try_id_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build an ID selector."""
    el_id = elem.get("id")
    if el_id and not _is_unstable(str(el_id)):
        return f"#{el_id}"
    return None


def _try_name_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build a name attribute selector."""
    tag = (elem.get("tag") or "").lower() or "*"
    name_attr = elem.get("name_attr")
    if name_attr:
        return f"{tag}[name='{_css_escape(str(name_attr))}']"
    return None


def _try_role_aria_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build a role + aria-label selector."""
    role = elem.get("role")
    aria = elem.get("aria_label")
    if role and aria:
        return f"[role='{_css_escape(str(role))}'][aria-label='{_css_escape(str(aria))}']"
    return None


def _try_input_type_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build an input type selector for distinctive types."""
    tag = (elem.get("tag") or "").lower()
    input_type = elem.get("input_type")
    if tag == "input" and input_type and input_type not in ("text", "submit", "button"):
        return f"input[type='{_css_escape(str(input_type))}']"
    return None


def _try_class_selector(elem: dict[str, Any]) -> Optional[str]:
    """Try to build a class selector using non-generic, stable classes."""
    tag = (elem.get("tag") or "").lower() or "*"
    classes = [c for c in (elem.get("classes") or []) if c and c not in _GENERIC_CLASSES]
    classes = [c for c in classes if not _is_unstable(c)]
    if classes:
        return f"{tag}.{classes[0]}"
    return None


# ---------------------------------------------------------------------------
# Default input values
# ---------------------------------------------------------------------------

_INPUT_VALUE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"e[\-_ ]?mail|@", re.I), "test@example.com"),
    (re.compile(r"password|has[lł]o", re.I), "Password123!"),
    (re.compile(r"phone|tel(efon)?|gsm", re.I), "555-0100"),
    (re.compile(r"url|website|link", re.I), "https://example.com"),
    (re.compile(r"search|szukaj|find|filter", re.I), "test"),
    (re.compile(r"first[\-_ ]?name|imi[eę]", re.I), "Test"),
    (re.compile(r"last[\-_ ]?name|nazwisko", re.I), "User"),
    (re.compile(r"name|nazw[ae]", re.I), "Test User"),
    (re.compile(r"id\b|identifier|pesel|nip", re.I), "TEST123"),
    (re.compile(r"city|miast[oa]", re.I), "Warsaw"),
    (re.compile(r"date|data|day|month|year", re.I), "2025-01-01"),
    (re.compile(r"comment|message|notes?|wiadomo", re.I), "Test message"),
    (re.compile(r"amount|kwota|price|cena|number|liczb", re.I), "1"),
]

_INPUT_TYPE_VALUES = {
    "email": "test@example.com",
    "password": "Password123!",
    "tel": "555-0100",
    "url": "https://example.com",
    "search": "test",
    "number": "1",
    "date": "2025-01-01",
    "time": "12:00",
    "datetime-local": "2025-01-01T12:00",
    "month": "2025-01",
    "week": "2025-W01",
    "color": "#000000",
}


def default_input_value(elem: dict[str, Any]) -> str:
    """Pick a sensible placeholder value for a typed-input field.

    Looks at ``input_type`` first (deterministic), then matches ``name_attr``,
    ``placeholder``, ``aria_label``, ``name``, and ``id`` against a list of
    domain hints. Falls back to ``"test value"``.
    """
    itype = (elem.get("input_type") or "").lower()
    if itype in _INPUT_TYPE_VALUES:
        return _INPUT_TYPE_VALUES[itype]

    haystack_parts: list[str] = []
    for key in ("name_attr", "placeholder", "aria_label", "name", "id"):
        v = elem.get(key)
        if v:
            haystack_parts.append(str(v))
    haystack = " ".join(haystack_parts)
    if haystack:
        for pattern, value in _INPUT_VALUE_PATTERNS:
            if pattern.search(haystack):
                return value
    return "test value"


# ---------------------------------------------------------------------------
# Element classification
# ---------------------------------------------------------------------------

_TYPED_INPUT_TYPES = frozenset({
    "text", "email", "password", "tel", "url", "search", "number",
    "date", "time", "datetime-local", "month", "week", "color",
})


def is_typed_input(elem: dict[str, Any]) -> bool:
    """Return True for elements that should receive a GUI_INPUT step."""
    tag = (elem.get("tag") or "").lower()
    if tag == "textarea":
        return True
    if tag != "input":
        return False
    itype = (elem.get("input_type") or "text").lower()
    return itype in _TYPED_INPUT_TYPES


def is_clickable(elem: dict[str, Any]) -> bool:
    """Return True for elements that should receive a GUI_CLICK step."""
    if elem.get("disabled"):
        return False
    tag = (elem.get("tag") or "").lower()
    role = (elem.get("role") or "").lower()
    if tag in {"button", "a", "summary"}:
        return True
    if role in {"button", "link", "menuitem", "tab", "switch", "checkbox", "radio"}:
        return True
    if tag == "input" and (elem.get("input_type") or "").lower() in {"submit", "button", "checkbox", "radio"}:
        return True
    return False


# ---------------------------------------------------------------------------
# Plan construction
# ---------------------------------------------------------------------------

@dataclass
class PageSnapshot:
    """Result of analysing one page — the input to plan construction."""

    url: str
    title: str = ""
    path: str = "/"
    elements: list[dict[str, Any]] = None  # type: ignore[assignment]
    nav_links: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.elements is None:
            self.elements = []
        if self.nav_links is None:
            self.nav_links = []


def _name_or_selector(elem: dict[str, Any], selector: str) -> str:
    """Short, unique step name."""
    name = (elem.get("name") or elem.get("text") or selector).strip()
    return name[:40] if name else selector


def snapshot_to_plan(
    snap: PageSnapshot,
    *,
    base_url: Optional[str] = None,
    include_inputs: bool = True,
    include_clicks: bool = True,
    include_assert_visible: bool = True,
    max_steps: int = 50,
) -> TestPlan:
    """Build a :class:`TestPlan` from one :class:`PageSnapshot`.

    Selectors are picked via :func:`pick_selector`; elements without a stable
    selector are skipped. Typed inputs receive a default value from
    :func:`default_input_value`. Buttons / links receive a click step. An
    ``ASSERT_VISIBLE`` step is added per selector when ``include_assert_visible``.
    """
    plan = _create_base_plan(snap, base_url)
    _add_navigate_step(plan, snap.path)
    
    seen_selectors = _process_elements(plan, snap.elements, include_inputs, include_clicks, include_assert_visible, max_steps)
    
    if include_assert_visible:
        _add_body_assertion(plan)
    
    return plan


def _create_base_plan(snap: PageSnapshot, base_url: Optional[str]) -> TestPlan:
    """Create the base test plan with metadata."""
    plan = TestPlan(metadata=ScenarioMetadata(
        name=f"Auto-generated for {snap.title or snap.url}",
        type="gui",
        extra={"source": "page_analyzer", "source_url": snap.url},
    ))
    if base_url:
        plan.config["base_url"] = base_url
    return plan


def _add_navigate_step(plan: TestPlan, path: str) -> None:
    """Add the initial navigate step."""
    plan.steps.append(GuiStep(
        action="navigate",
        path=path or "/",
        wait_ms=300,
        name="navigate",
    ))


def _process_elements(
    plan: TestPlan,
    elements: list[dict[str, Any]] | None,
    include_inputs: bool,
    include_clicks: bool,
    include_assert_visible: bool,
    max_steps: int,
) -> set[str]:
    """Process elements and add appropriate steps to the plan."""
    seen_selectors: set[str] = set()
    
    for elem in elements or []:
        if len(plan.steps) >= max_steps:
            break
        if not elem.get("visible", True):
            continue
        
        sel = pick_selector(elem)
        if not sel or sel in seen_selectors:
            continue
        
        if _should_add_input_step(elem, include_inputs):
            _add_input_step(plan, elem, sel)
            seen_selectors.add(sel)
        elif _should_add_click_step(elem, include_clicks):
            _add_click_step(plan, elem, sel)
            seen_selectors.add(sel)
        elif _should_add_assert_visible(elem, include_assert_visible):
            _add_assert_visible_step(plan, elem, sel)
            seen_selectors.add(sel)
    
    return seen_selectors


def _should_add_input_step(elem: dict[str, Any], include_inputs: bool) -> bool:
    """Check if an input step should be added for this element."""
    return is_typed_input(elem) and include_inputs


def _add_input_step(plan: TestPlan, elem: dict[str, Any], selector: str) -> None:
    """Add an input step to the plan."""
    value = default_input_value(elem)
    plan.steps.append(GuiStep(
        action="input",
        selector=selector,
        value=value,
        name=f"input_{_name_or_selector(elem, selector)}",
    ))


def _should_add_click_step(elem: dict[str, Any], include_clicks: bool) -> bool:
    """Check if a click step should be added for this element."""
    return is_clickable(elem) and include_clicks


def _add_click_step(plan: TestPlan, elem: dict[str, Any], selector: str) -> None:
    """Add a click step to the plan."""
    plan.steps.append(GuiStep(
        action="click",
        selector=selector,
        name=f"click_{_name_or_selector(elem, selector)}",
    ))


def _should_add_assert_visible(elem: dict[str, Any], include_assert_visible: bool) -> bool:
    """Check if an assert_visible step should be added for this element."""
    if not include_assert_visible:
        return False
    tag = (elem.get("tag") or "").lower()
    return tag in {"h1", "h2", "h3", "main", "header", "nav"}


def _add_assert_visible_step(plan: TestPlan, elem: dict[str, Any], selector: str) -> None:
    """Add an assert_visible step to the plan."""
    plan.steps.append(GuiStep(
        action="assert_visible",
        selector=selector,
        name=f"visible_{_name_or_selector(elem, selector)}",
        asserts=[Assertion(field=selector, op="==", expected="visible")],
    ))


def _add_body_assertion(plan: TestPlan) -> None:
    """Add final body-visibility sentinel step."""
    plan.steps.append(GuiStep(
        action="assert_visible",
        selector="body",
        name="visible_body",
    ))


# ---------------------------------------------------------------------------
# Heal: replacement selector lookup
# ---------------------------------------------------------------------------

def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def find_replacement(
    broken_selector: str,
    elements: Iterable[dict[str, Any]],
) -> Optional[str]:
    """Find a replacement selector by accessible-name match.

    Strategy: derive a *hint* from the broken selector (id, class name, attr
    value, or last path segment), then look for an element whose ``name`` /
    ``aria_label`` / ``id`` / ``classes`` contains a normalised version of
    that hint. Returns the new stable selector via :func:`pick_selector`,
    or ``None`` if nothing fuzzy-matches.
    """
    hint = _hint_from_selector(broken_selector)
    if not hint:
        return None
    
    normalised_hint = _normalise(hint)
    candidates = list(elements)
    
    # Try exact accessible-name match first
    exact_match = _find_exact_match(candidates, normalised_hint)
    if exact_match:
        return exact_match
    
    # Fallback to substring match
    return _find_fuzzy_match(candidates, normalised_hint)


def _find_exact_match(candidates: list[dict[str, Any]], normalised_hint: str) -> Optional[str]:
    """Find element with exact accessible-name match."""
    for elem in candidates:
        for key in ("name", "aria_label", "text"):
            v = elem.get(key)
            if v and _normalise(str(v)) == normalised_hint:
                sel = pick_selector(elem)
                if sel:
                    return sel
    return None


def _find_fuzzy_match(candidates: list[dict[str, Any]], normalised_hint: str) -> Optional[str]:
    """Find element with best substring match score."""
    tokens = [t for t in re.split(r"[\s\-_]+", normalised_hint) if t]
    if not tokens:
        return None
    
    best: tuple[int, Optional[str]] = (0, None)
    for elem in candidates:
        haystack_norm = _build_element_haystack(elem)
        score = sum(1 for t in tokens if t in haystack_norm)
        if score > best[0]:
            sel = pick_selector(elem)
            if sel:
                best = (score, sel)
    return best[1]


def _build_element_haystack(elem: dict[str, Any]) -> str:
    """Build a normalized search string from element attributes."""
    haystack_parts = [
        str(elem.get(k) or "")
        for k in (
            "name", "aria_label", "id", "name_attr",
            "data_testid", "data_test", "text", "placeholder",
        )
    ]
    haystack_parts.extend(elem.get("classes") or [])
    return _normalise(" ".join(haystack_parts))


_HINT_RE = re.compile(
    r"""
    (?:\#(?P<id>[A-Za-z][\w\-]*))                                   # #id
    | (?:\.(?P<cls>[A-Za-z][\w\-]*))                                # .class
    | (?:\[\s*[A-Za-z\-]+\s*[*~|^$]?=\s*['"]?(?P<attr>[^'"\]]+))    # [attr="value"]
    | (?:^(?P<tag>[A-Za-z][\w\-]*))                                 # leading tag
    """,
    re.VERBOSE,
)


def _hint_from_selector(selector: str) -> str:
    """Extract a human hint from a CSS selector for fuzzy matching."""
    m = _HINT_RE.search(selector or "")
    if not m:
        return selector
    return m.group("id") or m.group("cls") or m.group("attr") or m.group("tag") or selector


__all__ = [
    "PageSnapshot",
    "pick_selector",
    "default_input_value",
    "is_typed_input",
    "is_clickable",
    "snapshot_to_plan",
    "find_replacement",
]
