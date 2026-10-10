---
id: mattprd-07
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §7"
reboot_version: 1.4.1
severity: yellow
target: framework
names:
  - python/references/agent-pydantic-ai.md
tags: [negative-space, pattern]
cluster: "E"
still_applies: unknown
status: Resolved
resolved_by: "python/references/agent-pydantic-ai.md § Limits"
---

# No incremental streaming path for chat UX

**What happened.** The Reboot `Agent` drains `run_stream`/`run_stream_events` inside `at_least_once`, so tokens arrive as one batch when the model finishes ('true incremental streaming is incompatible with deterministic replay', per `agent-pydantic-ai.md`). For a chat app the UI shows a spinner for the full generation (~30-60s for a long document) then the whole response at once; targets like 'first assistant token < 1.5s' are unreachable.

**Expected.** A sanctioned side-channel for provisional output (e.g. partial text into an ephemeral, non-replayed surface such as a `Presence`/pub-sub-style actor or a 'live transcript' primitive that React hooks subscribe to, with the memoized final result as source of truth), or at least a cookbook pattern in the references.

**Repro.** Not recorded.

**Where in the skills.** `agent-pydantic-ai.md` states the limitation without an escape hatch.

**Resolution (2026-10-10).** `agent-pydantic-ai.md` § Limits already says streaming is drained and memoized inside `at_least_once`, so a chat UI gets the whole response at once, with no sanctioned side channel at 1.6.0; the rest is Reboot's.
