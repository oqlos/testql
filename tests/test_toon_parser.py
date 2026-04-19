"""Tests for toon_parser module."""

import tempfile
from pathlib import Path

import pytest

from testql.toon_parser import ToonParser, parse_toon_file
from testql.echo_schemas import APIContract


class TestToonParser:
    def test_init(self):
        parser = ToonParser()
        assert isinstance(parser.contract, APIContract)

    def test_parse_empty(self):
        parser = ToonParser()
        contract = parser.parse('')
        assert contract.endpoints == []
        assert contract.asserts == []
        assert contract.base_url == ''

    def test_parse_api_get(self):
        parser = ToonParser()
        content = 'API[ GET /api/users status: 200 ]'
        contract = parser.parse(content)
        assert len(contract.endpoints) == 1
        ep = contract.endpoints[0]
        assert ep['method'] == 'GET'
        assert ep['path'] == '/api/users'
        assert ep['status'] == '200'

    def test_parse_api_post(self):
        parser = ToonParser()
        content = 'API[ POST /api/items status: 201 ]'
        contract = parser.parse(content)
        assert len(contract.endpoints) == 1
        assert contract.endpoints[0]['method'] == 'POST'

    def test_parse_api_no_status_defaults_200(self):
        parser = ToonParser()
        content = 'API[ DELETE /api/item/1 ]'
        contract = parser.parse(content)
        assert len(contract.endpoints) == 1
        assert contract.endpoints[0]['status'] == '200'

    def test_parse_assert_block(self):
        parser = ToonParser()
        content = 'ASSERT[ status == 200 ]'
        contract = parser.parse(content)
        assert len(contract.asserts) == 1
        a = contract.asserts[0]
        assert a['field'] == 'status'
        assert a['op'] == '=='
        assert a['value'] == '200'

    def test_parse_log_block_sets_base_url(self):
        parser = ToonParser()
        content = 'LOG[ connecting to http://localhost:8000 ]'
        contract = parser.parse(content)
        assert contract.base_url == 'http://localhost:8000'

    def test_parse_multiple_api_blocks(self):
        parser = ToonParser()
        content = 'API[ GET /a ] API[ POST /b ]'
        contract = parser.parse(content)
        assert len(contract.endpoints) == 2

    def test_parse_resets_contract_between_calls(self):
        parser = ToonParser()
        parser.parse('API[ GET /first ]')
        contract = parser.parse('API[ POST /second ]')
        # Should only have the second parse result
        assert len(contract.endpoints) == 1
        assert contract.endpoints[0]['method'] == 'POST'

    def test_parse_file(self, tmp_path):
        test_file = tmp_path / 'test.toon.yaml'
        test_file.write_text('API[ GET /health ]\nASSERT[ code == 200 ]')
        contract = parse_toon_file(test_file)
        assert len(contract.endpoints) == 1
        assert len(contract.asserts) == 1
