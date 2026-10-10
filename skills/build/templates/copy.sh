#!/usr/bin/env sh
#
# Copy a front-door template into a new project directory and fill in
# its placeholders. See README.md next to this script.
#
#   copy.sh [--merge] <mcp-ui|web-app|both> <dest-dir> <project> <app> "<Title>"
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

set -eu

MERGE=0
if [ "${1:-}" = "--merge" ]; then
  MERGE=1
  shift
fi

if [ "$#" -ne 5 ]; then
  echo "usage: $0 [--merge] <mcp-ui|web-app|both> <dest-dir> <project> <app> \"<Title>\"" >&2
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

TEMPLATES="$(cd "$(dirname -- "$0")" && pwd)"
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

mkdir -p "$DEST"
if [ "$MERGE" = 0 ]; then
  # `/.` copies dotfiles (.rbtrc, .gitignore, ...) too.
  cp -R "$SRC/." "$DEST/"
  find "$DEST" -name .DS_Store -delete
else
  # File by file, with `__app__` already renamed in the destination
  # path so Step 1's API file is recognized as already there.
  (cd "$SRC" && find . -type f ! -name .DS_Store) | while IFS= read -r rel; do
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

if [ "$MERGE" = 1 ]; then
  echo "Merged $FRONT_DOOR template into $DEST"
else
  echo "Copied $FRONT_DOOR template to $DEST"
fi
