"""Configuration-based endpoint detector.

Detects endpoints from Docker Compose, Kubernetes configs, etc.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .base import BaseEndpointDetector
from .models import EndpointInfo


class ConfigEndpointDetector(BaseEndpointDetector):
    """Detect endpoints from configuration files."""

    COMMON_HTTP_PORTS = {80, 443, 8080, 3000, 5000, 8000, 8100, 8101, 8200, 8202}
    DATABASE_PORTS = {5432, 3306, 6379, 27017, 9200, 5433}

    def detect(self) -> list[EndpointInfo]:
        """Find endpoints in docker-compose, k8s configs."""
        self.endpoints = []

        compose_files = (
            self._find_files('**/docker-compose*.yml') +
            self._find_files('**/docker-compose*.yaml')
        )

        for compose_file in compose_files:
            try:
                self._analyze_docker_compose(compose_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_docker_compose(self, compose_file: Path) -> None:
        """Extract port mappings from docker-compose."""
        content = compose_file.read_text()
        spec = yaml.safe_load(content)

        if not spec or 'services' not in spec:
            return

        for service_name, service in spec['services'].items():
            if 'ports' not in service:
                continue

            for port_mapping in service['ports']:
                port = self._parse_port_mapping(port_mapping)
                if port:
                    protocol = self._infer_protocol(port)
                    self.endpoints.append(EndpointInfo(
                        path='/',
                        method='GET',
                        source_file=compose_file,
                        line_number=0,
                        endpoint_type=protocol,
                        framework='docker',
                        summary=f'Service {service_name} on port {port}',
                    ))

    def _parse_port_mapping(self, port_mapping: str | int) -> int | None:
        """Parse port number from docker-compose port mapping."""
        if isinstance(port_mapping, int):
            return port_mapping

        if isinstance(port_mapping, str):
            # Format: "host:container" or just "port"
            parts = port_mapping.split(':')
            host_port = parts[0] if len(parts) > 1 else port_mapping
            try:
                return int(host_port)
            except ValueError:
                pass
        return None

    def _infer_protocol(self, port: int) -> str:
        """Infer protocol from common port numbers."""
        if port in self.COMMON_HTTP_PORTS:
            return 'http'
        if port in self.DATABASE_PORTS:
            return 'database'
        return 'rest'
