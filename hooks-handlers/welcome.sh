#!/usr/bin/env sh
# PreToolUse and Stop: the app skill's welcome reaches the user as
# visible text, and the build goes on after it.
#
# Told only in words, the agent either wrote the welcome in thinking and
# went on to its tools (the user saw the app's one-line summary of it),
# or sent it as a message of its own, which ends the turn and leaves the
# build idle. So, in a new build (the app skill launched, no `.rbtrc` in
# the working directory or an ancestor):
#
# - PreToolUse refuses every tool call until a message opens with the
#   welcome, saying to send it now, as a message of its own.
# - Stop, when the turn's last message is that welcome, sends the agent
#   on to the build and front-door skills (once: `stop_hook_active`).
#
# Silent in every other session, and in the plugin's own checkout. A
# session whose welcome has gone out is remembered in the temp directory,
# so later calls skip the transcript.

set -eu

input=$(cat)

field() {
    printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

session=$(field session_id)
case "$session" in '' | *[!A-Za-z0-9_-]*) exit 0 ;; esac
dir="${TMPDIR:-/tmp}/reboot-welcome"
[ -f "${dir}/${session}" ] && exit 0

transcript=$(field transcript_path)
[ -n "$transcript" ] && [ -r "$transcript" ] || exit 0
grep -Fq -e '"content":"Launching skill: reboot:app"' -e '"content":"<command-message>reboot:app</command-message>' "$transcript" || exit 0

d=$(field cwd)
[ -n "$d" ] || d=$PWD
case "$d" in /*) ;; *) d="${PWD}/${d}" ;; esac
while [ -n "$d" ] && [ "$d" != "/" ]; do
    [ -f "${d}/.rbtrc" ] && exit 0
    [ -f "${d}/skills/app/SKILL.md" ] && [ -d "${d}/hooks-handlers" ] && exit 0
    d="${d%/*}"
done

WELCOME='"type":"text","text":"(\\n|[[:space:]])*(> )?\*\*Welcome to Reboot\.'

case "$(field hook_event_name)" in
PreToolUse)
    if grep -Eq "$WELCOME" "$transcript"; then
        if mkdir -p "$dir" 2>/dev/null; then : > "${dir}/${session}" 2>/dev/null || true; fi
        exit 0
    fi
    # shellcheck disable=SC1112  # the ’ is meant
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"[reboot-plugin-welcome] The welcome has not reached the user. Send the app skill’s welcome now, verbatim, as visible text in a message of its own, with no tool call, never in thinking. The build goes on after it."}}'
    ;;
Stop)
    [ "$(printf '%s' "$input" | sed -n 's/.*"stop_hook_active"[[:space:]]*:[[:space:]]*\(true\).*/\1/p')" = true ] && exit 0
    grep '"type":"assistant"' "$transcript" | tail -n 1 | grep -Eq "$WELCOME" || exit 0
    # shellcheck disable=SC2016  # Markdown backticks
    printf '%s' '{"decision":"block","reason":"[reboot-plugin-welcome] The user has the welcome. Go on now: invoke the `build` skill and the front-door skill, then the scope round, without another message first."}'
    ;;
esac
