from __future__ import annotations

from pathlib import Path

from testql.results.models import CheckResult, FailureFinding, RefactorPlan, SuggestedAction, TestResultEnvelope
from testql.topology import TopologyManifest, build_topology


def inspect_source(source: str | Path, scan_network: bool = False, use_browser: bool = False) -> tuple[TopologyManifest, TestResultEnvelope, RefactorPlan]:
    topology = build_topology(source, scan_network=scan_network, use_browser=use_browser)
    envelope = analyze_topology(topology, scan_network=scan_network, use_browser=use_browser)
    return topology, envelope, RefactorPlan.from_envelope(envelope)


def analyze_topology(topology: TopologyManifest, scan_network: bool = False, use_browser: bool = False) -> TestResultEnvelope:
    checks = [
        _check_confidence(topology),
        _check_nodes(topology),
        _check_edges(topology),
        _check_interfaces(topology),
        _check_evidence(topology),
        *_web_checks(topology),
        *_crawl_checks(topology, scan_network),
        *_sitemap_checks(topology),
        *_browser_checks(topology, use_browser),
    ]
    failures = _findings_from_checks(checks)
    actions = _actions_from_findings(failures, topology)
    status = _status_from_checks(checks)
    return TestResultEnvelope(
        topology_id=_topology_id(topology),
        run_id=_run_id(topology),
        status=status,
        checks=checks,
        failures=failures,
        traces=[trace.to_dict() for trace in topology.traces],
        suggested_actions=actions,
        metadata={
            "source": topology.root.location,
            "node_count": len(topology.nodes),
            "edge_count": len(topology.edges),
            "confidence": topology.confidence.value,
        },
    )


def _check_confidence(topology: TopologyManifest) -> CheckResult:
    if topology.confidence.value == "inferred":
        return CheckResult(
            "check.topology.confidence",
            "warning",
            "Manifest confidence is inferred; generated tests should stay smoke-level.",
            node_id="artifact.root",
            metadata={"confidence": topology.confidence.value},
        )
    return CheckResult(
        "check.topology.confidence",
        "passed",
        f"Manifest confidence is {topology.confidence.value}.",
        node_id="artifact.root",
        metadata={"confidence": topology.confidence.value},
    )


def _check_nodes(topology: TopologyManifest) -> CheckResult:
    status = "passed" if topology.nodes else "failed"
    return CheckResult(
        "check.topology.nodes",
        status,
        f"Topology contains {len(topology.nodes)} nodes.",
        metadata={"node_count": len(topology.nodes)},
    )


def _check_edges(topology: TopologyManifest) -> CheckResult:
    if topology.edges:
        status = "passed"
        summary = f"Topology contains {len(topology.edges)} edges."
    else:
        status = "warning"
        summary = "Topology has no edges; dependency and interface traversal will be limited."
    return CheckResult("check.topology.edges", status, summary, metadata={"edge_count": len(topology.edges)})


def _check_interfaces(topology: TopologyManifest) -> CheckResult:
    interfaces = [node for node in topology.nodes if node.kind == "interface"]
    if interfaces:
        return CheckResult(
            "check.topology.interfaces",
            "passed",
            f"Topology exposes {len(interfaces)} interface nodes.",
            metadata={"interface_count": len(interfaces)},
        )
    return CheckResult(
        "check.topology.interfaces",
        "warning",
        "No interface nodes detected; runtime validation may require hints or network scan.",
        metadata={"interface_count": 0},
    )


def _check_evidence(topology: TopologyManifest) -> CheckResult:
    evidence_nodes = [node for node in topology.nodes if node.kind == "evidence"]
    if evidence_nodes:
        return CheckResult(
            "check.topology.evidence",
            "passed",
            f"Topology has {len(evidence_nodes)} evidence nodes.",
            metadata={"evidence_count": len(evidence_nodes)},
        )
    return CheckResult(
        "check.topology.evidence",
        "warning",
        "No evidence nodes available; findings cannot be traced back to source artifacts.",
        metadata={"evidence_count": 0},
    )


def _crawl_checks(topology: TopologyManifest, scan_network: bool) -> list[CheckResult]:
    if not scan_network:
        return []
    page = _page_node(topology)
    if page is None:
        return []
    metadata = page.metadata
    return [
        _check_link_statuses(metadata, page.id),
        _check_asset_statuses(metadata, page.id),
    ]


def _check_link_statuses(metadata: dict, node_id: str) -> CheckResult:
    links = metadata.get("links", [])
    internal = [link for link in links if link.get("kind") == "internal"]
    if not internal:
        return CheckResult("check.web.link_status", "skipped", "No internal links to validate.", node_id=node_id, metadata={"checked": 0})
    results = _head_check_urls([link["url"] for link in internal])
    broken = [r for r in results if r["status"] is not None and (r["status"] < 200 or r["status"] >= 400)]
    if broken:
        return CheckResult(
            "check.web.link_status", "failed",
            f"{len(broken)} of {len(internal)} internal links returned error status.",
            node_id=node_id,
            metadata={"checked": len(internal), "broken": len(broken), "details": broken[:5]},
        )
    if any(r["status"] is None for r in results):
        unreachable = sum(1 for r in results if r["status"] is None)
        return CheckResult(
            "check.web.link_status", "warning",
            f"{unreachable} of {len(internal)} internal links were unreachable.",
            node_id=node_id,
            metadata={"checked": len(internal), "unreachable": unreachable},
        )
    return CheckResult(
        "check.web.link_status", "passed",
        f"All {len(internal)} checked internal links returned successful status.",
        node_id=node_id,
        metadata={"checked": len(internal)},
    )


def _check_asset_statuses(metadata: dict, node_id: str) -> CheckResult:
    assets = metadata.get("assets", [])
    if not assets:
        return CheckResult("check.web.asset_status", "skipped", "No assets to validate.", node_id=node_id, metadata={"checked": 0})
    results = _head_check_urls([asset["url"] for asset in assets])
    broken = [r for r in results if r["status"] is not None and (r["status"] < 200 or r["status"] >= 400)]
    if broken:
        return CheckResult(
            "check.web.asset_status", "failed",
            f"{len(broken)} of {len(assets)} assets returned error status.",
            node_id=node_id,
            metadata={"checked": len(assets), "broken": len(broken), "details": broken[:5]},
        )
    if any(r["status"] is None for r in results):
        unreachable = sum(1 for r in results if r["status"] is None)
        return CheckResult(
            "check.web.asset_status", "warning",
            f"{unreachable} of {len(assets)} assets were unreachable.",
            node_id=node_id,
            metadata={"checked": len(assets), "unreachable": unreachable},
        )
    return CheckResult(
        "check.web.asset_status", "passed",
        f"All {len(assets)} checked assets returned successful status.",
        node_id=node_id,
        metadata={"checked": len(assets)},
    )


def _head_check_urls(urls: list[str]) -> list[dict]:
    import httpx
    results: list[dict] = []
    for url in urls:
        try:
            with httpx.Client(follow_redirects=True, timeout=10.0, headers={"user-agent": "testql-inspector/0.1"}) as client:
                resp = client.head(url)
                results.append({"url": url, "status": resp.status_code})
        except Exception:
            results.append({"url": url, "status": None})
    return results



def _sitemap_checks(topology: TopologyManifest) -> list[CheckResult]:
    sitemap = _sitemap_node(topology)
    if sitemap is None:
        return []
    metadata = sitemap.metadata
    subpages = [node for node in topology.nodes if node.kind == "subpage"]
    if not subpages:
        return [
            CheckResult("check.sitemap.crawl", "skipped", "No subpages were crawled; sitemap checks skipped.", node_id=sitemap.id),
        ]
    checks = [
        _check_sitemap_crawl(sitemap, subpages),
        _check_sitemap_broken(sitemap, subpages),
        _check_sitemap_duplicates(sitemap, subpages),
    ]
    return checks


def _browser_checks(topology: TopologyManifest, use_browser: bool) -> list[CheckResult]:
    if not use_browser:
        return []
    page = _page_node(topology)
    if page is None:
        return []
    metadata = page.metadata
    return [
        _check_browser_render(page.id, metadata),
        _check_browser_console(page.id, metadata),
        _check_browser_network(page.id, metadata),
    ]


def _check_browser_render(node_id: str, metadata: dict) -> CheckResult:
    if metadata.get("console_errors") is not None or metadata.get("network_calls") is not None:
        return CheckResult("check.browser.render", "passed", "Page was rendered in a browser environment.", node_id=node_id)
    return CheckResult("check.browser.render", "warning", "No browser-rendered metadata detected; page may be static HTML only.", node_id=node_id)


def _check_browser_console(node_id: str, metadata: dict) -> CheckResult:
    errors = metadata.get("console_errors") or []
    if errors:
        return CheckResult("check.browser.console", "failed", f"{len(errors)} console error(s) detected during page load.", node_id=node_id, metadata={"errors": len(errors), "examples": errors[:5]})
    return CheckResult("check.browser.console", "passed", "No console errors detected.", node_id=node_id)


def _check_browser_network(node_id: str, metadata: dict) -> CheckResult:
    calls = metadata.get("network_calls") or []
    if calls:
        return CheckResult("check.browser.network", "passed", f"Captured {len(calls)} network call(s).", node_id=node_id, metadata={"calls": len(calls)})
    return CheckResult("check.browser.network", "warning", "No network calls captured during page load.", node_id=node_id)


def _sitemap_node(topology: TopologyManifest) -> Any:
    return next((node for node in topology.nodes if node.kind == "sitemap"), None)


def _check_sitemap_crawl(sitemap: Any, subpages: list[Any]) -> CheckResult:
    return CheckResult(
        "check.sitemap.crawl", "passed",
        f"Crawled {len(subpages)} subpage(s).",
        node_id=sitemap.id,
        metadata={"subpages": len(subpages)},
    )


def _check_sitemap_broken(sitemap: Any, subpages: list[Any]) -> CheckResult:
    broken = [sp for sp in subpages if sp.metadata.get("status_code") is not None and (sp.metadata["status_code"] < 200 or sp.metadata["status_code"] >= 400)]
    if broken:
        return CheckResult(
            "check.sitemap.broken", "failed",
            f"{len(broken)} of {len(subpages)} crawled subpages returned error status.",
            node_id=sitemap.id,
            metadata={"subpages": len(subpages), "broken": len(broken), "details": [{"url": sp.source, "status": sp.metadata.get("status_code")} for sp in broken[:5]]},
        )
    unreachable = [sp for sp in subpages if sp.metadata.get("status_code") is None]
    if unreachable:
        return CheckResult(
            "check.sitemap.broken", "warning",
            f"{len(unreachable)} of {len(subpages)} subpages were unreachable.",
            node_id=sitemap.id,
            metadata={"subpages": len(subpages), "unreachable": len(unreachable)},
        )
    return CheckResult(
        "check.sitemap.broken", "passed",
        f"All {len(subpages)} crawled subpages returned successful status.",
        node_id=sitemap.id,
        metadata={"subpages": len(subpages)},
    )


def _check_sitemap_duplicates(sitemap: Any, subpages: list[Any]) -> CheckResult:
    titles: dict[str, list[str]] = {}
    for sp in subpages:
        title = str(sp.metadata.get("title", "")).strip()
        if title:
            titles.setdefault(title, []).append(str(sp.source))
    dupes = {title: urls for title, urls in titles.items() if len(urls) > 1}
    if dupes:
        return CheckResult(
            "check.sitemap.duplicates", "warning",
            f"{len(dupes)} duplicate title(s) found across {len(subpages)} subpages.",
            node_id=sitemap.id,
            metadata={"duplicate_titles": len(dupes), "examples": [{"title": t, "urls": u[:3]} for t, u in list(dupes.items())[:3]]},
        )
    return CheckResult(
        "check.sitemap.duplicates", "passed",
        f"No duplicate titles found across {len(subpages)} subpages.",
        node_id=sitemap.id,
        metadata={"subpages": len(subpages)},
    )


def _web_checks(topology: TopologyManifest) -> list[CheckResult]:
    page = _page_node(topology)
    if page is None:
        return []
    metadata = page.metadata
    return [
        _check_web_status(page.id, metadata),
        _check_web_title(page.id, metadata),
        _check_web_links(page.id, metadata),
        _check_web_assets(page.id, metadata),
        _check_web_forms(page.id, metadata),
    ]


def _page_node(topology: TopologyManifest):
    return next((node for node in topology.nodes if node.kind == "page"), None)


def _check_web_status(node_id: str, metadata: dict) -> CheckResult:
    status_code = _status_code(metadata)
    if status_code is None:
        return CheckResult("check.web.status", "warning", "HTTP status code was not captured for the page.", node_id=node_id)
    if 200 <= status_code < 400:
        return CheckResult("check.web.status", "passed", f"Page returned HTTP {status_code}.", node_id=node_id, metadata={"status_code": status_code})
    return CheckResult("check.web.status", "failed", f"Page returned HTTP {status_code}.", node_id=node_id, metadata={"status_code": status_code})


def _check_web_title(node_id: str, metadata: dict) -> CheckResult:
    title = str(metadata.get("title") or "").strip()
    if title:
        return CheckResult("check.web.title", "passed", "Page title was extracted.", node_id=node_id, metadata={"title": title})
    return CheckResult("check.web.title", "warning", "Page title is missing or could not be extracted.", node_id=node_id)


def _check_web_links(node_id: str, metadata: dict) -> CheckResult:
    links = metadata.get("links") or []
    if links:
        internal = sum(1 for item in links if item.get("kind") == "internal")
        external = sum(1 for item in links if item.get("kind") == "external")
        return CheckResult("check.web.links", "passed", f"Extracted {len(links)} links ({internal} internal, {external} external).", node_id=node_id, metadata={"links": len(links), "internal": internal, "external": external})
    if _looks_like_spa(metadata):
        return CheckResult(
            "check.web.links",
            "skipped",
            "No static links were extracted; page looks like SPA with JS-rendered navigation.",
            node_id=node_id,
            metadata={"links": 0, "spa_suspected": True},
        )
    return CheckResult("check.web.links", "warning", "No links were extracted from the page.", node_id=node_id, metadata={"links": 0})


def _check_web_assets(node_id: str, metadata: dict) -> CheckResult:
    assets = metadata.get("assets") or []
    if assets:
        return CheckResult("check.web.assets", "passed", f"Extracted {len(assets)} page assets.", node_id=node_id, metadata={"assets": len(assets)})
    return CheckResult("check.web.assets", "warning", "No script, image, or stylesheet assets were extracted.", node_id=node_id, metadata={"assets": 0})


def _check_web_forms(node_id: str, metadata: dict) -> CheckResult:
    forms = metadata.get("forms") or []
    if forms:
        return CheckResult("check.web.forms", "passed", f"Extracted {len(forms)} forms.", node_id=node_id, metadata={"forms": len(forms)})
    return CheckResult("check.web.forms", "skipped", "No forms detected; form submission checks were skipped.", node_id=node_id, metadata={"forms": 0})


def _status_code(metadata: dict) -> int | None:
    value = metadata.get("status_code")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _looks_like_spa(metadata: dict) -> bool:
    assets = metadata.get("assets") or []
    script_assets = [asset for asset in assets if str(asset.get("kind", "")).lower() == "script"]
    return len(script_assets) > 0


def _findings_from_checks(checks: list[CheckResult]) -> list[FailureFinding]:
    findings = []
    for check in checks:
        if check.status in {"failed", "warning"}:
            severity = "high" if check.status == "failed" else "medium"
            findings.append(
                FailureFinding(
                    id=f"finding.{check.id.removeprefix('check.')}",
                    severity=severity,
                    summary=check.summary,
                    node_id=check.node_id,
                    edge_id=check.edge_id,
                    likely_cause=_likely_cause(check),
                    evidence_refs=list(check.evidence_refs),
                    metadata={"source_check": check.id, **check.metadata},
                )
            )
    return findings


def _actions_from_findings(findings: list[FailureFinding], topology: TopologyManifest) -> list[SuggestedAction]:
    actions = []
    for finding in findings:
        actions.append(
            SuggestedAction(
                id=f"action.{finding.id.removeprefix('finding.')}",
                type=_action_type(finding),
                summary=_action_summary(finding),
                target=finding.node_id or finding.edge_id or topology.root.location,
                priority=finding.severity,
                evidence_refs=list(finding.evidence_refs),
                metadata={"finding": finding.id},
            )
        )
    return actions


def _status_from_checks(checks: list[CheckResult]) -> str:
    if any(check.status == "failed" for check in checks):
        return "failed"
    if any(check.status == "warning" for check in checks):
        return "partial"
    return "passed"


def _likely_cause(check: CheckResult) -> str:
    causes = {
        "check.topology.confidence": "Discovery had insufficient manifest evidence.",
        "check.topology.nodes": "No artifact nodes were produced from the source.",
        "check.topology.edges": "Discovery found an isolated artifact without relationships.",
        "check.topology.interfaces": "No API/UI/CLI interface marker was discovered for runtime traversal.",
        "check.topology.evidence": "Probe results did not produce traceable source evidence.",
        "check.web.status": "The page did not return a successful HTTP status during network scan.",
        "check.web.title": "The HTML document has no title or the parser could not extract it.",
        "check.web.links": "The page contains no extractable anchors, or content requires browser-side rendering.",
        "check.web.assets": "The page contains no extractable script, image, or stylesheet references, or content requires browser-side rendering.",
        "check.web.link_status": "One or more internal links returned an error or were unreachable during HEAD validation.",
        "check.web.asset_status": "One or more page assets returned an error or were unreachable during HEAD validation.",
        "check.sitemap.crawl": "No subpages were available for crawling; this may indicate a single-page site or crawl limits.",
        "check.sitemap.broken": "One or more crawled subpages returned an error status or were unreachable.",
        "check.sitemap.duplicates": "Multiple subpages share the same title, which may indicate poor SEO or navigation structure.",
        "check.browser.render": "The page was not rendered in a browser; JavaScript-rendered content was not evaluated.",
        "check.browser.console": "Console errors were detected during browser page load, indicating potential JS issues.",
        "check.browser.network": "No network calls were captured during browser page load; this may indicate an empty or static page.",
    }
    return causes.get(check.id, "Topology check did not meet the expected condition.")


def _action_type(finding: FailureFinding) -> str:
    if "interfaces" in finding.id:
        return "add_runtime_hint_or_interface_probe"
    if "confidence" in finding.id:
        return "add_manifest_or_hint"
    if "edges" in finding.id:
        return "add_dependency_or_relation_probe"
    if "web.status" in finding.id:
        return "investigate_http_status"
    if "web.title" in finding.id:
        return "add_or_fix_page_title"
    if "web.links" in finding.id or "web.assets" in finding.id:
        return "add_browser_rendering_probe"
    if "web.link_status" in finding.id or "web.asset_status" in finding.id:
        return "investigate_broken_resources"
    if "sitemap.broken" in finding.id:
        return "investigate_broken_subpages"
    if "sitemap.duplicates" in finding.id:
        return "fix_duplicate_titles"
    if "browser.console" in finding.id:
        return "fix_js_errors"
    if "browser.network" in finding.id:
        return "investigate_static_page"
    return "investigate_topology"


def _action_summary(finding: FailureFinding) -> str:
    return f"Resolve {finding.id}: {finding.summary}"


def _topology_id(topology: TopologyManifest) -> str:
    return f"topology.{_safe(topology.root.location)}"


def _run_id(topology: TopologyManifest) -> str:
    return f"inspect.{_safe(topology.root.location)}"


def _safe(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_")
    return cleaned or "root"
