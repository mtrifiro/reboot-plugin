#!/usr/bin/env sh
# Every check that keeps the plugin honest, in one command for CI or a
# pre-commit hook; a thin wrapper over tools/check.sh's stages.
#   tools/check-all.sh            # lint, shell, unit; no network
#   tools/check-all.sh --full     # and integration: the CLI, symbol,
#                                 # template-build and rendered-style
#                                 # checks, and the mods when `claude`
#                                 # is on PATH (need network)
set -eu
if [ "${1:-}" = "--full" ]; then
    exec "$(dirname -- "$0")/check.sh" --upto integration
fi
exec "$(dirname -- "$0")/check.sh" --upto unit
