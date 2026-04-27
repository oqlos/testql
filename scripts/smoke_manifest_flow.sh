#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="${1:-$PWD}"
PROJECT_DIR="$(realpath "$PROJECT_DIR")"
OUT_DIR="${PROJECT_DIR}/.testql-manifest-smoke"
GEN_DIR="${OUT_DIR}/generated"
REP_DIR="${OUT_DIR}/reports"

mkdir -p "$GEN_DIR" "$REP_DIR"

echo "== testql manifest smoke =="
echo "project: $PROJECT_DIR"

gen_from() {
  local src="$1"
  local file="$2"
  local out="$3"

  if [[ -f "$file" ]]; then
    echo "[generate-ir] ${src}:${file}"
    testql generate-ir --from "${src}:${file}" --to testtoon --out "$out"
  else
    echo "[skip] file not found: $file"
  fi
}

# Manifest matrix
MAKEFILE_PATH="$PROJECT_DIR/Makefile"
TASKFILE_PATH="$PROJECT_DIR/Taskfile.yml"
DOCKER_COMPOSE_PATH="$PROJECT_DIR/docker-compose.yml"
BUF_PATH="$PROJECT_DIR/buf.yaml"

gen_from makefile "$MAKEFILE_PATH" "$GEN_DIR/makefile.testql.toon.yaml"
gen_from taskfile "$TASKFILE_PATH" "$GEN_DIR/taskfile.testql.toon.yaml"
gen_from docker-compose "$DOCKER_COMPOSE_PATH" "$GEN_DIR/docker-compose.testql.toon.yaml"
gen_from buf "$BUF_PATH" "$GEN_DIR/buf.testql.toon.yaml"

# Auto-detect aliases (config)
gen_from config "$MAKEFILE_PATH" "$GEN_DIR/config-makefile.testql.toon.yaml"
gen_from config "$TASKFILE_PATH" "$GEN_DIR/config-taskfile.testql.toon.yaml"
gen_from config "$DOCKER_COMPOSE_PATH" "$GEN_DIR/config-docker-compose.testql.toon.yaml"
gen_from config "$BUF_PATH" "$GEN_DIR/config-buf.testql.toon.yaml"

if compgen -G "$GEN_DIR/*.testql.toon.yaml" > /dev/null; then
  echo "[run] dry-run all generated scenarios"
  testql run "$GEN_DIR" --dry-run --quiet --output json > "$REP_DIR/manifest-run.json"
  echo "[ok] report: $REP_DIR/manifest-run.json"
else
  echo "[warn] no generated scenarios found"
fi

if command -v testql >/dev/null 2>&1; then
  echo "[topology]"
  testql topology "$PROJECT_DIR" --format json > "$REP_DIR/topology.json" || true
fi

echo "done"
