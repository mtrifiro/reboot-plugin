---
id: student-sor-15
project: student-sor
source: "student-sor/reboot-findings.md §9"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - web-app/SKILL.md
  - run/SKILL.md
  - dashboard/SKILL.md
  - python/references/rpc-calls.md
tags: [auth, operations, version-drift, negative-space]
cluster: "F"
still_applies: yes
status: Open
resolved_by: ""
---

# Small things: Development() identities, expunge --yes, dashboard flag and port, pydantic_settings warning, mypy **kwargs

**What happened.** (1) `Development()` has exactly five identities and mints opaque per-app user ids by design; any app with roles has to key its directory by the `email` claim, and `Development(claims=["email", "name"])` is the only way to get it; the author confirmed this by reading `oauth_providers.py`. (2) `rbt dev expunge` needs `--yes` from a non-interactive shell; the `run` skill does not mention it. (3) The `dashboard` skill starts `rbt dashboard --api-directory=api`, which rbt 1.5.0 rejects (`unrecognized arguments`); started plain it finds `api/` from `.rbtrc`. With two projects on one machine the default port 9871 is taken by whichever dashboard came first, and nothing warns that you are looking at the other project's API. (4) The `pydantic_settings` `IncompleteFieldDefinitionWarning` about `lifespan` prints on every backend start. (5) `mypy` needs `**kwargs` passed to generated methods to be a `TypedDict`, not `dict[str, str]`, or every overload fails.

**Expected.** The web-app skill should say up front what `Development()` provides. A line in `rpc-calls.md` about `TypedDict` for forwarded kwargs.

**Repro.** Not recorded.

**Where in the skills.** `web-app/SKILL.md`, `run/SKILL.md`, `dashboard/SKILL.md`, `python/references/rpc-calls.md`.

**Checked at 1.6.0.** `--api-directory` is gone from all skills (fixed). `run/SKILL.md` still has no `--yes`; `rpc-calls.md` has no `TypedDict` note (grep found none); `web-app/SKILL.md` lines ~70-127 describe `Development()` but not the five-identity limit or the `claims=["email",...]` need; no dashboard-port-collision warning.
