# TestQL - Visual Testing Framework dla C2004

Kompleksowy framework do testowania aplikacji C2004 z wizualizacją, analizą stron i raportowaniem.

## 🚀 Szybki Start

### Instalacja

```bash
cd ~/github/oqlos/testql

# Zainstaluj zależności (jeśli nie zainstalowane)
pip install playwright
python -m playwright install chromium
```

### Najprostsze Użycie

```bash
# Test wszystkich modułów
python testql_cli.py encoder

# Test jednej strony
python testql_cli.py analyze http://localhost:8100/connect-id

# Test wheel scroll
python testql_cli.py wheel
```

## 📋 Komendy CLI

### `encoder` - Test encoder mode

```bash
# Wszystkie moduły
python testql_cli.py encoder

# Wybrane moduły
python testql_cli.py encoder --modules connect-id connect-data

# Szybki test
python testql_cli.py encoder --fast --no-analysis

# Headless (CI/CD)
python testql_cli.py encoder --headless
```

### `analyze` - Analiza strony

```bash
# Analizuj stronę
python testql_cli.py analyze http://localhost:8100/connect-id

# Z encoder mode
python testql_cli.py analyze "http://localhost:8100/connect-data?mode=encoder"
```

### `wheel` - Test wheel scrolling

```bash
python testql_cli.py wheel
```

## 📊 Co Jest Testowane?

- ✅ **HTTP Status** (200/404/500)
- ✅ **DOM Structure** (elementy, przyciski, tabele)
- ✅ **Console Errors** (JavaScript errors)
- ✅ **Network Resources** (failed 404)
- ✅ **Performance** (load time, DOM ready)
- ✅ **Encoder Mode** (detection)
- ✅ **Screenshots** (full + viewport)

## 📝 Raporty

Każdy test generuje:

```
testql-reports/
├── testql_report.json    # JSON raport
├── testql_report.html    # HTML raport (otwórz w przeglądarce)
└── step_*.png            # Screenshots

testql-screenshots/
└── *.png                 # Screenshots z visual demo
```

Zobacz HTML:
```bash
firefox testql-reports/testql_report.html
```

## 🎯 Przykłady

### Pełny Test

```bash
cd ~/github/oqlos/testql
python testql_cli.py encoder
firefox testql-reports/testql_report.html
```

### Szybki Check

```bash
python testql_cli.py encoder --modules connect-id --fast
```

### Debug Strony

```bash
python testql_cli.py analyze http://localhost:8100/connect-data?mode=encoder
cat testql-reports/page_analysis.json | python -m json.tool
```

### CI/CD

```bash
python testql_cli.py encoder --headless --no-analysis
echo $?  # 0 = success
```

## 🔧 Wszystkie Opcje

```
--modules <list>     Test tylko wybrane moduły
--base-url <url>     Zmień base URL (default: localhost:8100)
--headless           Bez GUI
--no-analysis        Bez szczegółowej analizy (szybciej)
--fast               Fast mode (mniej delays)
--output <dir>       Katalog output (default: ./testql-reports)
```

## 📈 Interpretacja Wyników

### Console Output

```
[1/5] Testing connect-id...
================================================================================
📊 ANALYZING PAGE: http://localhost:8100/connect-id?mode=encoder
================================================================================
  ✅ HTTP 200 OK
  ✅ No console errors detected
  ✅ All resources loaded successfully
  ⏱️  Load time: 892ms
✅ connect-id: PASSED
```

### Summary

```
============================================================
SUMMARY
============================================================
✅ Passed:   5
❌ Failed:   0
⚠️  Warnings: 0
============================================================
```

### JSON Report

```json
{
  "summary": {
    "total_pages": 5,
    "total_errors": 0,
    "total_warnings": 0
  },
  "pages": [{
    "status": 200,
    "dom": {"total_elements": 456, "buttons": 70},
    "performance": {"load_time": 892},
    "errors": [],
    "warnings": []
  }]
}
```

## 🐛 Troubleshooting

**"Cannot connect to localhost:8100"**
```bash
# Sprawdź czy C2004 działa
curl http://localhost:8100

# Uruchom C2004
cd ~/github/maskservice/c2004
docker-compose up -d
```

**"ModuleNotFoundError: playwright"**
```bash
pip install playwright
python -m playwright install chromium
```

**"Permission denied"**
```bash
chmod 755 ~/github/oqlos/testql
mkdir -p testql-reports testql-screenshots
```

## 📁 Pliki

```
testql/
├── testql_cli.py              # CLI ⭐
├── testql/visual_demo.py      # Core
├── page_analyzer.py           # Analyzer
├── encoder_coverage_matrix.py # Matrix
└── README.md                  # Docs
```

## 🎨 Features

- **Visual Demo** - highlights, annotations, screenshots
- **Page Analysis** - HTTP, DOM, errors, performance
- **Coverage Matrix** - 9 modules × 10 shortcuts × 10 actions
- **Multiple Reports** - console, JSON, HTML
- **CLI Interface** - prosty i szybki
- **Playwright** - headless lub GUI

---

**TestQL - Visual Testing Made Simple** 🎉

Quick Start: `python testql_cli.py encoder`
