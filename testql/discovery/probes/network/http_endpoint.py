from __future__ import annotations

from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource, SourceKind


class HTTPPageProbe(BaseProbe):
    name = "network.http_endpoint"
    artifact_types = ("web_page", "http_endpoint")
    cost = "expensive"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def applicable(self, source: ArtifactSource) -> bool:
        return source.kind == SourceKind.URL

    def probe(self, source: ArtifactSource) -> ProbeResult:
        try:
            response = _fetch(source.location, self.timeout)
        except Exception as exc:
            return self.result(
                35,
                ["http_endpoint"],
                [self.evidence("http_error", source.location, str(exc))],
                {"url": source.location, "error": str(exc), "interfaces": [{"type": "web_page", "location": source.location, "metadata": {"reachable": False}}]},
            )
        content_type = response.headers.get("content-type", "")
        text = response.text if _looks_textual(content_type) else ""
        parsed = _parse_html(text, str(response.url)) if "html" in content_type.lower() or "<html" in text[:500].lower() else {}
        metadata = _metadata(source.location, response, content_type, parsed)
        confidence = 90 if 200 <= response.status_code < 400 else 55
        return self.result(confidence, ["web_page", "http_endpoint"], [self.evidence("http", source.location, f"HTTP {response.status_code}")], metadata)

    def evidence(self, kind: str, location, detail: str = ""):
        from testql.discovery.manifest import Evidence
        return Evidence(self.name, kind, str(location), detail)


def _fetch(url: str, timeout: float) -> httpx.Response:
    with httpx.Client(follow_redirects=True, timeout=timeout, headers={"user-agent": "testql-discovery/0.1"}) as client:
        return client.get(url)


def _looks_textual(content_type: str) -> bool:
    content_type = content_type.lower()
    return any(item in content_type for item in ("text/", "json", "xml", "html", "javascript"))


def _metadata(original_url: str, response: httpx.Response, content_type: str, parsed: dict[str, Any]) -> dict[str, Any]:
    final_url = str(response.url)
    return {
        "url": original_url,
        "final_url": final_url,
        "status_code": response.status_code,
        "content_type": content_type,
        "title": parsed.get("title", ""),
        "links": parsed.get("links", []),
        "assets": parsed.get("assets", []),
        "forms": parsed.get("forms", []),
        "page_schema": {
            "url": final_url,
            "status_code": response.status_code,
            "content_type": content_type,
            "title": parsed.get("title", ""),
            "links": parsed.get("links", []),
            "assets": parsed.get("assets", []),
            "forms": parsed.get("forms", []),
            "network_calls": [],
            "console_errors": [],
        },
        "interfaces": [{"type": "web_page", "location": final_url, "metadata": {"status_code": response.status_code, "title": parsed.get("title", "")}}],
    }


class _PageParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.links: list[dict[str, Any]] = []
        self.assets: list[dict[str, Any]] = []
        self.forms: list[dict[str, Any]] = []
        self._in_title = False
        self._title_chunks: list[str] = []
        self._current_link: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "a" and attrs_dict.get("href"):
            self._current_link = {"url": urljoin(self.base_url, attrs_dict["href"]), "text": "", "kind": _link_kind(self.base_url, attrs_dict["href"])}
            self.links.append(self._current_link)
        elif tag in {"script", "img", "link"}:
            ref = attrs_dict.get("src") or attrs_dict.get("href")
            if ref:
                kind = _asset_kind(tag, attrs_dict)
                self.assets.append({"url": urljoin(self.base_url, ref), "tag": tag, "kind": kind})
        elif tag == "form":
            self.forms.append({"action": urljoin(self.base_url, attrs_dict.get("action", self.base_url)), "method": attrs_dict.get("method", "get").lower()})

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if self._in_title:
            self._title_chunks.append(value)
        if self._current_link is not None and value:
            current = self._current_link.get("text", "")
            self._current_link["text"] = " ".join(item for item in (current, value) if item).strip()

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
            self.title = " ".join(chunk for chunk in self._title_chunks if chunk).strip()
        elif tag == "a":
            self._current_link = None


def _parse_html(text: str, base_url: str) -> dict[str, Any]:
    parser = _PageParser(base_url)
    parser.feed(text or "")
    return {"title": parser.title, "links": _limit(parser.links), "assets": _limit(parser.assets), "forms": _limit(parser.forms)}


def _limit(items: list[dict[str, Any]], limit: int = 100) -> list[dict[str, Any]]:
    return items[:limit]


def _asset_kind(tag: str, attrs: dict[str, str]) -> str:
    if tag == "script":
        return "script"
    if tag == "img":
        return "image"
    if tag == "link":
        rel = attrs.get("rel", "").lower()
        if "stylesheet" in rel:
            return "stylesheet"
        if "icon" in rel or "shortcut" in rel:
            return "icon"
        if "preload" in rel:
            return "preload"
        return "link"
    return "unknown"


def _link_kind(base_url: str, href: str) -> str:
    target = urljoin(base_url, href)
    base_host = urlparse(base_url).netloc
    target_host = urlparse(target).netloc
    if href.startswith("#"):
        return "anchor"
    if target_host and target_host != base_host:
        return "external"
    return "internal"
