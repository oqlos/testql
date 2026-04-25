# TestQL — Pluginy, integracje i formaty alternatywne

Ten dokument uzupełnia `DSL.md` i opisuje, jak nowy zunifikowany DSL `*.testql.yaml`
łączy się z istniejącymi adapterami, jak podpinać pluginy i jak używać DSL-a
w innych formatach niż YAML/TOON.

## 1. Co już mamy w kodzie

Repo ma już zalążek architektury wieloadapterowej:

- `testql.ir.TestPlan` — wspólne, neutralne IR (Unified IR).
- `testql.adapters.BaseDSLAdapter` — kontrakt adaptera (`detect/parse/render/validate`).
- `testql.adapters.AdapterRegistry` — rejestr adapterów (lookup po nazwie / rozszerzeniu / sniffingu treści).
- Wbudowane adaptery: `testtoon`, `nl`, `sql`, `proto`, `graphql`.
- `testql.ir_runner.IRRunner` + executor registry per `Step.kind`
  (`api`, `gui`, `shell`, `encoder`, `unit`, `nl`, `sql`, `proto`, `graphql`).

Refaktoryzacja w tej iteracji dokłada do tego:

- Adapter `scenario_yaml` dla nowego deklaratywnego DSL-a `*.testql.yaml`.
- Mechanizm pluginów w `AdapterRegistry`.
- Honorowanie konfiguracji planu (`targets.api.base_url`, ...) w `IRRunner`.
- Przykładowe scenariusze v2 w `examples/*/*.testql.yaml`.

## 2. Plugin contract

Plugin to dowolny moduł Pythona, który dostarcza adaptery DSL i/lub executorów IR.
Rejestracja odbywa się przez jeden z trzech mechanizmów:

1. **Funkcja hookowa** w module:

   ```python
   from testql.adapters import BaseDSLAdapter

   def register_testql_plugin(registry):
       registry.register(MyAdapter())
       # opcjonalnie:
       from testql.ir_runner.executors import register
       register("my-kind", my_executor)
   ```

2. **Atrybut `adapter` lub `adapters`** w module:

   ```python
   adapter = MyAdapter()        # albo
   adapters = [A1(), A2()]
   ```

3. **Bezpośrednia instancja `BaseDSLAdapter`** zwrócona przez entry point.

### Sposoby załadowania pluginu

- **Entry point** w `pyproject.toml` cudzego pakietu:

  ```toml
  [project.entry-points."testql.plugins"]
  my-plugin = "my_pkg.testql_plugin"
  ```

  Ładowanie odbywa się automatycznie przy pierwszym imporcie `testql.adapters`.

- **Zmienna środowiskowa**:

  ```bash
  export TESTQL_PLUGIN_MODULES="my_pkg.testql_plugin,other_pkg.adapters"
  ```

- **Programatycznie**:

  ```python
  from testql.adapters import registry
  registry.register_module("my_pkg.testql_plugin")
  registry.register_plugin(MyAdapter())
  ```

### Co może rozszerzyć plugin

- Nowy **format pliku** (JSON, TOML, HCL, własny tekst, ...) — implementuje
  `BaseDSLAdapter`, zwraca `TestPlan`.
- Nowy **typ kroku** (`Step.kind`) — rejestruje executor przez
  `testql.ir_runner.executors.register("kind", func)`.
- Nowe **asercje/operatory** — przez własne executory, używając
  `testql.ir_runner.assertion_eval` lub własnych funkcji.
- **Topology/discovery** — może być pluginem typu adapter rozumiejący
  np. format Markdown z osadzonymi blokami `testql:` albo OpenAPI.

## 3. Wpływ na sam język

Plugin model wymaga, żeby DSL pozostał **neutralny względem środowiska** —
inaczej każdy nowy plugin musiałby modyfikować rdzeń.

Stąd zasady, które trzymamy w DSL v2:

- Nazwy kroków są **czasownikami domenowymi** (`request`, `click`, `run`, `inspect`),
  nigdy `GUI_*` / `API_*`.
- `using:` deklaratywnie wybiera runtime/driver — plugin może dodać własne
  wartości (`using: my-driver`).
- `expect:` to mapa `field -> value` lub `field -> {operator: expected}`.
  Plugin może dodać własne operatory bez ruszania YAML.
- `targets:` to dowolna mapa konfiguracji środowisk; plugin po stronie
  executora może czytać własną sekcję (`targets.kafka.bootstrap`).
- `extra:` na `Step` przenosi pola, których core nie zna —
  plugin czyta je w swoim executorze.

Innymi słowy: DSL v2 jest **wystarczająco generyczny, żeby pluginy nic w nim
nie zmieniały** — tylko interpretowały dodatkowe pola.

## 4. Inne formaty zapisu (JSON, TOON, NL, SQL, ...)

DSL v2 ma jeden model (`TestPlan`) i wiele zapisów. Każdy zapis = jeden adapter:

| Format | Adapter | Status |
|---|---|---|
| `*.testql.yaml` (deklaratywny YAML) | `scenario_yaml` | **dodany w tej iteracji** |
| `*.testql.toon.yaml` (TOON) | `testtoon` | istnieje |
| `*.sql.testql.yaml` | `sql` | istnieje |
| `*.proto.testql.yaml` | `proto` | istnieje |
| `*.graphql.testql.yaml` | `graphql` | istnieje |
| Naturalny język (PL/EN) | `nl` | istnieje |
| `*.iql` (legacy imperative) | TODO: nowy adapter `iql` jako wrapper na obecny parser | **planowane** |
| `*.testql.json` | TODO: drobny adapter (json.loads + ten sam mapper co `scenario_yaml`) | **planowane** |
| `*.testql.toml` | TODO: opcjonalny plugin | **planowane** |
| Markdown z blokami ` ```testql ` | TODO: plugin (np. dla artykułów/dokumentacji) | **planowane** |

Praktyczne wnioski:

- Dla JSON wystarcza ~20 linii: `json.loads` + delegacja do
  `scenario_yaml._plan_from_yaml`.
- Dla TOML to samo z `tomllib`.
- Dla Markdown wystarczy wyciągnąć bloki kodu `testql` i przekazać do
  `scenario_yaml`.
- `*.iql` powinno żyć jako adapter używający istniejącego
  `testql.interpreter` — bez przepisywania logiki.

## 5. Plan wdrożenia

### Etap 1 — fundament (✅ ta iteracja)

- Adapter `scenario_yaml` + rejestracja.
- Plugin loader w `AdapterRegistry`.
- Przykładowe scenariusze `*.testql.yaml` w `examples/`.
- Testy jednostkowe adaptera i loadera pluginów.

### Etap 2 — pełna parytetowość formatów

- Adapter `iql` (wrapper na `testql.interpreter`) → `TestPlan`.
- Adaptery `scenario_json`, `scenario_toml` (delegacja do mappera YAML).
- `testql migrate <plik> --to testql.yaml` — konwerter w obie strony.
- Schemat JSON Schema dla `*.testql.yaml` + komenda `testql validate`.

### Etap 3 — pełna ekspresja DSL-a

- Kroki `inspect`, `discover`, `topology`, `compare`, `explain`,
  `refactor_plan` jako pełnoprawne `Step.kind` z executorami.
- Uniwersalne operatory `expect`: `length`, `exists`, `lt/gt/lte/gte`,
  `contains`, `matches`, `not`.
- `setup`/`cleanup` jako fazy egzekucji w `IRRunner`.

### Etap 4 — meta-platforma

- LLM generator generuje od razu `*.testql.yaml`, nie `*.iql`.
- MCP resources/tools używają tego samego DSL-a.
- Pluginy zewnętrzne (Kafka, gRPC, MQTT, ...) ładowane przez entry points.

## 6. Plan testowania

Każdy etap dostaje testy w `tests/`:

- `test_scenario_yaml_adapter.py` — parsowanie/render/round-trip
  kanonicznych scenariuszy (API/GUI/mixed/encoder/unit/shell). ✅
- `test_plugin_registry.py` — rejestracja przez instancję, listę,
  funkcję hookową, atrybut `adapter`/`adapters`, env var, idempotencja
  `ensure_plugins_loaded`. ✅
- `test_run_ir_cli.py` — integracja z `testql run-ir` (już istnieje;
  rozszerzane przy etapach 2–3).
- Smoke testy CLI po dodaniu `migrate`/`validate`.
- Testy round-trip między formatami: `yaml ⇄ toon ⇄ json`.

## 7. Jak korzystać już teraz

```bash
# Uruchomienie scenariusza w nowym formacie:
python -m testql run-ir examples/api-testing/health-check.testql.yaml --dry-run
python -m testql run-ir examples/shell-testing/basic-commands.testql.yaml
python -m testql run-ir examples/flow-control/mixed-smoke.testql.yaml --dry-run

# Załadowanie własnego pluginu:
TESTQL_PLUGIN_MODULES=my_pkg.testql_plugin python -m testql run-ir my-scenario.testql.yaml
```
