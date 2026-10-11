#!/usr/bin/env sh
# SessionStart hook: tell the model about Reboot dev processes an
# earlier session left running, so it can offer the developer to stop
# them.
#
# Every long-running dev process the skills start outlives the session
# that started it: the app (`rbt dev run`, its `main.py`s and Envoy),
# the dashboard (`rbt dashboard`, its backend, worker and Envoy), the
# frontend dev server (Vite), the tunnel and the MCPJam inspector. When
# the agent exits, the Bash tool's shell running each one is reparented
# to launchd/init (pid 1) and keeps it alive, unreachable by whatever
# started it. A new session starts another, and they pile up
# (reboot-crm, 1.6.0: three dashboards, ~1.5 GB, each worker at ~67%
# CPU; plugin-browser: a dashboard for 20 hours, an app and Vite).
#
# Such a process is reported as part of a group: its topmost ancestor
# below pid 1 and everything under it, so one line covers the shell, the
# `uv` and `rbt` wrappers and every child. A process belongs to a live
# owner, and is left alone, when walking up from it reaches anything
# that is not a launcher (`sh -c`, `uv`, `rbt`, Python, Node, npm,
# Envoy…): the `claude` process, an interactive shell in a terminal, a
# tmux server.
#
# Ownership records settle the rest. The plugin's `uv`, `rbt`, `npm`,
# `cloudflared` and `mcpjam-inspector` shims record each long-running
# command's pid with the Claude Code process that started it
# (`lib/own.sh`). A group holding a record is reported as soon as that
# owner has exited, and never while it is alive, even when the command
# was detached (`nohup`, `&`). When a recorded `rbt dev run` or `rbt
# dashboard` has itself exited, what it started (its `main.py`s, Envoy,
# the dashboard's backend) can survive it under pid 1, in its process
# group; those are reported at once, and the record is kept until none
# is left. A group with no record (started by hand,
# by Codex, or before the shims kept records) is reported once its top
# has run under pid 1 for at least `min_age` seconds, so one a parallel
# session is just starting is left alone.
#
# This handler only reports; it never kills. Unlike `remind.sh`, it is
# not gated on a `.rbtrc`: orphans from any project cost the same
# wherever the session starts. When there is nothing to report it
# prints nothing.

set -eu

# The hook input on stdin carries the event name; SessionStart is the
# only event this is registered for, so it is read and discarded.
cat >/dev/null

# One hour; overridable for testing.
min_age=${REBOOT_ORPHAN_MIN_AGE:-3600}
# Where `lib/own.sh` writes; overridable for testing.
owners=${REBOOT_OWNERS_DIR:-$HOME/.claude/plugins/data/reboot/owners}

# Each live record as `pid alive session kind`, where `alive` is 1
# while its owner runs. A record whose pid is gone, or now names another
# process (a different start time), is deleted, except an app's or a
# dashboard's: that one goes to `gone` as `pid<TAB>kind<TAB>pgid<TAB>cwd`,
# and is deleted below once nothing it started is left.
records=""
gone=""
gone_pids=""
if [ -d "$owners" ]; then
    for f in "$owners"/*; do
        [ -f "$f" ] || continue
        pid="" started="" owner="" owner_started="" session="" kind="" pgid="" cwd=""
        while IFS='=' read -r key value; do
            case "$key" in
                pid) pid=$value ;;
                started) started=$value ;;
                owner) owner=$value ;;
                owner_started) owner_started=$value ;;
                session) session=$value ;;
                kind) kind=$value ;;
                pgid) pgid=$value ;;
                cwd) cwd=$value ;;
            esac
        done <"$f"
        now=""
        [ -n "$pid" ] && now=$(ps -o lstart= -p "$pid" 2>/dev/null || true)
        if [ -z "$now" ] || [ "$now" != "$started" ]; then
            case "$kind" in
                app | dashboard)
                    if [ -n "$pgid$cwd" ] && [ "$f" = "$owners/$pid" ]; then
                        gone="${gone}${pid}\\t${kind}\\t${pgid:--}\\t${cwd}\\n"
                        gone_pids="$gone_pids $pid"
                        continue
                    fi
                    ;;
            esac
            rm -f "$f"
            continue
        fi
        alive=0
        if [ -n "$owner" ] &&
            [ "$(ps -o lstart= -p "$owner" 2>/dev/null || true)" = "$owner_started" ]
        then
            alive=1
        fi
        records="${records}${pid} ${alive} ${session:--} ${kind:--}\\n"
    done
fi

# One line per orphaned group: `top|age|session|pids|rss_kb|cpu|what|rbt`,
# where `rbt` is the pid of the exited `rbt` a group survived, if any.
# `-ww` keeps command lines untruncated so the patterns match. Only
# this user's processes are considered (the `uid` column): another
# user's are not ours to report or stop.
groups=$(ps -axww -o pid=,ppid=,uid=,pgid=,etime=,rss=,%cpu=,command= | awk \
    -v records="$records" -v gone="$gone" -v min_age="$min_age" -v me="$(id -u)" '
    # `[[dd-]hh:]mm:ss` to seconds.
    function seconds(t,    n, f, s) {
        n = split(t, f, /[-:]/)
        s = f[n] + 60 * f[n - 1]
        if (n >= 3) s += 3600 * f[n - 2]
        if (n >= 4) s += 86400 * f[n - 3]
        return s
    }
    function base(p,    a) {
        a = cmd[p]
        sub(/ .*/, "", a)
        sub(/.*\//, "", a)
        return a
    }
    # A process that only exists to run the one below it.
    function launcher(p,    a) {
        a = base(p)
        if (a ~ /^(sh|bash|zsh|dash)$/) return cmd[p] ~ / -c /
        return a ~ /^(uv|uvx|rbt|npm|npx|node|esbuild|vite|cloudflared)$/ ||
            a ~ /^python[0-9.]*$/ || a ~ /^envoy/
    }
    # A Reboot project root, from a path inside it. The path comes from
    # a command line, i.e. untrusted text, so it never reaches a shell:
    # `.rbtrc` is tested by opening it from awk (getline returns -1 when
    # it cannot be opened; an empty file reads 0).
    function in_project(path,    d, i, f, r) {
        d = path
        for (i = 0; i < 3 && d != ""; i++) {
            f = d "/.rbtrc"
            r = (getline line < f)
            close(f)
            if (r >= 0) return 1
            sub(/\/[^\/]*$/, "", d)
        }
        return 0
    }
    # What a process is, for the report; "" when not Reboot dev.
    function what(p,    c, m) {
        c = cmd[p]
        if (c ~ /-m reboot\.dashboard\.backend\.main|reboot\/dashboard\/backend\/main\.py/) return "dashboard"
        if (c ~ /\/rbt dashboard( |$)/) return "dashboard"
        if (c ~ /langserver\.index\.js/) return "dashboard pyright"
        if (c ~ /\/rbt dev run( |$)/) return "app"
        if (c ~ /\/plugins\/data\/reboot\/bin\/envoy-/) return "Envoy"
        if (c ~ /\/plugins\/data\/reboot\/bin\/cloudflared-/) return "tunnel"
        if (c ~ /@mcpjam\/inspector/) return "MCPJam"
        if (p in kind && kind[p] != "-") return kind[p]
        if (match(c, /[^ ]*\/backend\/src\/main\.py/)) {
            m = substr(c, RSTART, RLENGTH - length("/backend/src/main.py"))
            if (in_project(m)) return "app"
        }
        if (match(c, /[^ ]*\/node_modules\/(\.bin\/vite|vite\/bin\/vite\.js)/)) {
            m = substr(c, RSTART, RLENGTH)
            sub(/\/node_modules\/.*/, "", m)
            if (in_project(m)) return "frontend"
        }
        return ""
    }
    # Whether a process of this kind is something a recorded command
    # of `rkind` starts.
    function started_by(rkind, k) {
        if (rkind == "app") return k == "app" || k == "Envoy"
        return k == "dashboard" || k == "dashboard pyright" || k == "Envoy"
    }
    # Add `p` and everything under it to the group being built.
    function gather(p,    head, tail, x, m, j, ch, queue) {
        queue[1] = p; head = 1; tail = 1
        while (head <= tail) {
            x = queue[head++]
            if (x in taken) continue
            taken[x] = 1
            pids = pids (pids == "" ? "" : " ") x
            mem += rss[x]; load += cpu[x]
            k = what(x)
            if (k != "" && index(" " kinds ",", " " k ",") == 0)
                kinds = kinds (kinds == "" ? "" : " ") k ","
            m = split(kids[x], ch, / /)
            for (j = 1; j <= m; j++) if (ch[j] != "") queue[++tail] = ch[j]
        }
    }
    BEGIN {
        n = split(records, rows, /\n/)
        for (i = 1; i <= n; i++) {
            if (split(rows[i], r, / /) == 4) {
                owned[r[1]] = r[2]; sess[r[1]] = r[3]; kind[r[1]] = r[4]
            }
        }
    }
    $3 != me { next }
    {
        pid = $1
        ppid[pid] = $2; pgid[pid] = $4; etime[pid] = $5; rss[pid] = $6; cpu[pid] = $7
        c = $0
        sub(/^ *[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[^ ]+ +[0-9]+ +[0-9.,]+ +/, "", c)
        cmd[pid] = c
        kids[$2] = kids[$2] " " pid
        order[++count] = pid
    }
    END {
        # What an exited rbt left: processes of its group (or, in a
        # record with no group, naming its project) that it starts,
        # now under pid 1. Reported at once.
        ng = split(gone, grows, /\n/)
        for (gi = 1; gi <= ng; gi++) {
            if (split(grows[gi], g, /\t/) < 4) continue
            pids = ""; mem = 0; load = 0; kinds = ""; age = 0; top = ""
            for (i = 1; i <= count; i++) {
                p = order[i]
                if (p in taken) continue
                if (g[3] != "-") { if (pgid[p] != g[3]) continue }
                else if (g[4] == "" || index(cmd[p], g[4] "/") == 0) continue
                if (!started_by(g[2], what(p))) continue
                par = ppid[p]
                if (par != 1 && cmd[par] !~ /(^|\/)systemd( |$)/) continue
                if (top == "") top = p
                if (seconds(etime[p]) > age) age = seconds(etime[p])
                seen[p] = 1
                gather(p)
            }
            if (top == "") continue
            sub(/,$/, "", kinds)
            printf "%s|%d|%s|%s|%d|%.0f|%s|%s\n", top, age, "", pids, mem, load, kinds, g[1]
        }

        for (i = 1; i <= count; i++) {
            p = order[i]
            if (p in taken) continue
            if (!(p in owned) && what(p) == "") continue
            # Walk up to the topmost ancestor below pid 1, or to a live
            # owner.
            q = p; top = ""; session = ""; dead = 0
            while (1) {
                if (q in owned) {
                    if (owned[q] == 1) break
                    dead = 1; session = sess[q]
                }
                if (!launcher(q)) break
                par = ppid[q]
                if (par == 1 || cmd[par] ~ /(^|\/)systemd( |$)/) { top = q; break }
                if (!(par in ppid)) break
                q = par
            }
            if (top == "" || (top in seen)) continue
            seen[top] = 1
            age = seconds(etime[top])
            if (!dead && age < min_age) continue

            # The group: the top and everything under it.
            pids = ""; mem = 0; load = 0; kinds = ""
            gather(top)
            sub(/,$/, "", kinds)
            printf "%s|%d|%s|%s|%d|%.0f|%s|\n", top, age, (dead ? session : ""), pids, mem, load, kinds
        }
    }')

# A gone record is kept while something it started is reported.
for pid in $gone_pids; do
    case "
$groups" in
        *"|$pid
"* | *"|$pid") ;;
        *) rm -f "$owners/$pid" ;;
    esac
done

[ -n "$groups" ] || exit 0

# The group's project is its top process's working directory: the
# skills start everything from the project root. `lsof` is on macOS
# and most Linux installs; without it the project is reported unknown.
project_of() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
    fi
}

lines=""
count=0
old_ifs=$IFS
IFS='
'
for group in $groups; do
    IFS='|' read -r top age session pids rss cpu kinds rbt <<EOF
$group
EOF
    project=$(project_of "$top")
    if [ "$age" -ge 3600 ]; then
        up=$(awk -v s="$age" 'BEGIN { printf "%.1fh", s / 3600 }')
    else
        up="$((age / 60)) min"
    fi
    if [ -n "$rbt" ]; then
        why="its rbt (pid ${rbt}) has exited"
    elif [ -n "$session" ]; then
        why="its session ${session} has exited"
    else
        why="no record of its session; its parent has exited"
    fi
    lines="${lines}- ${project:-unknown project} (${kinds:-processes}): pids ${pids}, up ${up}, $((rss / 1024)) MB, ${cpu}% CPU; ${why}\\n"
    count=$((count + 1))
done
IFS=$old_ifs

# JSON-encoding needs no escaping beyond the `\n`s above: project
# paths with a double quote or backslash are not worth the code.
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"'
printf '[reboot-plugin-orphans] %s group(s) of Reboot dev processes from earlier sessions are still running:\\n' "$count"
printf '%s' "$lines"
printf 'Tell the developer about them in one or two lines, and offer to stop them. Do not stop them unless the developer says yes. To stop a group, kill every pid listed for it (SIGTERM), wait a few seconds, then kill -9 whichever are still running.'
printf '"}}\n'
