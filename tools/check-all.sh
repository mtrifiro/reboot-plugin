#!/usr/bin/env sh
# Every check that keeps the skills honest, in one command for CI or a
# pre-commit hook. Fails on the first broken check.
#   tools/check-all.sh            # fast checks
#   tools/check-all.sh --full     # also CLI, symbol and template-build checks (need network)
set -eu
cd "$(dirname -- "$0")/.."

python3 tools/gen-index.py --check --quiet
python3 tools/lint-references.py
python3 tools/findings.py > /dev/null
python3 tools/budget.py
if [ "${1:-}" = "--full" ]; then
    python3 tools/check-cli.py
    python3 tools/check-symbols.py
    tools/templates-smoke.sh
fi
