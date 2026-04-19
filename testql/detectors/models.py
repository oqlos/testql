"""Data models for endpoint detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EndpointInfo:
    """Standardized endpoint information."""
    path: str
    method: str
    source_file: Path
    line_number: int
    endpoint_type: str  # 'rest', 'graphql', 'grpc', 'websocket', 'static'
    framework: str  # 'fastapi', 'flask', 'django', 'express', 'openapi'
    handler_name: str | None = None
    parameters: list[dict] = field(default_factory=list)
    response_schema: dict | None = None
    request_body: dict | None = None
    tags: list[str] = field(default_factory=list)
    summary: str | None = None
    description: str | None = None
    auth_required: bool = False
    deprecated: bool = False

    def to_testql_api_call(self, base_url: str = "${api_url}") -> dict:
        """Convert endpoint to TestQL API call format."""
        return {
            "method": self.method,
            "endpoint": f"{base_url}{self.path}",
            "expected_status": self._infer_expected_status(),
            "description": self.summary or f"{self.method} {self.path}",
        }

    def _infer_expected_status(self) -> int:
        """Infer expected HTTP status code."""
        status_map = {
            "GET": 200,
            "POST": 201,
            "PUT": 200,
            "PATCH": 200,
            "DELETE": 204,
            "OPTIONS": 200,
            "HEAD": 200,
        }
        return status_map.get(self.method.upper(), 200)


@dataclass
class ServiceInfo:
    """Information about a service/application."""
    name: str
    root_path: Path
    service_type: str  # 'fastapi', 'flask', 'django', 'express', 'nodejs', 'python-lib'
    base_url: str | None = None
    port: int | None = None
    endpoints: list[EndpointInfo] = field(default_factory=list)
    config: dict = field(default_factory=dict)
