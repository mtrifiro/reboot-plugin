#!/usr/bin/env sh
# Package the plugin for the Claude app (Cowork), which installs a plugin
# from a `.plugin` file: a zip of the plugin directory in the same layout
# Claude Code reads (`.claude-plugin/plugin.json`, `skills/`, `hooks/`).
#
#   tools/package-plugin.sh [<out.plugin>]     # default: ~/Downloads/reboot.plugin
#
# Packages the committed tree at HEAD (`git archive`), never the working
# tree, so the file matches what `claude plugin update` installs: the
# manifest, the skills with their templates, the hooks and their
# handlers, the shims and their installers, the README and VERSION. The
# evals, findings, docs, tests, tools and mods stay out: the app runs no
# mods, and the rest is the maintainer's. The packaged manifest drops
# `dependencies` (the progress band is a Claude Code mod the app lacks).
# Then, in the app, attach the file in a chat and accept the plugin.

set -eu
cd "$(dirname -- "$0")/.."

out="${1:-$HOME/Downloads/reboot.plugin}"
case "$out" in /*) ;; *) out="$PWD/$out" ;; esac
stage="$(mktemp -d "${TMPDIR:-/tmp}/reboot-plugin.XXXXXX")"
trap 'rm -rf "$stage"' EXIT

git archive --format=tar HEAD \
    .claude-plugin skills hooks hooks-handlers bin lib README.md VERSION \
    | tar -x -C "$stage"
# What Bazel keeps for the upstream build is not part of the plugin, and
# the marketplace catalog names a mod the package does not carry.
find "$stage" -name BUILD.bazel -delete
rm -f "$stage/.claude-plugin/marketplace.json"
python3 - "$stage/.claude-plugin/plugin.json" <<'PY'
import json, sys
path = sys.argv[1]
manifest = json.load(open(path))
manifest.pop("dependencies", None)
json.dump(manifest, open(path, "w"), indent=2)
open(path, "a").write("\n")
PY

rm -f "$out"
(cd "$stage" && zip -q -r -X "$out" . -x '*.DS_Store')
printf '%s: %s, %s files, at %s\n' "$(basename "$out")" "$(du -h "$out" | cut -f1)" \
    "$(unzip -l "$out" | tail -1 | awk '{print $2}')" "$(git rev-parse --short HEAD)"
