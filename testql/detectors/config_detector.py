"""Configuration-based endpoint detector.

Detects endpoints from Docker Compose, Kubernetes configs, .env, config.py, etc.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from .base import BaseEndpointDetector
from .models import EndpointInfo


class ConfigEndpointDetector(BaseEndpointDetector):
    """Detect endpoints from configuration files."""

    COMMON_HTTP_PORTS = {80, 443, 8080, 3000, 5000, 8000, 8100, 8101, 8200, 8202}
    DATABASE_PORTS = {5432, 3306, 6379, 27017, 9200, 5433}

    def detect(self) -> list[EndpointInfo]:
        """Find endpoints in docker-compose, k8s configs, .env, config.py."""
        self.endpoints = []

        # Detect from docker-compose
        compose_files = (
            self._find_files('**/docker-compose*.yml') +
            self._find_files('**/docker-compose*.yaml')
        )

        for compose_file in compose_files:
            try:
                self._analyze_docker_compose(compose_file)
            except Exception:
                continue

        # Detect from .env files in common locations
        env_locations = [
            self.project_path / '.env',
            self.project_path / 'backend' / '.env',
            self.project_path / 'api' / '.env',
            self.project_path / 'client' / '.env',
        ]
        
        for env_file in env_locations:
            if env_file.exists():
                try:
                    self._analyze_env_file(env_file)
                except Exception:
                    continue

        # Detect from config.py files in common locations
        config_locations = [
            self.project_path / 'config.py',
            self.project_path / 'backend' / 'config.py',
            self.project_path / 'api' / 'config.py',
            self.project_path / 'backend' / 'api' / 'core' / 'config.py',
            self.project_path / 'backend' / 'app' / 'config.py',
        ]
        
        for config_file in config_locations:
            if config_file.exists():
                try:
                    self._analyze_config_py(config_file)
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
                    # Include port in path to make endpoints unique and actionable
                    path = f'/' if protocol in ('http', 'rest') else f'/docker/{service_name}:{port}'
                    self.endpoints.append(EndpointInfo(
                        path=path,
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

    def _analyze_env_file(self, env_file: Path) -> None:
        """Extract configuration from .env file."""
        content = env_file.read_text()
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            match = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$', line)
            if match:
                key, value = match.groups()
                value = value.strip().strip('"\'')
                
                # Look for URL/port configurations
                if 'URL' in key or 'HOST' in key or 'PORT' in key:
                    if value.startswith('http://') or value.startswith('https://'):
                        # Extract port from URL
                        port = self._extract_port_from_url(value)
                        if port and port in self.COMMON_HTTP_PORTS:
                            self.endpoints.append(EndpointInfo(
                                path='/',
                                method='GET',
                                source_file=env_file,
                                line_number=0,
                                endpoint_type='rest',
                                framework='env',
                                summary=f'{key}={value}',
                            ))
                    elif value.isdigit():
                        port = int(value)
                        if port in self.COMMON_HTTP_PORTS:
                            self.endpoints.append(EndpointInfo(
                                path='/',
                                method='GET',
                                source_file=env_file,
                                line_number=0,
                                endpoint_type='rest',
                                framework='env',
                                summary=f'{key}={value}',
                            ))

    def _analyze_config_py(self, config_file: Path) -> None:
        """Extract configuration from config.py file."""
        content = config_file.read_text()
        
        # Look for port/host/url configurations
        port_match = re.search(r'(?:DEFAULT_)?(?:API|SERVER|HOST|PORT)[_\w]*\s*=\s*(\d+)', content)
        host_match = re.search(r'(?:DEFAULT_)?(?:API|SERVER|HOST)[_\w]*\s*=\s*["\']([^"\']+)["\']', content)
        url_match = re.search(r'(?:BASE_)?(?:API|SERVER)[_\w]*\s*=\s*["\'](https?://[^"\']+)["\']', content)
        
        if port_match:
            port = int(port_match.group(1))
            if port in self.COMMON_HTTP_PORTS:
                self.endpoints.append(EndpointInfo(
                    path='/',
                    method='GET',
                    source_file=config_file,
                    line_number=0,
                    endpoint_type='rest',
                    framework='config.py',
                    summary=f'Port {port}',
                ))
        
        if url_match:
            port = self._extract_port_from_url(url_match.group(1))
            if port and port in self.COMMON_HTTP_PORTS:
                self.endpoints.append(EndpointInfo(
                    path='/',
                    method='GET',
                    source_file=config_file,
                    line_number=0,
                    endpoint_type='rest',
                    framework='config.py',
                    summary=url_match.group(1),
                ))

    def _extract_port_from_url(self, url: str) -> int | None:
        """Extract port number from URL."""
        match = re.search(r':(\d+)', url)
        if match:
            return int(match.group(1))
        if url.startswith('https://'):
            return 443
        if url.startswith('http://'):
            return 80
        return None
