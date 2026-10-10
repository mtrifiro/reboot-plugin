---
title: Evidence for Merge and Promote
impact: MEDIUM
impactDescription: Without it a pull request or a deploy ships with no record of the rules it touched or the scenarios that passed
tags: flywheel, prove, evidence, pull-request, release, model-diff, ledger
summary: "The pull request body (feature-file changes, scenarios, model diff, acceptance) and the release record `deploy.sh` keeps."
step: any
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you open a pull request or deploy"
verified: 1.6.0
docs: ""
---

# Evidence for Merge and Promote

## When you are here

The work is in Prove and about to cross a decision the user makes:
**merge** (a pull request) or **promote** (a deploy). Evidence is what
a person can read after this session ends, tied to the revision it
describes. The stages and the routing rule are in
[`flywheel.md`](flywheel.md).

## Do this

### Before a pull request

The template's `.github/workflows/prove.yml` runs the type check and
the full suite on every pull request and posts the model diff and the
scenario counts as one comment (`scripts/prove_comment.py`), so the
reviewer has evidence that is not the agent's own report. The body
below still carries the rules and the acceptance, in the agent's words.

1. Run the **full** suite (`uv run pytest`) at the commit you'll push.
   It writes `tests/.last-run.json`: passed, failed, `@wip`,
   `@blocked`, the revision, and whether the run was full.
2. `python3 scripts/model_diff.py --head`: from the accepted design
   (`design/accepted.json`), with its "Design accepted" verdict. A
   project with no record: `$(git merge-base origin/main HEAD)` as the
   base.
3. Write the body in this order, rules first, so a reviewer decides how
   much code to read:

```markdown
## Rules this changes
<the feature-file changes from the model diff, or "None: a code fix";
the tickets it names, when the feature files name any>

## Domain model
<the model diff's domain-model and who-may-call lines, or "No change">

## Scenarios
12 passed, 0 failed, 2 @wip, 1 @blocked (full suite at abc1234).
@blocked: <scenario> — <why>

## Design accepted
<the model diff's verdict: "Yes, at abc1234 on 2026-10-10", or
"No, 2 design changes since the acceptance at abc1234", or
"No record: built without stopping, at the user's request">
```

Then the attribution line the session's instructions give. A design
change in the diff with no acceptance behind it goes back to Design
before the pull request ([`flywheel.md`](flywheel.md)); once accepted,
`model_diff.py --accept` and a commit record it.

### Before a deploy

`scripts/deploy.sh --dry-run` prints the commits since the last deploy,
the model diff against it and the last test run, and warns when that run
is not a clean, full, passing run of the commit being deployed, or when
a servicer has no authorizer (allowed under `rbt dev`, denied on Reboot
Cloud). Show the user that output and let them decide; `deploy.sh`
itself never stops on it.

### The release record

Every deploy appends a row to `deploy/ledger.jsonl`, committed and
pushed. Its `release` field is the record:

```json
{"tests": {"passed": 12, "failed": 0, "wip": 2, "blocked": 1,
           "full": true, "revision": "abc1234"},
 "since": "9f8e7d6",
 "commits": ["abc1234 Book several rooms in one reservation"],
 "model_diff": {"design": ["`Reservation.create` added, Transaction"],
                "prove": []},
 "compatibility": {"base": "9f8e7d6", "additive": true, "notes": []},
 "unauthorized_servicers": [],
 "accepted": {"commit": "7c1d2e3...", "at": "2026-10-10T16:02:11-07:00",
              "fingerprint_ok": true, "is_base": true, "design_changes": 0}}
```

`compatibility` is the additive-API check the script ran against the
commit production serves; the runtime's own check at `rbt cloud up` is
implied, since a revision it rejects never reaches the ledger.
`unauthorized_servicers` names any servicer with no `authorizer()`.
`accepted` is the design this revision was built to and how many design
changes it carries since that acceptance; `null` when the project has
no record.

To answer "what shipped, and on what evidence?" later, read the row for
the deploy in question.

## Never

- A pull request body that lists files: list the rules and the domain
  model; the diff already lists the files.
- Evidence from another revision: a test run before the last commit,
  or with uncommitted changes, is not this revision's.
- Hand-editing `deploy/ledger.jsonl`; `deploy.sh` writes it.

## Limits

- The release record holds the test summary, not each scenario's
  result; failures and `@blocked` reasons go in the pull request body.
- `tests/.last-run.json` is git-ignored: it is this machine's last run,
  so run the suite again on the commit you ship.

## Scales as

- Not measured.

## Errors you will see

| Error / symptom | Meaning | Fix |
| --- | --- | --- |
| `deploy: tests: no run recorded` | No full run since the project got `tests/last_run.py` | Run `uv run pytest`, then deploy |
| `deploy: tests: not a clean, full, passing run of <sha>` | The last run was partial, failed, or older than the commit | Run the full suite on this commit; tell the user before promoting |

## See also

- [`flywheel.md`](flywheel.md) — the stages and the routing rule
- [`../../deploy/SKILL.md`](../../deploy/SKILL.md) — the deploy itself
