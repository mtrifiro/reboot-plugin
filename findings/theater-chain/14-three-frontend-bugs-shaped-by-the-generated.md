---
id: theater-chain-14
project: theater-chain
source: "theater-chain/reboot-findings.md §13b"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
  - web-app/references/react-client.md
tags: [frontend, pattern, negative-space]
cluster: "E"
still_applies: yes
status: Resolved
resolved_by: "python/references/patterns-react-state.md § Never"
---

# Three frontend bugs shaped by the generated client

**What happened.** Found chasing "held seats do not show up in the cart"; none Reboot-specific but all shaped by the generated client. (1) `crypto.randomUUID()` is undefined off a secure origin: the skill correctly has the browser mint ids and timestamps, but opening the SPA at the Vite `Network:` URL (`http://192.168.x.x:5173`) instead of `localhost` makes it throw inside the click handler, wedging the button with nothing shown. Every app following the caller-mints-the-id rule inherits this. (2) Mutations never throw, which is why a `try/catch` is easy to omit, but the catch is still needed for everything else in the handler (id minting, transport teardown) or a `setBusy(true)` never unwinds. (3) A derived array in a `useEffect` dependency list spins forever: reader hooks re-render on every push, so `response.seats.filter(...)` is a fresh array many times a second and produced `Maximum update depth exceeded`; depend on a derived string instead.

**Expected.** Ship a `newId()` helper with a `getRandomValues` fallback in `react-client.md` beside the mint-ids-client-side advice; add "wrap the handler, not the call" to "Mutations Never Throw"; add a warning about derived arrays in effect deps to "Live Updates Are Free".

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md` ("Mutations Never Throw", "Live Updates Are Free") and `web-app/references/react-client.md`.

**Checked at 1.6.0.** Still absent. Grep of `python/references/react-generated-client.md` and `web-app/references/react-client.md` for randomUUID / newId / useEffect found nothing relevant; "Mutations Never Throw" is at `python/references/react-generated-client.md:87`.
