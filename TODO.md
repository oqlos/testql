# testql — TODO

> Auto-derived from metrics. Last updated: 2026-04-19 (v0.6.6)

---

## P0 — Blockers

- [ ] Pokrycie testów zgłaszane jako `null` — naprawić konfigurację `pytest-cov` w `pyqual.yaml`
- [ ] Wersja w `app.doql.less` niezsynchronizowana z VERSION (0.4.2 vs 0.6.6)

---

## CC hotspots (funkcje ≥ CC 15, limit: 10)

| CC | Plik | Funkcja | Akcja |
|----|------|---------|-------|
| 15 | `commands/suite_cmd.py` | `_collect_test_files` | Wydziel `_collect_from_suite()`, `_collect_by_pattern()`, `_collect_recursive()` |
| 15 | `generators/generators.py` | `_build_api_test_endpoints` | Wydziel `_format_api_row()`, `_build_assert_block()` |
| 13 | `commands/endpoints_cmd.py` | `_format_endpoints` | Wydziel sekcje per-framework |
| 13 | `commands/suite_cmd.py` | `suite` | Wydziel `_load_config()`, `_resolve_url()` |
| 12 | `interpreter/_testtoon_parser.py` | `parse_testtoon` | Wydziel `_parse_section_rows()` |
| 12 | `interpreter/_converter.py` | `_detect_scenario_type` | Użyj lookup dict zamiast if-chain |
| 12 | `generators/analyzers.py` | `detect_project_type` | Lookup dict |
| 12 | `generators/analyzers.py` | `_analyze_python_tests` | Wydziel per-test-type parser |

---

## God moduły (pliki > 500L)

| Plik | Rozmiar | Klasy | Max CC | Akcja |
|------|---------|-------|--------|-------|
| `endpoint_detector.py` | 835L | 13 | 13 | Split wg frameworka: `detectors/fastapi.py`, `detectors/flask.py`, `detectors/openapi.py` etc. |
| `generator.py` | 709L | 4 | 23 | Przenieść do `generators/` (już częściowo) — usunąć duplikacje |

---

## Testy i pokrycie

- [ ] Włączyć `pytest-cov` — coverage zgłaszane jako `null`
- [ ] `tests/test_generate_cmd.py` — pokryć `generate`, `analyze`, `_is_workspace()`
- [ ] `tests/test_suite_cmd.py` — pokryć `suite`, `list`, `_collect_test_files`
- [ ] `tests/test_echo.py` — pokryć `parse_doql_less`, `format_text_output`
- [ ] Cel pokrycia: ≥ 60%

---

## Integracja z projektami OqlOS

- [ ] Przetestować `testql suite` na wygenerowanych scenariuszach z podniesionym serwerem oqlos
- [ ] `testql run` na `generated-api-smoke.testql.toon.yaml` — http://localhost:8101
- [ ] Zintegrować z CI (pyqual stage `test` → `testql suite`)

---

## ✅ Wykonane (2026-04-19)

- ✅ `convert_iql_to_testtoon` CC 66 → ≤12 — dispatch table, 12 handler functions
- ✅ `parse_doql_less` CC 29 → ≤8 — 7 helperów
- ✅ `format_text_output` CC 19 → ≤6 — 5 helperów
- ✅ `suite` CC 18 → 13
- ✅ `echo` (misc_cmds) CC 16 → ≤10
- ✅ Naprawiony `generate --analyze-only` crash (None profile)
- ✅ Naprawiona detekcja workspace vs. projekt Python
- ✅ Naprawiony `testql list` — tabela + TestTOON header
- ✅ Wygenerowane i zwalidowane scenariusze dla 6 projektów (17/17 OK)
- ✅ 22 testy zielone
