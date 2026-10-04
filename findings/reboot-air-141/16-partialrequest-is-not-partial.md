---
id: reboot-air-141-16
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §16"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [contradiction, frontend]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# partialRequest is not partial

**What happened.** `react-generated-client.md` says "`partialRequest` is optional and partial - every field has a default." The generated TypeScript emits a fully-required object; calling a reader with a subset fails to compile: `error TS2769: Argument of type '{ date: string; origin: string; destination: string; }' is not assignable ... is missing the following properties: cursor, limit`. Callers must pass `cursor: ""` and `limit: 50` explicitly even when the backend defaults them. Cost: one failed build and a permanently noisier call site.

**Expected.** If the emitted type is intended to be complete, correct the sentence and the parameter name in the docs; if partiality is intended, codegen should emit `Partial<...>`. Per the source, the reference is the one that is wrong.

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`.

**Checked at 1.6.0.** Still present. `python/references/react-generated-client.md:42-43` and `:52` still say `partialRequest` is optional and partial (`Foo.PartialBarRequest`).
