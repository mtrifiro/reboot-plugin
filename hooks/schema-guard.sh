#!/usr/bin/env sh
# The schema guard, for Claude Code and Codex: refuses API edits a
# Reboot app with persisted state couldn't boot over.
# `schema-guard/guard.mjs` holds the logic and says what it refuses;
# `hooks.json` registers this for PreToolUse (the edit tools and Bash),
# PostToolUse (Read and Bash) and PreCompact (the Claude app's hook
# schema lists PreCompact and not PostCompact; the guard takes both).
#
# A payload that mentions no `api` (an API definition file, the rules
# file, a `cd api/...`), no git command that replaces the working tree
# (stash, reset, checkout, restore, switch, clean), and isn't a
# compaction, exits at once, so most tool calls never start Node.
#
# Fails open: no plugin root, no Node, or an error in the script lets
# the tool call through.

root="${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
root="${root%/}"
[ -n "$root" ] || exit 0

input=$(cat)
case "$input" in
    *api* | *git*stash* | *git*reset* | *git*checkout* | *git*restore* | *git*switch* | *git*clean* \
        | *'"PreCompact"'* | *'"PostCompact"'*) ;;
    *) exit 0 ;;
esac

printf '%s' "$input" \
    | "$root/bin/node" --experimental-strip-types --no-warnings \
        "$root/hooks/schema-guard/guard.mjs" 2>/dev/null
exit 0
