#!/usr/bin/env sh
#
# Record which agent session owns a long-running dev process, so the
# SessionStart `orphans.sh` hook can tell a process a live session is
# still using from one whose session has exited.
#
#   own.sh <pid> <shim> <args...>
#
# Called by the `uv`, `rbt`, `npm`, `cloudflared` and `mcpjam-inspector`
# shims with their own pid, just before they `exec`: the pid is kept
# across the `exec`, so it is the pid of the dev process itself. Only
# the commands that keep running are recorded: `rbt dev run`,
# `rbt dashboard`, `npm run dev`, `cloudflared tunnel` and the MCPJam
# inspector. Anything else returns at once.
#
# The owner is `$CLAUDE_PID`, the Claude Code process every Bash tool
# call runs under. Without it (Codex, a developer's own terminal)
# nothing is recorded, and `orphans.sh` falls back to its age rule.
#
# One file per recorded pid, under `$REBOOT_OWNERS_DIR` (default: the
# plugin's data dir, which the hooks and the shims share). Each start
# time is stored beside its pid, so a reused pid never reads as the
# same process. `orphans.sh` deletes a record once its pid is gone.
#
# Never fails the shim: every error is swallowed, and the shims call
# this with `|| true`.

[ -n "${CLAUDE_PID:-}" ] || exit 0
[ "$#" -ge 2 ] || exit 0

pid=$1
shim=$2
shift 2

# Is this a long-running dev command?
case "$shim" in
    uv | rbt)
        # `rbt dev run …` or `rbt dashboard …`. Through `uv`, skip
        # `run` and its options up to `rbt` (`uv run --project <dir>
        # rbt dev run`); the `rbt` shim gets the subcommand directly.
        if [ "$shim" = uv ]; then
            while [ "$#" -gt 0 ] && [ "$1" != rbt ]; do shift; done
            [ "$#" -gt 0 ] || exit 0
            shift
        fi
        case "${1:-} ${2:-}" in
            "dev run") kind=app ;;
            "dashboard "*) kind=dashboard ;;
            *) exit 0 ;;
        esac
        ;;
    npm)
        case "${1:-} ${2:-}" in
            "run dev" | "run-script dev") kind=frontend ;;
            *) exit 0 ;;
        esac
        ;;
    cloudflared)
        [ "${1:-}" = tunnel ] || exit 0
        kind=tunnel
        ;;
    mcpjam-inspector)
        kind=MCPJam
        ;;
    *)
        exit 0
        ;;
esac

dir=${REBOOT_OWNERS_DIR:-$HOME/.claude/plugins/data/reboot/owners}
mkdir -p "$dir" 2>/dev/null || exit 0

started=$(ps -o lstart= -p "$pid" 2>/dev/null) || exit 0
owner_started=$(ps -o lstart= -p "$CLAUDE_PID" 2>/dev/null) || exit 0
[ -n "$started" ] && [ -n "$owner_started" ] || exit 0

# Written whole, then renamed, so the hook never reads half a record.
tmp="$dir/.$pid.$$"
{
    printf 'pid=%s\n' "$pid"
    printf 'started=%s\n' "$started"
    printf 'owner=%s\n' "$CLAUDE_PID"
    printf 'owner_started=%s\n' "$owner_started"
    printf 'session=%s\n' "${CLAUDE_CODE_SESSION_ID:-}"
    printf 'kind=%s\n' "$kind"
    printf 'cwd=%s\n' "$PWD"
} >"$tmp" 2>/dev/null && mv -f "$tmp" "$dir/$pid" 2>/dev/null
rm -f "$tmp" 2>/dev/null
exit 0
