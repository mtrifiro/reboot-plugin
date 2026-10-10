#!/usr/bin/env sh
# Codex's schema guard: what `mods/reboot-schema-guard` does in Claude
# Code, for Codex, which runs this plugin's `hooks.json` but not mods.
# `schema-guard/codex.mjs` holds the logic and says what it refuses.
#
# Codex sends a `turn_id` with every tool and compaction event; Claude
# Code never does for these, and the mod already guards there, so a
# payload without one exits at once. So does any payload that names
# neither an API definition file (`api/<pkg>/v1/<name>.py`) nor the
# rules file, so most tool calls never start Node.
#
# Fails open: no plugin root, no Node, or an error in the script lets
# the tool call through.

root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
root="${root%/}"
[ -n "$root" ] || exit 0

input=$(cat)
case "$input" in
    *'"turn_id"'*) ;;
    *) exit 0 ;;
esac
case "$input" in
    *api/*/v1/*.py* | *api-schema-evolution.md* | *'"PostCompact"'*) ;;
    *) exit 0 ;;
esac

printf '%s' "$input" \
    | "$root/bin/node" --experimental-strip-types --no-warnings \
        "$root/hooks/schema-guard/codex.mjs" 2>/dev/null
exit 0
