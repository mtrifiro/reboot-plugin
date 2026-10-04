---
id: reboot-crm-78
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P4.9"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - python/references/react-generated-client.md
  - web-app/references/react-client.md
tags: [frontend, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Two useFoo overloads confuse ReturnType

**What happened.** `ReturnType<typeof useAccount>` resolves to the no-argument overload (`{ account, isLoading }`), so passing a handle to a child typed that way fails. `UseAccountApi` is the right type.

**Expected.** One line in `react-generated-client.md`: type a handle as `UseFooApi`, not `ReturnType<typeof useFoo>`, which resolves to the no-argument overload (recommendation: do it).

**Repro.** Not recorded.

**Where in the skills.** `python/references/react-generated-client.md`.

**Checked at 1.6.0.** `python/references/react-generated-client.md` and `web-app/references/react-client.md` (lines ~221-242) show `UseFooApi` but neither warns against `ReturnType<typeof useFoo>`.
