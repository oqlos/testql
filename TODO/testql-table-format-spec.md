---
title: "TestTOON — Tabelaryczny Format Testów Inspirowany TOON"
slug: testtoon-format-spec
category: OQLos / DSL / Format Design
tags: TestQL, TOON, table-format, DSL, testing
status: publish
---

# TestTOON — Tabelaryczny Format Testów Inspirowany TOON

## Idea

TOON (używany przez `code2llm`) definiuje sekcje jako nagłówki z listą kolumn
w klamrach, a dane leci poniżej linia po linii:

```
WARNINGS[7]{path,score}:
  oqlos/hardware.py, 0.97
  oqlos/interpreter.py, 0.98
```

Ten sam wzorzec przeniesiony na testy daje **TestTOON** — format gdzie każda
sekcja deklaruje swój schemat, a dane poniżej są czytelne jak CSV bez nagłówków
w każdym wierszu.

---

## Składnia

### Nagłówek sekcji

```
SEKCJA[liczba_wierszy]{col1, col2, col3}:
```

- `SEKCJA` — typ kroków (NAVIGATE, API, ASSERT, SELECT, STEPS, ...)
- `[liczba]` — opcjonalny licznik (jak w TOON), pomaga walidacji
- `{col1, col2}` — kolejność kolumn dla wierszy poniżej
- `:` — koniec nagłówka

### Wiersze danych

```
  wartość1, wartość2, wartość3
```

- Wcięcie 2 spacje (jak w TOON)
- Separator: `,` (lub `|` dla czytelności z długimi stringami)
- Wartości ze spacjami: `"quoted string"`
- Brak wartości: `-`
- JSON inline: `{key:value}` bez cudzysłowów w kluczach

### Nagłówek pliku

```
# SCENARIO: Nazwa Scenariusza
# TYPE: e2e | api | gui | interaction
# VERSION: 1.0
# AUTHOR: ops@softreck.dev
# BASE_URL: http://localhost:8000
```

### Komentarze

```
# komentarz jednoliniowy
```

---

## Kompletny przykład: PSS 7000 Full Flow

```testtoon
# SCENARIO: PSS 7000 — Pełny Test
# TYPE: e2e
# VERSION: 1.0
# BASE_URL: http://localhost:8000

# ── Konfiguracja ──────────────────────────────────
CONFIG{key, value}:
  auth,        jwt
  timeout_ms,  30000
  device_model, PSS 7000

# ── Nawigacja ─────────────────────────────────────
NAVIGATE[3]{path, wait_ms}:
  /connect-test/testing,     500
  /connect-id/device-rfid,   300
  /connect-reports,          200

# ── Wybory UI ────────────────────────────────────
SELECT[2]{action, id, meta}:
  device,   d-001,  {type:PSS_7000, serial:PS12345}
  interval, 12m,    {code:periodic_12m}

# ── Wywołania API ─────────────────────────────────
API[4]{method, endpoint, expect_status}:
  GET,  /api/v3/health,              200
  GET,  /api/v3/devices/d-001,       200
  GET,  /api/v3/scenarios,           200
  POST, /api/v3/devices/d-001/start, 201

# ── Kroki testu ───────────────────────────────────
STEPS[5]{name, status, value}:
  Oględziny wizualne,    passed, -
  Test szczelności,      passed, -10.5 mbar
  Ciśnienie otwarcia,    passed, 145 bar
  Test funkcjonalny,     passed, -
  Weryfikacja końcowa,   passed, -

# ── Asercje końcowe ───────────────────────────────
ASSERT[4]{field, op, expected}:
  status,          ==, executed
  summary.passed,  ==, 5
  summary.failed,  ==, 0
  device.status,   ==, ready
```

---

## Elastyczność: różne typy testów w jednym pliku

Sekcje można dowolnie komponować. Plik może być czystym API testem:

```testtoon
# SCENARIO: Backend Smoke Test
# TYPE: api

API[10]{method, endpoint, status, assert_key, assert_val}:
  GET,  /api/v3/health,              200, status,    ok
  GET,  /api/v3/devices,             200, data.count, -
  GET,  /api/v3/scenarios,           200, -,          -
  GET,  /api/v3/dsl/functions,       200, -,          -
  GET,  /api/v3/dsl/units,           200, -,          -
  GET,  /api/v3/config/system,       200, -,          -
  GET,  /api/v3/schema/devices,      200, -,          -
  GET,  /api/v3/schema/customers,    200, -,          -
  GET,  /api/v3/data/protocols,      200, -,          -
  GET,  /api/v3/auth/session,        401, error,      Unauthorized
```

Lub czystym testem UI z encoderem:

```testtoon
# SCENARIO: Encoder Navigation
# TYPE: gui

NAVIGATE[1]{path, wait_ms}:
  /connect-workshop/requests-search, 500

ENCODER[4]{action, target, value}:
  on,      -,    -
  focus,   col3, -
  scroll,  -,    [1,1]
  click,   -,    -

ASSERT[2]{selector, property, expected}:
  .top-bar,         visible, true
  .two-pane-layout, visible, true
```

Lub sekwencją nagrania sesji:

```testtoon
# SCENARIO: Operator Daily Flow
# TYPE: interaction

RECORD_START{session_id}:
  session-pss7000-$(DATE)

NAVIGATE[2]{path, wait_ms}:
  /connect-id,    400
  /connect-test,  300

SELECT[1]{action, id, meta}:
  device, d-001, {type:PSS_7000}

STEPS[3]{name, status}:
  Inspekcja,  passed
  Ciśnienie,  passed
  Finalizacja, passed

RECORD_STOP{}:
```

---

## Reguły parsera

### Schemat parsowania (pseudokod)

```
dla każdej linii w pliku:
  jeśli linia pasuje do /^# (.+)/  → komentarz/metadane nagłówka
  jeśli linia pasuje do /^([A-Z_]+)(\[\d+\])?\{([^}]*)\}:/  →
    nowa_sekcja = { typ, liczba, kolumny: split(",") }
  jeśli linia zaczyna się od "  " (2 spacje) i jest aktywna sekcja →
    wiersz = { kolumna[0]: wartość[0], kolumna[1]: wartość[1], ... }
    dodaj do aktywna_sekcja.wiersze
```

### Parser Python (35 linii)

```python
import re
from dataclasses import dataclass, field
from typing import Optional

HEADER_RE = re.compile(r'^([A-Z_]+)(?:\[(\d+)\])?\{([^}]*)\}:\s*$')
META_RE   = re.compile(r'^#\s*([A-Z_]+):\s*(.+)$')

@dataclass
class Section:
    type: str
    columns: list[str]
    rows: list[dict] = field(default_factory=list)
    expected_count: Optional[int] = None

def parse_testtoon(text: str) -> dict:
    meta, sections, current = {}, [], None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        m = META_RE.match(line)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
            continue

        if line.startswith('#'):
            continue

        m = HEADER_RE.match(line)
        if m:
            cols = [c.strip() for c in m.group(3).split(',') if c.strip()]
            current = Section(
                type=m.group(1),
                columns=cols,
                expected_count=int(m.group(2)) if m.group(2) else None
            )
            sections.append(current)
            continue

        if current and raw.startswith('  '):
            values = [v.strip() for v in line.split(',', len(current.columns)-1)]
            row = dict(zip(current.columns, values))
            current.rows.append(row)

    return {'meta': meta, 'sections': sections}


# Użycie
result = parse_testtoon(open('pss7000-flow.testtoon').read())
for section in result['sections']:
    print(f"{section.type}: {len(section.rows)} rows")
    for row in section.rows:
        print(f"  {row}")
```

### Walidacja licznika

```python
def validate(parsed: dict) -> list[str]:
    errors = []
    for s in parsed['sections']:
        if s.expected_count and len(s.rows) != s.expected_count:
            errors.append(
                f"{s.type}[{s.expected_count}] — "
                f"znaleziono {len(s.rows)} wierszy"
            )
    return errors
```

---

## Konfiguracja edytorów

Format jest syntaktycznie podzbiorem YAML (wcięcia + nagłówki) ale bez
standardowego YAML parsowania. Dla highlightingu:

```
*.testtoon  linguist-language=YAML
```

**VS Code** — `settings.json`:
```json
"files.associations": {
  "*.testtoon": "yaml"
}
```

YAML highlighting podświetli:
- `# komentarze` → szare
- `{col1, col2}` → jako YAML flow mapping (żółte/pomarańczowe)
- `wartość1, wartość2` → białe (plain text)
- Nagłówki sekcji `NAVIGATE[3]{...}:` → jako YAML keys (niebieskie)

Wystarczająco czytelne bez dedykowanego rozszerzenia.

---

## Porównanie z innymi formatami

| Cecha | TestTOON | TOML | YAML | Robot FW |
|-------|:--------:|:----:|:----:|:--------:|
| Schemat kolumn per sekcja | ✅ | ❌ | ❌ | ❌ |
| Kompaktowe wiersze danych | ✅ | ❌ | ❌ | ✅ |
| Validacja licznika wierszy | ✅ | ❌ | ❌ | ❌ |
| Mieszanie typów kroków | ✅ | ✅ | ✅ | ✅ |
| Parser < 40 linii Python | ✅ | ❌ | ❌ | ❌ |
| Czytelność bez edytora | ✅ | ✅ | ✅ | ⚠️ |
| Natywne tablice | ✅ `[1,1]` | ✅ | ✅ | ❌ |
| JSON inline | ✅ `{k:v}` | ❌ | ✅ | ❌ |

---

## Ewolucja: TestTOON → TestTOON Pipe

Gdy wartości mają przecinki (np. URL z query stringiem), zamień separator na `|`:

```testtoon
# Wariant z separatorem pipe (dla wartości z przecinkami)
API[3]{method | endpoint | status | body}:
  GET  | /api/v3/devices?limit=5&page=1 | 200 | -
  POST | /api/v3/devices                | 201 | {model:PSS_7000,serial:PS12345}
  GET  | /api/v3/auth/session           | 401 | -
```

Detekcja separatora: parser sprawdza pierwszy wiersz danych — jeśli zawiera `|`,
używa `|` zamiast `,` dla całej sekcji.

---

## Zgodność z ekosystemem OQLos

TestTOON uzupełnia istniejące formaty, nie zastępuje:

```
*.oql       — sterowanie sprzętem (SET, WAIT, MIN, MAX)
*.doql.css  — definicja aplikacji (entity, interface, role)
*.testtoon  — testy tabelaryczne (NAVIGATE, API, ASSERT, STEPS)
*.testql.toon.yaml  — nagrania sesji (RECORD_START, NAVIGATE, SELECT_DEVICE)
```

Plik `.testtoon` może importować scenariusze OQL:

```testtoon
# SCENARIO: E2E z hardware
# TYPE: e2e

OQL[1]{file, device, mode}:
  scenarios/pss7000-full-test.oql, d-001, execute

API[1]{method, endpoint, status}:
  GET, /api/v3/devices/d-001/last-inspection, 200

ASSERT[2]{field, op, expected}:
  result,         ==, passed
  leakage_mbar,   <=, 0.05
```
