#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_ROOT="$BASE_DIR/.testql-matrix"
ROUTES_FILE="$BASE_DIR/routes.txt"

mkdir -p "$OUT_ROOT"
SUMMARY_FILE="$OUT_ROOT/summary.txt"
ISSUES_FILE="$OUT_ROOT/testql-issues.txt"

: > "$SUMMARY_FILE"
: > "$ISSUES_FILE"

echo "c2004 testql matrix summary" >> "$SUMMARY_FILE"
echo "==========================" >> "$SUMMARY_FILE"

index=0
while IFS= read -r url; do
  [[ -z "${url// }" ]] && continue
  index=$((index + 1))
  outdir="$OUT_ROOT/case-$index"
  echo "==> [$index] $url"
  bash "$BASE_DIR/run.sh" "$url" "$outdir"

done < "$ROUTES_FILE"

export TESTQL_MATRIX_ROOT="$OUT_ROOT"
python3 - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["TESTQL_MATRIX_ROOT"])
summary_file = root / "summary.txt"
issues_file = root / "testql-issues.txt"

rows = []
issues = []

for case in sorted(root.glob("case-*")):
    result_path = case / "result.json"
    if not result_path.exists():
        continue

    payload = json.loads(result_path.read_text())
    result = payload.get("result", {})
    source = result.get("metadata", {}).get("source", "unknown")
    status = result.get("status", "unknown")
    checks = result.get("checks", [])

    warning_checks = [c for c in checks if c.get("status") == "warning"]
    failed_checks = [c for c in checks if c.get("status") == "failed"]
    skipped_checks = [c for c in checks if c.get("status") == "skipped"]

    rows.append({
        "case": case.name,
        "source": source,
        "status": status,
        "warnings": len(warning_checks),
        "failed": len(failed_checks),
        "skipped": len(skipped_checks),
    })

    for c in warning_checks + failed_checks:
        issues.append({
            "case": case.name,
            "source": source,
            "check_id": c.get("id", "unknown"),
            "status": c.get("status", "unknown"),
            "summary": c.get("summary", ""),
            "metadata": c.get("metadata", {}),
        })

with summary_file.open("a") as f:
    for row in rows:
        f.write(f"\n[{row['case']}] {row['source']}\n")
        f.write(f"  status={row['status']} warnings={row['warnings']} failed={row['failed']} skipped={row['skipped']}\n")

with issues_file.open("w") as f:
    f.write("testql issues detected on c2004\n")
    f.write("=============================\n")
    if not issues:
        f.write("No warning/failed checks detected.\n")
    else:
        for issue in issues:
            f.write(f"\n[{issue['case']}] {issue['source']}\n")
            f.write(f"- {issue['status'].upper()} {issue['check_id']}: {issue['summary']}\n")

        f.write("\nRecommended testql fixes\n")
        f.write("------------------------\n")
        f.write("1. Add browser-rendered link extraction for SPA apps (menu buttons/router links), not only static <a href>.\n")
        f.write("2. Add route discovery from history/router APIs and clickable nav elements (e.g., data-route, role=button nav items).\n")
        f.write("3. Improve 'partial' classification: distinguish 'SPA-no-anchor' from true topology incompleteness.\n")
        f.write("4. Add optional Playwright-backed probe mode in inspect to populate links/forms after JS execution.\n")
        f.write("5. Deduplicate same asset URL occurrences in topology checks to reduce noisy node inflation.\n")
PY

echo "==> Matrix done"
echo "    - $SUMMARY_FILE"
echo "    - $ISSUES_FILE"
