#!/usr/bin/env sh
# PostToolUse and Stop: the app skill's welcome reaches the user as
# visible text, and the build goes on after it.
#
# Told only in words, the agent either wrote the welcome in thinking and
# went on to its tools (the user saw the app's one-line summary of it),
# or sent it as a message of its own, which ends the turn and leaves the
# build idle. So, in a new build (the app skill launched, no `.rbtrc` in
# the working directory or an ancestor):
#
# - PostToolUse, the moment the app skill loads, says the next output is
#   the welcome as visible text: said there, beside the skill, before the
#   agent has drafted anything in thinking.
# - No PreToolUse refusal: a tool hook can't see the text of the response
#   it belongs to (the transcript gets it after the hooks run), so it
#   refused calls that came right after a visible welcome (hotel-5,
#   3847b122: two failed calls and the welcome twice).
# - Stop, when the turn's last message is that welcome, sends the agent
#   on to the build and front-door skills (once: `stop_hook_active`).
#
# Silent in every other session, and in the plugin's own checkout.

set -eu

input=$(cat)

field() {
    printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" | head -n 1
}


in_new_build() {
    d=$(field cwd)
    [ -n "$d" ] || d=$PWD
    case "$d" in /*) ;; *) d="${PWD}/${d}" ;; esac
    while [ -n "$d" ] && [ "$d" != "/" ]; do
        [ -f "${d}/.rbtrc" ] && return 1
        [ -f "${d}/skills/app/SKILL.md" ] && [ -d "${d}/hooks-handlers" ] && return 1
        d="${d%/*}"
    done
}

if [ "$(field hook_event_name)" = PostToolUse ]; then
    [ "$(field skill)" = reboot:app ] || exit 0
    in_new_build || exit 0
    # shellcheck disable=SC1112  # the ’ is meant
    printf '%s' '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"[reboot-plugin-welcome] Your next output is the app skill’s welcome, as visible text: its paragraph verbatim, on one line, no quote marks, its examples from the user’s brief. Do not draft it or summarize it in thinking first. Then go straight on, in the same response, to the build and front-door skills."}}'
    exit 0
fi

transcript=$(field transcript_path)
[ -n "$transcript" ] || exit 0
[ -r "$transcript" ] || exit 0
grep -Fq -e '"content":"Launching skill: reboot:app"' -e '"content":"<command-message>reboot:app</command-message>' "$transcript" || exit 0

in_new_build || exit 0

WELCOME='"type":"text","text":"(\\n|[[:space:]])*(> )?\*\*Welcome to Reboot\.'

case "$(field hook_event_name)" in
Stop)
    [ "$(printf '%s' "$input" | sed -n 's/.*"stop_hook_active"[[:space:]]*:[[:space:]]*\(true\).*/\1/p')" = true ] && exit 0
    grep '"type":"assistant"' "$transcript" | tail -n 1 | grep -Eq "$WELCOME" || exit 0
    # shellcheck disable=SC2016  # Markdown backticks
    printf '%s' '{"decision":"block","reason":"[reboot-plugin-welcome] The user has the welcome. Go on now: invoke the `build` skill and the front-door skill, then the scope round, without another message first."}'
    ;;
esac
