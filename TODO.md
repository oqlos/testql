# testql — TODO

> Auto-derived from metrics. Last updated: 2026-04-24 (v0.6.7)

---

## P0 — Refaktoryzacja Executor'a (Nowe Funkcje)

### 1. CLI/Shell Test Execution ✅ (2026-04-24)

**Problem:** Generator tworzy `generated-cli-tests.testql.toon.yaml` z TYPE: cli, ale interpreter nie ma komend do wykonywania procesów shell.

**Status:** ✅ Zaimplementowane

**Wykonane:**
- ✅ `testql/interpreter/_shell.py` — nowy mixin z komendami:
  - `SHELL "command" [timeout_ms]` — wykonanie komendy shell
  - `EXEC "path/to/script" [args]` — wykonanie skryptu
  - `RUN "python -m module" [args]` — wykonanie modułu Python
  - `ASSERT_EXIT_CODE <code>` — asercja kodu wyjścia
  - `ASSERT_STDOUT_CONTAINS "pattern"` — asercja stdout
  - `ASSERT_STDERR_CONTAINS "pattern"` — asercja stderr
- ✅ `ShellMixin` dodany do `IqlInterpreter` w `interpreter.py`
- ✅ `_generate_cli_tests()` rozszerzone o realne komendy SHELL
- ✅ Testy w `tests/test_shell_execution.py` (9 testów ✅)

**Priorytet:** ✅ P0 — gotowe dla protogate i innych CLI projektów

---

### 2. Desktop GUI Test Execution ✅ (2026-04-24)

**Problem:** GUI tests (TYPE: gui) emitują tylko eventy, nie wykonują faktycznych akcji.

**Status:** ✅ Zaimplementowane (dry-run + Playwright/Selenium wsparcie)

**Wykonane:**
- ✅ `testql/interpreter/_gui.py` — mixin z driverami:
  - Playwright desktop (electron, native apps)
  - Selenium WebDriver
- ✅ Komendy:
  - `GUI_START "app_path" [args]` — uruchomienie aplikacji
  - `GUI_CLICK "selector"` — kliknięcie elementu
  - `GUI_INPUT "selector" "text"` — wprowadzenie tekstu
  - `GUI_ASSERT_VISIBLE "selector"` — asercja widoczności
  - `GUI_ASSERT_TEXT "selector" "expected"` — asercja tekstu
  - `GUI_CAPTURE "selector" "screenshot.png"` — screenshot
  - `GUI_STOP` — zamknięcie aplikacji
- ✅ Konfiguracja drivera w CONFIG: `gui_driver: playwright|selenium`
- ✅ `GuiMixin` dodany do `IqlInterpreter`
- ✅ `_generate_frontend_tests()` rozszerzone o realne komendy GUI
- ✅ Testy w `tests/test_gui_execution.py` (11 testów ✅)

**Priorytet:** ✅ P1 — gotowe dla projektów z UI (dry-run działa, pełne wymaga Playwright/Selenium)

---

### 3. Unit Test Execution ✅ (2026-04-24)

**Problem:** `_generate_lib_tests()` generuje tylko LOG placeholders, nie wykonuje testów jednostkowych.

**Status:** ✅ Zaimplementowane

**Wykonane:**
- ✅ `testql/interpreter/_unit.py` — mixin do wykonywania testów:
  - `UNIT_PYTEST "path/to/test.py"` — uruchomienie pytest
  - `UNIT_PYTEST_DISCOVER "tests/"` — discovery i run
  - `UNIT_ASSERT "module.func" "args" "expected"` — test pojedynczej funkcji
  - `UNIT_IMPORT "module"` — weryfikacja importu
- ✅ `UnitMixin` dodany do `IqlInterpreter`
- ✅ Integracja z istniejącymi testami Python (pytest)
- ✅ `_generate_lib_tests()` rozszerzone o realne komendy UNIT
- ✅ Testy w `tests/test_unit_execution.py` (9 testów ✅)

**Priorytet:** ✅ P1 — gotowe dla python-lib projektów

---

### 4. Architektura — Refaktoryzacja Dispatcher'a ✅ (2026-04-24)

**Obecny stan:** `_dispatch()` w `interpreter.py` używa `getattr(self, f"_cmd_{cmd.lower()}", None)`

**Status:** ✅ Zaimplementowane

**Wykonane:**
- ✅ `testql/interpreter/dispatcher.py` — nowy `CommandDispatcher` z:
  - Auto-discovery wszystkich `_cmd_*` metod z mixinów
  - `register()` dla custom komend
  - `dispatch()` z lepszymi błędami i sugestiami ("Did you mean...")
  - `list_commands()` i `has_command()` do introspekcji
- ✅ Zrefaktoryzowano `IqlInterpreter` — używa `CommandDispatcher`
- ✅ Uproszczono dodawanie nowych mixin (auto-discovery)
- ✅ Lepsze error messages: "Unknown command: FOO. Did you mean: FOR, FOO_BAR?"
- ✅ Testy w `tests/test_dispatcher.py` (10 testów ✅)

**Priorytet:** ✅ P1 — gotowe, architektura ulepszona

---

## P0 — Blockers

- ✅ Pokrycie testów: 16% → 65% (cel ≥ 50% osiągnięty)
- [ ] `pyqual.yaml` `coverage_min` ustawiony na 16 — podnosić do 65

---

## CC hotspots (funkcje ≥ CC 15, limit: 10)

**Status (2026-04-24):** Większość zrefaktoryzowana po migracji do struktury pakietów.

| CC | Plik | Funkcja | Status |
|----|------|---------|--------|
| 15 | `commands/suite_cmd.py` | `_collect_test_files` | ✅ Przeniesiona do `commands/suite/` |
| 15 | `generators/generators.py` | `_build_api_test_endpoints` | ✅ Zrefaktoryzowana (CC≈5) |
| 13 | `commands/endpoints_cmd.py` | `_format_endpoints` | ⏳ Do sprawdzenia |
| 13 | `commands/suite_cmd.py` | `suite` | ✅ Przeniesiona do `commands/suite/cli.py` |
| 12 | `interpreter/_testtoon_parser.py` | `parse_testtoon` | ✅ Zrefaktoryzowana |
| 12 | `interpreter/_converter.py` | `_detect_scenario_type` | ✅ Zrefaktoryzowana |
| 12 | `generators/analyzers.py` | `detect_project_type` | ✅ Zrefaktoryzowana |
| 12 | `generators/analyzers.py` | `_analyze_python_tests` | ✅ Zrefaktoryzowana |

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
