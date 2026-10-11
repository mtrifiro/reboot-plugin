#!/usr/bin/env bash
#
# Smoke-build every front-door template in skills/build/templates/.
#
# For each front door: copy the template into a temp dir with
# copy.sh, then, with the plugin's own shims (bin/rbt, bin/uv,
# bin/npm, bin/node) first on PATH:
#
#   uv sync -> npm install -> rbt generate
#   -> npm run build (tsc -b + vite) -> mypy backend/ tests/
#   -> pytest --collect-only
#
# Exits non-zero on the first failure. A template that does not build
# cannot ship.
#
#   tools/templates-smoke.sh [mcp-ui] [web-app] [both]   # default: all three
#   tools/templates-smoke.sh --reap                     # only stop leftovers
#
# The scenarios start each template's backend as its own process, in its
# own process group, so a run cut off before its servers stop leaves
# them running from a deleted folder. On exit the run stops every
# process whose program lives in its scratch folder (the scenario
# servers' .venv python); on start it stops those of earlier runs whose
# folder is gone, the case a hard kill leaves (no exit trap runs then).
# Only the program path counts, never other words on a command line, so
# a shell that merely mentions a path is never touched.
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
  FRONT_DOORS=(mcp-ui web-app both)
fi

# The pids of processes whose program (the first word of the command
# line) lies under the folder $1.
pids_running_from() {
  ps -axo pid=,command= | awk -v dir="$1/" -v self="$$" \
    '$1 != self && index($2, dir) == 1 { print $1 }'
}

# Stop the given pids: TERM, up to five seconds, then KILL.
stop_pids() {
  [ "$#" -gt 0 ] || return 0
  kill "$@" 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    alive=""
    for pid in "$@"; do kill -0 "$pid" 2>/dev/null && alive="$alive $pid"; done
    [ -z "$alive" ] && return 0
    sleep 0.5
  done
  # shellcheck disable=SC2086  # a list of pids
  kill -9 $alive 2>/dev/null || true
}

# Leftovers of earlier runs: processes naming a templates-smoke.* folder
# that no longer exists.
reap_stale() {
  local stale="" dir pid
  while read -r pid dir; do
    [ -n "$dir" ] && [ ! -d "$dir" ] && stale="$stale $pid"
  done < <(ps -axo pid=,command= | awk -v self="$$" '$1 != self {
      if (match($2, /^\/.*\/templates-smoke\.[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9]\//))
        print $1, substr($2, 1, RLENGTH - 1)
    }')
  if [ -n "$stale" ]; then
    echo "templates-smoke: stopping leftovers of an earlier run:$stale"
    # shellcheck disable=SC2086  # a list of pids
    stop_pids $stale
  fi
}

if [ "${1:-}" = "--reap" ]; then
  reap_stale
  exit 0
fi
reap_stale

WORK="$(mktemp -d "${TMPDIR:-/tmp}/templates-smoke.XXXXXX")"
cleanup() {
  # shellcheck disable=SC2046  # a list of pids
  stop_pids $(pids_running_from "$WORK")
  if [ "${SMOKE_KEEP:-0}" = "1" ]; then
    echo "kept: $WORK"
  else
    rm -rf "$WORK"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Each step prints the time the one before it took, so a slow smoke
# says where its time went.
STEP_START=""
STEP_NAME=""
step() {
  local now
  now=$(date +%s)
  if [ -n "$STEP_START" ]; then
    echo "    ($STEP_NAME: $((now - STEP_START)) s)"
  fi
  STEP_START=$now
  STEP_NAME="$*"
  echo
  echo "==> [$FD] $*"
}

for FD in "${FRONT_DOORS[@]}"; do
  case "$FD" in
    mcp-ui|both) FRONTEND=frontend ;;
    web-app) FRONTEND=web ;;
    *) echo "unknown front door: $FD" >&2; exit 2 ;;
  esac

  PROJ="$WORK/$FD"
  step "copy template"
  "$TEMPLATES/copy.sh" "$FD" "$PROJ" smoke-app smoke_app "Smoke App"

  step "no placeholders left"
  if grep -rn '__project__\|__app__\|__Title__\|__Initial__' "$PROJ"; then
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

  # npm install first: the React bindings need node_modules, so one
  # generate after it makes both the Python and the TypeScript code.
  step "npm install"
  (cd "$FRONTEND" && npm install --no-audit --no-fund --loglevel=error)

  step "rbt generate"
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

  step "done"
  echo "PASS: $FD"
done

echo
echo "All templates passed: ${FRONT_DOORS[*]}"
