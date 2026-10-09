---
id: crm-kit-11
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/api-pydantic.md
  - python/references/api-methods.md
tags: [error-text]
cluster: "4.1"
duplicate_of: reboot-crm-80
still_applies: no
status: Obsolete
resolved_by: ""
---

# Servicers type requests as <Type>.<MethodPascal>Request, whatever the model is called

**What happened.** Servicers must type request and response models as `<Type>.<MethodPascal>Request`, whatever the model is called. A model named for its content gets `AttributeError: type object 'Lead' has no attribute ...`. Rule: name request and response models after the method.

**Expected.** Not recorded.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.

**Checked at 1.6.0.** `python/references/api-pydantic.md` line ~95 (§ Do this) says each method yields `<Type>.<MethodPascalCase>Request`; `api-methods.md` line ~109 adds "never the class you passed"; `errors.md` line ~67 indexes the `AttributeError`.
