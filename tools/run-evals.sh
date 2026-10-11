#!/usr/bin/env bash
#
# Run the behavior evals in evals/ against this working tree with
# `claude plugin eval`, with and without the plugin.
#
#   tools/run-evals.sh [--smoke] [--fresh] [claude plugin eval flags...]
#   e.g. tools/run-evals.sh --tag routing --runs 1
#        tools/run-evals.sh --case design-ready-for-both -j 2
#        tools/run-evals.sh --smoke --case route-mcp   # 1 run, no ablation, Haiku judging
#
# The eval runner refuses an evals/ that links outside the plugin, and a
# run should get a copy of the skills and no leftover-process hook, so
# this builds a throwaway wrapper plugin: its own plugin.json, links to
# bin/ and hooks-handlers/, and copies of skills/, hooks/ and evals/.
# A case with a fixture (scaffold_script) gets --scaffold unless the
# flags already say --scaffold or --no-scaffold. Results are copied back
# into evals/results/ (gitignored; EVALS_RESULTS_DIR moves them).
#
# The result cache: each selected case gets a key, a hash of its
# directory, the skills its Skill graders name (with references/),
# hooks-handlers/remind.sh, the templates' AGENTS.md and the flags that
# change a score (runs, ablation, judge model, model, scaffold);
# tools/evals_cache.py has the list. A case whose key matches a clean
# earlier result prints that result and does not run; --fresh runs it
# anyway. Each result directory keeps its keys in cache-keys.json.
# After a run, and for a cached case, each grader's votes per run are
# printed (PPF: three judges, two passed), with the range of the
# per-run scores, so a small difference between two scores reads as
# the noise it is.
#
# --smoke: one run per case, ablation none, Haiku judging (a flag
# given explicitly wins). The full default stays three runs per case
# with Sonnet judging.

set -euo pipefail

ROOT="$(cd "$(dirname -- "$0")/.." && pwd)"
RESULTS="${EVALS_RESULTS_DIR:-$ROOT/evals/results}"

# This script's own flags, taken out before the rest reach the runner.
smoke=0
fresh=0
rest=()
for arg in "$@"; do
  case "$arg" in
    --smoke) smoke=1 ;;
    --fresh) fresh=1 ;;
    *) rest+=("$arg") ;;
  esac
done
set -- ${rest[@]+"${rest[@]}"}
if [ "$smoke" = 1 ]; then
  case " $* " in *" --runs "*|*" --runs="*) ;; *) set -- --runs 1 "$@" ;; esac
  case " $* " in *" --ablation "*|*" --ablation="*) ;; *) set -- --ablation none "$@" ;; esac
  case " $* " in *" --judge-model "*|*" --judge-model="*) ;; *) set -- --judge-model haiku "$@" ;; esac
fi

# The wrapper is a fresh temp dir every run and holds this working tree,
# so trust it: a non-interactive run can't ask, and refuses otherwise.
case " $* " in
  *" --trust-plugin "*) ;;
  *) set -- --trust-plugin "$@" ;;
esac

# A selected case with a fixture needs --scaffold: without it the runner
# skips the fixture and the case runs in an empty directory. Cases are
# selected as the runner selects them, by --case glob and --tag.
case " $* " in
  *" --scaffold "*|*" --no-scaffold "*) ;;
  *)
    if python3 - "$ROOT/evals" "$@" <<'PY'
import fnmatch, glob, os, re, sys
evals, args = sys.argv[1], sys.argv[2:]
pattern, tags, i = None, set(), 0
while i < len(args):
    a = args[i]
    if a.startswith("--case="):
        pattern = a.split("=", 1)[1]
    elif a == "--case" and i + 1 < len(args):
        i += 1
        pattern = args[i]
    elif a.startswith("--tag="):
        tags.add(a.split("=", 1)[1])
    elif a == "--tag":
        while i + 1 < len(args) and not args[i + 1].startswith("-"):
            i += 1
            tags.add(args[i])
    i += 1
for path in sorted(glob.glob(os.path.join(evals, "*", "case.yaml"))):
    name = os.path.basename(os.path.dirname(path))
    text = open(path).read()
    if pattern and not fnmatch.fnmatch(name, pattern):
        continue
    if tags:
        m = re.search(r"^tags:\s*\[(.*)\]", text, re.M)
        found = {t.strip().strip("'\"") for t in m.group(1).split(",")} if m else set()
        if not tags & found:
            continue
    if re.search(r"^\s*scaffold_script:\s*\S", text, re.M):
        sys.exit(0)
sys.exit(1)
PY
    then
      set -- --scaffold "$@"
    fi
    ;;
esac

# Sonnet judges by default: Haiku failed designs that plainly met a rubric.
case " $* " in
  *" --judge-model "*|*" --judge-model="*) ;;
  *) set -- --judge-model sonnet "$@" ;;
esac

# The cache: which selected cases already have a result for their key.
cached_status=0
selected=0
to_run=()
keys=()
fresh_flag=()
[ "$fresh" = 1 ] && fresh_flag=(--fresh)
while read -r what name where; do
  [ -n "$what" ] || continue
  selected=$((selected + 1))
  if [ "$what" = cached ]; then
    python3 "$ROOT/tools/evals_cache.py" show "$where" "$name" -- "$@" --cached || cached_status=1
  else
    to_run+=("$name")
    keys+=("$name=$where")
  fi
done <<< "$(python3 "$ROOT/tools/evals_cache.py" plan "$RESULTS" -- "$@" ${fresh_flag[@]+"${fresh_flag[@]}"})"
if [ "$selected" -gt 0 ] && [ "${#to_run[@]}" -eq 0 ]; then
  echo "every selected case is cached (--fresh runs them again)"
  exit "$cached_status"
fi

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



status=0
if [ "${#to_run[@]}" -eq "$selected" ]; then
  # Nothing cached: one run with the flags as given (cases share -j).
  (cd "$WRAP" && claude plugin eval . --no-publish "$@") || status=$?
else
  # Some cached: the rest one case at a time.
  filtered=()
  while IFS= read -r arg; do
    filtered+=("$arg")
  done <<< "$(python3 "$ROOT/tools/evals_cache.py" filters -- "$@")"
  for name in "${to_run[@]}"; do
    (cd "$WRAP" && claude plugin eval . --no-publish ${filtered[@]+"${filtered[@]}"} --case "$name") || status=$?
  done
fi

if [ -d "$WRAP/evals/results" ]; then
  mkdir -p "$RESULTS"
  for dir in "$WRAP/evals/results"/*/; do
    [ -f "$dir/aggregate-result.json" ] || continue
    name="$(basename -- "$dir")"
    cp -R "$dir" "$RESULTS/$name"
    python3 "$ROOT/tools/evals_cache.py" store "$RESULTS/$name" ${keys[@]+"${keys[@]}"} || true
    python3 "$ROOT/tools/evals_cache.py" show "$RESULTS/$name" -- "$@" || true
  done
  echo "results: $RESULTS/"
fi
[ "$status" -ne 0 ] || status="$cached_status"
exit "$status"
