---
id: showtime-32
project: showtime
source: "2026.08.18 reboot-findings.md #32"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/rpc-constructor-calls.md
tags: [negative-space, contradiction]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/rpc-constructor-calls.md § Never"
---

# A type with no factory=True gets no generated create

**What happened.** mypy: `"type[Lab]" has no attribute "create"`. The `Service.create(context, id)` idiom in the references applies to types whose example declared a factory; a factory-less type is created implicitly on its first mutator call. Reference wording reads as if bare `create` always exists.

**Expected.** Either codegen emits `create`, or the reference says 'factory-less types are created implicitly on first mutator call; there is no `create` to call.' (suggested improvement 6, naming `rpc-constructor-calls.md`).

**Repro.** Not recorded.

**Where in the skills.** `rpc-constructor-calls.md` ('when the Type has no explicit factory, use Service.create').

**Checked at 1.6.0.** python/references/rpc-constructor-calls.md:53-61 still reads 'When the Type has no explicit factory (no factory=True method), use Service.create from the initialize hook'.
