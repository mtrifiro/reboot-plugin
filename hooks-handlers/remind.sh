#!/usr/bin/env sh
# Inject a short "consult the Reboot skills, don't guess" reminder
# into the model's context. Registered in `hooks.json` for two hook
# events, and dispatches on `hook_event_name` from the hook input on
# stdin:
#
#   - SessionStart: always emits the reminder. This event fires at
#     the points where in-conversation copies of the reminder get
#     dropped (startup, resume, `/clear`, compaction), so it
#     re-injects right after each of them.
#   - UserPromptSubmit: emits the reminder only when the transcript's
#     recent tail no longer contains it, so long sessions see it
#     again every so often without it piling up on every turn.
#
# Both Claude Code and Codex run this handler: both auto-discover
# the plugin's `hooks/hooks.json`, set `$CLAUDE_PLUGIN_ROOT` for its
# commands, pass the same stdin fields, and accept the same
# `hookSpecificOutput.additionalContext` output shape, which each CLI
# records into the conversation for the model's next request.
#
# The reminder is scoped to Reboot projects: it is emitted when the
# session's working directory, or an ancestor, holds a `.rbtrc`, or,
# on a prompt, when the prompt names Reboot (a build's first lines
# come before its `.rbtrc` exists).
# The plugin is typically installed globally, so this handler runs in
# every session, including ones that have nothing to do with Reboot;
# those stay reminder-free.
#
# When the transcript path is absent, `null`, or unreadable, the
# handler errs on the side of emitting: a duplicate reminder costs a
# few tokens, while a skipped one defeats the hook's purpose.

set -eu

input=$(cat)

# Extract a top-level string field from the input JSON. Parses with
# `python3` when available, so field-shaped text inside other fields
# (e.g. a prompt that itself contains `"transcript_path": ...`) can
# not shadow the real value. Falls back to a naive sed parse
# otherwise; a sed mismatch at worst changes when the reminder is
# emitted.
field() {
    if command -v python3 >/dev/null 2>&1; then
        printf '%s' "$input" | python3 -c '
import json
import sys

value = json.load(sys.stdin).get(sys.argv[1])
print(value if isinstance(value, str) else "")
' "$1" 2>/dev/null && return 0
    fi
    printf '%s' "$input" | sed -n \
        "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p"
}

# True (0) when the session runs inside a Reboot project: the `cwd`
# the CLI passes in the hook input, or, when that field is absent,
# this process's own working directory, or any ancestor of it holds
# a `.rbtrc`. Mirrors the gate the `auto-approve.sh` PreToolUse hook
# applies to the `run` skill's dev commands.
in_reboot_project() {
    dir=$(field cwd)
    [ -n "$dir" ] || dir=$PWD
    # Resolve a relative directory against this process's own working
    # directory: the walk below strips one `/`-separated component per
    # iteration, so it terminates only when `dir` is absolute.
    case "$dir" in
        /*) ;;
        *) dir="${PWD}/${dir}" ;;
    esac
    while [ -n "$dir" ] && [ "$dir" != "/" ]; do
        [ -f "${dir}/.rbtrc" ] && return 0
        dir="${dir%/*}"
    done
    [ -f "/.rbtrc" ]
}

# A build starts in an empty folder, before any `.rbtrc` exists, and
# its first lines to the user are written then: a prompt that names
# Reboot gets the reminder too.
mentions_reboot() {
    field prompt | grep -qi 'reboot'
}

event=$(field hook_event_name)

if ! in_reboot_project; then
    [ "$event" = UserPromptSubmit ] && mentions_reboot || exit 0
fi

# First line of the reminder. The UserPromptSubmit throttle greps the
# transcript tail for it: both CLIs record every injected copy into
# the transcript verbatim, so finding this marker means a recent copy
# is still in context.
sentinel='[reboot-plugin-reminder]'

# How many trailing transcript lines count as "recent". A transcript
# line is one conversation entry (a user or assistant message or a
# tool result), so this is roughly twenty tool round-trips.
tail_lines=40

case "$event" in
    SessionStart)
        ;;
    UserPromptSubmit)
        transcript=$(field transcript_path)
        if [ -n "$transcript" ] && [ -r "$transcript" ] &&
            tail -n "$tail_lines" "$transcript" | grep -Fq "$sentinel"
        then
            exit 0
        fi
        ;;
    *)
        # Registered for the two events above only; stay silent on
        # anything else.
        exit 0
        ;;
esac

# The reminder is streamed straight from its heredoc into the JSON,
# rather than captured with `$(...)` first: bash 3.2, the `sh` on
# macOS, scans a heredoc inside a command substitution as if it were
# code, so an apostrophe in the prose there fails the whole script
# to parse. JSON-encoding it takes escaping only its newlines, since
# it contains no double quotes or backslashes by construction.
printf '{"hookSpecificOutput":{"hookEventName":"%s"' "$event"
printf ',"additionalContext":"'
# JSON-escape each line: backslashes, then the quotes the examples use.
awk 'NR > 1 { printf "\\n" } { gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); printf "%s", $0 }' <<'EOF'
[reboot-plugin-reminder] Reboot guidance for this session:
- A new build (no `.rbtrc` yet) opens with the `app` skill's "Welcome to
Reboot" and how the build proceeds, its examples from the user's brief,
before anything else.
- Speak as the build, never in the first person: no I, me, my, we or
us in anything said to the user. Not "I'll build this as a web app" or
"I've confirmed the rooms"; write "This is a web app" and "The 23
rooms are a fixed list". The subject is the app, the design, the build
or the prototype, and you is the user. A sentence that starts with I is
rewritten before it is sent.
- Speak in complete reports and stay quiet between them: the welcome,
one at each milestone (the build skill, "How the build talks": the app
has a domain model, has a feature spec with every scenario in plain
English, has been built, is being tested with the full feature suite),
each ending with what comes next and why, and the review at the
handoff. No commentary on steps, references, files or fixes, never
"Now the styles the timeline needs" or "The app shell is in place. The
gate board comes next"; the progress band shows where the build
stands. The model is proposed
until the user accepts it, never "settled". The first sentence about an
object says why it exists, with the object as its subject. Sentences
under about twenty words, one idea each, no em or en dashes, no
semicolons, no parentheses, no closing sentence that sums up.
- Do not guess Reboot platform behavior (idempotency, scheduling,
authorizers, state construction, contexts, generated APIs). Before
coding around any Reboot behavior, read the relevant reference in the
Reboot plugin's skills (`build`, `python`, `feature`, `mcp-ui`,
`web-app`, `run`, `upgrade`) and state what it says.
- Holding an error string? Grep a distinctive fragment of it in the
`python` skill's `references/errors.md` first; each row names the
reference that explains it.
- When a skill turns out wrong or silent about something you hit,
append an item to the project's `FINDINGS.md` (format inside it).
- An application's behavior is specified and tested as `.feature`
files (the `feature` skill): agree on a feature in English before
writing its API or code, and iterate on its scenarios with the user.
- Work follows the Reboot Flywheel (Design, Prove, Observe). The first
prototype comes after one round of scope questions (options, the
simplest recommended), then the whole design within that scope, each
object and decision with its why in the domain-model report, and
reviewed running: the architecture, the rules and the feature set, with
the user. Reboot is taught in the reports, in the user's nouns. After
it, agree
each feature in
English, show the slice of the model it adds, and write no
implementation until the user accepts it or said up front to build on
(the build skill, Accept the Design), recorded in
`design/accepted.json`. A change to a rule, to `api/` or to an
authorizer goes back there; `scripts/model_diff.py` sorts each change
from that record.
- Before hand-rolling a primitive (maps, queues, pub/sub, presence,
encryption), check Reboot's standard library: the `stdlib-*.md`
references in the `python` skill.
- Read a step's references together, one Read each, in parallel;
never several in one `cat`, which can be cut off unseen.
- Deploys and dev-loop restarts are slow; never use repeated deploys
or restarts to discover how Reboot behaves. After two failed attempts
at the same goal, stop, read the relevant skill reference, and explain
the constraint before trying again.
EOF
printf '"}}\n'
