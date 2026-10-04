---
id: reboot-crm-33
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P2.4"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/testing-web-app.md
tags: [testing, cost, frontend]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Every browser scenario pays a full Vite boot, because the backend URL is baked in at spawn

**What happened.** Browser scenarios cost about 11.6 s each against about 1.6 s for a backend scenario: 51 of 482 scenarios (11%) take 47% of the wall clock. One Vite dev server per module is not available: `reboot/bdd/vite.py` passes the backend address as `VITE_REBOOT_URL` in the environment of the `npx vite` subprocess at spawn, each scenario's `Reboot()` gets a fresh envoy port, and reusing a `Frontend` fails with `assert self._server is None, 'already serving'`. The `Frontend` docstring states this is deliberate.

**Expected.** That the stateless dev server could be module- or session-scoped while the `Application` stays function-scoped. Recommendation: let the frontend learn its backend URL at runtime (a URL the page fetches, or a proxied stable path), else say in `testing-web-app.md` that the per-scenario boot is intrinsic.

**Repro.** Change the `frontend` fixture in a browser test module to `scope="module"`; the first scenario passes, later ones fail with `AssertionError: already serving`.

**Where in the skills.** `python/references/testing-web-app.md`.

**Checked at 1.6.0.** `testing-web-app.md` (vite fixture, lines ~69-88) does not say the per-scenario boot is intrinsic or its cost.
