"""Tests for MODBUS interpreter commands."""

from __future__ import annotations

from testql.interpreter import OqlInterpreter
from testql.interpreter._testtoon_parser import testtoon_to_oql, parse_testtoon
from testql.base import StepStatus


class TestModbusToonExpansion:
    def test_modbus_probe_section(self):
        source = (
            "MODBUS[1]{action, serial, baud, parity, function}:\n"
            "  probe, /dev/ttyTEST0, 9600, N, read_coils\n"
        )
        script = testtoon_to_oql(source)
        assert len(script.lines) == 1
        assert script.lines[0].command == "MODBUS"
        assert "probe" in script.lines[0].args
        args = script.lines[0].args.lower()
        assert "probe" in args
        assert "serial=/dev/ttytest0" in args
        assert "baud=9600" in args


class TestModbusDryRun:
    def test_modbus_probe_dry_run(self):
        interp = OqlInterpreter(dry_run=True)
        interp.run("MODBUS probe serial=/dev/ttyTEST0 baud=9600", filename="<t>")
        assert interp.last_response is not None
        assert interp.last_response.get("ok") is True
        assert all(r.status == StepStatus.PASSED for r in interp.results)

    def test_modbus_skip_if_no_port(self, tmp_path):
        missing = tmp_path / "no-such-tty"
        interp = OqlInterpreter(dry_run=False)
        interp.run(f"MODBUS skip_if_no_port serial={missing}", filename="<t>")
        assert interp.vars.get("modbus_skip_probe") == "1"


class TestModbusApiExpansion:
    def test_modbus_api_plan_expansion(self):
        script = testtoon_to_oql("MODBUS[1]{action}:\n  plan\n")
        assert script.lines[0].command == "MODBUS"
        assert script.lines[0].args == "api plan"
