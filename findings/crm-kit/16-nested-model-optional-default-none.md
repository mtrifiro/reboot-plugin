---
id: crm-kit-16
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: framework
names:
  - python/references/api-pydantic.md
tags: [error-text]
cluster: "4.4"
duplicate_of: reboot-crm-54
still_applies: no
status: Resolved
resolved_by: "python/references/api-pydantic.md § Errors you will see"
---

# A nested model field is Optional[M] = Field(default=None), hydrated in the constructor

**What happened.** `default_factory=M` is refused ("Only `list`, `dict` types can have a `default_factory`"). Rule: `Optional[M] = Field(tag=..., default=None)`, hydrated in the constructor.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/errors.md` (line ~237) and `api-pydantic.md` § Errors you will see index the `default_factory` refusal; `patterns-common-gotchas.md` lists `default_factory=AccountCard` as a Never.
