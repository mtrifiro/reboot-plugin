---
id: reboot-crm-67
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P3.28"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/state-scalar-fields.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/state-scalar-fields.md § Never; python/references/api-pydantic.md § Limits"
---

# A model field cannot be bytes, though the reference lists its default; the refusal is an empty message

**What happened.** `state-scalar-fields.md` ("Common Scalar Defaults") lists `bytes` with default `b""`. Declared that way, `rbt generate` refuses: "Field `image` in model `LogoState` uses `default` which is not supported for type `bytes`", naming `str`, `int`, `float`, `bool`, `Optional` and `Literal` as the only types with a default. Declared `Optional[bytes] = None`, it fails with `Failed to import schema file: ` and nothing after the colon. `validate_all_fields_are_reboot_base_classes` asserts `field_type in (int, float, str, bool)` (`reboot/api.py:1169`), so `bytes` is not a field type, and the bare `AssertionError` has no message. Workaround: base64 in a `str`.

**Expected.** Either `bytes` fields (Protobuf has them), or the reference not listing them and the validator saying "`bytes` is not a supported field type" in words.

**Repro.** Any model with `x: Optional[bytes] = Field(tag=1, default=None)`, then `rbt generate`.

**Where in the skills.** `python/references/state-scalar-fields.md` "Common Scalar Defaults".

**Checked at 1.6.0.** `python/references/state-scalar-fields.md` line 65 still lists `bytes` with default `b""` in the defaults table.
