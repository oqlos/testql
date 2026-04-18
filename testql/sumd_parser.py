"""Parser for SUMD (Structured Unified Markdown Descriptor) files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SumdMetadata:
    """Metadata from SUMD."""
    name: str = ""
    version: str = ""
    description: str = ""
    ecosystem: str = ""
    ai_model: str = ""


@dataclass
class SumdInterface:
    """Interface from SUMD."""
    type: str = ""
    framework: str = ""
    endpoints: list[dict] = field(default_factory=list)


@dataclass
class SumdWorkflow:
    """Workflow from SUMD."""
    name: str = ""
    trigger: str = "manual"
    cmd: str = ""


@dataclass
class SumdDocument:
    """Parsed SUMD document."""
    metadata: SumdMetadata = field(default_factory=SumdMetadata)
    interfaces: list[SumdInterface] = field(default_factory=list)
    workflows: list[SumdWorkflow] = field(default_factory=list)
    testql_scenarios: list[dict] = field(default_factory=list)
    architecture: str = ""


class SumdParser:
    """Parser for SUMD markdown files."""
    
    def parse_file(self, path: Path) -> SumdDocument:
        """Parse SUMD.md file."""
        content = path.read_text(encoding="utf-8")
        return self.parse(content)
    
    def parse(self, content: str) -> SumdDocument:
        """Parse SUMD content."""
        doc = SumdDocument()
        
        # Parse metadata section
        doc.metadata = self._parse_metadata(content)
        
        # Parse interfaces
        doc.interfaces = self._parse_interfaces(content)
        
        # Parse workflows
        doc.workflows = self._parse_workflows(content)
        
        # Parse testql scenarios
        doc.testql_scenarios = self._parse_testql_scenarios(content)
        
        # Parse architecture
        doc.architecture = self._parse_architecture(content)
        
        return doc
    
    def _parse_metadata(self, content: str) -> SumdMetadata:
        """Parse metadata section."""
        meta = SumdMetadata()
        
        # Extract from Metadata section
        metadata_section = self._extract_section(content, "Metadata")
        if metadata_section:
            # name
            name_match = re.search(r'\*\*name\*\*:\s*`([^`]+)`', metadata_section)
            if name_match:
                meta.name = name_match.group(1)
            
            # version
            version_match = re.search(r'\*\*version\*\*:\s*`([^`]+)`', metadata_section)
            if version_match:
                meta.version = version_match.group(1)
            
            # ecosystem
            eco_match = re.search(r'\*\*ecosystem\*\*:\s*`([^`]+)`', metadata_section)
            if eco_match:
                meta.ecosystem = eco_match.group(1)
            
            # ai_model
            ai_match = re.search(r'\*\*ai_model\*\*:\s*`([^`]+)`', metadata_section)
            if ai_match:
                meta.ai_model = ai_match.group(1)
        
        # If no name, try from header
        if not meta.name:
            header_match = re.search(r'^#\s+(\w+)', content, re.MULTILINE)
            if header_match:
                meta.name = header_match.group(1).lower()
        
        return meta
    
    def _parse_interfaces(self, content: str) -> list[SumdInterface]:
        """Parse interfaces from SUMD."""
        interfaces = []
        
        # Look for interface blocks in code
        interface_pattern = r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}'
        for match in re.finditer(interface_pattern, content):
            iface = SumdInterface(type=match.group(1))
            body = match.group(2)
            
            # Extract framework
            framework_match = re.search(r'framework:\s*(\w+)', body)
            if framework_match:
                iface.framework = framework_match.group(1)
            
            interfaces.append(iface)
        
        # Also look for REST API endpoints in code blocks
        api_pattern = r'```toon.*?markpact:testql[^`]*API\[(\d+)\]\{([^}]+)\}:\s*\n(.*?)```'
        for match in re.finditer(api_pattern, content, re.DOTALL):
            count = match.group(1)
            fields = match.group(2)
            body = match.group(3)
            
            iface = SumdInterface(type="api", framework="rest")
            
            # Parse API entries
            for line in body.strip().split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Parse: GET, /path, 200 # comment
                parts = line.split('#')[0].strip()
                if ',' in parts:
                    vals = [v.strip() for v in parts.split(',')]
                    if len(vals) >= 2:
                        iface.endpoints.append({
                            "method": vals[0],
                            "path": vals[1],
                            "status": vals[2] if len(vals) > 2 else "200",
                        })
            
            if iface.endpoints:
                interfaces.append(iface)
        
        return interfaces
    
    def _parse_workflows(self, content: str) -> list[SumdWorkflow]:
        """Parse workflows from SUMD."""
        workflows = []
        
        # Look for workflow blocks in LESS code
        workflow_pattern = r'workflow\[name="([^"]+)"\]\s*\{([^}]+)\}'
        for match in re.finditer(workflow_pattern, content, re.DOTALL):
            wf = SumdWorkflow(name=match.group(1))
            body = match.group(2)
            
            # Extract trigger
            trigger_match = re.search(r'trigger:\s*(\w+)', body)
            if trigger_match:
                wf.trigger = trigger_match.group(1)
            
            # Extract cmd from step
            cmd_match = re.search(r'step-\d+:\s*run\s+cmd=([^;]+)', body)
            if cmd_match:
                wf.cmd = cmd_match.group(1).strip()
            
            workflows.append(wf)
        
        return workflows
    
    def _parse_testql_scenarios(self, content: str) -> list[dict]:
        """Parse testql scenarios from SUMD."""
        scenarios = []
        
        # Look for toon testql code blocks
        toon_pattern = r'```toon\s+markpact:testql\s+path=([^\s]+)\s*\n(.*?)```'
        for match in re.finditer(toon_pattern, content, re.DOTALL):
            path = match.group(1)
            body = match.group(2)
            
            scenario = {
                "file": path,
                "type": "api",
                "endpoints": [],
            }
            
            # Parse API blocks
            api_pattern = r'API\[(\d+)\]\{([^}]+)\}:\s*\n((?:\s+\w+,[^\n]+\n)+)'
            for api_match in re.finditer(api_pattern, body):
                for line in api_match.group(3).strip().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split('#')[0].strip()
                    if ',' in parts:
                        vals = [v.strip() for v in parts.split(',')]
                        if len(vals) >= 2:
                            scenario["endpoints"].append({
                                "method": vals[0],
                                "path": vals[1],
                                "status": vals[2] if len(vals) > 2 else "200",
                            })
            
            # Extract type from meta
            type_match = re.search(r'#\s*TYPE:\s*(\w+)', body)
            if type_match:
                scenario["type"] = type_match.group(1)
            
            if scenario["endpoints"]:
                scenarios.append(scenario)
        
        return scenarios
    
    def _parse_architecture(self, content: str) -> str:
        """Parse architecture diagram."""
        # Look for architecture section
        arch_section = self._extract_section(content, "Architecture")
        if arch_section:
            # Look for diagram code block
            diagram_match = re.search(r'```\s*\n(.*?)```', arch_section, re.DOTALL)
            if diagram_match:
                return diagram_match.group(1).strip()
        return ""
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract section content from markdown."""
        pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=##\s|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    def generate_testql_scenarios(self, doc: SumdDocument) -> str:
        """Generate testql scenario content from SUMD document."""
        lines = []
        
        lines.append(f"# SCENARIO: {doc.metadata.name} — generated from SUMD")
        lines.append(f"# TYPE: contract")
        lines.append(f"# VERSION: {doc.metadata.version}")
        lines.append("")
        
        # Generate CONFIG
        lines.append("CONFIG[1]{key, value}:")
        lines.append(f"  base_url, http://localhost:8101")
        lines.append("")
        
        # Collect all endpoints
        all_endpoints = []
        for iface in doc.interfaces:
            all_endpoints.extend(iface.endpoints)
        
        for scenario in doc.testql_scenarios:
            all_endpoints.extend(scenario.get("endpoints", []))
        
        if all_endpoints:
            lines.append(f"API[{len(all_endpoints)}]{{method, endpoint, status}}:")
            for ep in all_endpoints:
                method = ep.get("method", "GET")
                path = ep.get("path", "/")
                status = ep.get("status", "200")
                lines.append(f"  {method}, {path}, {status}")
            lines.append("")
        
        # Add assertions
        lines.append("ASSERT[3]{field, operator, expected}:")
        lines.append("  status, <, 500")
        lines.append("  content_type, contains, application/json")
        lines.append("")
        
        return "\n".join(lines)


def parse_sumd_file(path: Path) -> SumdDocument:
    """Parse a SUMD.md file."""
    parser = SumdParser()
    return parser.parse_file(path)
