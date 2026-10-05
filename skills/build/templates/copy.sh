#!/usr/bin/env sh
#
# Copy a front-door template into a new project directory and fill in
# its placeholders. See README.md next to this script.
#
#   copy.sh <mcp-ui|web-app> <dest-dir> <project> <app> "<Title>"
#
#   <project>  kebab-case project name  (e.g. todo-list)  -> __project__
#   <app>      snake_case API package   (e.g. todo_list)  -> __app__
#   <Title>    human-readable title     (e.g. Todo List)  -> __Title__
#
# Refuses to write into a directory that already has an `.rbtrc`.

set -eu

if [ "$#" -ne 5 ]; then
  echo "usage: $0 <mcp-ui|web-app> <dest-dir> <project> <app> \"<Title>\"" >&2
  exit 2
fi

FRONT_DOOR="$1"
DEST="$2"
PROJECT="$3"
APP="$4"
TITLE="$5"

TEMPLATES="$(cd "$(dirname -- "$0")" && pwd)"
SRC="$TEMPLATES/$FRONT_DOOR"

if [ ! -d "$SRC" ]; then
  echo "unknown front door '$FRONT_DOOR' (expected mcp-ui or web-app)" >&2
  exit 2
fi
case "$PROJECT" in
  *[!a-z0-9-]*|"") echo "<project> must be kebab-case: $PROJECT" >&2; exit 2 ;;
esac
case "$APP" in
  [!a-z]*|*[!a-z0-9_]*|"") echo "<app> must be a snake_case identifier: $APP" >&2; exit 2 ;;
esac
if [ -e "$DEST/.rbtrc" ]; then
  echo "$DEST already has an .rbtrc; not overwriting" >&2
  exit 1
fi

mkdir -p "$DEST"
# `/.` copies dotfiles (.rbtrc, .gitignore, ...) too.
cp -R "$SRC/." "$DEST/"
find "$DEST" -name .DS_Store -delete

# Rename paths containing `__app__`, deepest first.
find "$DEST" -depth -name '*__app__*' | while IFS= read -r path; do
  dir="$(dirname -- "$path")"
  base="$(basename -- "$path")"
  new="$(printf '%s' "$base" | sed "s/__app__/$APP/g")"
  mv "$path" "$dir/$new"
done

# Fill placeholders in file contents. Values go through the
# environment so a title with spaces or punctuation needs no escaping.
find "$DEST" -type f ! -path '*/node_modules/*' -print | while IFS= read -r file; do
  if grep -q '__project__\|__app__\|__Title__' "$file"; then
    T_PROJECT="$PROJECT" T_APP="$APP" T_TITLE="$TITLE" perl -pi -e \
      's/__project__/$ENV{T_PROJECT}/g; s/__app__/$ENV{T_APP}/g; s/__Title__/$ENV{T_TITLE}/g' \
      "$file"
  fi
done

echo "Copied $FRONT_DOOR template to $DEST"
