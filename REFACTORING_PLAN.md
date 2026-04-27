# TestQL Refactoring Plan

## Current State Analysis

### 1. Architecture Overview

```
testql/
├── discovery/          # Artifact manifest discovery system
│   ├── manifest.py     # ArtifactManifest dataclass
│   ├── registry.py     # ProbeRegistry for running probes
│   ├── source.py       # ArtifactSource abstraction
│   └── probes/         # Various probe implementations
│       ├── base.py     # BaseProbe, ProbeResult
│       ├── filesystem/ # DockerfileProbe, PythonPackageProbe, etc.
│       ├── network/    # HTTPPageProbe
│       └── browser/    # PlaywrightPageProbe
├── generators/         # Test generation engine
│   ├── analyzers.py    # ProjectAnalyzer
│   ├── base.py         # BaseAnalyzer, TestPattern
│   ├── generators.py   # Generator mixins
│   └── test_generator.py # Main TestGenerator class
├── adapters/           # DSL adapters
│   ├── base.py         # BaseDSLAdapter
│   ├── testtoon_adapter.py # TestTOON format
│   ├── nl/            # Natural language adapter
│   ├── proto/         # Protocol Buffers adapter
│   └── graphql/       # GraphQL adapter
├── ir/                # Unified Intermediate Representation
│   ├── model.py       # TestPlan, Step classes
│   └── runner/        # IR execution engine
└── cli/               # Command-line interface
```

### 2. Current Probe Types (Manifest Files)

| Probe | File Types | Detection Method | Confidence |
|-------|------------|------------------|------------|
| `PythonPackageProbe` | `pyproject.toml`, `setup.py`, `Pipfile` | Regex parsing + AST | 25-95 |
| `NodePackageProbe` | `package.json` | JSON parsing | 60-95 |
| `DockerfileProbe` | `Dockerfile`, `Containerfile` | File presence + content | 90 |
| `DockerComposeProbe` | `docker-compose.yml` | YAML parsing | 80 |
| `OpenAPIProbe` | `openapi*.yaml`, `swagger*.yaml` | YAML validation | 80 |
| `HTTPPageProbe` | N/A | Network request | 70 |
| `PlaywrightPageProbe` | N/A | Browser automation | 85 |

### 3. Current Generator Types

| Generator | Input | Output | Status |
|-----------|-------|--------|--------|
| `APIGeneratorMixin` | OpenAPI/FastAPI routes | `.testql.toon.yaml` | Working |
| `PythonTestGeneratorMixin` | Python test files | `.testql.toon.yaml` | Working |
| `ScenarioGeneratorMixin` | OQL/CQL files | `.testql.toon.yaml` | Partial |
| `SpecializedGeneratorMixin` | Project type specific | Various | Partial |

### 4. MCP Windsurf Integration Status

**Current State:** No direct MCP integration

**What works:**
- CLI with JSON output (`--format json`)
- Discover command returns structured data
- Generate command creates test files

**What needs work:**
- No MCP server implementation
- No real-time progress reporting
- No streaming results
- Limited error reporting format

---

## Refactoring Plan

### Phase 1: MCP Server Implementation (High Priority)

#### 1.1 Create MCP Server Module
```
testql/
├── mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server setup
│   ├── tools/             # MCP tool implementations
│   │   ├── __init__.py
│   │   ├── discover.py    # discover tool
│   │   ├── generate.py    # generate tool
│   │   ├── run.py         # run tests tool
│   │   └── report.py      # report generation tool
│   └── resources/         # MCP resources
│       ├── __init__.py
│       └── manifests.py   # manifest resource handler
```

#### 1.2 MCP Tools Design

```python
# @mcp.tool()
async def discover_project(
    path: str,
    include_network: bool = False,
    use_browser: bool = False
) -> dict:
    """Discover project structure and return manifest."""

# @mcp.tool()
async def generate_tests(
    path: str,
    output_dir: str | None = None,
    test_types: list[str] | None = None
) -> list[str]:
    """Generate tests for project."""

# @mcp.tool()
async def run_test_scenario(
    scenario_path: str,
    env: dict | None = None
) -> dict:
    """Run a test scenario and return results."""

# @mcp.tool()
async def get_test_report(
    run_id: str,
    format: str = "json"
) -> dict | str:
    """Get test report by run ID."""
```

### Phase 2: Test Coverage Expansion (High Priority)

#### 2.1 Missing Probe Tests

| Probe | Current Tests | Needed |
|-------|---------------|--------|
| `DockerComposeProbe` | 1 | Full service dependency graph |
| `OpenAPIProbe` | 1 | Version detection, security schemes |
| `HTTPPageProbe` | 0 | Network timeout, retry logic |
| `PlaywrightPageProbe` | 0 | Browser detection, SPA routing |

#### 2.2 Missing Generator Tests

| Generator | Current Tests | Needed |
|-----------|---------------|--------|
| `ScenarioGeneratorMixin` | 0 | Full OQL/CQL to IR |
| `SpecializedGeneratorMixin` | 0 | CLI, lib, frontend, hardware |
| `Round-trip` | 1 | Full fidelity preservation |

### Phase 3: Report System Refactoring (Medium Priority)

#### 3.1 Current Report Format Issues

**testql.toon.yaml**:
- Human readable but verbose
- No standard schema
- Difficult to parse programmatically

**Proposed Solution**:
```yaml
# New format: testql-report.json
{
  "version": "2.0",
  "run_id": "uuid",
  "timestamp": "iso8601",
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "skipped": 0
  },
  "manifests": [...],
  "tests": [...],
  "coverage": {...}
}
```

#### 3.2 Report Generation Pipeline

```python
class ReportPipeline:
    def collect(self, results: list[TestResult]) -> ReportData
    def transform(self, data: ReportData, format: str) -> FormattedReport
    def output(self, report: FormattedReport, destination: str) -> None
```

### Phase 4: IDE Integration Improvements (Medium Priority)

#### 4.1 JetBrains Plugin Support

Requirements:
- [ ] JSON Schema for `.testql.toon.yaml` files
- [ ] LSP server for syntax highlighting
- [ ] Run configuration templates
- [ ] Test result tree view

#### 4.2 VS Code Extension Support

Requirements:
- [ ] Language server protocol (LSP)
- [ ] Test explorer integration
- [ ] Live test result decoration
- [ ] Quick fixes and code actions

#### 4.3 Windsurf Integration

Already works via MCP, but needs:
- [ ] Better progress reporting
- [ ] Streaming test results
- [ ] Inline error annotations
- [ ] Test coverage overlays

---

## Testing Strategy

### 1. Unit Tests

```bash
# Run all probe tests
pytest tests/test_discovery.py -v

# Run specific probe
pytest tests/test_discovery.py::TestPythonPackageProbe -v

# Run generator tests
pytest tests/test_generators.py -v

# Run MCP tests
pytest tests/test_mcp.py -v  # To be created
```

### 2. Integration Tests

```bash
# Full pipeline test
python test_manifest_and_generators.py --all

# MCP integration
python test_manifest_and_generators.py --mcp-check

# With real projects
pytest tests/test_integration/ -v
```

### 3. E2E Tests

```bash
# Test with sample projects
cd examples/
make test-all

# Test with real-world projects
make test-real-world
```

---

## Implementation Timeline

### Week 1: MCP Server
- [ ] Set up `mcp` module structure
- [ ] Implement basic MCP server with FastMCP
- [ ] Add discover, generate, run tools
- [ ] Write tests for MCP tools

### Week 2: Report System
- [ ] Design new report schema
- [ ] Implement ReportPipeline
- [ ] Add JSON, HTML, Markdown exporters
- [ ] Update CLI to use new reports

### Week 3: Test Coverage
- [ ] Expand probe tests to 100% coverage
- [ ] Add missing generator tests
- [ ] Create integration test suite
- [ ] Add performance benchmarks

### Week 4: IDE Integration
- [ ] Create JSON Schema for `.testql.toon.yaml`
- [ ] Implement LSP server basics
- [ ] Add JetBrains plugin stub
- [ ] Add VS Code extension stub

### Week 5: Documentation & Polish
- [ ] Update README with MCP usage
- [ ] Create IDE integration guides
- [ ] Performance optimization
- [ ] Final testing and release

---

## Migration Guide

### For Existing Users

**No breaking changes** - all existing APIs remain unchanged.

New features are additive:
- MCP server is optional
- New report formats are opt-in
- CLI behavior unchanged

### For IDE Plugin Developers

1. Use MCP for Windsurf integration (already supported)
2. Use LSP for JetBrains/VS Code (coming in Phase 4)
3. Use JSON output for custom integrations

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Probe coverage | 70% | 95% |
| Generator coverage | 60% | 90% |
| MCP tool availability | 0 | 4+ |
| Report formats | 1 | 4+ |
| IDE integrations | 1 (Windsurf via MCP) | 3+ |
| Average test time | 30s | <10s |

---

## Next Steps

1. **Review this plan** - Check if priorities align with user needs
2. **Run test suite** - Execute `python test_manifest_and_generators.py --all`
3. **Create issues** - Break down tasks into GitHub issues
4. **Start Phase 1** - Begin MCP server implementation
5. **Iterate** - Gather feedback and adjust plan
