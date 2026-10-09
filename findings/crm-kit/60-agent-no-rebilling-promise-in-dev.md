---
id: crm-kit-60
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §9"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/agent-pydantic-ai.md
  - python/references/agent-tools.md
tags: [cost, contradiction]
cluster: "D"
duplicate_of: reboot-crm-04
still_applies: no
status: Open
resolved_by: ""
---

# reboot.agents.pydantic_ai.Agent's no-re-billing promise covers replay, not effect validation

**What happened.** The promise covers replay, not effect validation, so the source wraps the model call as in its paid-call rule. reboot 1.6.0 publishes only the `anthropic` and `dev` extras, so any other SDK is a dependency you add yourself. §11: `agent-pydantic-ai.md` and `agent-tools.md` promise "no re-billing", which dev effect validation breaks.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** `agent-pydantic-ai.md`, `agent-tools.md` (§11).

**Checked at 1.6.0.** `agent-pydantic-ai.md` § Limits (~117-119) now says the Agent's model calls pass `effect_validation=EffectValidation.DISABLED` (1.6.0 source), tool calls do not opt out, and the promise covers replay plus this opt-out, not other calls around the agent. `agent-tools.md` § Limits (~77) says tool calls keep effect validation on. The skill's statement disagrees with the source's claim about the Agent's own model calls; it was not re-verified here. `lifecycle-project-setup.md` names `reboot[anthropic]` as the extra.
