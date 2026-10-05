---
id: tool-checks-04
project: tool-checks
source: "Phase 2 summary trap check, 2026-10-04"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/rpc-calls.md
tags: [contradiction]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-calls.md § Never"
---

# How a Request-wrapper call fails is stated two ways

**What happened.** The pre-Phase-2 reading lists said passing a
`Request` wrapper instead of kwargs "passes type-check and fails at
runtime". `rpc-calls.md`'s `impactDescription` says it "fails at
type-check or runtime". The body only says "don't".

**Expected.** One verified statement of when the mistake surfaces
(mypy error, `TypeError` at call time, or something later), with the
literal error text, in `rpc-calls.md` § Never / Errors.

**Repro.** `await account.deposit(context, DepositRequest(amount=100))`
under mypy and at runtime, Reboot 1.6.0.

**Where in the skills.** `python/references/rpc-calls.md`.

**Checked at 1.6.0.** Not verified; the generated `reboot.py.j2` has
several call layers and the user-facing signature was not traced.
