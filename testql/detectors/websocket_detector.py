"""WebSocket endpoint detector."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class WebSocketDetector(BaseEndpointDetector):
    """Detect WebSocket endpoints."""

    WS_PATTERNS = [
        # FastAPI WebSocket
        r"@app\.websocket\s*\(\s*['\"]([^'\"]+)['\"]",
        # Generic websocket endpoint
        r"websocket\s*\(\s*['\"]([^'\"]+)['\"]",
    ]

    def detect(self) -> list[EndpointInfo]:
        """Detect WebSocket endpoints from code."""
        self.endpoints = []
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text()
                self._analyze_content(content, py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_content(self, content: str, py_file: Path) -> None:
        """Analyze file content for WebSocket patterns."""
        for pattern in self.WS_PATTERNS:
            for match in re.finditer(pattern, content):
                path = match.group(1)
                self.endpoints.append(EndpointInfo(
                    path=path,
                    method='WS',
                    source_file=py_file,
                    line_number=content[:match.start()].count('\n') + 1,
                    endpoint_type='websocket',
                    framework='fastapi',
                ))
