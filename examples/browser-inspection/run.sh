#!/usr/bin/env bash
# Browser inspection demo — run Playwright-backed inspection on a target URL

set -euo pipefail

URL="${1:-https://tom.sapletta.com/}"
OUTDIR="${2:-.testql-browser}"

echo "==> Browser-inspecting $URL"
echo "==> Output directory: $OUTDIR"

# Requires: pip install playwright && playwright install chromium
testql inspect "$URL" --scan-network --browser --out-dir "$OUTDIR"

echo "==> Generated files in $OUTDIR:"
ls -la "$OUTDIR"

echo "==> Browser checks summary"
python3 -c "
import json
with open('$OUTDIR/result.json') as f:
    data = json.load(f)
for c in data.get('checks', []):
    if c['id'].startswith('check.browser'):
        status = c['status'].upper()
        print(f\"  [{status:8}] {c['id']:40} {c['summary']}\")
"

echo "==> Console errors:"
python3 -c "
import json
with open('$OUTDIR/inspection.json') as f:
    d = json.load(f)['inspection']
page = next((n for n in d['topology']['nodes'] if n['kind']=='page'), {})
errors = page.get('metadata', {}).get('console_errors', [])
print(f\"  {len(errors)} console error(s)\")
for e in errors[:5]:
    print(f\"    - {e}\")
"

echo "==> Network calls:"
python3 -c "
import json
with open('$OUTDIR/inspection.json') as f:
    d = json.load(f)['inspection']
page = next((n for n in d['topology']['nodes'] if n['kind']=='page'), {})
calls = page.get('metadata', {}).get('network_calls', [])
print(f\"  {len(calls)} network call(s)\")
for c in calls[:5]:
    print(f\"    - {c.get('method', 'GET'):6} {c.get('url', '')[:70]}\")
"

echo "==> Done"
