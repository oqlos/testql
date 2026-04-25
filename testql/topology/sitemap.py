"""Bounded sitemap crawl — fetch sub-pages and extend topology."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from testql.topology.models import TopologyEdge, TopologyManifest, TopologyNode


class _SubpageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str = ""
        self.links: list[dict[str, Any]] = []
        self.assets: list[dict[str, Any]] = []
        self._in_title = False
        self._title_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "a" and attrs_dict.get("href"):
            self.links.append({"url": attrs_dict["href"], "text": "", "kind": "internal"})
        elif tag in {"script", "img", "link"}:
            ref = attrs_dict.get("src") or attrs_dict.get("href")
            if ref:
                self.assets.append({"url": ref, "tag": tag})

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if self._in_title:
            self._title_chunks.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            self.title = " ".join(chunk for chunk in self._title_chunks if chunk).strip()


def build_sitemap(topology: TopologyManifest, max_pages: int = 10, timeout: float = 5.0) -> TopologyManifest:
    """Extend *topology* with bounded sub-page crawl starting from the root page node."""
    page_node = next((node for node in topology.nodes if node.kind == "page"), None)
    if page_node is None:
        return topology

    base_url = str(page_node.source)
    internal = _extract_internal_links(page_node, max_pages)
    crawled = [_crawl_subpage(url, base_url, timeout) for url in _resolve_urls(base_url, internal)]
    _add_sitemap_nodes(topology, base_url, crawled, max_pages)
    return topology


def _extract_internal_links(page_node: TopologyNode, max_pages: int) -> list[dict[str, Any]]:
    links = (page_node.metadata or {}).get("links", [])
    return [link for link in links if link.get("kind") == "internal"][:max_pages]


def _resolve_urls(base_url: str, links: list[dict[str, Any]]) -> list[str]:
    resolved: list[str] = []
    for link in links:
        url = urljoin(base_url, link.get("url", ""))
        if url and url != base_url:
            resolved.append(url)
    return resolved


def _crawl_subpage(url: str, base_url: str, timeout: float) -> dict[str, Any]:
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers={"user-agent": "testql-sitemap/0.1"}) as client:
            resp = client.get(url)
    except Exception:
        return {"url": url, "status_code": None, "title": "", "links": 0, "error": True}

    text = resp.text if _looks_textual(resp.headers.get("content-type", "")) else ""
    parsed = _parse_subpage(text) if _is_html(resp.headers.get("content-type", ""), text) else {}
    return {
        "url": str(resp.url),
        "status_code": resp.status_code,
        "title": parsed.get("title", ""),
        "links": len(parsed.get("links", [])),
    }


def _is_html(content_type: str, text: str) -> bool:
    return "html" in content_type.lower() or "<html" in text[:500].lower()


def _add_sitemap_nodes(topology: TopologyManifest, base_url: str, crawled: list[dict[str, Any]], max_pages: int) -> None:
    sitemap_id = "sitemap.root"
    topology.nodes.append(TopologyNode(
        sitemap_id, "sitemap", base_url,
        metadata={"crawled": len(crawled), "max_pages": max_pages, "base_url": base_url},
    ))
    topology.edges.append(TopologyEdge("page.root", sitemap_id, "has_sitemap", "crawl"))

    for index, item in enumerate(crawled, start=1):
        node_id = f"subpage.{index}"
        topology.nodes.append(TopologyNode(
            node_id, "subpage", item["url"],
            metadata={"status_code": item["status_code"], "title": item["title"], "links": item["links"]},
        ))
        topology.edges.append(TopologyEdge(sitemap_id, node_id, "contains", "http"))
        topology.edges.append(TopologyEdge("page.root", node_id, "navigates_to", "http"))


def _looks_textual(content_type: str) -> bool:
    content_type = content_type.lower()
    return any(item in content_type for item in ("text/", "json", "xml", "html", "javascript"))


def _parse_subpage(text: str) -> dict[str, Any]:
    parser = _SubpageParser()
    parser.feed(text or "")
    return {"title": parser.title, "links": parser.links}
