---
id: theater-network-09
project: theater-network
source: "theater-network/docs/reboot-findings.md §9"
reboot_version: 1.4.0
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
  - python/references/react-generated-client.md
tags: [frontend, negative-space, error-text]
cluster: "4.2"
still_applies: yes
status: Open
resolved_by: ""
---

# Browser-side traps, all verified

**What happened.** Four traps. (a) `#` in an actor id breaks reactive subscriptions: the state id rides a WebSocket URL and `#` truncates it as a fragment (`Failed to construct 'WebSocket'`); `@`, `:`, `~` are safe. (b) Never subscribe to an actor that may not exist: the reader aborts `StateNotConstructed` and retries about once a second forever, tearing the page's shared channel under every other subscription; if the type has no factory a no-op `touch` writer constructs it implicitly, and the subscribing component should mount only after it resolves (a component can be conditional, a hook cannot). (c) Budget long-lived reader connections: reactive readers hold streaming fetches, HTTP/1.1 allows about 6 per host, and Reboot logs a warning naming the fix (HTTP/2 via TLS); keep subscription count small and never duplicate a poll. (d) The generated `_rbt_web.ts` is un-importable with multiple types in one API file (five top-level `_Reactively`/`_Idempotently` classes; tsc tolerates, esbuild refuses); mirror the one call needed with `reboot_web.httpCall` plus the `theater_pb` types.

**Expected.** Not recorded.

**Repro.** Not recorded beyond the symptoms above.

**Where in the skills.** `web-app/references/react-client.md`, `python/references/react-generated-client.md` (Never / Limits / Errors).

**Checked at 1.6.0.** No mention of `#` in ids, subscribing to unconstructed actors, the HTTP/1.1 connection limit or `_rbt_web.ts` import problems in `web-app/` or `python/references/react-generated-client.md`. Item (d) is proto-era (1.4.0) naming and may not apply to the pydantic API.
