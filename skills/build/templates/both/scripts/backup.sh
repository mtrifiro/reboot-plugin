#!/usr/bin/env bash
#
# Export everything the application holds, so an expunge is not a loss.
#
#   scripts/backup.sh dev     the local `rbt dev run` ($REBOOT_DEV_URL, or :9991)
#   scripts/backup.sh prod    Reboot Cloud: the API address deploy/ledger.jsonl
#                             records, the key in .deploy.env
#
# Writes exports/backups/<env>-<UTC stamp>/, git-ignored because it is
# every user's data. Inside:
#
#   manifest.json   where and when it was taken, on which commit, and
#                   how many actors of each type it holds
#   data/*.json     `rbt export`'s JSON lines, one file per server
#
# The data has a directory of its own because `rbt import` streams every
# file in the directory it is given: a manifest beside the data would be
# sent to the application as if it were state.
#
# `rbt export` reads what is committed, server by server and type by
# type, without stopping writers: it is not a point-in-time snapshot.
# Take one while nobody is working, and before an expunge take it last.
#
# An export that holds nothing is refused, so a deploy that runs this
# first (deploy/before-backend) never ships with an empty backup behind
# it. Run it on its own, never chained with `;` or a pipe, which hide
# its exit status. Loading one back is scripts/restore.py; the
# procedure is python/references/lifecycle-backup-restore.md.
#
# backup.sh version 1 (Reboot plugin, build templates).
set -euo pipefail
cd "$(dirname "$0")/.."

env_name="${1:-}"
case "$env_name" in
  dev|prod) ;;
  *) echo "usage: scripts/backup.sh <dev|prod>" >&2; exit 2 ;;
esac

die() { echo "backup: $*" >&2; exit 1; }

if [ "$env_name" = dev ]; then
  # `rbt export` defaults to the dev admin credential.
  url="${REBOOT_DEV_URL:-http://localhost:9991}"
else
  [ -f .deploy.env ] || die "no .deploy.env with REBOOT_CLOUD_API_KEY (the deploy skill writes it)."
  # The Cloud API key doubles as the admin credential for `*.rbt.cloud`
  # hosts; `rbt export` reads it from REBOOT_CLOUD_API_KEY.
  set -a
  # shellcheck source=/dev/null
  . ./.deploy.env
  set +a
  : "${REBOOT_CLOUD_API_KEY:?.deploy.env sets REBOOT_CLOUD_API_KEY}"
  # The address `rbt cloud up` printed, which scripts/deploy.sh records.
  url="$(python3 - deploy/ledger.jsonl <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
urls = [row["api_url"] for row in rows if row.get("api_url")]
print(urls[-1] if urls else "")
PY
)"
  [ -n "$url" ] || die "deploy/ledger.jsonl records no api_url. Add the address \`rbt cloud up\` printed: echo '{\"api_url\": \"https://<id>.<cell>.rbt.cloud\"}' >> deploy/ledger.jsonl"
fi

stamp="$(date -u '+%Y%m%d-%H%M%S')"
dir="exports/backups/$env_name-$stamp"
mkdir -p "$dir/data"

echo "backup: exporting $url"
uv run rbt export --application-url="$url" --directory="$dir/data" \
  || die "rbt export exited $?; $dir is not a backup."

uv run python - "$dir" "$env_name" "$url" "$stamp" <<'PY'
import collections, json, pathlib, subprocess, sys

dir, env_name, url, stamp = sys.argv[1:5]
data = pathlib.Path(dir) / "data"
actors: collections.Counter = collections.Counter()
items = 0
for path in sorted(data.glob("*.json")):
    with path.open() as lines:
        for line in lines:
            if not line.strip():
                continue
            item = json.loads(line)
            items += 1
            if "state" in item:
                actors[item["state_type"]] += 1


def output(*command: str) -> str:
    done = subprocess.run(command, capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


# Refused before the manifest is written, so the directory never looks
# like a backup: one that succeeded and holds nothing leaves a deploy
# nothing to restore.
if items == 0:
    sys.exit(f"backup: {dir}: the export holds nothing; this is not a backup")
manifest = {
    "environment": env_name,
    "application_url": url,
    "taken_at": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z",
    "git_rev": output("git", "rev-parse", "HEAD"),
    "rbt_version": output("uv", "run", "rbt", "--version"),
    "items": items,
    "actors": dict(sorted(actors.items())),
}
(pathlib.Path(dir) / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"\n{dir}")
for state_type, count in manifest["actors"].items():
    print(f"  {count:6d}  {state_type}")
PY
