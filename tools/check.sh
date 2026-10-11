#!/usr/bin/env sh
# The plugin's checks in stages by time and risk: lint, shell, unit,
# integration, behavior. `tools/check.sh --help` for the flags,
# `--list` for each stage's checks and times; the configuration is in
# tools/check.py.
exec python3 "$(dirname -- "$0")/check.py" "$@"
