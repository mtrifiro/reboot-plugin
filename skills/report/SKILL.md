---
name: report
description: File a Reboot project's FINDINGS.md upstream — turn each item the agent logged while building (a skill that was wrong or silent, unexpected framework or Reboot Cloud behaviour, reboot.bdd trouble, things that worked) into a GitHub issue for the Reboot team, after the user approves the batch. Use when the user asks to "report findings", "file the findings", "send feedback to Reboot", or at the end of a build or deploy when FINDINGS.md has unreported items. Never files anything without explicit approval.
argument-hint: "[path to FINDINGS.md]"
allowed-tools: Bash, Read, Edit
---

# report — File a Project's Findings with the Reboot Team

The skills improve only from what builders write down. Every Reboot
project made from `build/templates/` has a `FINDINGS.md`; the agent
appends to it whenever a skill is wrong or silent. This skill turns
those items into GitHub issues — **one issue per item, filed only
after the user approves the batch.** Filing an issue publishes it.

## Step 1 — Read the findings

1. Find `FINDINGS.md` at the project root (or the path given).
2. Collect every `### …` item that has no `- **Reported:** <url>`
   line. Note its section (Framework / Reboot Cloud / reboot.bdd /
   Plugin skills / Things that worked), severity, Reboot version and
   the five fields.
3. If an item is missing its Reboot version or "What happened", ask
   the user to fill it in, or skip it. Don't invent repro steps.

## Step 2 — Ask about the silent areas

Silence is a measurement only if someone asked. Ask the user once,
briefly, whether anything surprised them in these areas, which past
findings almost never mention, and add any answers as items:

- Codex (if they used it instead of Claude Code)
- the `deploy` skill and Reboot Cloud, beyond secrets
- proto-defined (rather than pydantic) APIs

## Step 3 — Check for existing issues

For each item, search the plugin's issues for its key phrase (the
error text, or the skill/reference name):

```sh
gh issue list --repo reboot-dev/reboot-plugin --state all --search "<phrase>" --limit 5
```

If an issue already covers it, plan a comment on that issue instead
of a new one.

## Step 4 — Show the batch and get approval

Show the user a table, one row per planned action:

| # | Action | Title | Labels | Section |
| --- | --- | --- | --- | --- |
| 1 | new issue | `run: stop leaves an orphaned Envoy` | `plugin-skills`, `severity:yellow` | Plugin skills |
| 2 | comment on #123 | … | | Framework |

Labels: the section (`framework`, `reboot-cloud`, `reboot-bdd`,
`plugin-skills`, `worked`) and `severity:red|yellow|green`. Strip
anything private first: customer names, emails, secrets, internal
URLs, proprietary code beyond the minimal repro. Point out anything
you removed.

**Stop and wait.** File only the rows the user approves, as worded
after their edits. No answer is not approval.

## Step 5 — File and record

Issue body, in this order: Reboot version, What happened, Expected,
Repro, Where in the skills — copied from the item — then a last line
`Reported via the report skill from FINDINGS.md`.

```sh
gh issue create --repo reboot-dev/reboot-plugin \
  --title "<title>" --label "<section>" --label "severity:<s>" \
  --body-file <tempfile>
```

If a label doesn't exist on the repo, file without it rather than
creating labels. After each issue is created, append
`- **Reported:** <issue url>` to the item in `FINDINGS.md` so it is
never filed twice. Finish with the list of URLs.

## Never

- File, comment, or create labels without the user's approval of that
  specific batch.
- Merge several items into one issue — one item, one issue, so each
  can be closed by the change that fixes it.
- Delete or rewrite items in `FINDINGS.md`; only append the
  `Reported:` line.
