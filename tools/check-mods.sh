#!/usr/bin/env sh
# Check every mod in mods/ the way the engine reads it: the manifest,
# the module and what it calls (`claude plugin validate`), then its
# *.test.ts files against the engine itself (`claude plugin test`).
# Neither needs a sign-in. Type-checking (`tsc -p .`) is not here: the
# engine writes a mod's tsconfig and types only when a session loads
# it, so run that from the mod's folder after one has (mods/README.md).
#
#   tools/check-mods.sh              # every mod
#   tools/check-mods.sh reboot-progress
set -eu
cd "$(dirname -- "$0")/.."

command -v claude >/dev/null 2>&1 || {
    echo "check-mods: claude is not on PATH" >&2
    exit 1
}

if [ "$#" -gt 0 ]; then
    mods=$*
else
    mods=$(ls mods)
fi

for name in $mods; do
    [ -f "mods/$name/.claude-plugin/plugin.json" ] || continue
    echo "==> mods/$name: validate"
    claude plugin validate "mods/$name"
    echo "==> mods/$name: test"
    (cd "mods/$name" && claude plugin test .)
done
