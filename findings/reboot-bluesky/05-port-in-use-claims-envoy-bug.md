---
id: reboot-bluesky-05
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §5"
reboot_version: 1.4.1
severity: unrated
target: framework
names: []
tags: [error-text, operations]
cluster: "4.4"
duplicate_of: mattprd-03
still_applies: unknown
status: Resolved
resolved_by: "python/references/lifecycle-rbtrc.md § Errors you will see; run/references/stop-restart-reset.md § Errors you will see"
---

# Port-in-use error claims to be a Reboot Envoy bug

**What happened.** Starting `rbt dev run` while another Reboot app held :9991 produced 'Envoy rejected the xDS listener configuration ... This is a bug in the Envoy configuration Reboot generated ... please report this bug', but the embedded cause was `cannot bind '0.0.0.0:9991': Address already in use`.

**Expected.** Detect the bind failure and print 'port 9991 is in use; pass `dev run --port=<other>`' instead of asking users to file a bug.

**Repro.** Not recorded.

**Where in the skills.** Not recorded.
