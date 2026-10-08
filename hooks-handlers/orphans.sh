#!/usr/bin/env sh
# SessionStart hook: tell the model about Reboot dashboards an earlier
# session left behind, so it can offer the developer to stop them.
#
# `rbt dashboard` runs its backend as `python -m
# reboot.dashboard.backend.main`, which starts Envoy (serving the
# dashboard port) and a worker process. When the shell that ran
# `rbt dashboard` goes away — a session closed, a terminal quit — the
# backend is not taken down with it: it is reparented to launchd/init
# (ppid 1) and keeps running, worker and Envoy included, no longer
# reachable by whatever started it. A new session then starts another
# one, and they pile up (reboot-crm, 1.6.0: three of them, ~1.5 GB,
# each worker at ~67% CPU).
#
# This handler only reports; it never kills. A dashboard the developer
# started on purpose from a terminal they then closed looks the same,
# so the decision stays with them. It reports a backend when:
#
#   - its parent is pid 1 (whoever started it has exited), and
#   - it has been running for at least `min_age` seconds, so one a
#     parallel session is just starting is left alone.
#
# Unlike `remind.sh`, this is not gated on a `.rbtrc`: orphans from any
# project cost the same wherever the session starts. When there is
# nothing to report it prints nothing.

set -eu

# The hook input on stdin carries the event name; SessionStart is the
# only event this is registered for, so it is read and discarded.
cat >/dev/null

# One hour; overridable for testing.
min_age=${REBOOT_ORPHAN_MIN_AGE:-3600}

# `ps -o etime` prints `[[dd-]hh:]mm:ss`; convert it to seconds.
etime_seconds() {
    printf '%s\n' "$1" | awk -F'[-:]' '{
        n = NF; s = $n + 60 * $(n - 1)
        if (n >= 3) s += 3600 * $(n - 2)
        if (n >= 4) s += 86400 * $(n - 3)
        print s
    }'
}

# The backend's project is its working directory: `rbt dashboard` runs
# from the project root. `lsof` is on macOS and most Linux installs;
# without it the project is reported as unknown.
project_of() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1
    fi
}

# The worker, Envoy and any other children of a backend, as a
# space-separated list.
children_of() {
    ps -axo pid=,ppid= | awk -v p="$1" '$2 == p { printf "%s ", $1 }'
}

# Resident memory in KB of a pid and its children.
rss_kb() {
    ps -o rss= -p "$(printf '%s' "$*" | tr ' ' ',' | sed 's/,$//')" 2>/dev/null |
        awk '{ s += $1 } END { print s + 0 }'
}

# CPU percent of a pid and its children.
cpu_pct() {
    ps -o %cpu= -p "$(printf '%s' "$*" | tr ' ' ',' | sed 's/,$//')" 2>/dev/null |
        awk '{ s += $1 } END { printf "%.0f", s }'
}

lines=""
count=0
# `-ww` keeps the command line untruncated so the module name matches.
for row in $(ps -axww -o pid=,ppid=,etime=,command= |
    awk '$2 == 1 && $0 ~ /-m reboot\.dashboard\.backend\.main/ { print $1 "," $3 }')
do
    pid=${row%%,*}
    age=$(etime_seconds "${row#*,}")
    [ "$age" -ge "$min_age" ] || continue

    pids="$pid $(children_of "$pid")"
    project=$(project_of "$pid")
    hours=$(awk -v s="$age" 'BEGIN { printf "%.1f", s / 3600 }')
    mb=$(( $(rss_kb $pids) / 1024 ))
    lines="${lines}- ${project:-unknown project}: pids ${pids% } (kill ${pid} first), up ${hours}h, ${mb} MB, $(cpu_pct $pids)% CPU\\n"
    count=$((count + 1))
done

# Processes orphaned on their own: SIGTERM to a backend stops it but
# not its worker or Envoy (1.6.0), which keep their memory and ports.
# Workers run `.../reboot/dashboard/backend/main.py`; Envoy is matched
# by the plugin's own `envoy` shim path only, so an Envoy the developer
# runs for something else is never reported.
strays=$(ps -axww -o pid=,ppid=,command= | awk '$2 == 1 &&
    ($0 ~ /reboot\/dashboard\/backend\/main\.py/ ||
     $3 ~ /\/plugins\/data\/reboot\/bin\/envoy-/) { printf "%s ", $1 }')
if [ -n "$strays" ]; then
    lines="${lines}- leftover workers/Envoy whose dashboard is gone: pids ${strays% }, $(( $(rss_kb $strays) / 1024 )) MB, $(cpu_pct $strays)% CPU\\n"
    count=$((count + 1))
fi

[ "$count" -gt 0 ] || exit 0

# JSON-encoding needs no escaping beyond the `\n`s above: project
# paths with a double quote or backslash are not worth the code.
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"'
printf '[reboot-plugin-orphans] %s group(s) of Reboot dashboard processes from earlier sessions are still running, orphaned (parent pid 1):\\n' "$count"
printf '%s' "$lines"
printf 'Tell the developer about them in one or two lines, and offer to stop them. Do not stop them unless the developer says yes. To stop one, kill its first pid (SIGTERM), wait a few seconds, then kill whichever of the others are still running.'
printf '"}}\n'
