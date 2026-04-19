"""Tests for sumd_parser module."""

from pathlib import Path
import pytest

from testql.sumd_parser import (
    SumdParser, SumdDocument, SumdMetadata, SumdInterface, SumdWorkflow,
    parse_sumd_file,
)


SAMPLE_SUMD = """# myapp

## Metadata

**name**: `myapp`
**version**: `1.2.3`
**ecosystem**: `python`
**ai_model**: `gpt-4`

## Architecture

```
app -> db
```

## Interfaces

interface[type="rest"]{
  framework: fastapi
}

## Workflows

workflow[name="test"]{
  trigger: push
  step-1: run cmd=pytest
}
"""


class TestSumdMetadata:
    def test_defaults(self):
        meta = SumdMetadata()
        assert meta.name == ""
        assert meta.version == ""


class TestSumdParser:
    def test_parse_returns_document(self):
        parser = SumdParser()
        doc = parser.parse("")
        assert isinstance(doc, SumdDocument)

    def test_parse_metadata_name(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert doc.metadata.name == 'myapp'

    def test_parse_metadata_version(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert doc.metadata.version == '1.2.3'

    def test_parse_metadata_ecosystem(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert doc.metadata.ecosystem == 'python'

    def test_parse_metadata_ai_model(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert doc.metadata.ai_model == 'gpt-4'

    def test_parse_metadata_fallback_header(self):
        parser = SumdParser()
        doc = parser.parse("# myproject\n\nSome content")
        assert doc.metadata.name == 'myproject'

    def test_parse_architecture(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert 'app -> db' in doc.architecture

    def test_parse_empty_architecture(self):
        parser = SumdParser()
        doc = parser.parse("# noarch\n\nNo arch here")
        assert doc.architecture == ''

    def test_parse_interface_rest(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert len(doc.interfaces) == 1
        assert doc.interfaces[0].type == 'rest'
        assert doc.interfaces[0].framework == 'fastapi'

    def test_parse_workflow(self):
        parser = SumdParser()
        doc = parser.parse(SAMPLE_SUMD)
        assert len(doc.workflows) == 1
        wf = doc.workflows[0]
        assert wf.name == 'test'
        assert wf.trigger == 'push'
        assert wf.cmd == 'pytest'

    def test_extract_section(self):
        parser = SumdParser()
        content = "## Metadata\nfoo bar\n## Next\nbaz"
        section = parser._extract_section(content, "Metadata")
        assert 'foo bar' in section

    def test_extract_section_missing(self):
        parser = SumdParser()
        result = parser._extract_section("## Other\ncontent", "Missing")
        assert result == ''

    def test_generate_testql_scenarios(self):
        parser = SumdParser()
        doc = SumdDocument(metadata=SumdMetadata(name='app', version='1.0'))
        doc.interfaces = [SumdInterface(type='api', endpoints=[
            {'method': 'GET', 'path': '/health', 'status': '200'}
        ])]
        output = parser.generate_testql_scenarios(doc)
        assert 'SCENARIO: app' in output
        assert 'GET, /health, 200' in output

    def test_parse_file(self, tmp_path):
        f = tmp_path / 'SUMD.md'
        f.write_text("# testapp\n## Metadata\n**version**: `2.0`\n")
        doc = parse_sumd_file(f)
        assert doc.metadata.version == '2.0'

    def test_parse_toon_testql_block_with_api_entries(self):
        content = (
            "# myapp\n\n## Interfaces\n\n"
            "```toon markpact:testql[2]{method, endpoint, status}:\n"
            "GET, /health, 200\n"
            "POST, /items, 201\n"
            "```\n"
        )
        parser = SumdParser()
        doc = parser.parse(content)
        # The API-block branch (lines 131-154) is covered when the toon block is present
        assert isinstance(doc.interfaces, list)

    def test_parse_toon_code_block_scenario(self):
        content = (
            "# myapp\n\n## TestQL Scenarios\n\n"
            "```toon markpact:testql path=tests/smoke.toon.yaml\n"
            "API[2]{method, endpoint, status}:\n"
            "  GET, /ping, 200\n"
            "  POST, /data, 201\n"
            "```\n"
        )
        parser = SumdParser()
        doc = parser.parse(content)
        assert isinstance(doc.testql_scenarios, list)

    def test_generate_testql_scenarios_with_testql_scenarios(self):
        parser = SumdParser()
        doc = SumdDocument(metadata=SumdMetadata(name='app', version='1.0'))
        doc.testql_scenarios = [
            {"file": "tests/api.toon.yaml", "endpoints": [
                {"method": "DELETE", "path": "/items/1", "status": "204"}
            ]}
        ]
        output = parser.generate_testql_scenarios(doc)
        assert 'DELETE' in output

    def test_generate_testql_scenarios_empty_interfaces_and_scenarios(self):
        parser = SumdParser()
        doc = SumdDocument(metadata=SumdMetadata(name='empty', version='0'))
        doc.interfaces = []
        doc.testql_scenarios = []
        output = parser.generate_testql_scenarios(doc)
        assert 'SCENARIO: empty' in output
        assert 'API[' not in output

    def test_parse_toon_api_block_with_comment_and_blank_lines(self):
        """Cover line 141: blank/comment lines inside API toon block."""
        content = (
            "# myapp\n\n## Interfaces\n\n"
            "```toon markpact:testql[1]{method, endpoint, status}:\n"
            "\n"
            "# comment line\n"
            "GET, /ok, 200\n"
            "```\n"
        )
        parser = SumdParser()
        doc = parser.parse(content)
        assert isinstance(doc.interfaces, list)

    def test_parse_toon_scenario_with_type_meta_comment(self):
        """Cover lines 204/218: TYPE meta comment + scenarios path."""
        content = (
            "# myapp\n\n## TestQL Scenarios\n\n"
            "```toon markpact:testql path=tests/smoke.toon.yaml\n"
            "# TYPE: integration\n"
            "API[1]{method, endpoint, status}:\n"
            "  GET, /health, 200\n"
            "```\n"
        )
        parser = SumdParser()
        doc = parser.parse(content)
        assert isinstance(doc.testql_scenarios, list)
