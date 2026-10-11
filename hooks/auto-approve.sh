#!/usr/bin/env sh
# Auto-approve two narrow, safe categories of tool call so a
# skill's own steps don't each trigger a permission prompt.
# Dispatches on `tool_name` from the PreToolUse hook input on
# stdin.
#
#   1. Read-only inspection of this plugin's OWN skill files, so a
#      skill can read its sibling references. Covers the Read, LS,
#      Glob, and Grep tools, plus a small allowlist of read-only
#      Bash binaries (ls, cat, head, tail, wc, file, stat) whose
#      every path argument lies under `$CLAUDE_PLUGIN_ROOT/skills/`
#      and whose flags come from a short per-command list. `find`
#      is not on the list: `-exec`, `-delete` and `-fprint` make it
#      a write.
#
#   2. The Reboot dev commands issued by the `run` and `dashboard`
#      skills: `uv sync`, `npm install`, `npm run dev`,
#      `cloudflared tunnel …`, `uv run rbt dev run …`,
#      `uv run rbt dashboard …`, the MCPJam inspector. These
#      are approved ONLY inside a Reboot project tree (the working
#      directory, or an ancestor, holds a `.rbtrc`), and only with
#      the flags each may take.
#
# Guards that hold for every case:
#
#   - $CLAUDE_PLUGIN_ROOT must be set. Both Claude Code and Codex
#     set it to the plugin's real install path when invoking these
#     hooks; without it the `.../skills/` prefix check is
#     meaningless.
#   - No argument may contain `..` — that would let a path step
#     out of whatever directory it was checked against.
#
# For Bash, the command is split — on `;` `&&` `||` `|` — into
# parts validated independently. A part with a metacharacter that
# could chain, redirect, or interpolate (`&` `<` `>` `` ` `` `$`
# `(` `)` `\`) is never approved. Every part must match category
# 1, a stdin filter, a bare `cd`, or a category-2 Reboot dev
# command; the call is approved only if at least one part is a
# real op and none is unsafe. Every token of every part is checked:
# a path must lie under the plugin's `skills/`, a flag must be one
# the command may take, a bare integer is a count. Anything else (a
# second path, `~`, a quote, a flag with a path value such as
# `sort -o`) defers to the prompt.
#
# `tests/hooks/auto_approve_test.py` is the table of commands this
# must approve and must defer; `tools/check-all.sh` runs it.
#
# Anything not matching exits silently with status 0; Claude Code
# then falls back to the normal permission prompt.

# Adding a local directory as the marketplace source — what
# `install.sh` does when run from a checkout — leaves a trailing slash
# on the root. Strip it, so the `"${CLAUDE_PLUGIN_ROOT}/skills/"`
# prefixes below don't end in `//` and match nothing: the agent
# normalizes the paths it sends, so nothing can match a `//` prefix.
CLAUDE_PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT%/}"

# No env var ⇒ defer to normal prompt. Also catches a root of `/`,
# emptied by the strip above, whose `/skills/` prefix would match
# paths anywhere on the filesystem.
if [ -z "${CLAUDE_PLUGIN_ROOT}" ]; then
    exit 0
fi

input=$(cat)

# Claude Code and Codex both run this plugin's hooks, but only Claude
# Code understands a permissionDecision:"allow" response. Codex's
# parser REJECTS a bare "allow" (it reserves "allow" for responses
# that also rewrite the call via `updatedInput`) and reports
# "PreToolUse hook returned unsupported permissionDecision:allow".
# Codex has no hook-driven auto-approve at all -- its parser only acts
# on "deny", and the documented output for an allow/defer is empty
# stdout. See https://github.com/reboot-dev/reboot/issues/118. So emit
# the allow JSON only when the runtime is positively Claude Code, and
# stay silent otherwise (the Codex-safe default).
#
# Two signals must agree:
#
#   - $CLAUDECODE, which Claude Code exports into the processes it
#     spawns, hooks included. Codex exports only the two
#     compatibility variables $CLAUDE_PLUGIN_ROOT and
#     $CLAUDE_PLUGIN_DATA.
#   - No `turn_id` in the payload. Codex's
#     `pre-tool-use.command.input` schema requires `turn_id`, as a
#     documented Codex extension; Claude Code sends it only for
#     `MessageDisplay`, never for PreToolUse.
#
# The payload half is what catches a Codex running inside a Claude
# Code session, where $CLAUDECODE is inherited across the boundary
# but the payload still comes from Codex.
#
# `permission_mode` cannot serve as the signal, despite reading like
# a Claude Code-only concept: Codex's schema requires it too, with
# Claude Code's exact enum.
is_claude_code() {
    [ -n "${CLAUDECODE:-}" ] && [ -z "$(field turn_id)" ]
}

emit_allow() {
    is_claude_code || return 0
    echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
}

# Extract a top-level string field from the input JSON. Naive sed parse
# — fine for Claude Code's flat tool_input shape (no escaped quotes in
# paths). A value holding an escaped quote keeps its backslash, which
# the metacharacter screen below rejects.
field() {
    printf '%s' "$input" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p"
}

is_in_plugin() {
    # Empty string fails (no prefix match against a non-empty constant).
    case "$1" in
        "${CLAUDE_PLUGIN_ROOT}/skills" | "${CLAUDE_PLUGIN_ROOT}/skills/"*)
            return 0
            ;;
    esac
    return 1
}

has_traversal() {
    case "$1" in *..* ) return 0 ;; esac
    return 1
}

# True (0) when the flag token $1 is one a command may take: an exact
# flag from $2 (space-separated; one ending in `=` takes a value of
# letters, digits and `_ . / : @ -`), or `-` followed only by letters
# from $3, or, when $4 is `num`, `-` followed by digits (`head -40`).
flag_ok() {
    for exact in $2; do
        [ "$1" = "$exact" ] && return 0
        case "$exact" in
            *=)
                case "$1" in
                    "$exact"?*)
                        value="${1#"$exact"}"
                        case "$value" in *[!A-Za-z0-9_./:@-]*) ;; *) return 0 ;; esac
                        ;;
                esac
                ;;
        esac
    done
    case "$1" in
        --*) return 1 ;;
        -?*) ;;
        *) return 1 ;;
    esac
    letters="${1#-}"
    case "$letters" in
        *[!0-9]*) ;;
        *) [ "${4:-}" = num ] && return 0; return 1 ;;
    esac
    [ -n "$3" ] || return 1
    while [ -n "$letters" ]; do
        c="${letters%"${letters#?}"}"
        case "$3" in *"$c"*) ;; *) return 1 ;; esac
        letters="${letters#?}"
    done
    return 0
}

# True (0) when every token in $1 is a flag `flag_ok` accepts for the
# spec in $2 $3 $4, or a bare integer. An empty list is fine.
args_ok() {
    list=$1; shift
    for arg in $list; do
        case "$arg" in
            *[!0-9]*) flag_ok "$arg" "$@" || return 1 ;;
        esac
    done
    return 0
}

# True (0) when $1 holds at least one path, and every token is a path
# under this plugin's `skills/`, a flag `flag_ok` accepts for the spec
# in $2 $3 $4, or a bare integer.
args_in_plugin() {
    list=$1; shift
    paths=0
    for arg in $list; do
        case "$arg" in
            "${CLAUDE_PLUGIN_ROOT}/skills" | "${CLAUDE_PLUGIN_ROOT}/skills/"*) paths=$((paths + 1)) ;;
            *[!0-9]*) flag_ok "$arg" "$@" || return 1 ;;
        esac
    done
    [ "$paths" -gt 0 ]
}

# A read-only binary that reads files or stdin: with a plugin path
# among its arguments it is a file reader (every path under `skills/`),
# otherwise a stdin filter (flags only).
reader_or_filter() {
    list=$1; shift
    case " $list" in
        *" ${CLAUDE_PLUGIN_ROOT}/skills"*) args_in_plugin "$list" "$@" ;;
        *) args_ok "$list" "$@" ;;
    esac
}

# True (0) when every token in $1 is one of `rbt`'s own long flags
# (`--no-chaos`, `--port=9991`, `--env-file=.env`, …) or a bare
# integer. `rbt` flags only configure `rbt`; the project gate and the
# metacharacter screen are what keep the command local.
rbt_args_ok() {
    for arg in $1; do
        case "$arg" in
            --[a-z]*)
                name="${arg%%=*}"
                case "$name" in *[!a-z-]*) return 1 ;; esac
                case "$arg" in
                    *=*)
                        value="${arg#*=}"
                        case "$value" in *[!A-Za-z0-9_./:@-]*) return 1 ;; esac
                        ;;
                esac
                ;;
            *[!0-9]*) return 1 ;;
        esac
    done
    return 0
}

# True (0) when $1 is the MCPJam inspector's argument list as the `run`
# skill issues it: `--url http://localhost:<port>/mcp`, `--oauth`,
# `--no-open`, in any order. `--config` (a file that can name stdio
# servers, i.e. commands to run) and anything else defer.
mcpjam_args_ok() {
    expect_url=0
    for arg in $1; do
        if [ "$expect_url" -eq 1 ]; then
            case "$arg" in
                http://localhost:*/mcp | http://127.0.0.1:*/mcp)
                    port="${arg#http://*:}"; port="${port%/mcp}"
                    case "$port" in ''|*[!0-9]*) return 1 ;; esac
                    ;;
                *) return 1 ;;
            esac
            expect_url=0
            continue
        fi
        case "$arg" in
            --url) expect_url=1 ;;
            --oauth | --no-open) ;;
            *) return 1 ;;
        esac
    done
    [ "$expect_url" -eq 0 ]
}

# True (0) when $1 — resolved against $cwd when relative — sits
# inside a Reboot project: that directory, or any ancestor, holds
# a `.rbtrc`. Gates auto-approval of the `run` skill's Reboot dev
# commands; outside a project they fall through to the prompt.
in_reboot_project() {
    dir=$1
    case "$dir" in
        /*) ;;
        *) dir="${cwd}/${dir}" ;;
    esac
    while [ -n "$dir" ] && [ "$dir" != "/" ]; do
        [ -f "${dir}/.rbtrc" ] && return 0
        dir="${dir%/*}"
    done
    [ -f "/.rbtrc" ]
}

tool=$(field tool_name)

case "$tool" in
    Skill)
        # A skill routed by this plugin auto-approves its own Skill
        # invocation so the hand-off between skills doesn't trigger a
        # prompt. Only this plugin's skills qualify, matched by their
        # `reboot:` selector; `deploy`, `inspect` and `report` are
        # intentionally excluded because they reach outside the local
        # project.
        case "$(field skill)" in
            reboot:app | reboot:build | reboot:dashboard | reboot:feature | \
            reboot:mcp-ui | reboot:web-app | reboot:python | reboot:run | \
            reboot:upgrade)
                emit_allow
                ;;
        esac
        ;;
    Read)
        path=$(field file_path)
        has_traversal "$path" && exit 0
        is_in_plugin "$path" && emit_allow
        ;;
    LS|Glob|Grep)
        # All three take a `path` parameter (optional for Glob/Grep —
        # if absent the field is empty and is_in_plugin will reject).
        path=$(field path)
        has_traversal "$path" && exit 0
        is_in_plugin "$path" && emit_allow
        ;;
    Bash)
        cmd=$(field command)
        has_traversal "$cmd" && exit 0
        # The directory Claude Code launched the tool from. Used to
        # resolve relative paths and to gate the Reboot dev commands.
        cwd=$(field cwd)
        # Normalize: strip known-safe I/O redirects, then split chained
        # commands (`&&`, `||`, `|`, `;`) into one-per-line. Each part
        # is then validated independently. Anything still containing
        # risky metacharacters after normalization (`&`, `<`, `>`,
        # `` ` ``, `$`, `(`, `)`, `\`) falls through to a normal
        # permission prompt.
        parts=$(printf '%s' "$cmd" | sed \
            -e 's/[[:space:]]*2>&1//g' \
            -e 's/[[:space:]]*2>\/dev\/null//g' \
            -e 's/[[:space:]]*>\/dev\/null//g' \
            -e 's/&&/\n/g' \
            -e 's/||/\n/g' \
            -e 's/|/\n/g' \
            -e 's/;/\n/g')
        case "$parts" in
            *\&* | *\<* | *\>* | *\`* | *\$* | *\(* | *\)* | *\\* )
                exit 0
                ;;
        esac
        # Iterate each part. Approve only if at least one non-empty
        # part is a real safe op AND no part is unsafe. A part is
        # "safe" if it is one of:
        #
        #   (a) a read-only binary whose paths all lie under this
        #       plugin's skills and whose flags are on its list (the
        #       producer side of a pipeline, or a standalone op);
        #
        #   (b) a pure stdin filter — head, tail, wc, sort, uniq —
        #       with flags from its list and bare counts only. Covers
        #       `… | head -50`, `… | wc -l`; rejects `… | head x.txt`
        #       and `… | sort -o file`;
        #
        #   (c) a bare `cd` — no side effects of its own; it only
        #       moves the working directory tracked in `effective_dir`
        #       so the Reboot project gate below sees the right place;
        #
        #   (d) a Reboot dev command the `run` or `dashboard` skill
        #       issues — gated on `in_reboot_project` and on the flags
        #       that command may take.
        #
        # A `cd` part is safe but is not itself a "real op", so a
        # command that is only `cd …` still defers to the prompt.
        printf '%s\n' "$parts" | (
            approved=0
            effective_dir=$cwd
            while IFS= read -r part; do
                trimmed=$(printf '%s' "$part" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
                [ -z "$trimmed" ] && continue
                case "$trimmed" in
                    'ls '*)
                        args_in_plugin "${trimmed#ls}" "" 1aAlhR || exit 1
                        approved=$((approved + 1))
                        ;;
                    'cat '*)
                        args_in_plugin "${trimmed#cat}" "" nb || exit 1
                        approved=$((approved + 1))
                        ;;
                    'file '*)
                        args_in_plugin "${trimmed#file}" "" b || exit 1
                        approved=$((approved + 1))
                        ;;
                    'stat '*)
                        args_in_plugin "${trimmed#stat}" "" "" || exit 1
                        approved=$((approved + 1))
                        ;;
                    head | 'head '* | tail | 'tail '*)
                        cmd_name="${trimmed%% *}"
                        reader_or_filter "${trimmed#"$cmd_name"}" "-n -c" qv num || exit 1
                        approved=$((approved + 1))
                        ;;
                    wc | 'wc '*)
                        reader_or_filter "${trimmed#wc}" "" lwcm || exit 1
                        approved=$((approved + 1))
                        ;;
                    sort | 'sort '*)
                        args_ok "${trimmed#sort}" "" nrfub || exit 1
                        approved=$((approved + 1))
                        ;;
                    uniq | 'uniq '*)
                        args_ok "${trimmed#uniq}" "" cdu || exit 1
                        approved=$((approved + 1))
                        ;;
                    cd | 'cd '*)
                        # No side effects; just retarget the working
                        # directory for the Reboot project gate below.
                        target="${trimmed#cd}"
                        target="${target# }"
                        case "$target" in
                            '') ;;
                            /*) effective_dir=$target ;;
                            *) effective_dir="${effective_dir}/${target}" ;;
                        esac
                        ;;
                    'uv sync' | 'uv sync '*)
                        # `run` skill — backend dependency install.
                        in_reboot_project "$effective_dir" || exit 1
                        args_ok "${trimmed#uv sync}" \
                            "--quiet --frozen --locked --all-groups --no-dev" q || exit 1
                        approved=$((approved + 1))
                        ;;
                    'npm install' | 'npm install '*)
                        # `run` skill — frontend dependency install.
                        # Never a package name, `-g` or a registry.
                        in_reboot_project "$effective_dir" || exit 1
                        args_ok "${trimmed#npm install}" \
                            "--no-audit --no-fund --silent --quiet --prefer-offline --loglevel=" "" || exit 1
                        approved=$((approved + 1))
                        ;;
                    'npm run dev' | 'npm run dev '*)
                        # `run` skill — frontend dev server.
                        in_reboot_project "$effective_dir" || exit 1
                        args_ok "${trimmed#npm run dev}" \
                            "-- --host --strictPort --port --port=" "" || exit 1
                        approved=$((approved + 1))
                        ;;
                    'uv run rbt dev run' | 'uv run rbt dev run '*)
                        # `run` skill — start the Reboot backend.
                        in_reboot_project "$effective_dir" || exit 1
                        rbt_args_ok "${trimmed#uv run rbt dev run}" || exit 1
                        approved=$((approved + 1))
                        ;;
                    'uv run rbt dashboard' | 'uv run rbt dashboard '*)
                        # `dashboard` skill — start the developer
                        # dashboard while an app is being built.
                        in_reboot_project "$effective_dir" || exit 1
                        rbt_args_ok "${trimmed#uv run rbt dashboard}" || exit 1
                        approved=$((approved + 1))
                        ;;
                    'cloudflared tunnel '* )
                        # `run` skill — start the Cloudflare quick tunnel before `rbt dev run`.
                        in_reboot_project "$effective_dir" || exit 1
                        args="${trimmed#cloudflared tunnel }"
                        # Require exactly: --metrics localhost:<port> and --url http://localhost:<port> (either order).
                        # shellcheck disable=SC2086  # splitting into words is the point
                        set -- $args
                        [ "$#" -eq 4 ] || exit 1
                        if [ "$1" = "--metrics" ] && [ "$3" = "--url" ]; then
                            metrics="$2"; url="$4"
                        elif [ "$1" = "--url" ] && [ "$3" = "--metrics" ]; then
                            metrics="$4"; url="$2"
                        else
                            exit 1
                        fi
                        case "$metrics" in localhost:*) mport="${metrics#localhost:}" ;; *) exit 1 ;; esac
                        case "$url" in http://localhost:*) bport="${url#http://localhost:}" ;; *) exit 1 ;; esac
                        case "$mport" in ''|*[!0-9]*) exit 1 ;; esac
                        case "$bport" in ''|*[!0-9]*) exit 1 ;; esac
                        approved=$((approved + 1))
                        ;;
                    'npx @mcpjam/inspector@'* | mcpjam-inspector | 'mcpjam-inspector '*)
                        # `run` skill — MCPJam inspector for MCP UIs, via
                        # the plugin's `mcpjam-inspector` shim or a pinned
                        # `npx @mcpjam/inspector@<version>`; only the
                        # `--url`, `--oauth` and `--no-open` arguments.
                        in_reboot_project "$effective_dir" || exit 1
                        program="${trimmed%% *}"
                        case "$program" in
                            'npx')
                                package="${trimmed#npx }"; package="${package%% *}"
                                version="${package#@mcpjam/inspector@}"
                                case "$version" in ''|*[!0-9.]*) exit 1 ;; esac
                                rest="${trimmed#npx "$package"}"
                                ;;
                            *) rest="${trimmed#mcpjam-inspector}" ;;
                        esac
                        mcpjam_args_ok "$rest" || exit 1
                        approved=$((approved + 1))
                        ;;
                    *)
                        exit 1
                        ;;
                esac
            done
            [ "$approved" -gt 0 ]
        ) && emit_allow
        ;;
esac

# Always exit 0: this hook either emits an "allow" decision JSON or
# silently defers to the normal permission prompt. A non-zero status
# would surface as a "PreToolUse hook error" in Claude Code, even
# though the intent is just "no decision". Several branches above can
# fall through with a non-zero last-command status (e.g. `is_in_plugin
# … && emit_allow` when the path is not in the plugin, or the Bash
# subshell exiting 1 to signal "did not match the allowlist"); this
# normalizes all of those to a clean defer.
exit 0
