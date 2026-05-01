# TODO — TestQL Development Roadmap

Last updated: 2026-05-01

## 🎯 Active Development Priorities

### Phase 1: Topology-Aware Orchestration (In Progress)
- [ ] Build TopologyManifest with TopologyNode/TopologyEdge/TraversalTrace
- [ ] Implement PageSchema with structured web page representation
- [ ] Add TestResultEnvelope for standardized test results
- [ ] Create RefactorPlan generator with NLP summaries
- [ ] Implement JSON schemas for validation
- [ ] Add JSON/YAML/TOON round-tripping support

### Phase 2: Browser & GUI Testing Enhancement
- [ ] Full Playwright integration with screenshots support
- [ ] Accessibility checks (WCAG compliance scanning)
- [ ] Performance metrics collection (Lighthouse-like)
- [ ] Auth flow automation (login sequences)
- [ ] Browser network interception and mocking

### Phase 3: MCP Service Integration
- [ ] MCP resources for topology access
- [ ] MCP tools for discovery/topology/run/explain operations
- [ ] MCP refactor plan generation endpoint
- [ ] MCP service code generation workflows

### Phase 4: DSL Unification
- [ ] Unified scenario DSL with metadata, vars, targets, steps
- [ ] Compile to internal TestStep model
- [ ] YAML/TOON/Imperative syntax parity
- [ ] Environment-prefixed command migration (GUI_*, ENCODER_*, API → unified)

### Phase 5: Quality & Test Coverage
- [ ] Increase test coverage to 75% (from current 65%)
- [ ] Add integration tests for browser discovery
- [ ] Add E2E tests for CLI workflows
- [ ] Performance benchmarks for large topology graphs

## 📋 Technical Debt & Code Quality

> **Note:** Complete prefact-generated issues (848 items) archived to `.archive/TODO_prefact_2026-04-25.md`

### Issue Categories

| Category | Count | Example |
|----------|-------|---------|
| Unused imports (`annotations`) | ~120 | `testql/adapters/base.py:8` |
| Relative imports | ~95 | `testql/adapters/__init__.py:10` |
| String concatenations | ~85 | Convert to f-strings |
| Magic numbers | ~45 | Extract to named constants |
| Duplicate imports | ~25 | Clean up double imports |
| Missing return types | ~15 | Add type hints |

### Top Files Requiring Attention

- `testql/adapters/*` — 200+ issues (imports, concatenations)
- `testql/commands/*` — 150+ issues (magic numbers, imports)
- `testql/detectors/*` — 100+ issues (relative imports)
- `testql/interpreter/*` — 80+ issues (various)

### Quick Fixes Available

```bash
# Fix unused imports
ruff check --select F401 testql/ --fix

# Fix string concatenations  
ruff check --select UP032 testql/ --fix

# Show all issues
prefact -a --show-todos
```

## 🚀 Planned Features

### Runtime vs Code Delta Analysis
- [ ] Static analysis of codebase
- [ ] Runtime service discovery
- [ ] Delta report generation (missing/extra services)
- [ ] Auto-synchronization recommendations

### Service Generation
- [ ] LLM-driven service stub generation
- [ ] OpenAPI-to-service scaffolding
- [ ] Test-to-service verification

### Advanced Web Inspection
- [ ] Form submission testing
- [ ] Cookie/session handling
- [ ] Multi-page flow testing
- [ ] Visual regression support

## 📁 Related Documentation

- [CHANGELOG.md](./CHANGELOG.md) — Release history
- [SUMD.md](./SUMD.md) — Complete project structure and architecture
- [DSL.md](./DSL.md) — Language specification
- [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) — Long-term refactoring strategy

---

*For complete prefact issues list, see `.archive/TODO_prefact_2026-04-25.md` or run `prefact -a --export-todos`*
