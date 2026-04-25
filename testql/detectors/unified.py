"""Unified endpoint detector that orchestrates all specialized detectors."""

from __future__ import annotations

from pathlib import Path

from .models import EndpointInfo
from .fastapi_detector import FastAPIDetector
from .flask_detector import FlaskDetector
from .django_detector import DjangoDetector
from .express_detector import ExpressDetector
from .openapi_detector import OpenAPIDetector
from .graphql_detector import GraphQLDetector
from .websocket_detector import WebSocketDetector
from .test_detector import TestEndpointDetector
from .config_detector import ConfigEndpointDetector


class UnifiedEndpointDetector:
    """Unified detector that runs all specialized detectors."""

    DETECTORS = [
        FastAPIDetector,
        FlaskDetector,
        DjangoDetector,
        ExpressDetector,
        OpenAPIDetector,
        GraphQLDetector,
        WebSocketDetector,
        TestEndpointDetector,
        ConfigEndpointDetector,
    ]

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.all_endpoints: list[EndpointInfo] = []
        self.detectors_used: list[str] = []

    def detect_all(self) -> list[EndpointInfo]:
        """Run all detectors and merge results."""
        self.all_endpoints = []
        self.detectors_used = []

        for detector_class in self.DETECTORS:
            try:
                detector = detector_class(self.project_path)
                endpoints = detector.detect()
                if endpoints:
                    self.detectors_used.append(detector_class.__name__)
                    self.all_endpoints.extend(endpoints)
            except Exception as e:
                print(f"Detector {detector_class.__name__} failed: {e}")
                continue

        self.all_endpoints = self._deduplicate_endpoints(self.all_endpoints)
        return self.all_endpoints

    def _deduplicate_endpoints(self, endpoints: list[EndpointInfo]) -> list[EndpointInfo]:
        """Remove duplicate endpoints based on method+path+summary.

        For docker-compose and other config-based sources, summary contains
        service name and port info, which must be included in the key to
        preserve all distinct services.
        """
        seen: set[tuple[str, str, str | None]] = set()
        unique: list[EndpointInfo] = []
        for ep in endpoints:
            key = (ep.method.upper(), ep.path, ep.summary)
            if key not in seen:
                seen.add(key)
                unique.append(ep)
        return unique

    def get_endpoints_by_type(self, endpoint_type: str) -> list[EndpointInfo]:
        """Filter endpoints by type."""
        return [ep for ep in self.all_endpoints if ep.endpoint_type == endpoint_type]

    def get_endpoints_by_framework(self, framework: str) -> list[EndpointInfo]:
        """Filter endpoints by framework."""
        return [ep for ep in self.all_endpoints if ep.framework == framework]

    def generate_testql_scenario(self, output_file: Path | None = None) -> str:
        """Generate TestQL scenario from detected endpoints."""
        if not self.all_endpoints:
            return ""

        rest_eps = [ep for ep in self.all_endpoints if ep.endpoint_type == "rest"]
        graphql_eps = [ep for ep in self.all_endpoints if ep.endpoint_type == "graphql"]
        ws_eps = [ep for ep in self.all_endpoints if ep.endpoint_type == "websocket"]

        lines = ["# SCENARIO: Auto-detected API Endpoints", "# TYPE: api", ""]
        lines.extend(self._rest_block(rest_eps))
        lines.extend(self._graphql_block(graphql_eps))
        lines.extend(self._ws_block(ws_eps))
        lines += ["ASSERT[1]{field, operator, expected}:", "  status, <, 500"]

        content = "\n".join(lines)
        if output_file:
            output_file.write_text(content)
        return content

    def _rest_block(self, rest_eps: list[EndpointInfo]) -> list[str]:
        """Generate REST API section for scenario."""
        if not rest_eps:
            return []
        lines = [
            "CONFIG[2]{key, value}:",
            "  base_url, ${api_url:-http://localhost:8101}",
            "  timeout_ms, 10000",
            "",
            f"API[{len(rest_eps[:30])}]{{method, endpoint, expected_status}}:",
        ]
        for ep in rest_eps[:30]:
            lines.append(f"  {ep.method}, {ep.path}, {ep._infer_expected_status()}")
        lines.append("")
        return lines

    def _graphql_block(self, graphql_eps: list[EndpointInfo]) -> list[str]:
        """Generate GraphQL section for scenario."""
        if not graphql_eps:
            return []
        lines = [f"GRAPHQL[{len(graphql_eps[:10])}]{{query, variables}}:"]
        for ep in graphql_eps[:10]:
            lines.append(f'  {ep.handler_name or "query"}, {{}}')
        lines.append("")
        return lines

    def _ws_block(self, ws_eps: list[EndpointInfo]) -> list[str]:
        """Generate WebSocket section for scenario."""
        if not ws_eps:
            return []
        lines = [f"WEBSOCKET[{len(ws_eps[:5])}]{{url, action}}:"]
        for ep in ws_eps[:5]:
            lines.append(f"  ws://localhost:8101{ep.path}, connect")
        lines.append("")
        return lines


def detect_endpoints(project_path: str | Path) -> list[EndpointInfo]:
    """Convenience function to detect all endpoints in a project."""
    detector = UnifiedEndpointDetector(project_path)
    return detector.detect_all()
