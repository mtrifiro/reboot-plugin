---
id: reboot-crm-54
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.18"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/api-pydantic.md
tags: [error-text, negative-space]
cluster: "4.4"
still_applies: unknown
status: Resolved
resolved_by: "python/references/api-pydantic.md § Errors you will see"
---

# Nested Model fields: the error names the fix only halfway

**What happened.** `Field(default_factory=AccountCard)` fails with "`default_factory` ... not supported for type `AccountCard`. Only `list`, `dict` types can have a `default_factory`". The actual rule (`Optional[AccountCard] = Field(default=None)`, hydrate in the constructor) is in `api-pydantic.md` but not in the message.

**Expected.** Extend the error with "use `Optional[AccountCard] = Field(default=None)` and hydrate it in the constructor". The source: the difference between a lookup and a guess.

**Repro.** Declare a nested `Model` field with `Field(default_factory=<Model>)`.

**Where in the skills.** `python/references/api-pydantic.md` (rule is documented there per the source).

**Checked at 1.6.0.** `api-pydantic.md` shows `default_factory=list`/`dict` (lines ~309-402); the `Optional[Model]` rule was not located by grep.
