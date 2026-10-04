---
id: team-memo-0826-09
project: team-memo-0826
source: "2026.08.26 Findings for Reboot Team - Docs, Skills, and Runtime.md Q3"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/testing-harness.md
  - mcp-ui/references/auth-custom-oauth-provider.md
tags: [auth, negative-space]
cluster: "8.4"
duplicate_of: student-sor-03
still_applies: unknown
status: Open
resolved_by: ""
---

# set_claims context type

**What happened.** The generated `User` base declares `set_claims` with a `TransactionContext`; the auth reference's example reads like an ordinary writer.

**Expected.** Source asks which is canonical, and whether `set_claims` may call other actors.

**Repro.** Not recorded.

**Where in the skills.** Auth references (proposal 8.4: missing `auth-claims.md`).

**Checked at 1.6.0.** python/references/testing-harness.md:230 and mcp-ui/references/auth-custom-oauth-provider.md:64-96 mention `set_claims` (full replace, idempotent) but I found no statement of its context type or whether it may call other actors.
