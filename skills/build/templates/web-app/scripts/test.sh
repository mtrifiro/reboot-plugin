#!/usr/bin/env sh
# The suite, in the size a change needs. Past a few dozen scenarios a
# full run takes many minutes, so iterate on the areas a change touches
# and run everything once before a handoff or a push to `main`.
#
#   scripts/test.sh changed [<rev>]   the feature files changed since <rev> (default HEAD),
#                                     untracked ones included, through the modules that run them
#   scripts/test.sh smoke             the scenarios tagged @smoke
#   scripts/test.sh backend           everything but the browser scenarios (feature files tagged @browser)
#   scripts/test.sh <area>            the feature files tagged @<area> (one area tag per feature file;
#                                     register each in pytest.ini's `markers`)
#   scripts/test.sh full              everything, the gate before a handoff or a push to main
#
# Anything after the mode goes to pytest. Every run records its results
# in tests/.last-run.json (tests/last_run.py), with the hash of the tree
# it ran on; `full` is the only run the pre-push hook (.githooks/pre-push)
# accepts for a push to main. A scenario that hangs fails on its own
# after pytest.ini's `timeout`.
#
# `PYTEST` names the pytest to run (default `uv run pytest`).

set -eu
cd "$(dirname -- "$0")/.."

mode="${1:-full}"
[ "$#" -eq 0 ] || shift
pytest="${PYTEST:-uv run pytest}"

case "$mode" in
  changed)
    rev="HEAD"
    if [ "$#" -gt 0 ] && [ "${1#-}" = "$1" ]; then
      rev="$1"
      shift
    fi
    features="$( (git diff --name-only "$rev" -- 'tests/*.feature' 'tests/**/*.feature';
                  git ls-files --others --exclude-standard -- 'tests/*.feature' 'tests/**/*.feature') \
                | sort -u)"
    if [ -z "$features" ]; then
      echo "test.sh: no feature file changed since $rev; nothing to run (scripts/test.sh full runs everything)"
      exit 0
    fi
    modules=""
    for feature in $features; do
      name="$(basename -- "$feature")"
      found="$(grep -l -F -- "$name" tests/*_test.py 2>/dev/null || true)"
      if [ -z "$found" ]; then
        echo "test.sh: no module under tests/ names $name in its scenarios(...); it runs nowhere" >&2
        exit 1
      fi
      modules="$modules $found"
    done
    # shellcheck disable=SC2086  # the modules and the user's pytest arguments are word lists
    exec $pytest $(printf '%s\n' $modules | sort -u) "$@"
    ;;
  smoke)
    # shellcheck disable=SC2086
    exec $pytest -m smoke "$@"
    ;;
  backend)
    # shellcheck disable=SC2086
    exec $pytest -m "not browser" "$@"
    ;;
  full)
    # shellcheck disable=SC2086
    exec $pytest "$@"
    ;;
  -*|"")
    echo "usage: scripts/test.sh changed [<rev>] | smoke | backend | <area> | full  [pytest args]" >&2
    exit 2
    ;;
  *)
    # shellcheck disable=SC2086
    exec $pytest -m "$mode" "$@"
    ;;
esac
