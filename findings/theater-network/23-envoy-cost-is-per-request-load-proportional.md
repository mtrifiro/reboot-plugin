---
id: theater-network-23
project: theater-network
source: "theater-network/docs/reboot-findings.md §23"
reboot_version: 1.4.0
severity: unrated
target: framework
names:
  - run/SKILL.md
  - python/references/rpc-forall.md
tags: [cost, operations]
cluster: "D"
still_applies: unknown
status: Resolved
resolved_by: "python/references/patterns-load-and-benchmarking.md § Scales as"
---

# Envoy's cost is per-request and load-proportional; a busy app pays a core

**What happened.** The dev sidecar's CPU burn is not a startup warm-up. Admin-interface stats during a burn window: 16,108 requests / 1,772 connections in 639s (about 25 req/s) through `:9991` from ONE idle page (all boot work: seeding about 200 actors, a room build, catch-up timers, subscription re-establishment), against 3 config updates and 7 clusters. Every request crosses a gRPC-JSON transcoder plus a Lua filter at milliseconds of proxy CPU each, so sustained traffic holds about a full core and internal RPCs degrade under it (feeding item 18's spirals). The materialized seat map re-pushes the WHOLE room per seat change, re-transcoded per subscriber.

**Expected.** Not recorded. Source practical rules: treat proxy CPU as a load gauge, expect it amber during builds/crowds, pace expensive readers (item 8's audit) down while the crowd runs. Reported upstream with asks.

**Repro.** Idle page against a seeded app with a room build and crowd running.

**Where in the skills.** Primarily framework; relevant to a 'Scales as' line.

**Checked at 1.6.0.** Not checked against 1.6.0; `skills/` mention Envoy only in `testing-web-app.md` (CORS) and `dashboard/SKILL.md`.

**Resolution (2026-10-10).** `patterns-load-and-benchmarking.md` § Scales as: Envoy's cost is per request and grows with load; proxy CPU is a load gauge. The proxy's cost itself is Reboot's.
