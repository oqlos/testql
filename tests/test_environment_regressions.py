"""Regression tests found while integrating TestQL with a full environment."""

from testql.interpreter import OqlInterpreter
from testql.interpreter._testtoon_parser import testtoon_to_oql as convert_testtoon_to_oql
from testql.interpreter._parser import OqlLine


def test_navigate_section_starts_browser_before_navigation():
    source = """\
# SCENARIO: navigation
# TYPE: gui
NAVIGATE[2]{path, wait_ms}:
  http://127.0.0.1:8091, 10
  /projects, 20
"""

    commands = [line.command for line in convert_testtoon_to_oql(source).lines]

    assert commands == ["GUI_START", "WAIT", "NAVIGATE", "WAIT"]


def test_shell_result_keeps_bounded_stdout_and_stderr():
    interpreter = OqlInterpreter(api_url="http://localhost", quiet=True)
    line = OqlLine(
        number=1,
        command="SHELL",
        args='"printf output; printf error >&2; exit 7" 5000',
        raw='SHELL "printf output; printf error >&2; exit 7" 5000',
    )

    interpreter._cmd_shell(line.args, line)

    details = interpreter.results[-1].details
    assert details["returncode"] == 7
    assert details["stdout"] == "output"
    assert details["stderr"] == "error"
