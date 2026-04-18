"""Parser for toon test format - extracts API contracts."""

import re
from pathlib import Path
from typing import List, Dict, Any

from testql.echo_schemas import APIContract


class ToonParser:
    """Parser for toon test files."""
    
    def __init__(self):
        self.contract = APIContract()
    
    def parse_file(self, path: Path) -> APIContract:
        """Parse a toon test file.
        
        Args:
            path: Path to the toon test file
            
        Returns:
            APIContract: Extracted API contract
        """
        content = path.read_text(encoding="utf-8")
        return self.parse(content)
    
    def parse(self, content: str) -> APIContract:
        """Parse toon test content.
        
        Args:
            content: Toon test content
            
        Returns:
            APIContract: Extracted API contract
        """
        self.contract = APIContract()
        
        # Extract API blocks
        api_pattern = r'API\[\s*([^\]]+)\s*\]'
        for match in re.finditer(api_pattern, content):
            api_content = match.group(1).strip()
            self._parse_api_block(api_content)
        
        # Extract ASSERT blocks
        assert_pattern = r'ASSERT\[\s*([^\]]+)\s*\]'
        for match in re.finditer(assert_pattern, content):
            assert_content = match.group(1).strip()
            self._parse_assert_block(assert_content)
        
        # Extract LOG blocks for base_url
        log_pattern = r'LOG\[\s*([^\]]+)\s*\]'
        for match in re.finditer(log_pattern, content):
            log_content = match.group(1).strip()
            self._parse_log_block(log_content)
        
        return self.contract
    
    def _parse_api_block(self, content: str):
        """Parse API block content."""
        # Extract method, path, status
        method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)', content)
        if method_match:
            method = method_match.group(1)
            path = method_match.group(2)
            
            # Extract expected status
            status_match = re.search(r'status[:\s]+(\d+)', content, re.IGNORECASE)
            status = status_match.group(1) if status_match else "200"
            
            self.contract.endpoints.append({
                "method": method,
                "path": path,
                "status": status,
            })
    
    def _parse_assert_block(self, content: str):
        """Parse ASSERT block content."""
        # Extract field, operator, value
        assert_match = re.search(r'(\w+)\s*([=!<>]+)\s*(.+)', content)
        if assert_match:
            field = assert_match.group(1)
            op = assert_match.group(2)
            value = assert_match.group(3).strip()
            
            self.contract.asserts.append({
                "field": field,
                "op": op,
                "value": value,
            })
    
    def _parse_log_block(self, content: str):
        """Parse LOG block content for base_url."""
        # Extract base URL from log content
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match:
            self.contract.base_url = url_match.group(0)


def parse_toon_file(path: Path) -> APIContract:
    """Parse a toon test file.
    
    Args:
        path: Path to the toon test file
        
    Returns:
        APIContract: Extracted API contract
    """
    parser = ToonParser()
    return parser.parse_file(path)
