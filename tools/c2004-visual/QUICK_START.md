# TestQL - Quick Start Guide

## 🚀 Najprostsze Użycie (3 komendy!)

### 1. Test Encoder Mode

```bash
cd ~/github/oqlos/testql
./testql encoder
```

To jest TO! Jedna komenda testuje wszystkie moduły C2004.

### 2. Analizuj Stronę

```bash
./testql analyze http://localhost:8100/connect-id
```

Szczegółowa analiza jednej strony (HTTP, DOM, errors, performance).

### 3. Test Wheel Scroll

```bash
./testql wheel
```

Test scrollowania encoder wheel.

---

## 📊 Przykładowy Output

```
🚀 Starting TestQL Encoder Test
   Base URL: http://localhost:8100
   Modules: 5
   Analysis: ON

[1/5] Testing connect-id...
================================================================================
📊 ANALYZING PAGE: http://localhost:8100/connect-id?mode=encoder
================================================================================
  ✅ HTTP 200 OK
  • Total elements: 456
  • Buttons: 70
  • Load time: 892ms
✅ connect-id: PASSED

[2/5] Testing connect-data...
✅ connect-data: PASSED

[3/5] Testing connect-reports...
✅ connect-reports: PASSED

[4/5] Testing connect-manager...
✅ connect-manager: PASSED

[5/5] Testing connect-config...
✅ connect-config: PASSED

============================================================
SUMMARY
============================================================
✅ Passed:   5
❌ Failed:   0
⚠️  Warnings: 0
============================================================
```

---

## 📝 Zobacz Raporty

```bash
# HTML raport (wizualny)
firefox testql-reports/testql_report.html

# JSON raport (dla automation)
cat testql-reports/testql_report.json | python -m json.tool

# Screenshots
ls testql-screenshots/
```

---

## ⚡ Szybkie Warianty

### Szybki test (bez analizy)

```bash
./testql encoder --fast --no-analysis
```

Czas: ~10s zamiast ~60s

### Test tylko wybranych modułów

```bash
./testql encoder --modules connect-id connect-data
```

### Headless (dla CI/CD)

```bash
./testql encoder --headless
```

---

## 🎯 Use Cases

**Daily Check:**
```bash
./testql encoder --fast
```

**Debug Problem:**
```bash
./testql analyze http://localhost:8100/problematic-page
```

**Pre-Deployment:**
```bash
./testql encoder --headless
echo $?  # Check exit code
```

**Full Regression:**
```bash
./testql encoder  # Wszystkie moduły z analizą
```

---

## 🔧 Opcje

```
encoder              Test encoder mode (wszystkie lub wybrane moduły)
analyze <url>        Analizuj pojedynczą stronę
wheel                Test wheel scrolling

--modules <list>     Test tylko wybrane moduły
--fast               Szybki tryb (mniej delays)
--no-analysis        Bez szczegółowej analizy (szybciej)
--headless           Bez GUI (dla CI/CD)
--base-url <url>     Zmień base URL
```

---

## 📋 Checklist Przed Testem

1. ✅ C2004 działa: `curl http://localhost:8100`
2. ✅ Playwright zainstalowany: `python -m playwright --version`
3. ✅ W katalogu testql: `cd ~/github/oqlos/testql`

Gotowe? Uruchom:

```bash
./testql encoder
```

**To wszystko!** 🎉

---

Pełna dokumentacja: [README.md](README.md)
