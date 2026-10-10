---
id: plugin-browser-08
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 6"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - web-app/references/react-client.md
  - python/references/react-generated-client.md
tags: [frontend, negative-space]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---
# A page with more than ~6 live reads starves its own data

**What happened.** The Architecture page added nine `useListElements` subscriptions (one per kind) to its five existing reactive reads. One of the page's `useFlow(...).useGet()` reads then never resolved: its counts stayed as loading placeholders, with no error in the console. Browsers keep at most six HTTP/1.1 connections open to one origin, and each reactive read holds one open. Fetching the nine lists once with plain calls (`catalog.listElements(...)`, a promise), refetched when a scan changes the counts, fixed it.

**Expected.** The React client reference to say how many reactive reads one page can hold open against a local backend, and to suggest a plain call for data that only needs reading once.

**Repro.** One page with seven or more `use<Method>()` reactive reads against `rbt dev run` on `http://localhost`.

**Where in the skills.** `web-app/references/react-client.md`; `python/references/react-generated-client.md`.
