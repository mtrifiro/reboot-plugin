#!/usr/bin/env sh
# Every check that keeps the plugin honest, in one command for CI or a
# pre-commit hook. Fails on the first broken check.
#   tools/check-all.sh            # fast checks; no network
#   tools/check-all.sh --full     # also the CLI, symbol, template-build and
#                                 # rendered-style checks, and the mods when
#                                 # `claude` is on PATH (need network)
set -eu
cd "$(dirname -- "$0")/.."

python3 tools/gen-index.py --check --quiet
python3 tools/lint-references.py
python3 tools/lint-frontmatter.py
python3 tools/findings.py --check
python3 tools/budget.py --readme check
python3 tools/style-check.py
python3 tools/templates-drift.py
python3 tools/check-manifests.py
python3 tests/hooks/auto_approve_test.py -q
python3 tests/hooks/orphans_test.py -q
python3 tests/templates/copy_test.py -q
if command -v shellcheck >/dev/null 2>&1; then
    shellcheck install.sh hooks/*.sh hooks-handlers/*.sh lib/*.sh bin/* tools/*.sh \
        skills/build/templates/copy.sh
else
    echo "check-all: shellcheck is not installed; skipped (CI runs it)" >&2
fi
if [ "${1:-}" = "--full" ]; then
    python3 tools/check-cli.py
    python3 tools/check-symbols.py
    SMOKE_FULL=1 tools/templates-smoke.sh
    bin/uv run --no-project --with playwright sh -c \
        'python -m playwright install --with-deps chromium >/dev/null && python tools/style-check.py --browser'
    if command -v claude >/dev/null 2>&1; then
        tools/check-mods.sh
    else
        echo "check-all: claude is not on PATH; mods skipped (CI runs them)" >&2
    fi
fi
