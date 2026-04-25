#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CMD="${1:-echo}"
FORMAT="${2:-text}"

case "$CMD" in
  echo)
    echo "=== Generating Project Echo ($FORMAT) ==="
    testql echo \
      --toon-path "$ROOT_DIR/examples/project-echo" \
      --doql-path "$ROOT_DIR/examples/project-echo/app.doql.less" \
      --format "$FORMAT"
    echo ""
    echo "Done. Use 'json' format for LLM consumption."
    ;;
  build)
    echo "=== Building application from DOQL ==="
    doql -f "$ROOT_DIR/examples/project-echo/app.doql" build
    echo ""
    echo "Done. Application code is in build/"
    ;;
  export-less)
    echo "=== Exporting DOQL to LESS ==="
    doql -f "$ROOT_DIR/examples/project-echo/app.doql" export --format less -o "$ROOT_DIR/examples/project-echo/app.doql.less"
    echo "Done. app.doql.less updated."
    ;;
  *)
    echo "Usage: $0 {echo|build|export-less} [format]"
    echo ""
    echo "  echo         — Run testql echo (default). Format: text|json|sumd"
    echo "  build        — Run doql build to generate working application"
    echo "  export-less  — Re-export app.doql → app.doql.less"
    exit 1
    ;;
esac
