#!/usr/bin/env bash
#
# Deploy a pushed commit to production: the backend to Reboot Cloud when
# what it serves changed, then the web frontend to Cloudflare Pages, each
# rule checked rather than remembered. The deploy skill sets it up once
# (deploy/config, .deploy.env); after that, every deploy is this.
#
#   scripts/deploy.sh                  backend if it changed, then frontend
#   scripts/deploy.sh --backend-only   the backend alone
#   scripts/deploy.sh --frontend-only  the frontend alone
#   scripts/deploy.sh --dry-run        every check, and what would ship; nothing deployed
#   scripts/deploy.sh --first          the first deploy: no ledger yet to check the API against
#
# In order, stopping at the first thing wrong:
#   1. clean, on the production branch and pushed: production runs a commit.
#   2. The API change since the commit production runs is additive
#      (scripts/api_removals.py, deploy/api-exceptions.md).
#   3. Backend (when backend/, api/, .rbtrc or the Dockerfile changed since
#      the last backend deploy, or asked for):
#        a. deploy/before-backend, when the project has one (a backup);
#        b. `rbt cloud up`, and the revision and address it names;
#        c. the new revision serving (/__/inspect answers, not 503).
#   4. Frontend: built from the commit in a scratch copy (generated code is
#      not tracked, so it is generated there), published with wrangler, and
#      the live site checked to serve the new bundle.
#   5. A line in deploy/ledger.jsonl, committed and pushed: when, which
#      commit, revision and bundle (step 2 compares against it next time),
#      and the release record: the commits, the model diff
#      (scripts/model_diff.py) and the last test run (tests/.last-run.json)
#      since the last deploy, all printed before anything ships.
#   6. deploy/after, when the project has one.
#
# Settings are in deploy/config; credentials in .deploy.env (git-ignored):
#   REBOOT_CLOUD_API_KEY, REBOOT_CLOUD_ORGANIZATION,
#   CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID (with a frontend).
#
# deploy.sh version 2 (Reboot plugin, build templates).
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

LEDGER="deploy/ledger.jsonl"
SCRATCH="${TMPDIR:-/tmp}/$(basename "$ROOT")-deploy"

frontend=1; backend=auto; dry=0; first=0; only=""
for arg in "$@"; do
  case "$arg" in
    --frontend-only) backend=no; only=frontend ;;
    --backend-only) frontend=0; backend=yes; only=backend ;;
    --dry-run) dry=1 ;;
    --first) first=1 ;;
    *) echo "usage: scripts/deploy.sh [--backend-only|--frontend-only] [--dry-run] [--first]" >&2; exit 2 ;;
  esac
done

say() { echo "deploy: $*"; }
die() { echo "deploy: $*" >&2; exit 1; }

# -- settings and credentials ---------------------------------------------
[ -f deploy/config ] || die "no deploy/config; the deploy skill writes it on the first deploy."
# shellcheck source=/dev/null
. deploy/config
: "${APP:?deploy/config sets APP, the Reboot Cloud application name}"
SIZE="${SIZE:-xsmall}"
BRANCH="${BRANCH:-main}"
FRONTEND_DIR="${FRONTEND_DIR:-}"
[ -n "$FRONTEND_DIR" ] || frontend=0
if [ "$frontend" = 1 ]; then
  : "${PUBLISH_DIR:?deploy/config sets PUBLISH_DIR, the built site (web/dist, frontend/dist/web)}"
  : "${ENV_DIR:?deploy/config sets ENV_DIR, where the SPA reads .env.production}"
  : "${PAGES_PROJECT:?deploy/config sets PAGES_PROJECT, the Cloudflare Pages project}"
  SITE_URL="${SITE_URL:-https://$PAGES_PROJECT.pages.dev}"
fi
[ -f .deploy.env ] || die "no .deploy.env with the credentials (see the top of this script)."
set -a
# shellcheck source=/dev/null
. ./.deploy.env
set +a
: "${REBOOT_CLOUD_API_KEY:?.deploy.env sets REBOOT_CLOUD_API_KEY}"
: "${REBOOT_CLOUD_ORGANIZATION:?.deploy.env sets REBOOT_CLOUD_ORGANIZATION}"
if [ "$frontend" = 1 ]; then
  : "${CLOUDFLARE_API_TOKEN:?.deploy.env sets CLOUDFLARE_API_TOKEN}"
  : "${CLOUDFLARE_ACCOUNT_ID:?.deploy.env sets CLOUDFLARE_ACCOUNT_ID}"
fi

# -- 1. clean, on the branch, pushed --------------------------------------
[ -z "$(git status --porcelain)" ] || die "the tree has uncommitted changes; production runs a commit. Commit or stash first."
[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || die "not on $BRANCH; production runs $BRANCH."
git fetch -q origin "$BRANCH" || die "could not fetch origin/$BRANCH."
[ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$BRANCH")" ] || die "$BRANCH is not what origin/$BRANCH is; push (or pull) first."
sha="$(git rev-parse --short HEAD)"
say "deploying $sha: $(git log -1 --format=%s | cut -c1-90)"

# The last value of a field in the ledger.
last_field() {
  [ -f "$LEDGER" ] || return 0
  python3 - "$LEDGER" "$1" <<'PY'
import json, sys
path, field = sys.argv[1:]
rows = [json.loads(line) for line in open(path) if line.strip()]
rows = [r for r in rows if r.get(field)]
print(rows[-1][field] if rows else "")
PY
}

# -- 2. additive API -------------------------------------------------------
last_backend="$(last_field backend_commit)"
api_url="$(last_field api_url)"
if [ -z "$last_backend" ]; then
  [ "$first" = 1 ] || die "no backend commit in $LEDGER to check the API against. For the first deploy, run with --first; for an app already in production, add the commit it runs: echo '{\"backend_commit\": \"<sha>\"}' >> $LEDGER"
  backend=yes
  say "first deploy: no API to compare against"
else
  git cat-file -e "$last_backend^{commit}" 2>/dev/null || die "$LEDGER names $last_backend, which this clone does not have."
  if ! api_check="$(python3 scripts/api_removals.py "$last_backend" --head 2>&1)"; then
    echo "$api_check" >&2
    die "the API lost or changed lines since $last_backend (above); that needs an expunge and a restore, not this script."
  fi
  echo "$api_check" | while IFS= read -r line; do say "API: $line"; done
  if [ "$backend" = auto ]; then
    if [ -n "$(git diff --name-only "$last_backend"..HEAD -- backend/ api/ .rbtrc Dockerfile)" ]; then backend=yes; else backend=no; fi
  fi
fi
if [ "$backend" = yes ]; then say "backend: deploy${last_backend:+ (production runs $last_backend)}"
elif [ "$only" = frontend ]; then say "backend: skip (--frontend-only)"
else say "backend: skip (production runs $last_backend; nothing it serves changed)"; fi
if [ "$frontend" = 1 ]; then say "frontend: deploy to $SITE_URL"
elif [ -z "$FRONTEND_DIR" ]; then say "frontend: none (an MCP UI ships in the backend)"
else say "frontend: skip (--backend-only)"; fi

# -- before anything ships: what the steps need ---------------------------
if [ "$backend" = yes ]; then
  [ -f Dockerfile ] || die "no Dockerfile, which rbt cloud up builds the image from (python/references/lifecycle-dockerfile.md)."
  # Docker Desktop on macOS: rbt cloud up pushes through a temporary docker
  # config, which loses the desktop context and looks for
  # /var/run/docker.sock; point it at Docker Desktop's socket.
  if [ -z "${DOCKER_HOST:-}" ] && [ -S "$HOME/.docker/run/docker.sock" ] && [ ! -S /var/run/docker.sock ]; then
    export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
  fi
  docker info >/dev/null 2>&1 || die "Docker is not running, and rbt cloud up builds the backend image with it. Start it; nothing deployed."
  say "docker: running"
fi
if [ "$frontend" = 1 ]; then
  git cat-file -e "HEAD:$ENV_DIR/.env.production" 2>/dev/null \
    || die "no $ENV_DIR/.env.production in the commit: write VITE_REBOOT_URL=<the API address> there and commit it${api_url:+ (the production API is at $api_url)}. The first deploy: --backend-only first, which prints the address."
fi

# -- the release record: what ships, as evidence ---------------------------
# Promoting is the developer's decision (the Reboot Flywheel); this shows
# what it rests on (build/references/evidence.md), and never stops a deploy.
last_commit="$(last_field commit)"
model_json='{}'
if [ -n "$last_commit" ] && git cat-file -e "$last_commit^{commit}" 2>/dev/null; then
  say "since $last_commit:"
  git log --format='  %h %s' "$last_commit"..HEAD
  python3 scripts/model_diff.py "$last_commit" --head | sed 's/^/  /'
  model_json="$(python3 scripts/model_diff.py "$last_commit" --head --json)"
fi
tests_json="$(cat tests/.last-run.json 2>/dev/null || echo '{}')"
python3 - "$tests_json" "$sha" <<'PY'
import json, sys
run, sha = json.loads(sys.argv[1]), sys.argv[2]
if not run:
    print("deploy: tests: no run recorded (tests/.last-run.json); run the full suite first")
    sys.exit()
where = "the full suite" if run.get("full") else "a partial run"
print(f"deploy: tests: {run.get('passed', 0)} passed, {run.get('failed', 0)} failed, "
      f"{run.get('wip', 0)} @wip, {run.get('blocked', 0)} @blocked; {where} at "
      f"{run.get('revision', '?')}{' with uncommitted changes' if run.get('dirty') else ''}")
if run.get("revision") != sha or run.get("dirty") or not run.get("full") or run.get("failed"):
    print(f"deploy: tests: not a clean, full, passing run of {sha}; tell the developer before promoting")
PY

if [ "$dry" = 1 ]; then say "dry run: stopping before anything is deployed."; exit 0; fi

revision=""
if [ "$backend" = yes ]; then
  # -- 3a. the project's own step first (a backup) ------------------------
  if [ -x deploy/before-backend ]; then
    say "deploy/before-backend"
    deploy/before-backend || die "deploy/before-backend exited $?; nothing deployed."
  fi

  # -- 3b. cloud up ---------------------------------------------------------
  log="$(mktemp)"
  say "rbt cloud up $APP (a few minutes)"
  uv run rbt cloud up --application-name="$APP" --size="$SIZE" --organization="$REBOOT_CLOUD_ORGANIZATION" > "$log" 2>&1
  status=$?
  cat "$log"
  [ $status -eq 0 ] || die "rbt cloud up exited $status."
  revision="$(grep -oE "revision [0-9]+ is available" "$log" | grep -oE "[0-9]+" | tail -1)"
  [ -n "$revision" ] || die "rbt cloud up did not name a revision."
  api_url="$(grep -oE "Your API is available at: *https://[^ ]+" "$log" | grep -oE "https://[^ ]+" | tail -1)"
  api_url="${api_url%/}"
  [ -n "$api_url" ] || die "rbt cloud up did not print the API address."

  # -- 3c. serving ----------------------------------------------------------
  # rbt cloud up exits before the revision serves: /__/inspect answers 503
  # for about thirty seconds.
  say "revision $revision is up at $api_url; waiting for it to serve"
  code=""
  for _ in $(seq 1 60); do
    code="$(curl -s -o /dev/null -w '%{http_code}' "$api_url/__/inspect" || true)"
    [ "$code" = 200 ] && break
    sleep 5
  done
  [ "$code" = 200 ] || die "revision $revision did not serve within five minutes (/__/inspect answered $code); see: uv run rbt cloud logs --application-name=$APP --organization=$REBOOT_CLOUD_ORGANIZATION --revisions=$revision"
  say "revision $revision serves"
fi

bundle=""
if [ "$frontend" = 1 ]; then
  # -- 4. frontend from the commit ----------------------------------------
  build="$SCRATCH/build-$sha"
  rm -rf "$build"; mkdir -p "$build"
  git archive "$sha" | tar -x -C "$build"
  [ -d "$ROOT/$FRONTEND_DIR/node_modules" ] || die "no $FRONTEND_DIR/node_modules; run npm install in $FRONTEND_DIR first."
  ln -s "$ROOT/$FRONTEND_DIR/node_modules" "$build/$FRONTEND_DIR/node_modules"
  say "generating the API clients in the build copy"
  ( cd "$build" && PATH="$ROOT/.venv/bin:$PATH" rbt generate > "$build/generate.log" 2>&1 ) \
    || { tail -20 "$build/generate.log"; die "rbt generate failed in the build copy."; }
  say "building the frontend"
  ( cd "$build/$FRONTEND_DIR" && npm run build > "$build/build.log" 2>&1 ) \
    || { tail -20 "$build/build.log"; die "the frontend build failed."; }
  bundle="$(cd "$build/$PUBLISH_DIR" && find . -path '*assets/index-*.js' | head -1 | xargs -n1 basename 2>/dev/null)"
  [ -n "$bundle" ] || die "the build left no assets/index-*.js under $PUBLISH_DIR."
  say "publishing $bundle"
  ( cd "$build/$FRONTEND_DIR" && npx --yes wrangler@4 pages deploy "$build/$PUBLISH_DIR" \
      --project-name="$PAGES_PROJECT" --branch="$BRANCH" --commit-hash="$sha" > "$build/wrangler.log" 2>&1 ) \
    || { tail -20 "$build/wrangler.log"; die "wrangler did not publish."; }
  live=""
  for _ in $(seq 1 12); do
    live="$(curl -s -H 'Cache-Control: no-cache' "$SITE_URL/?v=$RANDOM" | grep -oE 'index-[A-Za-z0-9_-]+\.js' | head -1)"
    [ "$live" = "$bundle" ] && break
    sleep 5
  done
  [ "$live" = "$bundle" ] || die "published, but $SITE_URL still serves ${live:-no bundle} after a minute."
  say "$SITE_URL serves $bundle"
fi

# -- 5. the ledger, in git -------------------------------------------------
python3 - "$LEDGER" "$sha" "$revision" "$bundle" "$last_backend" "$api_url" "${SITE_URL:-}" \
  "$last_commit" "$model_json" "$tests_json" <<'PY'
import datetime, json, subprocess, sys
ledger, sha, revision, bundle, last_backend, api_url, site, since, model, tests = sys.argv[1:]
row = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "commit": sha}
row["backend_commit"] = sha if revision else last_backend
if revision: row["revision"] = int(revision)
if api_url: row["api_url"] = api_url
if bundle: row["bundle"], row["site"] = bundle, site
# The release record (build/references/evidence.md).
release = {"tests": json.loads(tests)}
if since:
    release["since"] = since
    release["commits"] = subprocess.run(
        ["git", "log", "--format=%h %s", f"{since}..{sha}"], capture_output=True, text=True
    ).stdout.splitlines()
    diff = json.loads(model)
    release["model_diff"] = {"design": diff.get("design", []), "prove": diff.get("prove", [])}
row["release"] = release
open(ledger, "a").write(json.dumps(row) + "\n")
PY
git add "$LEDGER"
git commit -q -m "Deploy log: $sha${revision:+, backend revision $revision}${bundle:+, frontend $bundle}" \
  || die "could not commit $LEDGER; commit it before the next deploy."
git push -q origin "$BRANCH" || die "could not push $LEDGER; push it before the next deploy (it refuses an unpushed $BRANCH)."
say "done: $sha${revision:+, backend revision $revision at $api_url}${bundle:+, frontend $bundle at $SITE_URL}. Recorded in $LEDGER."

# -- 6. the project's own step after --------------------------------------
if [ -x deploy/after ]; then
  say "deploy/after"
  deploy/after || die "deploy/after exited $? (the deploy itself is done and recorded)."
fi
