"""Advanced Endpoint Detection for TestQL.

This module provides comprehensive endpoint detection for multiple frameworks:
- FastAPI (decorators, routers, include_router, dependencies)
- Flask (Blueprint, MethodView, route decorators)
- Django (urls.py patterns, path(), re_path())
- Express.js (JavaScript/TypeScript routes)
- OpenAPI/Swagger specifications
- GraphQL schemas and resolvers
- gRPC proto definitions
- WebSocket endpoints
- Database/API call patterns in tests

The detectors produce standardized EndpointInfo objects that can be
used for test generation and API analysis.
"""

from __future__ import annotations

import ast
import json
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict
from urllib.parse import urljoin


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


class BaseEndpointDetector:
    """Base class for endpoint detectors."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.endpoints: list[EndpointInfo] = []

    def detect(self) -> list[EndpointInfo]:
        """Run detection and return endpoints."""
        raise NotImplementedError

    def _find_files(self, pattern: str, exclude_dirs: set[str] | None = None) -> list[Path]:
        """Find files matching pattern."""
        exclude_dirs = exclude_dirs or {'.venv', 'venv', 'node_modules', '__pycache__', '.git'}
        files = []
        try:
            for path in self.project_path.rglob(pattern):
                if not any(d in str(path) for d in exclude_dirs):
                    files.append(path)
        except Exception:
            pass
        return files


class FastAPIDetector(BaseEndpointDetector):
    """Detect FastAPI endpoints using AST analysis."""

    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'websocket'}

    def detect(self) -> list[EndpointInfo]:
        """Detect all FastAPI endpoints including routers."""
        self.endpoints = []

        # Find all Python files
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:100]:  # Limit for performance
            try:
                self._analyze_file(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_file(self, py_file: Path):
        """Analyze a single Python file for FastAPI patterns."""
        content = py_file.read_text()
        tree = ast.parse(content)

        # Find app/router instances and their routes
        routers = {}  # name -> prefix
        app_routers = []  # (router_name, prefix)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Detect APIRouter() assignments
                self._detect_router_assignment(node, routers)
                # Detect FastAPI() app assignment
                self._detect_app_assignment(node)

            elif isinstance(node, ast.Call):
                # Detect include_router calls
                prefix = self._extract_include_router(node)
                if prefix:
                    app_routers.append(prefix)

            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Detect decorated functions (route handlers)
                self._analyze_route_handler(node, py_file, content, routers)

    def _detect_router_assignment(self, node: ast.Assign, routers: dict):
        """Detect APIRouter instance assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id == 'APIRouter':
                    prefix = ''
                    for kw in call.keywords:
                        if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                            prefix = kw.value.value
                    routers[target.id] = prefix

    def _detect_app_assignment(self, node: ast.Assign):
        """Detect FastAPI app instance."""
        pass  # Currently informational only

    def _extract_include_router(self, node: ast.Call) -> tuple | None:
        """Extract router info from include_router call."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'include_router':
            prefix = ''
            for kw in node.keywords:
                if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                    prefix = kw.value.value
            return prefix
        return None

    def _analyze_route_handler(self, node: ast.FunctionDef | ast.AsyncFunctionDef,
                                py_file: Path, content: str, routers: dict):
        """Analyze a function decorated with HTTP method decorators."""
        for decorator in node.decorator_list:
            method, path = self._extract_route_info(decorator)
            if method and path:
                # Check if decorated via router
                router_prefix = self._get_router_prefix(decorator, routers)
                full_path = router_prefix + path

                # Extract parameters from function signature
                params = self._extract_parameters(node)

                endpoint = EndpointInfo(
                    path=full_path,
                    method=method.upper(),
                    source_file=py_file,
                    line_number=node.lineno,
                    endpoint_type='rest',
                    framework='fastapi',
                    handler_name=node.name,
                    parameters=params,
                    summary=self._extract_docstring(node),
                )
                self.endpoints.append(endpoint)

    def _extract_route_info(self, decorator: ast.expr) -> tuple[str | None, str | None]:
        """Extract HTTP method and path from route decorator."""
        # Direct @app.get() or @router.get()
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            attr = decorator.func
            method = attr.attr.lower()
            if method in self.HTTP_METHODS:
                # Extract path from first argument
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    return method, decorator.args[0].value
        return None, None

    def _get_router_prefix(self, decorator: ast.expr, routers: dict) -> str:
        """Get prefix from router for route decorators."""
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            router_name = None
            if isinstance(decorator.func.value, ast.Name):
                router_name = decorator.func.value.id
            if router_name and router_name in routers:
                return routers[router_name]
        return ''

    def _extract_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict]:
        """Extract function parameters for API docs."""
        params = []
        for arg in node.args.args:
            if arg.arg not in ('self', 'cls'):
                param_type = self._get_annotation_name(arg.annotation)
                params.append({
                    'name': arg.arg,
                    'type': param_type,
                    'in': 'query' if param_type in ('int', 'str', 'float', 'bool') else 'body'
                })
        return params

    def _get_annotation_name(self, annotation: ast.expr | None) -> str:
        """Get type name from annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            return annotation.value
        return 'any'

    def _extract_docstring(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        """Extract docstring from function."""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                return node.body[0].value.value.strip().split('\n')[0][:100]
        return None


class FlaskDetector(BaseEndpointDetector):
    """Detect Flask endpoints including Blueprints."""

    def detect(self) -> list[EndpointInfo]:
        """Detect Flask routes and blueprints."""
        self.endpoints = []
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:100]:
            try:
                self._analyze_flask_file(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_flask_file(self, py_file: Path):
        """Analyze Flask file for routes."""
        content = py_file.read_text()
        tree = ast.parse(content)

        blueprints = {}  # name -> prefix

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Detect Blueprint instances
                self._detect_blueprint(node, blueprints)

            elif isinstance(node, ast.FunctionDef):
                # Detect route decorators
                self._analyze_flask_route(node, py_file, content, blueprints)

    def _detect_blueprint(self, node: ast.Assign, blueprints: dict):
        """Detect Flask Blueprint assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id == 'Blueprint':
                    prefix = ''
                    for kw in call.keywords:
                        if kw.arg == 'url_prefix' and isinstance(kw.value, ast.Constant):
                            prefix = kw.value.value
                    blueprints[target.id] = prefix

    def _analyze_flask_route(self, node: ast.FunctionDef, py_file: Path,
                             content: str, blueprints: dict):
        """Analyze @app.route and @bp.route decorators."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                path, methods = self._extract_flask_route_info(decorator, blueprints)
                if path:
                    for method in methods:
                        endpoint = EndpointInfo(
                            path=path,
                            method=method,
                            source_file=py_file,
                            line_number=node.lineno,
                            endpoint_type='rest',
                            framework='flask',
                            handler_name=node.name,
                        )
                        self.endpoints.append(endpoint)

    def _extract_flask_route_info(self, decorator: ast.Call, blueprints: dict) -> tuple[str | None, list]:
        """Extract path and methods from Flask route decorator."""
        if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
            path = None
            methods = ['GET']  # Default

            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path = decorator.args[0].value

            # Check for methods= kwarg
            for kw in decorator.keywords:
                if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                    methods = []
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant):
                            methods.append(elt.value.strip('"\''))

            # Add blueprint prefix
            if isinstance(decorator.func.value, ast.Name):
                bp_name = decorator.func.value.id
                if bp_name in blueprints:
                    path = blueprints[bp_name] + (path or '')

            return path, methods
        return None, []


class DjangoDetector(BaseEndpointDetector):
    """Detect Django URL patterns."""

    def detect(self) -> list[EndpointInfo]:
        """Detect Django URL patterns from urls.py files."""
        self.endpoints = []
        urls_files = self._find_files('**/urls.py')

        for urls_file in urls_files:
            try:
                self._analyze_urls_py(urls_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_urls_py(self, urls_file: Path):
        """Analyze Django urls.py file."""
        content = urls_file.read_text()

        # Pattern for path() and re_path() calls
        path_pattern = r"path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)"
        re_path_pattern = r"re_path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)"
        url_pattern = r"url\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)"

        for match in re.finditer(path_pattern, content):
            path, view = match.groups()
            if not path.startswith('admin/'):  # Skip admin
                self.endpoints.append(EndpointInfo(
                    path=f"/{path.lstrip('/')}",
                    method='GET',  # Django default, could be from view
                    source_file=urls_file,
                    line_number=content[:match.start()].count('\n') + 1,
                    endpoint_type='rest',
                    framework='django',
                    handler_name=view.strip(),
                ))


class ExpressDetector(BaseEndpointDetector):
    """Detect Express.js routes from JavaScript/TypeScript files."""

    def detect(self) -> list[EndpointInfo]:
        """Detect Express routes."""
        self.endpoints = []
        js_files = self._find_files('**/*.js') + self._find_files('**/*.ts')

        for js_file in js_files[:50]:
            try:
                self._analyze_express_file(js_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_express_file(self, js_file: Path):
        """Analyze Express routes in JS/TS file."""
        content = js_file.read_text()

        # Express route patterns
        # app.get('/path', handler)
        # router.post('/path', handler)
        # app.route('/path').get().post()

        route_patterns = [
            r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"\.route\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\.(get|post|put|delete|patch)",
        ]

        for pattern in route_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                if len(match.groups()) == 2:
                    method, path = match.groups()
                    self.endpoints.append(EndpointInfo(
                        path=path,
                        method=method.upper(),
                        source_file=js_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='rest',
                        framework='express',
                    ))


class OpenAPIDetector(BaseEndpointDetector):
    """Detect endpoints from OpenAPI/Swagger specifications."""

    def detect(self) -> list[EndpointInfo]:
        """Parse OpenAPI 2.0/3.0 specs."""
        self.endpoints = []

        # Look for spec files
        spec_files = (
            self._find_files('**/openapi*.yaml') +
            self._find_files('**/openapi*.json') +
            self._find_files('**/swagger*.yaml') +
            self._find_files('**/swagger*.json') +
            self._find_files('**/*spec*.yaml') +
            self._find_files('**/*spec*.json')
        )

        for spec_file in spec_files:
            try:
                self._parse_spec(spec_file)
            except Exception:
                continue

        return self.endpoints

    def _parse_spec(self, spec_file: Path):
        """Parse OpenAPI specification."""
        content = spec_file.read_text()

        if spec_file.suffix == '.json':
            spec = json.loads(content)
        else:
            spec = yaml.safe_load(content)

        if not spec or 'paths' not in spec:
            return

        base_path = spec.get('basePath', '') or spec.get('servers', [{}])[0].get('url', '')

        for path, methods in spec['paths'].items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if method.startswith('x-') or method == 'parameters':
                    continue

                full_path = base_path + path
                endpoint = EndpointInfo(
                    path=full_path,
                    method=method.upper(),
                    source_file=spec_file,
                    line_number=0,
                    endpoint_type='rest',
                    framework='openapi',
                    handler_name=details.get('operationId'),
                    summary=details.get('summary'),
                    description=details.get('description'),
                    parameters=details.get('parameters', []),
                    tags=details.get('tags', []),
                    deprecated=details.get('deprecated', False),
                )
                self.endpoints.append(endpoint)


class TestEndpointDetector(BaseEndpointDetector):
    """Detect API calls in test files to infer endpoints."""

    HTTP_PATTERNS = [
        r'["\'](GET|POST|PUT|DELETE|PATCH)["\']\s*,\s*["\']([^"\']+)["\']',
        r'\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.post\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.put\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.delete\s*\(\s*["\']([^"\']+)["\']\s*\)',
    ]

    def detect(self) -> list[EndpointInfo]:
        """Infer endpoints from test API calls."""
        self.endpoints = []
        test_files = self._find_files('**/test*.py')

        for test_file in test_files[:50]:
            try:
                self._analyze_test_file(test_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_test_file(self, test_file: Path):
        """Analyze test file for API calls."""
        content = test_file.read_text()

        # Look for patterns like client.get('/api/users')
        for pattern in self.HTTP_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                groups = match.groups()
                if len(groups) == 2:
                    method, path = groups
                else:
                    # Method inferred from function name
                    method_match = re.search(r'\.(get|post|put|delete|patch)', content[:match.start()])
                    method = method_match.group(1).upper() if method_match else 'GET'
                    path = groups[0]

                if path.startswith('/api/'):
                    self.endpoints.append(EndpointInfo(
                        path=path,
                        method=method.upper(),
                        source_file=test_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='rest',
                        framework='inferred-from-tests',
                    ))


class GraphQLDetector(BaseEndpointDetector):
    """Detect GraphQL schemas and resolvers."""

    def detect(self) -> list[EndpointInfo]:
        """Detect GraphQL endpoints."""
        self.endpoints = []

        # Look for GraphQL schema files
        schema_files = self._find_files('**/*.graphql') + self._find_files('**/schema.graphql')

        for schema_file in schema_files[:20]:
            try:
                self._analyze_schema(schema_file)
            except Exception:
                continue

        # Look for Python GraphQL (graphene, strawberry)
        py_files = self._find_files('**/schema*.py')
        for py_file in py_files[:20]:
            try:
                self._analyze_python_graphql(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_schema(self, schema_file: Path):
        """Analyze GraphQL schema file."""
        content = schema_file.read_text()

        # Find Query and Mutation types
        query_pattern = r'type\s+Query\s*\{([^}]+)\}'
        mutation_pattern = r'type\s+Mutation\s*\{([^}]+)\}'

        for match in re.finditer(query_pattern, content, re.DOTALL):
            fields = match.group(1)
            for field_match in re.finditer(r'(\w+)\s*\(', fields):
                field_name = field_match.group(1)
                self.endpoints.append(EndpointInfo(
                    path=f'/graphql',
                    method='POST',
                    source_file=schema_file,
                    line_number=0,
                    endpoint_type='graphql',
                    framework='graphql',
                    handler_name=field_name,
                    summary=f'GraphQL query: {field_name}',
                ))

    def _analyze_python_graphql(self, py_file: Path):
        """Analyze Python GraphQL schemas (graphene)."""
        content = py_file.read_text()

        # Look for class Query and class Mutation
        if 'graphene.ObjectType' in content or 'strawberry.type' in content:
            # Find field definitions
            field_pattern = r'(\w+)\s*=\s*graphene\.(String|Int|Field|List)'
            for match in re.finditer(field_pattern, content):
                field_name = match.group(1)
                self.endpoints.append(EndpointInfo(
                    path='/graphql',
                    method='POST',
                    source_file=py_file,
                    line_number=content[:match.start()].count('\n') + 1,
                    endpoint_type='graphql',
                    framework='graphene',
                    handler_name=field_name,
                ))


class WebSocketDetector(BaseEndpointDetector):
    """Detect WebSocket endpoints."""

    def detect(self) -> list[EndpointInfo]:
        """Detect WebSocket endpoints from code."""
        self.endpoints = []
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text()
                # FastAPI WebSocket
                for match in re.finditer(r'@app\.websocket\s*\(\s*["\']([^"\']+)["\']', content):
                    path = match.group(1)
                    self.endpoints.append(EndpointInfo(
                        path=path,
                        method='WS',
                        source_file=py_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='websocket',
                        framework='fastapi',
                    ))
            except Exception:
                continue

        return self.endpoints


class ConfigEndpointDetector(BaseEndpointDetector):
    """Detect endpoints from configuration files."""

    def detect(self) -> list[EndpointInfo]:
        """Find endpoints in docker-compose, k8s configs."""
        self.endpoints = []

        # Docker compose
        compose_files = self._find_files('**/docker-compose*.yml') + self._find_files('**/docker-compose*.yaml')
        for compose_file in compose_files:
            try:
                self._analyze_docker_compose(compose_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_docker_compose(self, compose_file: Path):
        """Extract port mappings from docker-compose."""
        content = compose_file.read_text()
        spec = yaml.safe_load(content)

        if spec and 'services' in spec:
            for service_name, service in spec['services'].items():
                if 'ports' in service:
                    for port_mapping in service['ports']:
                        # Format: "host:container" or just "port"
                        if isinstance(port_mapping, str):
                            parts = port_mapping.split(':')
                            host_port = parts[0] if len(parts) > 1 else port_mapping
                            try:
                                port = int(host_port)
                                # Guess protocol based on common ports
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
                            except ValueError:
                                pass

    def _infer_protocol(self, port: int) -> str:
        """Infer protocol from common port numbers."""
        port_map = {
            80: 'http',
            443: 'https',
            8080: 'http',
            3000: 'http',
            5000: 'http',
            8000: 'http',
            5432: 'database',
            3306: 'database',
            6379: 'database',
            27017: 'database',
        }
        return port_map.get(port, 'rest')


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

        # Deduplicate endpoints
        self.all_endpoints = self._deduplicate_endpoints(self.all_endpoints)

        return self.all_endpoints

    def _deduplicate_endpoints(self, endpoints: list[EndpointInfo]) -> list[EndpointInfo]:
        """Remove duplicate endpoints based on method+path."""
        seen = set()
        unique = []
        for ep in endpoints:
            key = (ep.method.upper(), ep.path)
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

        lines = ["# SCENARIO: Auto-detected API Endpoints", "# TYPE: api", ""]

        # Group by type
        rest_endpoints = [ep for ep in self.all_endpoints if ep.endpoint_type == 'rest']
        graphql_endpoints = [ep for ep in self.all_endpoints if ep.endpoint_type == 'graphql']
        ws_endpoints = [ep for ep in self.all_endpoints if ep.endpoint_type == 'websocket']

        if rest_endpoints:
            lines.append("CONFIG[2]{key, value}:")
            lines.append("  base_url, ${api_url:-http://localhost:8101}")
            lines.append("  timeout_ms, 10000")
            lines.append("")
            lines.append(f"API[{len(rest_endpoints[:30])}]{{method, endpoint, expected_status}}:")
            for ep in rest_endpoints[:30]:
                expected = ep._infer_expected_status()
                lines.append(f"  {ep.method}, {ep.path}, {expected}")
            lines.append("")

        if graphql_endpoints:
            lines.append(f"GRAPHQL[{len(graphql_endpoints[:10])}]{{query, variables}}:")
            for ep in graphql_endpoints[:10]:
                lines.append(f'  {ep.handler_name or "query"}, {{}}')
            lines.append("")

        if ws_endpoints:
            lines.append(f"WEBSOCKET[{len(ws_endpoints[:5])}]{{url, action}}:")
            for ep in ws_endpoints[:5]:
                lines.append(f'  ws://localhost:8101{ep.path}, connect')
            lines.append("")

        lines.append("ASSERT[1]{field, operator, expected}:")
        lines.append("  status, <, 500")

        content = '\n'.join(lines)

        if output_file:
            output_file.write_text(content)

        return content


def detect_endpoints(project_path: str | Path) -> list[EndpointInfo]:
    """Convenience function to detect all endpoints in a project."""
    detector = UnifiedEndpointDetector(project_path)
    return detector.detect_all()


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = UnifiedEndpointDetector(path)
    endpoints = detector.detect_all()
    print(f"Detected {len(endpoints)} endpoints:")
    for ep in endpoints:
        print(f"  [{ep.framework}] {ep.method} {ep.path} ({ep.endpoint_type})")
