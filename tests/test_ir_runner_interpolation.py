"""Tests for `testql.ir_runner.interpolation`."""

from __future__ import annotations

from testql.base import VariableStore
from testql.ir_runner.interpolation import interp_value


def _store(**kw) -> VariableStore:
    return VariableStore(kw)


class TestInterpValue:
    def test_string_brace_form(self):
        assert interp_value("/users/${id}", _store(id=42)) == "/users/42"

    def test_string_dollar_form(self):
        assert interp_value("$name", _store(name="alice")) == "alice"

    def test_unset_passthrough(self):
        # Unknown variables are left as-is by VariableStore.interpolate
        assert interp_value("${missing}", _store()) == "${missing}"

    def test_dict_recursion(self):
        out = interp_value({"path": "/x/${id}", "n": 1}, _store(id=7))
        assert out == {"path": "/x/7", "n": 1}

    def test_list_recursion(self):
        out = interp_value(["${a}", "b", "${a}-${b}"], _store(a="X", b="Y"))
        assert out == ["X", "b", "X-Y"]

    def test_nested(self):
        payload = {"headers": {"Auth": "Bearer ${token}"}, "rows": [{"k": "${a}"}]}
        out = interp_value(payload, _store(token="abc", a=1))
        assert out == {"headers": {"Auth": "Bearer abc"}, "rows": [{"k": "1"}]}

    def test_non_string_passthrough(self):
        assert interp_value(42, _store()) == 42
        assert interp_value(None, _store()) is None
        assert interp_value(True, _store()) is True
