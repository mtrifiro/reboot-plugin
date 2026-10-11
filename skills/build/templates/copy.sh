#!/usr/bin/env sh
#
# Copy a front-door template into a new project directory and fill in
# its placeholders. See README.md next to this script.
#
#   copy.sh [--merge] <mcp-ui|web-app|both> <dest-dir> <project> <app> "<Title>"
#   copy.sh --ports <project>
#
#   <project>  kebab-case project name  (e.g. todo-list)  -> __project__
#   <app>      snake_case API package   (e.g. todo_list)  -> __app__
#   <Title>    human-readable title     (e.g. Todo List)  -> __Title__
#              and its first letter, capitalized (T)     -> __Initial__
#
# Without `--merge`, refuses to write into a directory that already has
# an `.rbtrc`. With `--merge`, the build flow's Step 2: the project
# already has its API file (Step 1) and the dashboard's stub `.rbtrc`,
# `pyproject.toml` and `.python-version`. Every file the project has is
# kept (and listed), except those three stubs, which the template's
# versions replace.
#
# Ports: every project gets a backend, dashboard and Vite port of its
# own, written into `.rbtrc`, the Vite config, `.env.development` and
# `scripts/screenshots.py`. The set starts from a hash of the project
# name, so two projects on one machine rarely meet, and moves on to
# the next set when one of its ports is held, so two copies of one
# project don't either. `--merge` keeps a backend or dashboard port the
# project's `.rbtrc` already names (the dashboard may be running on
# it). `--ports <project>` prints the set the dashboard skill should
# start on, before the scaffold exists. `REBOOT_PORTS="<backend>
# <dashboard> <vite>"` overrides the choice.

set -eu

TEMPLATES="$(cd "$(dirname -- "$0")" && pwd)"

# The project's ports: "<backend> <dashboard> <vite>". $2..$4 fix a
# port already chosen ("-" for none). Without python3 (or with every
# set held) the framework's defaults are used, as before.
choose_ports() {
  if [ -n "${REBOOT_PORTS:-}" ]; then
    echo "$REBOOT_PORTS"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "9991 9871 5273"
    return 0
  fi
  python3 - "$1" "${2:--}" "${3:--}" "${4:--}" <<'EOF'
import errno
import socket
import sys
import zlib

name, fixed = sys.argv[1], sys.argv[2:5]
start = zlib.crc32(name.encode()) % 80


def free(port):
    # Both stacks: a listener on `0.0.0.0` or `[::]` (gRPC's dual-stack
    # bind) shows on either, and only an address in use counts as held.
    for family, host in ((socket.AF_INET, "127.0.0.1"), (socket.AF_INET6, "::1")):
        sock = socket.socket(family, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
        except OSError as error:
            if error.errno == errno.EADDRINUSE:
                return False
        finally:
            sock.close()
    return True


for i in range(80):
    j = (start + i) % 80
    chosen = [9900 + j, 9800 + j, 5300 + j]
    ports = [int(f) if f != "-" else c for f, c in zip(fixed, chosen)]
    if all(f != "-" or free(p) for f, p in zip(fixed, ports)):
        print(*ports)
        break
else:
    print(9991, 9871, 5273)
EOF
}

if [ "${1:-}" = "--ports" ]; then
  if [ "$#" -ne 2 ]; then
    echo "usage: $0 --ports <project>" >&2
    exit 2
  fi
  choose_ports "$2"
  exit 0
fi

MERGE=0
if [ "${1:-}" = "--merge" ]; then
  MERGE=1
  shift
fi

if [ "$#" -ne 5 ]; then
  echo "usage: $0 [--merge] <mcp-ui|web-app|both> <dest-dir> <project> <app> \"<Title>\"" >&2
  echo "       $0 --ports <project>" >&2
  exit 2
fi

FRONT_DOOR="$1"
DEST="$2"
PROJECT="$3"
APP="$4"
TITLE="$5"
# The title's first character, upper-cased (Unicode-aware), for the
# placeholder favicon.
INITIAL="$(perl -CSA -e 'print uc substr($ARGV[0], 0, 1)' "$TITLE")"

SRC="$TEMPLATES/$FRONT_DOOR"

if [ ! -d "$SRC" ]; then
  echo "unknown front door '$FRONT_DOOR' (expected mcp-ui, web-app or both)" >&2
  exit 2
fi
case "$PROJECT" in
  *[!a-z0-9-]*|"") echo "<project> must be kebab-case: $PROJECT" >&2; exit 2 ;;
esac
case "$APP" in
  [!a-z]*|*[!a-z0-9_]*|"") echo "<app> must be a snake_case identifier: $APP" >&2; exit 2 ;;
esac
if [ -e "$DEST/.rbtrc" ] && [ "$MERGE" = 0 ]; then
  echo "$DEST already has an .rbtrc; not overwriting (--merge keeps what is there)" >&2
  exit 1
fi

# Ports the project already chose (a merge: the dashboard skill's stub
# may name where its dashboard runs), kept; the rest chosen now.
HAVE_BACKEND="-"
HAVE_DASHBOARD="-"
if [ "$MERGE" = 1 ] && [ -f "$DEST/.rbtrc" ]; then
  HAVE_BACKEND="$(sed -n 's/^dev run --port=\([0-9]*\).*/\1/p' "$DEST/.rbtrc" | head -n 1)"
  HAVE_DASHBOARD="$(sed -n 's/^dashboard --port=\([0-9]*\).*/\1/p' "$DEST/.rbtrc" | head -n 1)"
  [ -n "$HAVE_DASHBOARD" ] ||
    HAVE_DASHBOARD="$(sed -n 's/^dev run --dashboard-port=\([0-9]*\).*/\1/p' "$DEST/.rbtrc" | head -n 1)"
  [ -n "$HAVE_BACKEND" ] || HAVE_BACKEND="-"
  [ -n "$HAVE_DASHBOARD" ] || HAVE_DASHBOARD="-"
fi
PORTS="$(choose_ports "$PROJECT" "$HAVE_BACKEND" "$HAVE_DASHBOARD" "-")"
BACKEND_PORT="${PORTS%% *}"
rest="${PORTS#* }"
DASHBOARD_PORT="${rest%% *}"
VITE_PORT="${rest#* }"

# Build and test leftovers a developer may have left in the template
# directory (git ignores them; a new project must not start with them).
JUNK_DIRS='-name __pycache__ -o -name .mypy_cache -o -name .pytest_cache -o -name .reboot -o -name node_modules -o -name .venv -o -name dist -o -name *.recordings'
JUNK_FILES='-name .DS_Store -o -name .last-run.json -o -name .suite-running'

mkdir -p "$DEST"
if [ "$MERGE" = 0 ]; then
  # `/.` copies dotfiles (.rbtrc, .gitignore, ...) too.
  cp -R "$SRC/." "$DEST/"
  # shellcheck disable=SC2086  # the expressions are lists of find predicates
  find "$DEST" \( $JUNK_DIRS \) -prune -exec rm -rf {} + 2>/dev/null
  # shellcheck disable=SC2086
  find "$DEST" \( $JUNK_FILES \) -type f -delete
else
  # File by file, with `__app__` already renamed in the destination
  # path so Step 1's API file is recognized as already there.
  # shellcheck disable=SC2086
  (cd "$SRC" && find . \( $JUNK_DIRS \) -prune -o -type f ! \( $JUNK_FILES \) -print) | while IFS= read -r rel; do
    rel="${rel#./}"
    target="$(printf '%s' "$rel" | sed "s/__app__/$APP/g")"
    if [ -e "$DEST/$target" ]; then
      case "$rel" in
        .rbtrc|pyproject.toml|.python-version) echo "replaced $target (the dashboard's stub)" ;;
        *) echo "kept $target"; continue ;;
      esac
    fi
    mkdir -p "$DEST/$(dirname -- "$target")"
    cp "$SRC/$rel" "$DEST/$target"
  done
fi

# Rename paths containing `__app__`, deepest first.
find "$DEST" -depth -name '*__app__*' | while IFS= read -r path; do
  dir="$(dirname -- "$path")"
  base="$(basename -- "$path")"
  new="$(printf '%s' "$base" | sed "s/__app__/$APP/g")"
  mv "$path" "$dir/$new"
done

# Fill placeholders in file contents. Values go through the
# environment so a title with spaces or punctuation needs no escaping.
find "$DEST" -type f ! -path '*/node_modules/*' ! -path '*/.venv/*' ! -path '*/.git/*' -print | while IFS= read -r file; do
  if grep -q '__project__\|__app__\|__Title__\|__Initial__' "$file"; then
    T_PROJECT="$PROJECT" T_APP="$APP" T_TITLE="$TITLE" T_INITIAL="$INITIAL" perl -pi -e \
      's/__project__/$ENV{T_PROJECT}/g; s/__app__/$ENV{T_APP}/g; s/__Title__/$ENV{T_TITLE}/g; s/__Initial__/$ENV{T_INITIAL}/g' \
      "$file"
  fi
done

# The project's ports, in place of the templates' defaults (the backend's
# 9991, the dashboard's 9871, Vite's 5273 for a web app and 4444 behind
# Envoy for an MCP UI). Only these files name a port.
for file in .rbtrc web/vite.config.ts frontend/vite.config.ts web/.env.development \
    frontend/web/.env.development scripts/screenshots.py; do
  [ -f "$DEST/$file" ] || continue
  T_B="$BACKEND_PORT" T_D="$DASHBOARD_PORT" T_V="$VITE_PORT" perl -pi -e '
    s/--port=9991\b/--port=$ENV{T_B}/g;
    s/localhost:9991\b/localhost:$ENV{T_B}/g;
    s/--dashboard-port=9871\b/--dashboard-port=$ENV{T_D}/g;
    s/^dashboard --port=9871\b/dashboard --port=$ENV{T_D}/;
    s/port: 5273\b/port: $ENV{T_V}/;
    s/localhost:5273\b/localhost:$ENV{T_V}/g;
    s/localhost:4444\b/localhost:$ENV{T_V}/g;
    s/"4444"/"$ENV{T_V}"/' "$DEST/$file"
done

# A repository runs the hooks in .githooks/ (the pre-push gate for a
# `main` workflow); a clone sets this itself (AGENTS.md).
if [ -d "$DEST/.githooks" ] && [ "$(git -C "$DEST" rev-parse --show-toplevel 2>/dev/null || true)" = "$(cd "$DEST" && pwd -P)" ]; then
  git -C "$DEST" config core.hooksPath .githooks
fi

if [ "$MERGE" = 1 ]; then
  echo "Merged $FRONT_DOOR template into $DEST"
else
  echo "Copied $FRONT_DOOR template to $DEST"
fi
echo "Ports: backend $BACKEND_PORT, dashboard $DASHBOARD_PORT, Vite $VITE_PORT"
