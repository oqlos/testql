---
title: "TestQL → Multi-DSL Test Platform: plan refaktoryzacji 0.7.0 → 1.0.0"
slug: testql-multi-dsl-refactor-plan
date: 2026-04-25
project: testql
version_from: 0.6.23
version_target: 1.0.0
phases: 6
status: proposed
audience: [llm-executor, human-reviewer]
markpact: { plan: { path: "articles/testql-multi-dsl-refactor-plan.md" } }
tags: [testql, refactoring, dsl, nlp, sql, protobuf, graphql, semcod]
---

# TestQL → Multi-DSL Test Platform

Plan refaktoryzacji rozszerzającej TestQL z DSL dla testów GUI/API/encoder na platformę testową obsługującą języki naturalne (NLP), SQL, Protocol Buffers, GraphQL i dowolne inne DSL — z generowaniem i meta-testowaniem.

## 1. Cel strategiczny

Przekształcić TestQL z interpretera jednego DSL (TestTOON) w **platformę adapterów DSL** ze wspólną reprezentacją pośrednią (IR), zdolną do:

- testowania interfejsów opisanych w **języku naturalnym** ("kliknij login, wprowadź email, sprawdź czy widać dashboard")
- walidacji **kontraktów SQL** (schemat, zapytania, oczekiwane wyniki, integralność)
- testowania **schematów Protocol Buffers** (round-trip, zgodność wersji, wire-format)
- testowania **GraphQL** (queries, mutations, subskrypcje, schema introspection)
- generowania testów z dowolnego źródła (OpenAPI, schema SQL, plik `.proto`, opis NL, ekran UI)
- **meta-testowania** — testowania samego frameworka, walidacji wygenerowanych testów

**Wynik:** TestQL 1.0.0 jako uniwersalny runner kontraktów, niezależny od formatu zapisu testu.

## 2. Punkt wyjścia (stan na 0.6.23)

Dane z `project/map.toon.yaml`:

- 132 moduły, 195 klas, 204 funkcje, 15.6k linii Pythona
- CC̄ = 3.9 (dobre), 8 pozycji krytycznych
- Hotspoty CC: `parse_testtoon=14`, `suite=13`, `parse_value=11`, `detect_scenario_type=11`, `_execute_oql_line=10`
- Hotspoty fan-out: `generate=19`, `watch=19`, `suite=19`, `main=18`, `_run_oql_lines=15`
- Test coverage: 65% (vallm 64.6%)
- Zero cykli importów

**Co już jest gotowe pod rozszerzenie:**

| Element | Lokalizacja | Wzorzec | Wykorzystanie |
| --- | --- | --- | --- |
| Handlery komend | `interpreter/converter/handlers/` | strategia + auto-discovery | Wzorzec do powtórzenia dla parserów DSL |
| Detektory frameworków | `detectors/` (FastAPI, Flask, Django, Express, GraphQL, OpenAPI, WebSocket) | plugin + `BaseDetector` | Wzorzec do powtórzenia dla `BaseDSLAdapter` |
| Generatory | `generators/` (analyzers, multi, test_generator) | analyzer + generator pipeline | Rozszerzane, nie zastępowane |
| Mixin'y wykonania | `interpreter/_shell.py`, `_gui.py`, `_unit.py`, `_api_runner.py`, `_websockets.py` | mixin per typ wykonania | Stabilna baza — bez zmian |
| Echo (LLM context) | `commands/echo/` | parser → context → formatter | Rozszerzone o nowe formaty |

**Co wymaga refaktoryzacji:**

- `_testtoon_parser.py` (414 linii, CC=14) — twardo zakodowany jako jedyny parser. Trzeba uogólnić.
- `runner.py` (372 linii, fan-out=15) — orkiestracja zakłada TestTOON. Trzeba wyciągnąć dispatch DSL.
- `generator.py` + `generators/generators.py` (373 linie) — generuje tylko TestTOON. Trzeba wprowadzić strategię docelowego DSL.
- `detect_scenario_type` (CC=11) — rozwidlenia per typ scenariusza, dziś w jednej funkcji.

## 3. Architektura docelowa

```text
                  ┌─────────────────────────────────┐
                  │   Source artifact (input)       │
                  │   .testql.toon.yaml             │
                  │   .nl.md  (natural language)    │
                  │   .sql / .ddl                   │
                  │   .proto                        │
                  │   .graphql                      │
                  │   openapi.yaml                  │
                  └────────────┬────────────────────┘
                               │
                  ┌────────────▼────────────────────┐
                  │   DSLAdapter registry           │  ◄── pluginowy, auto-discovery
                  │   (detect format → adapter)     │
                  └────────────┬────────────────────┘
                               │
                  ┌────────────▼────────────────────┐
                  │   Unified IR (Intermediate)     │
                  │   TestPlan { steps, asserts,    │
                  │     fixtures, metadata }        │
                  └────────────┬────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼─────┐          ┌─────▼─────┐         ┌─────▼─────┐
   │ Executor │          │ Generator │         │ Validator │
   │ pipeline │          │ pipeline  │         │ (vallm)   │
   └────┬─────┘          └─────┬─────┘         └─────┬─────┘
        │                      │                      │
   ┌────▼─────────────────────▼──────────────────────▼────┐
   │  Existing mixins: shell, gui, unit, api, websocket   │
   └──────────────────────────────────────────────────────┘
```

**Kluczowe decyzje architektoniczne:**

- **Unified IR** (`testql.ir.TestPlan`) staje się "lingua franca" — wszystkie adaptery produkują, wszystkie executory konsumują.
- **DSLAdapter** to interfejs analogiczny do `BaseDetector` — każdy język ma własny adapter z metodami `detect()`, `parse()`, `to_ir()`, `from_ir()` (dla generowania w drugą stronę).
- **Backward compatibility:** stare `*.testql.toon.yaml` działa bez zmian — `TestTOONAdapter` to po prostu jeden z adapterów.
- **Re-export shims** w `testql/__init__.py` zachowują wszystkie aktualne ścieżki importu.

## 4. Faza 0 — Fundament: warstwa IR i abstrakcja DSL

**Cel:** wprowadzić Unified IR i interfejs DSLAdapter bez zmiany istniejącego zachowania.

**Czas:** 1–2 sesje. **Wersja docelowa:** `0.7.0-rc1`.

### 4.1 Nowe moduły

```text
testql/
├── ir/                          # NEW — Unified Intermediate Representation
│   ├── __init__.py              # re-export TestPlan, Step, Assertion, Fixture
│   ├── plan.py                  # TestPlan dataclass (root)
│   ├── steps.py                 # Step, ApiStep, GuiStep, EncoderStep, ShellStep, NlStep, SqlStep, ProtoStep, GraphqlStep
│   ├── assertions.py            # Assertion (operator, expected, actual_path)
│   ├── fixtures.py              # Fixture (setup/teardown)
│   └── metadata.py              # ScenarioMetadata (name, type, version, tags)
│
├── adapters/                    # NEW — DSL adapter registry
│   ├── __init__.py              # auto-discovery (scan na *_adapter.py)
│   ├── base.py                  # BaseDSLAdapter (ABC) + DSLDetectionResult
│   ├── registry.py              # AdapterRegistry — singleton
│   └── testtoon_adapter.py      # MIGRATION — wraps existing TestTOON parser
```

### 4.2 BaseDSLAdapter API

```python
class BaseDSLAdapter(ABC):
    name: str                              # "testtoon", "nl", "sql", "proto", "graphql"
    file_extensions: tuple[str, ...]       # (".testql.toon.yaml",)
    mime_types: tuple[str, ...] = ()

    @abstractmethod
    def detect(self, source: str | Path) -> DSLDetectionResult: ...

    @abstractmethod
    def parse(self, source: str | Path) -> TestPlan: ...

    @abstractmethod
    def render(self, plan: TestPlan) -> str:                     # IR → DSL (dla generatora)
        ...

    def validate(self, plan: TestPlan) -> list[ValidationIssue]: # default: pusta lista
        return []
```

### 4.3 Migracja istniejącego parsera

- Przenieść logikę z `interpreter/_testtoon_parser.py` do `adapters/testtoon_adapter.py` jako `TestToonAdapter`.
- Rozbić `parse_testtoon` (CC=14) na łańcuch metod prywatnych:
  - `_split_sections(text) -> list[Section]`
  - `_parse_header(section) -> dict`
  - `_parse_table(section) -> list[dict]`
  - `_section_to_step(section, kind) -> Step`
- Zostawić `interpreter/_testtoon_parser.py` jako re-export shim:

```python
from testql.adapters.testtoon_adapter import parse_testtoon, Section  # backward compat
```

### 4.4 Kryteria sukcesu Fazy 0

- [ ] Wszystkie istniejące testy przechodzą bez zmian (`pytest -q`).
- [ ] CC `parse_testtoon` ≤ 6 (z 14).
- [ ] `TestPlan` IR z 100% pokryciem testowym (nowy moduł — łatwo).
- [ ] Brak nowych zależności runtime.
- [ ] `testql echo` działa identycznie.
- [ ] `pyqual run` przechodzi z dotychczasowymi gate'ami (coverage_min: 65, vallm_pass_min: 64).

### 4.5 Toon artefakty do wygenerowania po fazie

- `project/map.toon.yaml` — porównanie z baseline (oczekiwany spadek max-CC z 14 do ≤6).
- `project/duplication.toon.yaml` — sprawdzić czy nie wprowadziliśmy duplikacji w shimach.

## 5. Faza 1 — Adapter NLP (testowanie języka naturalnego)

**Cel:** umożliwić zapis testów w języku naturalnym i ich automatyczne wykonanie.

**Czas:** 2–3 sesje. **Wersja docelowa:** `0.8.0-rc1`.

### 5.1 Nowy adapter

```text
testql/adapters/nl/
├── __init__.py
├── nl_adapter.py                # NLDSLAdapter — implementuje BaseDSLAdapter
├── intent_recognizer.py         # mapowanie czasowników → intent (CLICK, INPUT, ASSERT, NAVIGATE, ...)
├── entity_extractor.py          # ekstrakcja URL, selektorów, wartości, statusów HTTP
├── grammar.py                   # gramatyka deterministyczna (rozszerzalna)
├── llm_fallback.py              # opcjonalny LLM fallback dla niejednoznacznych zdań
└── lexicon/
    ├── __init__.py
    ├── pl.yaml                  # polski słownik intencji (kliknij, wprowadź, sprawdź, otwórz, ...)
    ├── en.yaml                  # angielski (click, type, assert, navigate, ...)
    └── de.yaml                  # niemiecki — opcjonalnie
```

### 5.2 Format wejściowy `.nl.md`

```markdown
# SCENARIO: Logowanie użytkownika
TYPE: gui
LANG: pl

1. Otwórz `/login`
2. Wprowadź "admin@example.com" do pola email
3. Wprowadź "password123" do pola hasło
4. Kliknij przycisk "Zaloguj"
5. Sprawdź że widoczny jest element `[data-testid='dashboard']`
6. Sprawdź że URL zawiera "/dashboard"
```

### 5.3 Pipeline parsowania NL

```text
text → tokenize → match_intent (lexicon) → extract_entities → resolve_targets → IR step
                       │ no match
                       ▼
                  llm_fallback (opt)
```

Deterministyczna ścieżka najpierw (gramatyka + leksykon), LLM tylko jako fallback dla niejednoznacznych zdań — z kosztorysowaniem przez `costs` (już zintegrowane w stacku).

### 5.4 Wzorzec tłumaczenia

| NL (PL) | Intent | IR Step |
| --- | --- | --- |
| "Otwórz /login" | `NAVIGATE` | `GuiStep(action="navigate", path="/login")` |
| "Kliknij `[data-action='login']`" | `CLICK` | `GuiStep(action="click", selector="[data-action='login']")` |
| "Wprowadź X do Y" | `INPUT` | `GuiStep(action="input", selector=Y, value=X)` |
| "Sprawdź że status to 200" | `ASSERT` | `Assertion(field="status", op="==", expected=200)` |
| "Wykonaj GET /api/health" | `API` | `ApiStep(method="GET", path="/api/health")` |
| "Zapytanie SQL SELECT * FROM users" | `SQL` | `SqlStep(query="SELECT * FROM users")` |

### 5.5 Kryteria sukcesu Fazy 1

- [ ] `testql run scenarios/nl/login.nl.md` wykonuje test identyczny z `scenarios/views/login.testql.toon.yaml`.
- [ ] Pokrycie leksykonu PL: 30+ czasowników intencji, 95% test scenariuszy daje deterministyczną ścieżkę bez LLM.
- [ ] CC nowych modułów < 8 (każdy).
- [ ] Test coverage adaptera NL ≥ 80%.
- [ ] `vallm` walidacja semantyczna passrate ≥ 70%.
- [ ] `testql nl-to-toon scenario.nl.md` produkuje równoważny `.testql.toon.yaml` (bidirectional).

### 5.6 Konkretne testy E2E

- `scenarios/nl/login.nl.md` (PL) → wywołuje GUI mixin → przechodzi
- `scenarios/nl/api-smoke.nl.md` (PL) → wywołuje API mixin → 3 endpointy
- `scenarios/nl/encoder-flow.nl.md` (PL) → wywołuje encoder mixin

## 6. Faza 2 — Adapter SQL (testowanie kontraktów bazodanowych)

**Cel:** testować schematy SQL, zapytania, integralność danych.

**Czas:** 2 sesje. **Wersja docelowa:** `0.9.0-rc1`.

### 6.1 Nowe moduły

```text
testql/adapters/sql/
├── __init__.py
├── sql_adapter.py               # SqlDSLAdapter
├── ddl_parser.py                # CREATE TABLE / ALTER / INDEX → schema IR
├── query_parser.py              # SELECT/INSERT/UPDATE/DELETE → query IR (sqlglot)
├── dialect_resolver.py          # postgres / sqlite / mysql / mssql
└── fixtures.py                  # SQL fixtures: setup/teardown, transactions

testql/interpreter/_sql.py       # SQL execution mixin
```

### 6.2 Format wejściowy `.sql.testql.yaml`

```yaml
# SCENARIO: User table contract
# TYPE: sql
# DIALECT: postgres
# VERSION: 1.0

CONFIG[1]{key, value}:
  connection_url, postgresql://localhost/test_db

SCHEMA[3]{table, column, type}:
  users, id, INT
  users, email, VARCHAR(255)
  users, created_at, TIMESTAMP

QUERY[2]{name, sql}:
  count_users, SELECT COUNT(*) FROM users
  active_users, SELECT id FROM users WHERE active = true

ASSERT[3]{query, op, expected}:
  count_users, ==, 100
  active_users.length, >, 0
  active_users[0].id, !=, null
```

### 6.3 Zakres testów SQL

- **Schema validation** — czy DDL zgadza się z deklaracją
- **Query execution** — uruchomienie, sprawdzenie wyników
- **Migration safety** — czy migracja zachowuje integralność (przed/po)
- **Dialect compatibility** — ten sam test na PG i SQLite (`sqlglot` transpile)

### 6.4 Zależności

- `sqlglot>=20.0` — parser i transpiler
- `sqlalchemy>=2.0` — już używane w semcod, więc spójne ze stackiem
- `psycopg[binary]` — runtime dla PG (opcjonalne, `extras_require=["sql"]`)

### 6.5 Kryteria sukcesu Fazy 2

- [ ] `testql run scenarios/sql/users-contract.sql.testql.yaml` przechodzi na PG i SQLite.
- [ ] Generator: `testql generate-sql --from postgres://... --table users` produkuje testowy scenariusz.
- [ ] CC nowych modułów < 8.
- [ ] Test coverage adaptera SQL ≥ 75%.

## 7. Faza 3 — Adaptery Proto i GraphQL

**Cel:** testować schematy Protocol Buffers (binary contracts) i GraphQL (queries/mutations).

**Czas:** 2 sesje. **Wersja docelowa:** `0.9.5-rc1`.

### 7.1 Adapter Proto

```text
testql/adapters/proto/
├── __init__.py
├── proto_adapter.py             # ProtoDSLAdapter
├── descriptor_loader.py         # parsowanie .proto → FileDescriptorSet
├── message_validator.py         # message round-trip, field validation
└── compatibility.py             # backward/forward compat między wersjami schematu

testql/interpreter/_proto.py     # Proto execution mixin
```

Format wejściowy `.proto.testql.yaml`:

```yaml
# SCENARIO: User proto contract
# TYPE: proto
# VERSION: 1.0

PROTO[1]{file}:
  schemas/user.proto

MESSAGE[2]{name, fields}:
  User, "id:int64=1, email:string=user@example.com, active:bool=true"
  Order, "id:int64=42, user_id:int64=1, total:double=99.99"

ASSERT[3]{name, check}:
  User, round_trip_equal
  User, all_required_present
  User_v1_compatible_with_v2, true
```

Zakres: round-trip serialization, required field check, cross-version compatibility, wire format integrity.

### 7.2 Adapter GraphQL

```text
testql/adapters/graphql/
├── __init__.py
├── graphql_adapter.py           # GraphQLDSLAdapter
├── schema_introspection.py
├── query_executor.py
└── subscription_runner.py       # WS-based subscriptions

testql/interpreter/_graphql.py   # GraphQL execution mixin (reuses existing _websockets.py)
```

Format wejściowy `.graphql.testql.yaml`:

```yaml
# SCENARIO: User GraphQL contract
# TYPE: graphql
# VERSION: 1.0

CONFIG[1]{key, value}:
  endpoint, http://localhost:8000/graphql

QUERY[1]{name, body, variables}:
  getUser, "query($id: ID!) { user(id: $id) { id email } }", "{id: '42'}"

ASSERT[2]{path, op, expected}:
  data.user.id, ==, 42
  data.user.email, contains, @
```

### 7.3 Kryteria sukcesu Fazy 3

- [ ] Round-trip Proto messages przechodzi dla 5+ przykładowych schematów.
- [ ] GraphQL queries + mutations + subscriptions wykonywane.
- [ ] Re-use istniejącego `GraphQLDetector` z `detectors/graphql_detector.py` (już mamy).
- [ ] Test coverage każdego adaptera ≥ 75%.

## 8. Faza 4 — Silnik generowania testów

**Cel:** dla dowolnego źródła (OpenAPI, schema SQL, plik proto, opis NL, ekran UI) wygenerować scenariusze TestQL — w dowolnym docelowym DSL.

**Czas:** 2–3 sesje. **Wersja docelowa:** `0.9.9-rc1`.

### 8.1 Refaktoryzacja istniejącego generatora

Aktualnie `generators/generators.py` (373 linie) generuje TestTOON. Trzeba rozbić:

```text
testql/generators/
├── __init__.py
├── base.py                      # BaseGenerator (ABC) — istniejący, rozszerzony
├── analyzers.py                 # bez zmian (analiza struktury projektu)
├── multi.py                     # bez zmian (multi-target orchestration)
│
├── sources/                     # NEW — generatory ze źródła
│   ├── __init__.py
│   ├── openapi_source.py        # OpenAPI → TestPlan IR
│   ├── sql_source.py            # SQL DDL → TestPlan IR (CRUD coverage)
│   ├── proto_source.py          # .proto → TestPlan IR (round-trip tests)
│   ├── graphql_source.py        # GraphQL schema → TestPlan IR
│   ├── nl_source.py             # NL spec → TestPlan IR (via NLAdapter.parse)
│   └── ui_source.py             # screenshot/HTML → TestPlan IR (via LLM)
│
├── targets/                     # NEW — render IR → DSL
│   ├── __init__.py
│   ├── testtoon_target.py       # IR → .testql.toon.yaml
│   ├── nl_target.py             # IR → .nl.md
│   └── pytest_target.py         # IR → pytest-friendly Python (bonus)
│
└── llm/                         # NEW — LLM-driven enrichment
    ├── __init__.py
    ├── edge_case_generator.py   # generowanie edge cases via LLM
    └── coverage_optimizer.py    # propozycje brakujących testów
```

### 8.2 Pipeline generowania

```text
source → SourceAnalyzer → TestPlan IR → TargetRenderer → output file
                                ▲
                                │
                          LLM enrichment (opt)
```

Każdy krok może być pominięty lub zastąpiony — pipeline jest pluginowy.

### 8.3 Nowe komendy CLI

```bash
testql generate --from openapi:./api.yaml --to testtoon --out scenarios/api/
testql generate --from sql:postgres://... --to nl --lang pl --out scenarios/nl/
testql generate --from proto:./schemas/ --to testtoon --out scenarios/proto/
testql generate --from nl:./specs/login.md --to testtoon --out scenarios/views/
testql generate --from ui:http://localhost:3000/login --to nl --lang pl --out scenarios/nl/
```

### 8.4 Kryteria sukcesu Fazy 4

- [ ] Istniejące `testql generate` działa bez zmian (backward compat).
- [ ] 6 nowych source × 3 target = 18 par działa, z testami E2E dla 6 reprezentatywnych.
- [ ] Fan-out `generate` ≤ 8 (z 19 — kluczowy wskaźnik).
- [ ] CC `generate` ≤ 6 (z aktualnego stanu).
- [ ] LLM enrichment opcjonalny i zawsze opcja `--no-llm`.

## 9. Faza 5 — Meta-testowanie (testy testów)

**Cel:** walidacja generowanych testów, mutation testing dla samego frameworka, "self-hosting" — TestQL testuje TestQL.

**Czas:** 1–2 sesje. **Wersja docelowa:** `1.0.0`.

### 9.1 Komponenty

```text
testql/meta/
├── __init__.py
├── mutator.py                   # mutuje TestPlan IR (zmienia operatory, wartości, kroki)
├── self_test.py                 # generuje testy dla testql.* z OpenAPI + SUMD
├── coverage_analyzer.py         # analiza pokrycia kontraktu (vs OpenAPI / DDL / proto)
└── confidence_scorer.py         # ocena pewności wygenerowanego testu (deterministic vs LLM)
```

### 9.2 Self-test pipeline

- `testql self-test` generuje scenariusze z `openapi.yaml` TestQL-a.
- Uruchamia je przeciwko własnemu API (FastAPI w `commands/encoder_routes.py`).
- Raportuje pokrycie kontraktu względem deklaracji OpenAPI.

### 9.3 Mutation testing

Dla każdego scenariusza:

- Zmień operator asercji (`==` → `!=`)
- Zmień oczekiwaną wartość statusu (`200` → `201`)
- Usuń wymagany krok

Jeśli zmutowany test **nadal przechodzi**, oryginalny test jest słaby (false-positive).

### 9.4 Kryteria sukcesu Fazy 5

- [ ] `testql self-test` raportuje ≥ 90% pokrycie endpointów `openapi.yaml`.
- [ ] Mutation testing pokazuje ≤ 10% scenariuszy "tolerujących mutacje" (mutants killed ratio ≥ 90%).
- [ ] Wszystkie kryteria z poprzednich faz zachowane.
- [ ] Release `1.0.0`: stabilne API, semver gwarancje.

## 10. Strategia migracji i kompatybilności wstecznej

### 10.1 Reguły niezłamywalne

- Każdy istniejący `*.testql.toon.yaml` musi działać w 1.0.0 bez zmian.
- Wszystkie publiczne importy z 0.6.23 muszą działać przez shimy w 1.0.0.
- `testql run`, `testql generate`, `testql echo` mają identyczne CLI dla starych use case'ów.
- `pyqual.yaml` gate'y nigdy nie obniżane — nowe testy podnoszą próg, nie obniżają.

### 10.2 Re-export shim wzorzec

Po przeniesieniu logiki:

```python
"""Backward-compat shim. Real implementation in testql.adapters.testtoon_adapter."""
from testql.adapters.testtoon_adapter import (
    parse_testtoon,
    Section,
    detect_separator,
    parse_value,
)

__all__ = ["parse_testtoon", "Section", "detect_separator", "parse_value"]
```

### 10.3 Deprecation policy

- Brak deprecation w 0.7.x – 0.9.x (wszystko działa równolegle).
- Deprecation warnings dopiero w 1.1.0+ jeśli zajdzie potrzeba.
- Usuwanie API tylko w 2.0.0.

## 11. Quality gates per fazę

| Faza | Wersja | coverage_min | vallm_pass_min | max_cc | max_fan_out | Krytyczne moduły |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `0.7.0-rc1` | 65 | 64 | 10 | 19 | + `ir/`, `adapters/base.py` |
| 1 | `0.8.0-rc1` | 68 | 66 | 9 | 17 | + `adapters/nl/` |
| 2 | `0.9.0-rc1` | 70 | 68 | 8 | 15 | + `adapters/sql/` |
| 3 | `0.9.5-rc1` | 72 | 70 | 8 | 13 | + `adapters/proto/`, `adapters/graphql/` |
| 4 | `0.9.9-rc1` | 75 | 72 | 7 | 10 | + `generators/sources/`, `generators/targets/` |
| 5 | `1.0.0` | 80 | 75 | 6 | 8 | + `meta/` |

**Zasada:** progi rosną. Jeśli faza nie spełni progu — pisze się testy, nie obniża się progu.

## 12. Toon analysis artifacts (per faza)

Dla każdej fazy generujemy zestaw artefaktów (Tom's standard pattern):

```text
project/phase-N/
├── map.toon.yaml              # struktura modułów, CC, fan-out
├── calls.toon.yaml            # graf wywołań
├── duplication.toon.yaml      # detekcja duplikacji (redup)
├── validation.toon.yaml       # walidacja semantyczna (vallm)
└── evolution.toon.yaml        # delta vs poprzednia faza
```

Każdy artefakt jest committowany razem z release tagiem (`v0.7.0-rc1`, etc.) — historia decyzji architektonicznych jako reproducible commit.

## 13. Ryzyka i ich mitygacja

| Ryzyko | Prawd. | Wpływ | Mitygacja |
| --- | --- | --- | --- |
| LLM fallback w NL adapter podnosi koszty | wysokie | śred. | Deterministyczna gramatyka jako default; LLM tylko opt-in (`--use-llm`); cost tracking via `costs` |
| IR za wąski (nie obejmie proto/SQL edge cases) | śred. | wysokie | Faza 0 prototypuje IR z 3 adapterami równolegle przed Phase 1 freeze |
| Backward compat ślepy zaułek | śred. | krytyczne | E2E test suite na repo-snapshot 0.6.23 — nie wolno go zepsuć |
| Generator + NL = nieskończona pętla (test generuje test który generuje test) | niskie | śred. | Hard limit `--max-depth=3` w generatorze |
| Wzrost zależności runtime (`sqlglot`, `protobuf`, `graphql-core`) | wysokie | śred. | Wszystko jako `extras_require`: `pip install testql[sql,proto,graphql]` |
| Multilingual NL leksykon trudno utrzymać | wysokie | niskie | Start tylko z PL i EN; DE/FR przez community contrib |

## 14. Sekwencja wykonania (concrete LLM tasks)

Lista zadań do wykonania (każde to ~1 sesja LLM):

**Faza 0:**

1. Stwórz `testql/ir/` z dataclassami i 100% testami.
2. Stwórz `testql/adapters/base.py` z `BaseDSLAdapter`.
3. Refaktoryzuj `_testtoon_parser.py` → `adapters/testtoon_adapter.py` + shim.
4. Rozbij `parse_testtoon` (CC=14) na 4 metody pomocnicze.
5. Wygeneruj toon artifacts, porównaj z baseline, podbij gate'y.

**Faza 1:**
6. Stwórz `adapters/nl/` z deterministyczną gramatyką + leksykonem PL.
7. Implementuj `intent_recognizer` + `entity_extractor`.
8. Dodaj `_execute_oql_line` reuse dla NL steps (kompatybilność z runner).
9. Stwórz 5 scenariuszy E2E `.nl.md`.
10. Toon artifacts + bump gate'ów.

**Faza 2:** ditto dla SQL.
**Faza 3:** ditto dla Proto + GraphQL.
**Faza 4:** rozbicie generatora, pluginowe sources/targets, CLI rozbudowa.
**Faza 5:** meta + self-test + mutation + 1.0.0.

## 15. Dlaczego ten plan jest LLM-friendly

- Każda faza ma **explicit success criteria** — LLM wie kiedy przestać.
- **Konkretne ścieżki plików** — żadnego "stwórz odpowiednią klasę".
- **Quality gates jako walidacja** — `pyqual run` mówi czy faza zakończona.
- **Re-export shimy zdefiniowane wprost** — LLM nie musi domyślać się polityki backward compat.
- **Toon artifacts jako diff** — porównanie przed/po jest deterministyczne.
- **Hierarchia zależności faz** — Faza N+1 nigdy nie wymaga zmian w fazie N-1.

## 16. Co dalej (poza 1.0.0)

Pomysły do rozważenia po 1.0.0 (nie część tego planu):

- Adapter dla **Cucumber/Gherkin** (BDD) — kolejny język NL z formalną gramatyką.
- Adapter dla **TLA+ / Alloy** — testowanie modeli formalnych.
- Adapter dla **OpenAPI 3.1 + JSON Schema** — pełna walidacja schematu.
- **Visual regression testing** — adapter dla porównań screenshotów (Playwright + pixelmatch).
- **Property-based testing** integracja z Hypothesis.
- **Distributed test runner** — `testql-cluster`, równoległe wykonanie scenariuszy.

---

Plan opracowany na bazie `SUMD.md` TestQL 0.6.23, `project/map.toon.yaml`, `project/calls.toon.yaml`. Zgodny z konwencjami ekosystemu Semcod (SUMD/DOQL/Taskfile/pyqual/vallm).
