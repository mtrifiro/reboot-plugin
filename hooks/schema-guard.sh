#!/usr/bin/env sh
# The schema guard, for Claude Code and Codex: refuses API edits a
# Reboot app with persisted state couldn't boot over.
# `schema-guard/guard.mjs` holds the logic and says what it refuses;
# `hooks.json` registers this for PreToolUse (the edit tools and Bash),
# PostToolUse (Read and Bash) and PostCompact.
#
# A payload that names neither an API definition file
# (`api/<pkg>/v1/<name>.py`) nor the rules file, and isn't a
# compaction, exits at once, so most tool calls never start Node.
#
# Fails open: no plugin root, no Node, or an error in the script lets
# the tool call through.

root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
root="${root%/}"
[ -n "$root" ] || exit 0

input=$(cat)
case "$input" in
    *api/*/v1/*.py* | *api-schema-evolution.md* | *'"PostCompact"'*) ;;
    *) exit 0 ;;
esac

printf '%s' "$input" \
    | "$root/bin/node" --experimental-strip-types --no-warnings \
        "$root/hooks/schema-guard/guard.mjs" 2>/dev/null
exit 0
