Rozumiem: chcesz propozycję uniwersalnego, prostego DSL-a na podstawie obecnych przykładów w `examples/*/*`, tak żeby dało się pisać scenariusze dla różnych środowisk. Najpierw przejrzę strukturę przykładów i aktualną składnię, a potem zaproponuję spójny model języka oraz przykłady migracji.

Widzę, że aktywne pliki są w [/home/tom/github/oqlos/testql/examples](cci:9://file:///home/tom/github/oqlos/testql/examples:0:0-0:0), a zarejestrowany workspace to [/home/tom/github/oqlos/sumd](cci:9://file:///home/tom/github/oqlos/sumd:0:0-0:0). Sprawdzę jeszcze bezpośrednio katalog `testql/examples`, żeby oprzeć propozycję na faktycznych przykładach, nie tylko na scenariuszach z `sumd`.


Mam listę plików przykładów. Teraz przeczytam reprezentatywne scenariusze `.oql`, `.testql.toon.yaml`, `README` i skrypty uruchomieniowe, żeby wyciągnąć wspólne operacje DSL-a.

Widać już główne problemy: dziś są trzy style (`.oql`, `.testql.toon.yaml`, `.tql`) i komendy są silnie prefiksowane typem środowiska (`GUI_*`, `API`, `SHELL`, `ENCODER_*`). Doczytam jeszcze przykłady TestTOON, topologii i discovery, żeby propozycja objęła też introspekcję/projekt.

Na podstawie przykładów mam już obraz składni i środowisk. Zapiszę krótki kontekst projektu, żeby kolejne rozmowy mogły kontynuować ten kierunek spójnie.
# Propozycja: jeden DSL `TestQL Scenario`

Na podstawie `examples/*/*` proponuję odejść od rozdziału:

- `.oql` dla imperatywnych komend
- `.testql.toon.yaml` dla tabel API
- `.tql` jako legacy
- komend typu `GUI_*`, `ENCODER_*`, `SHELL`, `UNIT_*`

i wprowadzić **jeden semantyczny DSL scenariuszy**, który opisuje:

- **co testujemy**
- **w jakim środowisku**
- **jakie akcje wykonujemy**
- **co asercyjnie sprawdzamy**
- **co przechwytujemy**
- **jakie artefakty/topologię odkrywamy**

Format powinien być łatwy dla człowieka, ale też bardzo łatwy do parsowania przez LLM, parser i runner.

---

# Główna idea

## Zamiast obecnie

```oql
GUI_START "${base_url}/login"
GUI_INPUT "#username" "${username}"
GUI_INPUT "#password" "${password}"
GUI_CLICK "button[type='submit']"
GUI_ASSERT_VISIBLE "[data-testid='dashboard']"
GUI_STOP
```

albo:

```yaml
API[3]{method, endpoint, expected_status}:
  GET, ${base_url}/api/health, 200
  GET, ${base_url}/api/v3/data/devices, 200
  GET, ${base_url}/api/v3/scenarios, 200
```

proponuję jeden model:

```yaml
scenario: Login Form Test
type: gui

vars:
  base_url: https://example.com
  username: testuser
  password: testpass123

steps:
  - open: ${base_url}/login
  - input: "#username"
    value: ${username}
  - input: "#password"
    value: ${password}
  - click: "button[type='submit']"
  - expect:
      visible: "[data-testid='dashboard']"
  - expect:
      text:
        selector: h1
        equals: "Welcome, ${username}"
```

Czyli komendy są **czasownikami domenowymi**, a środowisko wynika z `type`, `target` albo `driver`.

---

# Proponowana struktura DSL

```yaml
scenario: Human readable name
type: api | gui | shell | unit | encoder | topology | discovery | mixed
version: 2

vars:
  key: value

targets:
  api:
    base_url: http://localhost:8101
    timeout_ms: 5000

  browser:
    engine: chromium
    headless: true

  shell:
    cwd: .
    timeout_ms: 10000

setup:
  - log: Preparing scenario

steps:
  - action...

cleanup:
  - action...

artifacts:
  save:
    - result.json
    - topology.yaml
```

---

# Najważniejsze zasady języka

## 1. Jeden wspólny model akcji

Każdy krok to:

```yaml
- <verb>: <main argument>
  option: value
```

Przykłady:

```yaml
- log: Starting test
- wait: 500ms
- run: echo Hello
- request:
    method: GET
    url: ${api.base_url}/health
- click: "#submit"
- input: "#username"
  value: tom
- expect:
    status: 200
- capture:
    scenario_id: response.data.id
```

---

## 2. Środowisko jest kontekstem, nie prefiksem komendy

Zamiast:

```oql
GUI_CLICK
ENCODER_CLICK
SHELL
UNIT_ASSERT
API GET
```

proponuję:

```yaml
- click: "#submit"
  using: browser

- click: confirm
  using: encoder

- run: ls -la
  using: shell

- eval: "math.sqrt(16)"
  using: python
```

Albo krócej, gdy `type` wskazuje domyślny driver.

---

## 3. `expect` jako uniwersalna asercja

Zamiast wielu osobnych:

```oql
ASSERT_STATUS 200
ASSERT_EXIT_CODE 0
GUI_ASSERT_VISIBLE "#x"
UNIT_ASSERT "x == y"
```

jeden blok:

```yaml
- expect:
    status: 200

- expect:
    exit_code: 0

- expect:
    visible: "#dashboard"

- expect:
    expression: "math.sqrt(16) == 4"

- expect:
    json:
      path: data.id
      not: null

- expect:
    response_time:
      lt: 1000ms
```

---

# Przykłady migracji

## API health-check

Obecnie:

```yaml
CONFIG[2]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 5000

API[3]{method, endpoint, expected_status}:
  GET, ${base_url}/api/health, 200
  GET, ${base_url}/api/v3/data/devices, 200
  GET, ${base_url}/api/v3/scenarios, 200

ASSERT[3]{field, operator, expected}:
  status, <, 500
  content_type, contains, application/json
  response_time, <, 1000
```

Proponowane:

```yaml
scenario: API Health Check
type: api
version: 2

targets:
  api:
    base_url: http://localhost:8101
    timeout_ms: 5000

steps:
  - request: GET /api/health
    expect:
      status: 200

  - request: GET /api/v3/data/devices
    expect:
      status: 200

  - request: GET /api/v3/scenarios
    expect:
      status: 200

  - expect:
      status:
        lt: 500
      content_type:
        contains: application/json
      response_time:
        lt: 1000ms
```

---

## CRUD workflow

Proponowane:

```yaml
scenario: CRUD Workflow Test
type: api
version: 2

targets:
  api:
    base_url: http://localhost:8101

steps:
  - request:
      method: POST
      path: /api/v3/scenarios
    expect:
      status: 201
      json:
        data.id:
          exists: true
    capture:
      scenario_id: response.data.id

  - request: GET /api/v3/scenarios/${scenario_id}
    expect:
      status: 200
      json:
        data.id:
          equals: ${scenario_id}

  - request: PUT /api/v3/scenarios/${scenario_id}
    expect:
      status: 200

  - request: DELETE /api/v3/scenarios/${scenario_id}
    expect:
      status: 204
```

---

## GUI login

Proponowane:

```yaml
scenario: Login Form Test
type: gui
version: 2

targets:
  browser:
    base_url: https://example.com
    engine: chromium
    headless: true

vars:
  username: testuser
  password: testpass123

steps:
  - open: /login

  - input: "#username"
    value: ${username}

  - input: "#password"
    value: ${password}

  - click: "button[type='submit']"

  - expect:
      visible: "[data-testid='dashboard']"

  - expect:
      text:
        selector: h1
        equals: "Welcome, ${username}"
```

---

## Shell

Obecnie:

```oql
SHELL "echo Hello TestQL"
ASSERT_EXIT_CODE 0
```

Proponowane:

```yaml
scenario: Basic Shell Commands Test
type: shell
version: 2

steps:
  - run: echo Hello TestQL
    expect:
      exit_code: 0
      stdout:
        contains: Hello TestQL

  - run: ls -la
    expect:
      exit_code: 0
```

---

## Unit testing

Obecnie:

```oql
UNIT_IMPORT "math"
UNIT_ASSERT "math.sqrt(16) == 4"
```

Proponowane:

```yaml
scenario: Unit Testing — Math Module
type: unit
version: 2

targets:
  runtime:
    language: python

steps:
  - import: math

  - expect:
      expression: "math.sqrt(16) == 4"

  - expect:
      expression: "'hello'.upper() == 'HELLO'"

  - expect:
      expression: "[x*2 for x in [1,2,3]] == [2,4,6]"
```

---

## Encoder

Obecnie:

```oql
ENCODER_ON
ENCODER_STATUS
ENCODER_FOCUS column1
ENCODER_SCROLL 3
ENCODER_CLICK
ENCODER_OFF
```

Proponowane:

```yaml
scenario: Basic Encoder Lifecycle
type: encoder
version: 2

steps:
  - power: on

  - status: encoder

  - focus: column1

  - scroll: 3

  - click: confirm

  - power: off
```

Albo bardziej jawnie:

```yaml
steps:
  - encoder:
      power: on

  - encoder:
      status: true

  - encoder:
      focus: column1

  - encoder:
      scroll: 3

  - encoder:
      click: true

  - encoder:
      power: off
```

---

# Ważna część: scenariusze mieszane

Największa wartość nowego DSL-a to nie tylko API albo GUI, ale **pełne scenariusze cross-environment**:

```yaml
scenario: Full App Smoke
type: mixed
version: 2

targets:
  api:
    base_url: http://localhost:8101

  browser:
    base_url: http://localhost:8101
    headless: true

  shell:
    cwd: .

steps:
  - run: python mock_server.py
    background: true
    capture:
      server_pid: process.pid

  - request: GET /api/health
    using: api
    expect:
      status: 200

  - open: /
    using: browser

  - expect:
      visible: body

  - inspect:
      url: ${browser.base_url}
      scan_network: true
      browser: true
    capture:
      topology: result.topology

cleanup:
  - kill: ${server_pid}
```

To jest kierunek, który moim zdaniem najlepiej pasuje do TestQL: **jeden scenariusz może przechodzić przez shell, API, GUI, discovery, topology i artifacts**.

---

# Topology/discovery jako first-class DSL

Z przykładów [discovery](cci:9://file:///home/tom/github/oqlos/testql/examples/discovery:0:0-0:0), [topology](cci:9://file:///home/tom/github/oqlos/testql/examples/topology:0:0-0:0), [web-inspection](cci:9://file:///home/tom/github/oqlos/testql/examples/web-inspection:0:0-0:0), [browser-inspection](cci:9://file:///home/tom/github/oqlos/testql/examples/browser-inspection:0:0-0:0) wynika, że to powinno być częścią DSL-a, nie tylko osobną komendą CLI.

Proponuję:

```yaml
scenario: Inspect Production Website
type: topology
version: 2

targets:
  web:
    url: https://tom.sapletta.com

steps:
  - discover:
      target: ${web.url}

  - inspect:
      target: ${web.url}
      scan_network: true
      browser: true

  - expect:
      page.status: 200
      browser.console_errors:
        length: 0
      assets.failed:
        equals: 0

  - topology:
      build: true
      format: toon.yaml
      save: .testql/topology.toon.yaml
```

---

# Moja rekomendacja nazwy i formatów

## Format główny

Proponuję wprowadzić:

```text
*.testql.yaml
```

jako **główny format v2**.

## Pozostawić kompatybilność

- **`.oql`** jako legacy imperative
- **`.testql.toon.yaml`** jako format tabelaryczny/kompaktowy
- **`.tql`** jako deprecated legacy

## Docelowo

```text
scenario.testql.yaml       # podstawowy format dla ludzi
scenario.testql.toon.yaml  # format zwarty/AI-friendly/tabelaryczny
scenario.oql               # legacy
```

---

# Minimalna składnia DSL-a v2

Najmniejszy poprawny scenariusz:

```yaml
scenario: Smoke Test
type: api

steps:
  - request: GET http://localhost:8101/api/health
    expect:
      status: 200
```

To powinno być główne kryterium: **nowy użytkownik ma rozumieć scenariusz bez czytania dokumentacji**.

---

# Wewnętrzny model AST

Niezależnie od formatu pliku parser powinien sprowadzać wszystko do jednego modelu:

```yaml
Scenario:
  metadata
  vars
  targets
  setup
  steps
  cleanup
  artifacts

Step:
  id
  kind
  using
  action
  input
  expect
  capture
  retry
  timeout
  continue_on_error
```

Dzięki temu można potem kompilować:

```text
.oql                -> Scenario AST
.testql.toon.yaml   -> Scenario AST
.testql.yaml        -> Scenario AST
LLM-generated text  -> Scenario AST
```

Runner nie powinien znać składni źródłowej. Runner powinien wykonywać tylko AST.

---

# Proponowany zestaw czasowników DSL

## Core

- **`log`** — wypisz komunikat
- **`set`** — ustaw zmienną
- **`wait`** — poczekaj
- **`expect`** — asercja
- **`capture`** — zapisz wartość do zmiennej
- **`retry`** — ponów krok
- **`include`** — dołącz inny scenariusz

## API

- **`request`** — HTTP request
- **`graphql`** — GraphQL request
- **`ws`** — WebSocket event/send/expect

## GUI/browser

- **`open`** — otwórz URL
- **`click`** — kliknij
- **`input`** — wpisz tekst
- **`select`** — wybierz opcję
- **`screenshot`** — zapisz screenshot
- **`inspect`** — zbierz DOM/network/console

## Shell/system

- **`run`** — uruchom komendę
- **`spawn`** — proces w tle
- **`kill`** — zakończ proces
- **`file`** — operacje na plikach

## Unit/runtime

- **`import`** — import modułu
- **`eval`** — wykonaj wyrażenie
- **`call`** — wywołaj funkcję

## Topology/discovery

- **`discover`** — znajdź artefakty
- **[topology](cci:9://file:///home/tom/github/oqlos/testql/examples/topology:0:0-0:0)** — zbuduj graf
- **`compare`** — porównaj static/runtime
- **`explain`** — wygeneruj opis NLP
- **`refactor_plan`** — wygeneruj plan zmian

## Hardware/encoder

- **`encoder`** — jawny blok urządzenia
- **`focus`**
- **`scroll`**
- **`power`**
- **`status`**

---

# Najważniejsza decyzja składniowa

Proponuję **nie mnożyć komend typu `GUI_*`, `API_*`, `ENCODER_*`**.

Lepszy kierunek:

```yaml
- click: "#submit"
  using: browser
```

niż:

```yaml
- GUI_CLICK: "#submit"
```

Dlaczego?

- **Czytelniejsze dla nowych użytkowników**
- **Łatwiejsze dla LLM**
- **Łatwiejsze do mapowania na różne runtime**
- **Mniej specjalnych komend**
- **Pozwala robić scenariusze mieszane**

---

# Wersja TOON tego samego modelu

Dla AI-friendly/tabular można zachować TOON, ale jako reprezentację tego samego AST:

```yaml
# SCENARIO: API Health Check
# TYPE: api
# VERSION: 2

TARGET[1]{name, kind, base_url}:
  api, http, http://localhost:8101

STEP[3]{id, using, action, input, expect}:
  health, api, request, GET /api/health, status == 200
  devices, api, request, GET /api/v3/data/devices, status == 200
  scenarios, api, request, GET /api/v3/scenarios, status == 200
```

Czyli TOON zostaje, ale nie jako osobny język — tylko jako **kompaktowy zapis tego samego DSL-a**.

---

# Proponowana ścieżka wdrożenia

## Etap 1

Dodać parser `*.testql.yaml` v2 i mapowanie do obecnego runnera.

## Etap 2

Zrobić migrator:

```bash
testql migrate examples/gui-testing/login-form.oql --to testql.yaml
testql migrate examples/api-testing/health-check.testql.toon.yaml --to testql.yaml
```

## Etap 3

Dodać walidację schematem JSON Schema:

```bash
testql validate scenario.testql.yaml
```

## Etap 4

Runner wykonuje już tylko wspólny AST.

## Etap 5

LLM generator generuje DSL v2, nie legacy `.oql`.

---

# Moja finalna rekomendacja

Najlepszy kierunek to:

```text
TestQL v2 = declarative scenario YAML + wspólny AST + opcjonalny TOON jako format kompaktowy
```

Czyli:

- **`*.testql.yaml`** jako podstawowy format
- **`steps`** jako uniwersalna lista akcji
- **`expect`** jako wspólna asercja
- **`targets`** jako opis środowisk
- **`using`** jako wybór runtime/drivera
- **`discover` / `inspect` / [topology](cci:9://file:///home/tom/github/oqlos/testql/examples/topology:0:0-0:0)** jako normalne akcje DSL-a
- **legacy `.oql` i `.testql.toon.yaml`** konwertowane do tego samego AST

Status: przeanalizowałem reprezentatywne przykłady z `examples/*/*` i proponuję DSL v2 oparty o jeden model scenariusza, zamiast kilku równoległych składni.



Sprawdzę renderer/parser TOON pod kątem brakujących sekcji (`SHELL`, `UNIT`, `LOG`), bo obecny [TestToonAdapter](cci:2://file:///home/tom/github/oqlos/testql/testql/adapters/testtoon_adapter.py:288:0-320:33) nie renderuje shell/unit/log — bez tego konwersja nowych przykładów `*.testql.yaml → *.testql.toon.yaml` byłaby niekompletna.



Rozszerzę [TestToonAdapter](cci:2://file:///home/tom/github/oqlos/testql/testql/adapters/testtoon_adapter.py:288:0-320:33) o sekcje `SHELL`, `UNIT`, `LOG` w obu kierunkach (parse + render), żeby konwersja `*.testql.yaml → *.testql.toon.yaml` była pełna dla wszystkich 6 nowych przykładów.


Teraz dodam rendery dla `SHELL`, `UNIT`, `LOG` i wpinam je w [_render_plan](cci:1://file:///home/tom/github/oqlos/testql/testql/adapters/testtoon_adapter.py:263:0-283:53).


Dodam też sekcję `GUI[N]{action, selector, value, wait_ms}` dla nie-navigate akcji (click/input/assert_visible/assert_text), żeby login-form mógł zrobić round-trip.


Teraz dodam `_render_gui_actions_steps` i wpięcie. Filtr: `GuiStep`, których action != "navigate".


Teraz uruchomię testy adaptera, żeby upewnić się, że nic się nie zepsuło, i przeprowadzę konwersję `*.testql.yaml → *.testql.toon.yaml` dla wszystkich nowych przykładów.