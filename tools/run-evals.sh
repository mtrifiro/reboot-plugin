#!/usr/bin/env bash
#
# Run the behavior evals in evals/ against this working tree with
# `claude plugin eval`, with and without the plugin.
#
#   tools/run-evals.sh [claude plugin eval flags...]
#   e.g. tools/run-evals.sh --tag routing --runs 1
#        tools/run-evals.sh --case design-ready-for-both -j 2
#
# The repo has a marketplace manifest but no plugin.json, and the eval
# runner refuses an evals/ that links outside the plugin, so this builds
# a throwaway wrapper plugin: a plugin.json, links to skills/, bin/ and
# the hooks, and a copy of evals/. Results are copied back into
# evals/results/ (gitignored).

set -euo pipefail

ROOT="$(cd "$(dirname -- "$0")/.." && pwd)"
WRAP="$(mktemp -d "${TMPDIR:-/tmp}/reboot-evals.XXXXXX")"
trap 'rm -rf "$WRAP"' EXIT

mkdir -p "$WRAP/.claude-plugin"
for d in bin hooks-handlers; do
  ln -s "$ROOT/$d" "$WRAP/$d"
done
# The skills are copied, not linked: a run may read inside the plugin
# under test, judged by the real path, so a link to the checkout left
# every reference read denied and the design cases measured the
# SKILL.md text alone (the Skill tool loads a SKILL.md itself; its
# references need Read).
rsync -a "$ROOT/skills/" "$WRAP/skills/"
# The hooks, less the leftover-process report: it runs at session start
# and tells the agent about dev processes on this machine, which then
# opens its answer by offering to stop them. An eval measures the
# skills, not the machine.
cp -R "$ROOT/hooks" "$WRAP/hooks"
python3 - "$WRAP/hooks/hooks.json" <<'PY'
import json, sys
path = sys.argv[1]
doc = json.load(open(path))
events = doc["hooks"] if isinstance(doc.get("hooks"), dict) else doc
for entries in events.values():
    for entry in entries:
        entry["hooks"] = [h for h in entry.get("hooks", []) if "orphans.sh" not in h.get("command", "")]
json.dump(doc, open(path, "w"), indent=2)
PY
cat > "$WRAP/.claude-plugin/plugin.json" <<EOF
{
  "name": "reboot",
  "version": "0.0.0-$(git -C "$ROOT" rev-parse --short HEAD)",
  "description": "Eval wrapper for the reboot-plugin working tree."
}
EOF
rsync -a --exclude results "$ROOT/evals/" "$WRAP/evals/"


# The wrapper is a fresh temp dir every run and holds this working tree,
# so trust it: a non-interactive run can't ask, and refuses otherwise.
case " $* " in
  *" --trust-plugin "*) ;;
  *) set -- --trust-plugin "$@" ;;
esac

# Sonnet judges by default: Haiku failed designs that plainly met a rubric.
case " $* " in
  *" --judge-model "*|*" --judge-model="*) ;;
  *) set -- --judge-model sonnet "$@" ;;
esac

status=0
(cd "$WRAP" && claude plugin eval . --no-publish "$@") || status=$?

if [ -d "$WRAP/evals/results" ]; then
  mkdir -p "$ROOT/evals/results"
  cp -R "$WRAP/evals/results/." "$ROOT/evals/results/"
  echo "results: $ROOT/evals/results/"
fi
exit "$status"
