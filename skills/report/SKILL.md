---
name: report
description: File a Reboot project's FINDINGS.md upstream — turn each item the agent logged while building (a skill that was wrong or silent, unexpected framework or Reboot Cloud behavior, reboot.bdd trouble, things that worked) into a GitHub issue for the Reboot team, after the user approves the batch. Use when the user asks to "report findings", "file the findings", "send feedback to Reboot", or at the end of a build or deploy when FINDINGS.md has unreported items. Never files anything without explicit approval.
argument-hint: "[path to FINDINGS.md]"
allowed-tools: Bash, Read, Edit
---

# report — File a Project's Findings with the Reboot Team

Every project made from `build/templates/` has a `FINDINGS.md` the agent
appends to whenever a skill is wrong or silent; the skills improve only
from it. This skill files each item as a GitHub issue — **one issue per
item, only after the user approves the batch.** Filing publishes it.

## Step 1 — Read the findings

1. Open `FINDINGS.md` at the project root (or the given path).
2. Collect every `### …` item with no `- **Reported:** <url>` line; note
   its section (Framework / Reboot Cloud / reboot.bdd / Plugin skills /
   Things that worked), severity, Reboot version and the five fields.
3. Missing Reboot version or "What happened": ask the user to fill it
   in, or skip it. Don't invent repro steps.

## Step 2 — Ask about the silent areas

Silence measures nothing unless someone asked. Ask once, briefly,
whether anything surprised them in these rarely reported areas; add
answers as items:

- Codex (if used instead of Claude Code)
- the `deploy` skill and Reboot Cloud, beyond secrets
- proto-defined (rather than pydantic) APIs

## Step 3 — Check for existing issues

Search for each item's key phrase (error text, or skill/reference name):

```sh
gh issue list --repo reboot-dev/reboot-plugin --state all --search "<phrase>" --limit 5
```

If one covers it, plan a comment on it instead.

## Step 4 — Show the batch and get approval

One row per planned action:

| # | Action | Title | Labels | Section |
| --- | --- | --- | --- | --- |
| 1 | new issue | `run: stop leaves an orphaned Envoy` | `plugin-skills`, `severity:yellow` | Plugin skills |
| 2 | comment on #123 | … | | Framework |

Labels: the section (`framework`, `reboot-cloud`, `reboot-bdd`,
`plugin-skills`, `worked`) and `severity:red|yellow|green`. First strip
anything private — customer names, emails, secrets, internal URLs,
proprietary code beyond the minimal repro — and say what you removed.

**Stop and wait.** File only approved rows, as worded after the user's
edits. No answer is not approval.

## Step 5 — File and record

Body, in order, copied from the item: Reboot version, What happened,
Expected, Repro, Where in the skills; last line
`Reported via the report skill from FINDINGS.md`.

```sh
gh issue create --repo reboot-dev/reboot-plugin \
  --title "<title>" --label "<section>" --label "severity:<s>" \
  --body-file <tempfile>
```

A label missing on the repo: file without it; don't create labels.
After each issue, append `- **Reported:** <issue url>` to the item so it
is never filed twice. Finish with the list of URLs.

## Never

- File, comment, or create labels without the user's approval of that
  specific batch.
- Merge several items into one issue — one item, one issue, so each
  closes with its fix.
- Delete or rewrite items in `FINDINGS.md`; only append the
  `Reported:` line.
