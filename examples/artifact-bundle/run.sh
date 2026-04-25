#!/usr/bin/env bash
# Artifact bundle generation demo — inspect a URL and write .testql/ bundle

set -euo pipefail

URL="${1:-https://tom.sapletta.com/}"
OUTDIR="${2:-.testql}"

echo "==> Generating artifact bundle for $URL"
python3 generate_bundle.py "$URL" "$OUTDIR"

echo "==> Bundle contents:"
ls -la "$OUTDIR"

echo "==> Metadata:"
cat "$OUTDIR/metadata.json" | python3 -m json.tool

echo "==> Done"
