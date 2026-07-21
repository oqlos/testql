from __future__ import annotations

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine
from testql.interpreter._performance import parse_measure_navigation_args


class FakePage:
    def __init__(self) -> None:
        self.init_script = ""
        self.url = "about:blank"

    def add_init_script(self, script: str) -> None:
        self.init_script = script

    def goto(self, url: str, *, timeout: int) -> None:
        self.url = url

    def performance_metrics(self, script: str) -> list[dict]:
        return [
            {
                "time_origin": 1_000,
                "ready_ms": None,
                "response_ms": 12.25,
                "dom_content_loaded_ms": 100.0,
                "load_event_ms": 150.0,
                "resource_count": 5,
                "transfer_bytes": 700,
                "script_bytes": 300,
                "long_task_count": 0,
                "long_task_ms": 0.0,
            },
            {
                "time_origin": 1_200,
                "ready_ms": 121.5,
                "resource_count": 3,
                "transfer_bytes": 324,
                "script_bytes": 212,
                "long_task_count": 0,
                "long_task_ms": 0.0,
            },
        ]


def test_parse_measure_navigation_args() -> None:
    assert parse_measure_navigation_args(
        '"/connect-scenario?view=protocol" ".scenario-embedded-root" timeout=9000 as=_perf'
    ) == ("/connect-scenario?view=protocol", ".scenario-embedded-root", 9000, "_perf")


def test_gui_measure_navigation_captures_structured_metrics() -> None:
    interpreter = OqlInterpreter(variables={"base_url": "http://localhost:8100"}, quiet=True)
    page = FakePage()
    interpreter._gui_page = page
    interpreter._gui_driver = "playwright"

    interpreter._cmd_gui_measure_navigation(
        '"/connect-scenario" ".scenario-embedded-root" timeout=1000 as=_performance',
        OqlLine(number=1, command="GUI_MEASURE_NAVIGATION", args="", raw=""),
    )

    metrics = interpreter.vars.get("_performance")
    assert metrics["ready_ms"] == 321.5
    assert metrics["response_ms"] == 12.25
    assert metrics["frame_count"] == 2
    assert metrics["navigation_ms"] >= 0
    assert page.url == "http://localhost:8100/connect-scenario"
    assert ".scenario-embedded-root" in page.init_script
    assert interpreter.results[-1].details["transfer_bytes"] == 1024


def test_about_blank_is_a_supported_browser_start_target() -> None:
    class StartProbe(OqlInterpreter):
        def _init_gui_driver(self) -> bool:
            self._gui_driver = "playwright"
            return True

        def _start_playwright(self, app_path: str, extra_args: str) -> None:
            self.started_path = app_path

    interpreter = StartProbe(quiet=True)
    interpreter._cmd_gui_start(
        '"about:blank"',
        OqlLine(number=1, command="GUI_START", args='"about:blank"', raw='GUI_START "about:blank"'),
    )
    assert interpreter.started_path == "about:blank"
