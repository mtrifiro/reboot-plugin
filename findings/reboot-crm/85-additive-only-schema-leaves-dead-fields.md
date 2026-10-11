---
id: reboot-crm-85
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md A.4"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/api-schema-evolution.md
  - python/references/state-scalar-fields.md
tags: [negative-space, pattern]
cluster: "4.1"
still_applies: unknown
status: Resolved
resolved_by: "python/references/api-schema-evolution.md § Do this"
---

# Additive-only schema change leaves dead fields and methods that read as live (compounds with the zero-default rule)

**What happened.** Only additions are safe on an existing store (see reboot-crm-10, -11), so a retired feature leaves its schema behind: Poggio fields and methods, `templates_for`, `LogoState.image`, method descriptions kept word for word though stale. Each is a false lead when the API is read, and the generated clients keep offering them. It compounds with the rule that a field cannot have a non-zero default: a change of mind costs a second field named after the constraint. Examples: flipping a default meant adding `show_tags` beside `hide_tags` (old field kept forever, `not` written on both read and write); house idiom now names fields so off is the zero value (`show_tags`, `show_account_drawer`, `ask_ai_for`, the last a three-way audience whose empty string the servicer resolves to `nobody`); retired features and test-only seeders had to stay until the expunge. Expunge stops being available exactly when accretion starts to matter: before production every mistake is free, afterwards wiping is an outage plus data loss and nothing warns that the escape hatch has closed. The 2026-09-25 expunge removed `hide_tags`, `account_view`/`set_account_view`/`account_defaults`/`set_account_defaults`, power mode's `Lead.set_notes` and `LeadSummary.notes`, `Pipeline.ensure_fit_criteria`, the ambassador flow's second index and every read-time fallback; it also rewrote the frozen method descriptions and renumbered every model's tags. The app keeps a `docs/NEXT_EXPUNGE.md` list and a planned export, expunge and restore.

**Expected.** Asked of Reboot, in order: (1) allow non-zero defaults (or document why absent and default must be indistinguishable on the wire); (2) reserved-style deletion for Pydantic models, as protobuf has; (3) failing both, say it in the schema-evolution reference: what you add, you keep; name fields so the default is the zero value; expect to carry superseded fields and document them where they sit. Also a way to mark a field or method deprecated that the clients and dashboard show.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-schema-evolution.md`, `python/references/state-scalar-fields.md`.

**Checked at 1.6.0.** `api-schema-evolution.md` (line ~142) says an old field stays declared and reads as its zero value, and `state-scalar-fields.md` is titled "Use Zero-Value Defaults"; the compounding effect, naming-for-zero-default idiom and the closing escape hatch were not found stated.
