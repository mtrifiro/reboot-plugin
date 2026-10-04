---
id: reboot-air-141-06
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §6"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - web-app/references/react-client.md
tags: [auth, frontend, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Sign-in guidance assumes a User state type

**What happened.** The canonical sign-in example in "Sign-in and Sign-out" uses `useUser()` from the generated client, and the whole gate (`user === undefined` when signed out) depends on it. `useUser` exists only if the app declares a state type named `User`, yet the skill's own comparison table says the `User` type is "Optional - only if your app needs per-user state" for a web app. This app has no per-user state, so no `User` type and no `useUser()`, but still needs authenticated callers and a sign-in button. The author invented a shape: read a domain reader at the top of the tree and treat `aborted.error.type === "Unauthenticated"` as the signed-out signal, with no way to know whether that was the intended pattern.

**Expected.** A short "No `User` type?" subsection with the supported shape. If `@reboot-dev/reboot-react` exposes a surface-agnostic session probe (a `useSession`/`useAuth` equivalent of `/__/oauth/whoami`), name it; if not, say so and bless the guard-on-reader's-`aborted` pattern.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`, "Sign-in and Sign-out".

**Checked at 1.6.0.** Still present. `web-app/references/react-client.md:209-227` still builds the gate on `useUser()` with no no-`User`-type variant; `web-app/SKILL.md:61` still calls the `User` type optional.
