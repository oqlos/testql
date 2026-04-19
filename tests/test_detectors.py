"""Tests for endpoint detectors – FastAPI, Flask, unified, models."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from testql.detectors.models import EndpointInfo
from testql.detectors.fastapi_detector import FastAPIDetector
from testql.detectors.flask_detector import FlaskDetector
from testql.detectors.unified import UnifiedEndpointDetector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, name: str, content: str) -> Path:
    f = tmp_path / name
    f.write_text(textwrap.dedent(content))
    return f


# ---------------------------------------------------------------------------
# EndpointInfo model
# ---------------------------------------------------------------------------

class TestEndpointInfoModel:
    def test_to_testql_api_call(self, tmp_path):
        ep = EndpointInfo(
            path="/health",
            method="GET",
            source_file=tmp_path / "main.py",
            line_number=10,
            endpoint_type="rest",
            framework="fastapi",
            handler_name="health_check",
        )
        call = ep.to_testql_api_call("http://localhost:8000")
        assert call["method"] == "GET"
        assert "/health" in call["endpoint"]

    def test_defaults(self, tmp_path):
        ep = EndpointInfo(
            path="/x", method="POST",
            source_file=tmp_path / "f.py", line_number=1,
            endpoint_type="rest", framework="flask",
        )
        assert ep.parameters == []
        assert ep.tags == []
        assert ep.auth_required is False
        assert ep.deprecated is False


# ---------------------------------------------------------------------------
# FastAPIDetector
# ---------------------------------------------------------------------------

class TestFastAPIDetector:
    def test_detects_route_decorator(self, tmp_path):
        _write(tmp_path, "main.py", """\
            from fastapi import FastAPI
            app = FastAPI()

            @app.get("/items")
            async def list_items():
                return []

            @app.post("/items")
            async def create_item():
                return {}
        """)
        det = FastAPIDetector(tmp_path)
        eps = det.detect()
        paths = {ep.path for ep in eps}
        assert "/items" in paths
        methods = {ep.method for ep in eps if ep.path == "/items"}
        assert "GET" in methods
        assert "POST" in methods

    def test_empty_project(self, tmp_path):
        det = FastAPIDetector(tmp_path)
        assert det.detect() == []

    def test_non_route_decorators_ignored(self, tmp_path):
        _write(tmp_path, "main.py", """\
            from fastapi import FastAPI
            app = FastAPI()

            @app.on_event("startup")
            async def startup():
                pass
        """)
        det = FastAPIDetector(tmp_path)
        eps = det.detect()
        assert all(ep.method in {"GET", "POST", "PUT", "DELETE", "PATCH"} for ep in eps)


# ---------------------------------------------------------------------------
# FlaskDetector
# ---------------------------------------------------------------------------

class TestFlaskDetector:
    def test_detects_route(self, tmp_path):
        _write(tmp_path, "app.py", """\
            from flask import Flask
            app = Flask(__name__)

            @app.route('/ping', methods=['GET'])
            def ping():
                return 'pong'
        """)
        det = FlaskDetector(tmp_path)
        eps = det.detect()
        assert any(ep.path == "/ping" for ep in eps)

    def test_empty_project(self, tmp_path):
        det = FlaskDetector(tmp_path)
        assert det.detect() == []


# ---------------------------------------------------------------------------
# UnifiedEndpointDetector
# ---------------------------------------------------------------------------

class TestUnifiedDetector:
    def test_returns_list(self, tmp_path):
        det = UnifiedEndpointDetector(tmp_path)
        eps = det.detect_all()
        assert isinstance(eps, list)

    def test_detects_fastapi(self, tmp_path):
        _write(tmp_path, "main.py", """\
            from fastapi import FastAPI
            app = FastAPI()

            @app.get("/status")
            def status():
                return {"ok": True}
        """)
        det = UnifiedEndpointDetector(tmp_path)
        eps = det.detect_all()
        assert any(ep.path == "/status" for ep in eps)

    def test_detectors_used_populated(self, tmp_path):
        det = UnifiedEndpointDetector(tmp_path)
        det.detect_all()
        assert hasattr(det, "detectors_used")


# ---------------------------------------------------------------------------
# OpenAPIDetector
# ---------------------------------------------------------------------------

from testql.detectors.openapi_detector import OpenAPIDetector


class TestOpenAPIDetector:
    def test_empty_project(self, tmp_path):
        det = OpenAPIDetector(tmp_path)
        assert det.detect() == []

    def test_detects_yaml_spec(self, tmp_path):
        _write(tmp_path, "openapi.yaml", """\
            openapi: "3.0.0"
            info:
              title: Test
              version: "1.0"
            paths:
              /users:
                get:
                  operationId: listUsers
                  summary: List users
                post:
                  summary: Create user
        """)
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        paths = [ep.path for ep in eps]
        assert "/users" in paths
        methods = [ep.method for ep in eps]
        assert "GET" in methods
        assert "POST" in methods

    def test_detects_json_spec(self, tmp_path):
        import json
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "T", "version": "1"},
            "paths": {
                "/items": {
                    "get": {"summary": "list"}
                }
            }
        }
        (tmp_path / "openapi.json").write_text(json.dumps(spec))
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        assert any(ep.path == "/items" for ep in eps)

    def test_framework_is_openapi(self, tmp_path):
        _write(tmp_path, "openapi.yaml", """\
            openapi: "3.0.0"
            info:
              title: T
              version: "1"
            paths:
              /ping:
                get:
                  summary: ping
        """)
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        assert eps[0].framework == "openapi"

    def test_base_path_from_servers(self, tmp_path):
        _write(tmp_path, "openapi.yaml", """\
            openapi: "3.0.0"
            info:
              title: T
              version: "1"
            servers:
              - url: /api/v1
            paths:
              /health:
                get:
                  summary: health
        """)
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        assert eps[0].path == "/api/v1/health"

    def test_base_path_swagger2(self, tmp_path):
        _write(tmp_path, "swagger.yaml", """\
            swagger: "2.0"
            info:
              title: T
              version: "1"
            basePath: /v2
            paths:
              /users:
                get:
                  summary: list
        """)
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        assert eps[0].path == "/v2/users"

    def test_x_extension_methods_skipped(self, tmp_path):
        _write(tmp_path, "openapi.yaml", """\
            openapi: "3.0.0"
            info:
              title: T
              version: "1"
            paths:
              /data:
                x-custom: ignored
                get:
                  summary: get data
        """)
        det = OpenAPIDetector(tmp_path)
        eps = det.detect()
        assert all(ep.method != "X-CUSTOM" for ep in eps)

    def test_invalid_yaml_skipped(self, tmp_path):
        (tmp_path / "openapi.yaml").write_text("not: valid: yaml: {{{{")
        det = OpenAPIDetector(tmp_path)
        # Should not raise, just return empty
        result = det.detect()
        assert isinstance(result, list)

    def test_spec_without_paths_skipped(self, tmp_path):
        _write(tmp_path, "openapi.yaml", """\
            openapi: "3.0.0"
            info:
              title: T
              version: "1"
        """)
        det = OpenAPIDetector(tmp_path)
        assert det.detect() == []


# ---------------------------------------------------------------------------
# ExpressDetector
# ---------------------------------------------------------------------------

from testql.detectors.express_detector import ExpressDetector


class TestExpressDetector:
    def test_empty_project(self, tmp_path):
        det = ExpressDetector(tmp_path)
        assert det.detect() == []

    def test_detects_app_get(self, tmp_path):
        _write(tmp_path, "index.js", """\
            const express = require('express');
            const app = express();
            app.get('/users', (req, res) => res.json([]));
        """)
        det = ExpressDetector(tmp_path)
        eps = det.detect()
        assert any(ep.path == "/users" for ep in eps)
        assert any(ep.method == "GET" for ep in eps)

    def test_detects_router_post(self, tmp_path):
        _write(tmp_path, "routes.js", """\
            const router = express.Router();
            router.post('/items', handler);
        """)
        det = ExpressDetector(tmp_path)
        eps = det.detect()
        assert any(ep.method == "POST" for ep in eps)

    def test_framework_is_express(self, tmp_path):
        _write(tmp_path, "app.js", """\
            app.get('/ping', ping);
        """)
        det = ExpressDetector(tmp_path)
        eps = det.detect()
        assert all(ep.framework == "express" for ep in eps)

    def test_typescript_file_detected(self, tmp_path):
        _write(tmp_path, "routes.ts", """\
            app.delete('/users/:id', deleteUser);
        """)
        det = ExpressDetector(tmp_path)
        eps = det.detect()
        assert any(ep.method == "DELETE" for ep in eps)
