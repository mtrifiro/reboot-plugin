#!/usr/bin/env sh
# PostToolUse on Write and Bash: a build report saved under
# `design/reports/` that the chat has not shown is sent now.
#
# The build skill says each report goes to the chat first, then to its
# file. hotel-4 (35fe0731) saved the brief with a heredoc and went on;
# the user saw only the app's summary of its thinking. So when a call
# writes `design/reports/<n>-<name>.md`, the report's title (its `# `
# line) is looked for in the transcript's visible text; missing, the
# agent is told to send the report now.
#
# Silent for any other call and when the title has been shown.

set -eu

input=$(cat)

field() {
    printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

case "$input" in *design/reports/*) ;; *) exit 0 ;; esac

path=$(field file_path)
case "$path" in
*design/reports/[0-9]*.md) ;;
*) path=$(printf '%s' "$input" | grep -o '[^ "'"'"'<>|;&]*design/reports/[0-9][A-Za-z0-9_-]*\.md' | head -n 1) ;;
esac
[ -n "$path" ] || exit 0
case "$path" in
/*) ;;
*) cwd=$(field cwd); path="${cwd:-$PWD}/${path}" ;;
esac
[ -r "$path" ] || exit 0

title=$(grep -m 1 '^# ' "$path" | sed 's/^# *//') || true
[ -n "$title" ] || exit 0

transcript=$(field transcript_path)
[ -n "$transcript" ] || exit 0
[ -r "$transcript" ] || exit 0
# The agent's own text only: the build skill's text, which a user line
# carries, holds the brief's title as its example.
if grep -F '"type":"assistant"' "$transcript" | grep -F '"type":"text"' | grep -Fv '"type":"tool_use"' | grep -Fq -- "$title"; then
    exit 0
fi

name=${path##*/}
# shellcheck disable=SC2016  # Markdown backticks
printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[reboot-plugin-report] `design/reports/%s` is saved, but the user has not seen it. A report only saved has not been given. Send it now in the chat, as visible text, verbatim with its frame. Never in thinking."}}' "$name"
