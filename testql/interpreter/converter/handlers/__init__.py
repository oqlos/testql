"""Command handlers for OQL/TQL converter.

Each handler takes (filtered_commands, index) and returns (new_index, section).
"""

from .api import handle_api
from .assertions import collect_assert
from .encoder import handle_encoder
from .flow import handle_flow, FLOW_COMMANDS
from .include import handle_include
from .navigate import handle_navigate
from .record import handle_record_start, handle_record_stop
from .select import handle_select
from .wait import handle_wait
from .unknown import handle_unknown

__all__ = [
    "handle_api",
    "collect_assert",
    "handle_encoder",
    "handle_flow",
    "FLOW_COMMANDS",
    "handle_include",
    "handle_navigate",
    "handle_record_start",
    "handle_record_stop",
    "handle_select",
    "handle_wait",
    "handle_unknown",
]
