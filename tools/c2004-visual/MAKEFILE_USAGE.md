# TestQL Makefile Usage

## 🚀 Quick Start

TestQL ma wbudowane komendy make dla łatwego uruchamiania testów.

### Podstawowe Komendy

```bash
cd ~/github/oqlos/testql

# Pokaż dostępne komendy
make help

# Uruchom encoder test (szybki, 9 modułów)
make testql-encoder

# Uruchom complete menu test (69 kombinacji)
make testql-menu

# Uruchom parallel test (najszybszy)
make testql-parallel

# Uruchom visual test (widoczne okno)
make testql-visual

# Uruchom wszystkie testy
make testql-all

# Zobacz wyniki
make testql-results
```

## 📊 Szczegóły Komend

### `make testql-encoder`

**Co robi:**
- Testuje 9 podstawowych modułów
- Używa parallel testing (5 concurrent)
- Headless mode (szybkie)
- Czas: ~13 sekund

**Wynik:**
- `parallel_test_results.json`

**Przykład:**
```bash
$ make testql-encoder

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎯 TestQL Encoder Test - Basic (9 modules)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Passed:       9/9
❌ Failed:       0/9
⏱️  Total time:   13.06s

  ✅ Encoder test completed!
  📄 Results: parallel_test_results.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `make testql-menu`

**Co robi:**
- Testuje WSZYSTKIE 69 kombinacji menu
- col-1 × col-2 dla każdego modułu
- 200ms delays (reliable)
- Encoder verification
- Czas: ~2.5 minuty

**Wynik:**
- `complete_menu_test_results.json`

**Przykład:**
```bash
$ make testql-menu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎯 TestQL Menu Test - Complete (69 combinations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Passed:        69/69
❌ Failed:        0/69
⏱️  Total time:    130.17s

  ✅ Menu test completed!
  📄 Results: complete_menu_test_results.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `make testql-parallel`

**Co robi:**
- Najszybszy test (9 concurrent)
- Wszystkie moduły równolegle
- Headless mode
- Czas: ~6-8 sekund

**Wynik:**
- `parallel_test_results.json`

**Przykład:**
```bash
$ make testql-parallel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🚀 TestQL Parallel Test - Fast
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Passed:       9/9
⏱️  Total time:   7.42s
🚀 Speedup:      ~7x faster than sequential

  ✅ Parallel test completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `make testql-visual`

**Co robi:**
- Otwiera widoczne okno Chrome
- Purple/Green message boxes
- Yellow highlights
- Real-time navigation
- Czas: ~30 sekund

**Uwaga:** SPRAWDŹ EKRAN! Zobaczysz okno.

**Przykład:**
```bash
$ make testql-visual

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎬 TestQL Visual Test - Browser Window
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  📺 WATCH YOUR SCREEN - Browser window will open!

  [okno Chrome się otwiera...]

  ✅ Visual test completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `make testql-all`

**Co robi:**
- Uruchamia WSZYSTKIE testy
- Najpierw parallel (szybki baseline)
- Potem complete menu (comprehensive)
- Czas: ~3 minuty total

**Przykład:**
```bash
$ make testql-all

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎯 TestQL - Running ALL Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Parallel Test...
[runs parallel test...]

2️⃣  Complete Menu Test...
[runs menu test...]

  ✅ All tests completed!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### `make testql-results`

**Co robi:**
- Pokazuje podsumowanie wyników
- Czyta JSON files
- Wyświetla kluczowe metryki

**Przykład:**
```bash
$ make testql-results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 TestQL Results Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Parallel Test:
        "total": 9,
        "passed": 9,
        "failed": 0,
        "total_time": 13.06,

📄 Complete Menu Test:
        "total": 69,
        "passed": 69,
        "failed": 0,
        "total_time": 130.17,

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📋 Workflow Examples

### Daily Testing (Fast)
```bash
# Quick smoke test
make testql-encoder

# Zobacz wyniki
make testql-results
```

### Comprehensive Testing (Before Deploy)
```bash
# Full coverage
make testql-menu

# Sprawdź wyniki
cat complete_menu_test_results.json | python -m json.tool | less
```

### Debug Mode (Visual)
```bash
# Zobacz co się dzieje
make testql-visual
```

### CI/CD Pipeline
```bash
# All tests
make testql-all

# Check results
make testql-results
```

---

## 🎯 Porównanie Komend

| Komenda | Testy | Czas | Użycie |
|---------|-------|------|--------|
| `testql-encoder` | 9 modułów | ~13s | Daily smoke test |
| `testql-menu` | 69 kombinacji | ~2.5min | Pre-deploy comprehensive |
| `testql-parallel` | 9 modułów | ~7s | Fastest baseline |
| `testql-visual` | 3 strony | ~30s | Debug/demo |
| `testql-all` | Wszystko | ~3min | CI/CD full suite |

---

## 💡 Tips

**Szybki test przed commitem:**
```bash
make testql-encoder && git commit -m "..."
```

**Full test przed merging:**
```bash
make testql-all && git push
```

**Debug problemów:**
```bash
make testql-visual  # Zobacz co się dzieje
```

**Check status:**
```bash
make testql-results  # Quick summary
```

---

## 🚀 Integration

### Git Hooks (pre-push)

Dodaj do `.git/hooks/pre-push`:
```bash
#!/bin/bash
cd ~/github/oqlos/testql
make testql-encoder
if [ $? -ne 0 ]; then
    echo "❌ TestQL encoder test failed!"
    exit 1
fi
```

### CI/CD (GitLab CI)

`.gitlab-ci.yml`:
```yaml
test:
  script:
    - cd testql
    - make testql-all
  artifacts:
    paths:
      - testql/*.json
```

---

**🎉 TestQL Makefile jest gotowy do użycia!**

Wszystkie komendy działają przez prosty `make testql-*` interface!
