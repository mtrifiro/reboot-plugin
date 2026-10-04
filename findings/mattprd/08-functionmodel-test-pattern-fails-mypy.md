---
id: mattprd-08
project: mattprd
source: "2026.08.22 REBOOT_FINDINGS.md §8"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - python/references/testing-external-context.md
tags: [testing, scaffold]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# The documented test pattern for swapping agent models fails mypy

**What happened.** `testing-external-context.md` documents mocking LLMs with `module.agent.wrapped.model = FunctionModel(...)`. pydantic-ai types `AbstractAgent.model` as a read-only property, so mypy reports `Property "model" defined in "AbstractAgent" is read-only [misc]` on the prescribed line, while the assignment works at runtime.

**Expected.** Either a supported `Agent.set_model_for_testing(...)` (or context-manager override) on the Reboot wrapper, or `# type: ignore[misc]` in the reference snippet with a sentence explaining why.

**Repro.** Not recorded.

**Where in the skills.** `testing-external-context.md`.

**Checked at 1.6.0.** python/references/testing-external-context.md:281 still shows `wiki_module.librarian.wrapped.model = FunctionModel(self.script.step)` with no `type: ignore[misc]` (grep found none in that file).
