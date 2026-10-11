---
id: mattprd-01
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §1"
reboot_version: 1.4.1
severity: red
target: plugin
names:
  - python/references/agent-pydantic-ai.md
tags: [version-drift, error-text]
cluster: "A"
still_applies: no
status: Obsolete
resolved_by: ""
---

# pydantic-ai-slim[anthropic]==1.87.0 resolves a broken anthropic version

**What happened.** `agent-pydantic-ai.md` told builders to add `pydantic-ai-slim[anthropic]==1.87.0`. With no upper bound on the transitive `anthropic` dependency, `uv sync` resolves `anthropic==1.0.0`, which switched its HTTP layer to `httpx2`. pydantic-ai 1.87.0 still passes an `httpx.AsyncClient`, so the first `Agent(...)` construction raises `TypeError: Invalid http_client argument; Expected an instance of httpx2.AsyncClient but got <class 'httpx.AsyncClient'>`. Agents are module-scope, so the whole app and every test collection die at import with a trace that never names the real cause. Workaround: pin `anthropic<1.0` (resolved 0.125.0).

**Expected.** Reference pins a compatible pair (or an explicit `anthropic<1.0` beside it); consider a plugin startup preflight that detects the mismatch and prints the pin fix.

**Repro.** Fresh project following the reference; `uv sync`; import the module that constructs an `Agent`.

**Where in the skills.** `agent-pydantic-ai.md`.

**Checked at 1.6.0.** python/references/agent-pydantic-ai.md:158-161 now says `reboot` already pins pydantic-ai-slim and not to add the `[anthropic]` extra or `anthropic` yourself because a fresh resolve picks an httpx2 SDK; upgrade/migrations/1.6.0/anthropic-extra.md covers the migration. The exact-pin advice is gone.
