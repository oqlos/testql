"""Schemas for testql echo command - AI-friendly project metadata."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class APIContract:
    """API contract layer from toon tests."""
    base_url: str = ""
    timeout_ms: int = 30000
    retry_count: int = 3
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    asserts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Entity:
    """Entity from doql model."""
    name: str
    fields: List[str] = field(default_factory=list)
    intent: Optional[str] = None
    domain: Optional[str] = None
    lifecycle: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Workflow:
    """Workflow from doql."""
    name: str
    trigger: str
    cmd: str
    intent: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Interface:
    """Interface from doql."""
    type: str
    framework: Optional[str] = None


@dataclass
class SystemModel:
    """System model from doql."""
    project_name: str = ""
    version: str = ""
    interfaces: List[Interface] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    workflows: List[Workflow] = field(default_factory=list)
    deploy_target: str = ""
    environment: str = ""


@dataclass
class ProjectEcho:
    """Combined project echo for LLM consumption."""
    api_contract: APIContract = field(default_factory=APIContract)
    system_model: SystemModel = field(default_factory=SystemModel)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "api_contract": {
                "base_url": self.api_contract.base_url,
                "timeout_ms": self.api_contract.timeout_ms,
                "retry_count": self.api_contract.retry_count,
                "endpoints": self.api_contract.endpoints,
                "asserts": self.api_contract.asserts,
            },
            "system_model": {
                "project": {
                    "name": self.system_model.project_name,
                    "version": self.system_model.version,
                    "interfaces": [
                        {"type": i.type, "framework": i.framework}
                        for i in self.system_model.interfaces
                    ],
                    "domains": self.system_model.domains,
                },
                "entities": [
                    {
                        "name": e.name,
                        "fields": e.fields,
                        "intent": e.intent,
                        "domain": e.domain,
                        "lifecycle": e.lifecycle,
                        "description": e.description,
                    }
                    for e in self.system_model.entities
                ],
                "workflows": [
                    {
                        "name": w.name,
                        "trigger": w.trigger,
                        "cmd": w.cmd,
                        "intent": w.intent,
                        "domain": w.domain,
                        "description": w.description,
                    }
                    for w in self.system_model.workflows
                ],
                "deploy": {
                    "target": self.system_model.deploy_target,
                    "environment": self.system_model.environment,
                },
            },
        }
    
    def to_text(self) -> str:
        """Convert to human-readable text format."""
        lines = []
        
        # Project header
        lines.append(f"📦 Project: {self.system_model.project_name} ({self.system_model.version})")
        lines.append("")
        
        # Type
        lines.append("🧠 Type:")
        for interface in self.system_model.interfaces:
            framework = f" ({interface.framework})" if interface.framework else ""
            lines.append(f"- {interface.type.upper()}{framework}")
        lines.append("")
        
        # Workflows
        lines.append("🛠️ Workflows:")
        for workflow in self.system_model.workflows:
            intent = f" ({workflow.intent})" if workflow.intent else ""
            lines.append(f"- {workflow.name}: {workflow.cmd}{intent}")
        lines.append("")
        
        # API endpoints
        if self.api_contract.endpoints:
            lines.append("🌐 API endpoints (based on toon tests):")
            for endpoint in self.api_contract.endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "")
                status = endpoint.get("status", "")
                lines.append(f"- {method} {path} → {status}")
            lines.append("")
        
        # LLM suggestions
        lines.append("✅ LLM suggestions:")
        lines.append("- Run tests: task test")
        if self.system_model.deploy_target == "docker":
            lines.append("- Run API locally: task run")
        lines.append("- Generate docs + model: task doql:build")
        
        return "\n".join(lines)
