---
id: tool-checks-01
project: tool-checks
source: "tools/check-symbols.py, 2026-10-04"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/stdlib-oauth-tokens.md
  - python/references/auth-external-api-calls.md
  - mcp-ui/references/auth-store-tokens.md
tags: [version-drift, auth, error-text]
cluster: "A"
still_applies: yes
status: Open
resolved_by: ""
---

# `reboot.std.oauth.v1.oauth` does not exist in the reboot 1.6.0 wheel

**What happened.** Three references tell the agent to
`from reboot.std.oauth.v1.oauth import oauth_library` (and the `GOOGLE`
/ `GITHUB` constants, `_key_manager_id`) and to mount `oauth_library()`
for `store_tokens=True` and `OAuthTokenManager`. In the
`reboot[anthropic,dev]==1.6.0` wheel uv resolves for macOS / Python 3.12,
`reboot/std/` contains only `ciphertext`, `collections`, `item`,
`presence` and `pubsub`. The generated `rbt/std/oauth/v1/oauth_rbt.py`
(with `OAuthTokenManager`) ships, but the servicer module that defines
`oauth_library` does not. The framework's own boot error
(`reboot/aio/applications.py:994-996`) points at the same missing module.

**Expected.** Either the module ships (framework packaging fix, file
upstream), or the references name where `oauth_library` actually lives.

**Repro.** `bin/uv run --no-project --python=3.12 --with='reboot[anthropic,dev]==1.6.0' python -c 'import reboot.std.oauth.v1.oauth'`
→ `ModuleNotFoundError: No module named 'reboot.std.oauth'`.

**Where in the skills.** `python/references/stdlib-oauth-tokens.md:19,39,71`;
`python/references/auth-external-api-calls.md:36,209,303`;
`mcp-ui/references/auth-store-tokens.md:49`.

**Checked at 1.6.0.** Found by `tools/check-symbols.py`. Not verified on
Linux wheels; check whether this is platform-specific before filing.

**Phase 3 follow-up (2026-10-04).** Also absent from the PyPI
`manylinux_2_34_x86_64` 1.6.0 wheel (its `RECORD` has no
`reboot/std/oauth/`; aarch64 not checked), so it is not
platform-specific. `Application._require_oauth_libraries`
(`reboot/aio/applications.py:727,984`) imports the module whenever a
provider sets `store_tokens=True`, so from the source such an app should
fail at startup with `ModuleNotFoundError` (read, not run). Of the three
documented ways to call an external API as the user, the two built on
`OAuthTokenManager` cannot work at 1.6.0; the `Ciphertext` path does.
The references now say so in Limits / Errors. **Target: file upstream
as a packaging bug** — the plugin can only document it.
