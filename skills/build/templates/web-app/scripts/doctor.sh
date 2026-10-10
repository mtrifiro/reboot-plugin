#!/usr/bin/env sh
# Rules out the local causes that look exactly like a framework flake
# (the Reboot plugin's findings P3.169, P3.39, P3.156, P3.73, A.14)
# before anyone blames Reboot. Run it when a scenario fails for no
# reason you can see, a run hangs, or the app will not start:
#
#   scripts/doctor.sh
#
# It reports, and exits 1 when it found something; it never kills.
#
# - processes of this project left behind by an earlier session (parent
#   pid 1): the app's main.py, its Envoy, a dashboard, Vite;
# - the application's state lock (RocksDB LOCK) and who holds it;
# - a test run in progress (tests/.suite-running) or two at once;
# - the sign-in allowlist variables in this shell (ALLOWED_EMAILS,
#   ALLOWED_EMAIL_DOMAINS), which change what the scenarios see;
# - who serves this project's ports, and from which directory: another
#   project's backend or dashboard answering on them, or two listeners
#   (one per IP stack) that are not the same process.

set -eu
cd "$(dirname -- "$0")/.."
root="$(pwd -P)"
found=0

say() {
  found=1
  printf 'doctor: %s\n' "$1"
}

app="$(sed -n 's/^dev run --application-name=//p' .rbtrc 2>/dev/null | head -n 1)"

# Processes of this project reparented to pid 1 (their session is gone).
ps -axww -o pid=,ppid=,etime=,command= | awk -v root="$root" '
  $2 == 1 && index($0, root "/") { print }
  $2 == 1 && /\/plugins\/data\/reboot\/bin\/envoy-/ { print }
' | while IFS= read -r line; do
  say "left behind by an earlier session (parent pid 1): $line"
done | tee /tmp/doctor.$$ >/dev/null
[ ! -s /tmp/doctor.$$ ] || { found=1; cat /tmp/doctor.$$; }
rm -f /tmp/doctor.$$

# The state lock.
if [ -n "$app" ] && command -v lsof >/dev/null 2>&1; then
  for lock in ".rbt/dev/$app"/*/LOCK; do
    [ -f "$lock" ] || continue
    pid="$(lsof -t -- "$lock" 2>/dev/null | head -n 1 || true)"
    if [ -n "$pid" ]; then
      say "the state lock $lock is held by pid $pid ($(ps -o command= -p "$pid" 2>/dev/null)); a second rbt dev run or an expunge now crash-loops"
    fi
  done
fi

# A suite in progress.
if [ -f tests/.suite-running ]; then
  pid="$(sed -n 's/.*"pid": *\([0-9]*\).*/\1/p' tests/.suite-running | head -n 1)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    say "a test run is in progress (pid $pid); regenerating, restarting or editing code now fails its scenarios with Method not found!"
  fi
fi
if command -v lsof >/dev/null 2>&1; then
  suites=0
  for pid in $(ps -axww -o pid=,command= | awk '/[p]ytest/ { print $1 }'); do
    cwd="$(lsof -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1)"
    [ "$cwd" = "$root" ] && suites=$((suites + 1))
  done
  if [ "$suites" -gt 1 ]; then
    say "$suites pytest processes are running in this project; two suites in one directory deadlock on a singleton (PRESUMED_DEADLOCK)"
  fi
fi

# Allowlist variables.
for var in ALLOWED_EMAILS ALLOWED_EMAIL_DOMAINS; do
  if [ -n "$(printenv "$var" 2>/dev/null || true)" ]; then
    say "$var is set in this shell; the scenarios run with it (run them under env -u $var)"
  fi
done

# Ports: who answers, and from where.
ports="$(sed -n 's/^dev run --port=\([0-9]*\).*/\1/p; s/^dashboard --port=\([0-9]*\).*/\1/p' .rbtrc 2>/dev/null | sort -u)"
for config in web/vite.config.ts frontend/vite.config.ts; do
  [ -f "$config" ] || continue
  ports="$ports $(sed -n 's/.*port: \([0-9][0-9]*\).*/\1/p; s/.*"\([0-9][0-9]*\)".*RBT_VITE_PORT.*/\1/p; s/.*RBT_VITE_PORT || "\([0-9]*\)".*/\1/p' "$config" | head -n 1)"
done
if command -v lsof >/dev/null 2>&1; then
  for port in $ports; do
    pids="$(lsof -nP -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sort -u || true)"
    [ -n "$pids" ] || continue
    if [ "$(printf '%s\n' "$pids" | wc -l)" -gt 1 ]; then
      say "port $port has more than one listener ($(printf '%s' "$pids" | tr '\n' ' ')): one per IP stack, so localhost may reach either"
    fi
    for pid in $pids; do
      cwd="$(lsof -a -d cwd -p "$pid" -Fn 2>/dev/null | sed -n 's/^n//p' | head -n 1)"
      if [ -n "$cwd" ] && [ "$cwd" != "$root" ]; then
        say "port $port is served by pid $pid from $cwd, not this project ($(ps -o command= -p "$pid" 2>/dev/null))"
      fi
    done
  done
fi

if [ "$found" = 0 ]; then
  echo "doctor: nothing found; the cause is not one of the usual local ones"
  exit 0
fi
exit 1
