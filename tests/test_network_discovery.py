from __future__ import annotations

import json

import httpx
from click.testing import CliRunner

from testql.cli import cli
from testql.discovery import discover_path
from testql.topology import build_topology
from testql.results import inspect_source, render_inspection


HTML = """
<html>
  <head>
    <title>Example Site</title>
    <link rel="stylesheet" href="/style.css">
  </head>
  <body>
    <a href="/about">About</a>
    <a href="https://external.example/docs">Docs</a>
    <img src="/logo.png">
    <form action="/contact" method="post"></form>
  </body>
</html>
"""


SPA_HTML = """
<html>
    <head>
        <title>SPA App</title>
        <script src="/assets/app.js"></script>
        <script src="/assets/vendor.js"></script>
    </head>
    <body>
        <div id="app"></div>
    </body>
</html>
"""


class FakeClient:
    status_code = 200
    html = HTML

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url: str):
        return httpx.Response(
            self.status_code,
            headers={"content-type": "text/html; charset=utf-8"},
            text=self.html,
            request=httpx.Request("GET", url),
        )

    def head(self, url: str):
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="",
            request=httpx.Request("HEAD", url),
        )


class FakeErrorClient(FakeClient):
    status_code = 500
    html = "<html><head></head><body></body></html>"


class FakeSpaClient(FakeClient):
    status_code = 200
    html = SPA_HTML


def test_discover_url_requires_scan_network_for_match(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    without_network = discover_path("https://example.test/")
    assert without_network.types == []
    with_network = discover_path("https://example.test/", scan_network=True)
    assert "web_page" in with_network.types
    assert with_network.metadata["title"] == "Example Site"
    assert len(with_network.metadata["links"]) == 2
    assert with_network.metadata["links"][0]["text"] == "About"


def test_topology_url_builds_page_schema_nodes(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    topology = build_topology("https://example.test/", scan_network=True)
    kinds = {node.kind for node in topology.nodes}
    assert "page" in kinds
    assert "link" in kinds
    assert "asset" in kinds
    assert "form" in kinds
    assert any(edge.relation == "links_to" for edge in topology.edges)
    assert any(edge.relation == "submits_to" for edge in topology.edges)


def test_inspect_url_nlp_passes_with_mocked_network(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    topology, envelope, plan = inspect_source("https://example.test/", scan_network=True)
    output = render_inspection(topology, envelope, plan, "nlp")
    assert envelope.status == "passed"
    check_ids = {check.id for check in envelope.checks}
    assert "check.web.status" in check_ids
    assert "check.web.title" in check_ids
    assert "check.web.links" in check_ids
    assert "check.web.assets" in check_ids
    assert "check.web.forms" in check_ids
    assert "check.web.link_status" in check_ids
    assert "check.web.asset_status" in check_ids
    assert "Inspection status: passed." in output


def test_inspect_cli_url_json_with_scan_network(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    runner = CliRunner()
    result = runner.invoke(cli, ["inspect", "https://example.test/", "--scan-network", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["inspection"]["result"]["status"] == "passed"
    assert any(node["kind"] == "page" for node in data["inspection"]["topology"]["nodes"])


def test_inspect_url_reports_http_failure(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeErrorClient)
    _, envelope, plan = inspect_source("https://example.test/", scan_network=True)
    assert envelope.status == "failed"
    assert any(check.id == "check.web.status" and check.status == "failed" for check in envelope.checks)
    assert any(finding.id == "finding.web.status" for finding in envelope.failures)
    assert any(action.type == "investigate_http_status" for action in plan.actions)


def test_inspect_url_builds_sitemap_with_mocked_network(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeClient)
    topology, envelope, plan = inspect_source("https://example.test/", scan_network=True)
    sitemap = next((node for node in topology.nodes if node.kind == "sitemap"), None)
    assert sitemap is not None
    assert any(node.kind == "subpage" for node in topology.nodes)
    check_ids = {check.id for check in envelope.checks}
    assert "check.sitemap.crawl" in check_ids
    assert "check.sitemap.broken" in check_ids
    assert "check.sitemap.duplicates" in check_ids


def test_inspect_spa_without_anchors_skips_web_links(monkeypatch):
    monkeypatch.setattr(httpx, "Client", FakeSpaClient)
    _, envelope, _ = inspect_source("https://spa.example.test/", scan_network=True)

    links_check = next((check for check in envelope.checks if check.id == "check.web.links"), None)
    assert links_check is not None
    assert links_check.status == "skipped"
    assert envelope.status == "passed"
    assert not any(finding.id == "finding.web.links" for finding in envelope.failures)
