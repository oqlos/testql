"""Runtime environment context commands."""

from __future__ import annotations

import json
from typing import Any

from testql.base import StepResult, StepStatus
from testql.context.runtime import RuntimeProfile, apply_profile, detect_runtime_profile

from ._parser import OqlLine


class ContextMixin:
    """Mixin for ENVIRONMENT / CONTEXT profile commands."""

    _runtime_profile: RuntimeProfile | None = None

    def _cmd_context_detect(self, args: str, line: OqlLine) -> None:
        app_type = ""
        source = ""
        if args:
            for token in args.split():
                if token.startswith("app="):
                    app_type = token.split("=", 1)[1]
                elif token.startswith("source="):
                    source = token.split("=", 1)[1]
        profile = detect_runtime_profile(app_type=app_type, source_runtime=source)
        apply_profile(self, profile)
        self._runtime_profile = profile
        self._record_context_step(line, "CONTEXT_DETECT", profile.to_dict())

    def _cmd_context_apply(self, args: str, line: OqlLine) -> None:
        from testql.context.runtime import _coerce_profile_dict

        if args.strip():
            try:
                payload = json.loads(args)
            except json.JSONDecodeError:
                payload = {"app_type": args.strip()}
            profile = _coerce_profile_dict(payload) if isinstance(payload, dict) else detect_runtime_profile()
        elif self._runtime_profile is not None:
            profile = self._runtime_profile
        else:
            profile = detect_runtime_profile()
        apply_profile(self, profile)
        self._runtime_profile = profile
        self._record_context_step(line, "CONTEXT_APPLY", profile.to_dict())

    def _record_context_step(self, line: OqlLine, name: str, payload: dict[str, Any]) -> None:
        self.results.append(
            StepResult(
                name=name,
                status=StepStatus.PASSED,
                message=f"capabilities={payload.get('capabilities', [])}",
                details=payload,
            )
        )
        if not getattr(self, "quiet", False):
            caps = payload.get("capabilities") or []
            self.out.ok(f"{name}: os={payload.get('os_family')} browser={payload.get('browser_engine')} caps={len(caps)}")
