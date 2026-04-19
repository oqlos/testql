"""TestQL Endpoint Detectors — Framework and specification endpoint detection.

This package provides comprehensive endpoint detection for:
- FastAPI, Flask, Django, Express.js (framework detectors)
- OpenAPI/Swagger, GraphQL, WebSocket (specification detectors)
- Docker Compose, Kubernetes configs (config-based detectors)

Usage:
    from testql.detectors import UnifiedEndpointDetector
    
    detector = UnifiedEndpointDetector("/path/to/project")
    endpoints = detector.detect_all()
    
    # Or use specific detectors directly
    from testql.detectors import FastAPIDetector
    fastapi_eps = FastAPIDetector(project_path).detect()
"""

from .models import EndpointInfo, ServiceInfo
from .base import BaseEndpointDetector
from .fastapi_detector import FastAPIDetector
from .flask_detector import FlaskDetector
from .django_detector import DjangoDetector
from .express_detector import ExpressDetector
from .openapi_detector import OpenAPIDetector
from .graphql_detector import GraphQLDetector
from .websocket_detector import WebSocketDetector
from .test_detector import TestEndpointDetector
from .config_detector import ConfigEndpointDetector
from .unified import UnifiedEndpointDetector, detect_endpoints

__all__ = [
    # Data models
    "EndpointInfo",
    "ServiceInfo",
    # Base class
    "BaseEndpointDetector",
    # Framework detectors
    "FastAPIDetector",
    "FlaskDetector",
    "DjangoDetector",
    "ExpressDetector",
    # Specification detectors
    "OpenAPIDetector",
    "GraphQLDetector",
    "WebSocketDetector",
    # Other detectors
    "TestEndpointDetector",
    "ConfigEndpointDetector",
    # Unified
    "UnifiedEndpointDetector",
    "detect_endpoints",
]
