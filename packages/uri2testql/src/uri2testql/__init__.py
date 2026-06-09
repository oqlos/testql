"""testql:// URI driver for TestQL manifests."""

from uri2testql.files import resolve_testql_file
from uri2testql.materialize import materialize_uri
from uri2testql.patch import append_uri, apply_uri, patch_uri, update_uri
from uri2testql.query import query_uri
from uri2testql.uri import (
    build_testql_uri_index,
    is_testql_uri,
    parse_testql_uri,
    uri_for_block,
    uri_for_file,
    uri_for_generate,
)

__all__ = [
    "resolve_testql_file",
    "materialize_uri",
    "append_uri",
    "apply_uri",
    "patch_uri",
    "update_uri",
    "query_uri",
    "build_testql_uri_index",
    "is_testql_uri",
    "parse_testql_uri",
    "uri_for_block",
    "uri_for_file",
    "uri_for_generate",
]
