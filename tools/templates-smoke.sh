#!/usr/bin/env bash
#
# Smoke-build every front-door template in skills/build/templates/.
#
# For each front door: copy the template into a temp dir with
# copy.sh, then, with the plugin's own shims (bin/rbt, bin/uv,
# bin/npm, bin/node) first on PATH:
#
#   uv sync -> rbt generate -> npm install -> rbt generate
#   -> npm run build (tsc -b + vite) -> mypy backend/ tests/
#   -> pytest --collect-only
#
# Exits non-zero on the first failure. A template that does not build
# cannot ship.
#
#   tools/templates-smoke.sh [mcp-ui] [web-app]   # default: both
#
# Environment:
#   SMOKE_FULL=1   also run the scenarios (`pytest`), not just collect
#   SMOKE_KEEP=1   keep the temp dirs (printed) for inspection

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname -- "$0")/.." && pwd)"
TEMPLATES="$PLUGIN_ROOT/skills/build/templates"
export PATH="$PLUGIN_ROOT/bin:$PATH"

FRONT_DOORS=("$@")
if [ "${#FRONT_DOORS[@]}" -eq 0 ]; then
  FRONT_DOORS=(mcp-ui web-app)
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/templates-smoke.XXXXXX")"
cleanup() {
  if [ "${SMOKE_KEEP:-0}" = "1" ]; then
    echo "kept: $WORK"
  else
    rm -rf "$WORK"
  fi
}
trap cleanup EXIT

step() {
  echo
  echo "==> [$FD] $*"
}

for FD in "${FRONT_DOORS[@]}"; do
  case "$FD" in
    mcp-ui) FRONTEND=frontend ;;
    web-app) FRONTEND=web ;;
    *) echo "unknown front door: $FD" >&2; exit 2 ;;
  esac

  PROJ="$WORK/$FD"
  step "copy template"
  "$TEMPLATES/copy.sh" "$FD" "$PROJ" smoke-app smoke_app "Smoke App"

  step "no placeholders left"
  if grep -rn '__project__\|__app__\|__Title__' "$PROJ"; then
    echo "FAIL: unsubstituted placeholders" >&2
    exit 1
  fi
  if find "$PROJ" -name '__init__.py' | grep .; then
    echo "FAIL: template ships an __init__.py" >&2
    exit 1
  fi

  cd "$PROJ"

  step "uv sync"
  uv sync --quiet

  step "rbt generate (before npm install)"
  rbt generate

  step "npm install"
  (cd "$FRONTEND" && npm install --no-audit --no-fund --loglevel=error)

  step "rbt generate (with node_modules)"
  rbt generate

  step "npm run build (tsc -b + vite build)"
  (cd "$FRONTEND" && npm run build)

  step "mypy backend/ tests/"
  uv run mypy backend/ tests/

  step "pytest --collect-only"
  uv run pytest --collect-only -q

  if [ "${SMOKE_FULL:-0}" = "1" ]; then
    step "pytest (scenarios)"
    uv run pytest -q
  fi

  echo
  echo "PASS: $FD"
done

echo
echo "All templates passed: ${FRONT_DOORS[*]}"
