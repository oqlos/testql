"""Parser for doql LESS format - extracts system model."""

import re
from pathlib import Path
from typing import List, Optional

from testql.echo_schemas import Entity, Workflow, Interface, SystemModel


class DoqlParser:
    """Parser for doql LESS files."""
    
    def __init__(self):
        self.system_model = SystemModel()
    
    def parse_file(self, path: Path) -> SystemModel:
        """Parse a doql LESS file.
        
        Args:
            path: Path to the doql LESS file
            
        Returns:
            SystemModel: Extracted system model
        """
        content = path.read_text(encoding="utf-8")
        return self.parse(content)
    
    def parse(self, content: str) -> SystemModel:
        """Parse doql LESS content.
        
        Args:
            content: Doql LESS content
            
        Returns:
            SystemModel: Extracted system model
        """
        self.system_model = SystemModel()
        
        # Extract app block
        app_match = re.search(r'app\s*\{([^}]+)\}', content, re.DOTALL)
        if app_match:
            app_content = app_match.group(1)
            self._parse_app_block(app_content)
        
        # Extract entity blocks
        entity_pattern = r'entity\[name="([^"]+)"\]\s*\{([^}]+)\}'
        for match in re.finditer(entity_pattern, content, re.DOTALL):
            entity_name = match.group(1)
            entity_content = match.group(2)
            self._parse_entity_block(entity_name, entity_content)
        
        # Extract workflow blocks
        workflow_pattern = r'workflow\[name="([^"]+)"\]\s*\{([^}]+)\}'
        for match in re.finditer(workflow_pattern, content, re.DOTALL):
            workflow_name = match.group(1)
            workflow_content = match.group(2)
            self._parse_workflow_block(workflow_name, workflow_content)
        
        # Extract interface blocks
        interface_pattern = r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}'
        for match in re.finditer(interface_pattern, content, re.DOTALL):
            interface_type = match.group(1)
            interface_content = match.group(2)
            self._parse_interface_block(interface_type, interface_content)
        
        # Extract deploy block
        deploy_match = re.search(r'deploy\s*\{([^}]+)\}', content, re.DOTALL)
        if deploy_match:
            deploy_content = deploy_match.group(1)
            self._parse_deploy_block(deploy_content)
        
        return self.system_model
    
    def _parse_app_block(self, content: str):
        """Parse app block for project metadata."""
        name_match = re.search(r'name:\s*([^;]+)', content)
        if name_match:
            self.system_model.project_name = name_match.group(1).strip()
        
        version_match = re.search(r'version:\s*([^;]+)', content)
        if version_match:
            self.system_model.version = version_match.group(1).strip()
    
    def _parse_entity_block(self, name: str, content: str):
        """Parse entity block."""
        entity = Entity(name=name)
        
        # Extract fields
        field_pattern = r'(\w+):\s*([^;]+)'
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            field_type = match.group(2).strip()
            entity.fields.append(f"{field_name}: {field_type}")
        
        # Extract semantic fields
        intent_match = re.search(r'intent:\s*"([^"]+)"', content)
        if intent_match:
            entity.intent = intent_match.group(1)
        
        domain_match = re.search(r'domain:\s*"([^"]+)"', content)
        if domain_match:
            entity.domain = domain_match.group(1)
        
        lifecycle_match = re.search(r'lifetime:\s*"([^"]+)"', content)
        if lifecycle_match:
            entity.lifecycle = lifecycle_match.group(1)
        
        description_match = re.search(r'description:\s*"([^"]+)"', content)
        if description_match:
            entity.description = description_match.group(1)
        
        self.system_model.entities.append(entity)
    
    def _parse_workflow_block(self, name: str, content: str):
        """Parse workflow block."""
        workflow = Workflow(name=name)
        
        trigger_match = re.search(r'trigger:\s*([^;]+)', content)
        if trigger_match:
            workflow.trigger = trigger_match.group(1).strip()
        
        cmd_match = re.search(r'cmd\s*=\s*([^;]+)', content)
        if cmd_match:
            workflow.cmd = cmd_match.group(1).strip()
        
        # Extract semantic fields
        intent_match = re.search(r'intent:\s*"([^"]+)"', content)
        if intent_match:
            workflow.intent = intent_match.group(1)
        
        domain_match = re.search(r'domain:\s*"([^"]+)"', content)
        if domain_match:
            workflow.domain = domain_match.group(1)
        
        description_match = re.search(r'description:\s*"([^"]+)"', content)
        if description_match:
            workflow.description = description_match.group(1)
        
        self.system_model.workflows.append(workflow)
    
    def _parse_interface_block(self, interface_type: str, content: str):
        """Parse interface block."""
        interface = Interface(type=interface_type)
        
        framework_match = re.search(r'framework:\s*([^;]+)', content)
        if framework_match:
            interface.framework = framework_match.group(1).strip()
        
        self.system_model.interfaces.append(interface)
    
    def _parse_deploy_block(self, content: str):
        """Parse deploy block."""
        target_match = re.search(r'target:\s*([^;]+)', content)
        if target_match:
            self.system_model.deploy_target = target_match.group(1).strip()
        
        env_match = re.search(r'environment:\s*([^;]+)', content)
        if env_match:
            self.system_model.environment = env_match.group(1).strip()


def parse_doql_file(path: Path) -> SystemModel:
    """Parse a doql LESS file.
    
    Args:
        path: Path to the doql LESS file
        
    Returns:
        SystemModel: Extracted system model
    """
    parser = DoqlParser()
    return parser.parse_file(path)
