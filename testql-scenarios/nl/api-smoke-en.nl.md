# SCENARIO: API smoke (EN)
TYPE: api
LANG: en
VERSION: 1.0

1. Send GET /api/health
2. Check that status is 200
3. Send POST /api/items
4. Check that status is 201
5. Wait 100
