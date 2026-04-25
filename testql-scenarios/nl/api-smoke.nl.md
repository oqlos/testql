# SCENARIO: API smoke
TYPE: api
LANG: pl
VERSION: 1.0

1. Wykonaj GET /api/health
2. Sprawdź że status to 200
3. Wyślij POST /api/items
4. Sprawdź że status to 201
5. Wykonaj GET /api/items
6. Sprawdź że status to 200
