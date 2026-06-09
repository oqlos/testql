"""TestQL control DSL — query, patch, validate and generate test scenarios."""

from dsl2testql.bus import dispatch
from dsl2testql.engine import DslResult, execute_dsl, execute_dsl_line

__all__ = ["DslResult", "execute_dsl", "execute_dsl_line", "dispatch"]
