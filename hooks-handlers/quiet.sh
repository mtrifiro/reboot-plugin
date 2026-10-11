#!/usr/bin/env sh
# PostToolUse: every QUIET_EVERY tool calls of a Reboot build, repeat
# the one rule a long build forgets: the chat hears only reports, and a
# step line goes to `reboot-now`, which the progress band shows.
#
# The prompt-time reminder (remind.sh) arrives once per prompt, and a
# build is one prompt that runs dozens of tool calls; by the middle the
# rule sits far back and the habit of narrating between calls wins.
#
# A Reboot build is a session whose working directory, or an ancestor,
# holds a `.rbtrc`, or whose transcript has a message that opens with
# the welcome (a build's design comes before its `.rbtrc`). The count is kept per session in
# the temp directory; any other session stays silent, and the gate is
# only looked at on the calls that would speak.

set -eu

input=$(cat)

field() {
    printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}

every=${QUIET_EVERY:-12}
session=$(field session_id)
case "$session" in '' | *[!A-Za-z0-9_-]*) exit 0 ;; esac

dir="${TMPDIR:-/tmp}/reboot-quiet"
mkdir -p "$dir" 2>/dev/null || exit 0
count_file="${dir}/${session}"
count=$(cat "$count_file" 2>/dev/null || echo 0)
case "$count" in '' | *[!0-9]*) count=0 ;; esac
count=$((count + 1))
printf '%s\n' "$count" > "$count_file" 2>/dev/null || exit 0
[ $((count % every)) -eq 0 ] || exit 0

in_build() {
    d=$(field cwd)
    [ -n "$d" ] || d=$PWD
    case "$d" in /*) ;; *) d="${PWD}/${d}" ;; esac
    while [ -n "$d" ] && [ "$d" != "/" ]; do
        [ -f "${d}/.rbtrc" ] && return 0
        d="${d%/*}"
    done
    transcript=$(field transcript_path)
    [ -n "$transcript" ] && [ -r "$transcript" ] && grep -Eq '"text":"(> )?\*\*Welcome to Reboot\.\*\*' "$transcript"
}
in_build || exit 0

# shellcheck disable=SC2016  # the backticks are Markdown, not expansions
printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[reboot-plugin-quiet] Quiet between reports. A step line goes to `reboot-now <plain words>`, which the progress band shows, never to the chat: not \"The project shell is in place\", not \"The servicers are written. The tests come next\". The chat hears only the brief, the milestone reports and the review, each framed, and a question only the user can answer."}}'
