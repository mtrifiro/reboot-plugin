---
id: student-sor-03
project: student-sor
source: "student-sor/reboot-findings.md §3"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - mcp-ui/references/auth-oauth-providers.md
  - python/references/servicer-authorizer.md
  - web-app/SKILL.md
tags: [negative-space, auth, index-gap]
cluster: "8.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/auth-claims.md § Do this"
---

# set_claims is documented with a state parameter it does not take, and claims are not covered by any reference

**What happened.** The generated `UserBaseServicer.set_claims` (and a comment in `sor_rbt.py`) has the shape `(self, context, state, request)`, so the author wrote that. `mypy`: `Signature of "set_claims" incompatible with supertype "sor.v1.sor_rbt.UserServicer"`. The class an application subclasses (`User.Servicer`) declares `set_claims(self, context, request)` and expects `self.state`; the `state`-taking twin belongs to the singleton variant. No reference covered how claims reach the app (`Development(claims=[...])`, the transaction context, full-replace semantics); the author found it by grepping the generated file.

**Expected.** A short `auth-claims.md` (or a section in `servicer-authorizer.md`): which providers deliver which claims, that `set_claims` is a `TransactionContext` method (so it may call other actors, which is what a role lookup needs), and the `self.state` signature.

**Repro.** Not recorded.

**Where in the skills.** No reference under `python/references/` covers `set_claims`.

**Checked at 1.6.0.** `mcp-ui/references/auth-oauth-providers.md` (lines ~72-96) now documents `set_claims(self, context: TransactionContext, request)` with `self.state` and full-replace semantics, but only in the mcp-ui skill; `python/references/` and `web-app/` have no claims reference (a testing mention exists at `python/references/testing-harness.md` line ~230).
