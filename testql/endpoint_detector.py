"""TestQL Endpoint Detector — Backward-compatible re-export.

This module re-exports all detector functionality from the new
structured detectors package for backward compatibility.

New code should import directly from `testql.detectors`:
    from testql.detectors import UnifiedEndpointDetector, EndpointInfo

Legacy imports still work:
    from testql.endpoint_detector import UnifiedEndpointDetector, EndpointInfo
"""

# Re-export everything from the new structured package
from .detectors import (
    # Data models
    EndpointInfo,
    ServiceInfo,
    # Base class
    BaseEndpointDetector,
    # Framework detectors
    FastAPIDetector,
    FlaskDetector,
    DjangoDetector,
    ExpressDetector,
    # Specification detectors
    OpenAPIDetector,
    GraphQLDetector,
    WebSocketDetector,
    # Other detectors
    TestEndpointDetector,
    ConfigEndpointDetector,
    # Unified
    UnifiedEndpointDetector,
    detect_endpoints,
)

__all__ = [
    "EndpointInfo",
    "ServiceInfo",
    "BaseEndpointDetector",
    "FastAPIDetector",
    "FlaskDetector",
    "DjangoDetector",
    "ExpressDetector",
    "OpenAPIDetector",
    "GraphQLDetector",
    "WebSocketDetector",
    "TestEndpointDetector",
    "ConfigEndpointDetector",
    "UnifiedEndpointDetector",
    "detect_endpoints",
]


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = UnifiedEndpointDetector(path)
    endpoints = detector.detect_all()
    print(f"Detected {len(endpoints)} endpoints:")
    for ep in endpoints:
        print(f"  [{ep.framework}] {ep.method} {ep.path} ({ep.endpoint_type})")
