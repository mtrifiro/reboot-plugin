---
id: reboot-bluesky-11
project: reboot-bluesky
source: "REBOOT_FINDINGS.md §11"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [cost, pattern, frontend]
cluster: "D"
still_applies: yes
status: Open
resolved_by: ""
---

# Reader-subscription establishment is expensive under burst

**What happened.** A feed page mounting N reactive reader hooks opens N server-streaming subscriptions at once; on `rbt dev run` the slowest of the burst takes seconds: with 50 concurrent subscriptions (25 cards x 2 readers) the slowest completed ~6.8s after navigation; 25 combined readers ~4.6s; 12 ~4.9s (high variance; floor never near the ~100ms of a single subscription in isolation). Median setup is fine; the tail under concurrency is the problem. Update: implementing a hydrated-page pattern (one reader returning a full page of post snapshots incl. per-viewer like state) took full-first-page paint from ~5-7s to ~1.5s cold, all cards in a single frame.

**Expected.** Profile subscription establishment under concurrent load, consider multiplexing on the shared WebSocket, document the cost of 'one hook per list item', and bless a server-side hydrated-page pattern (one reader returning N child snapshots) for first paint with per-item subscriptions only for visible rows. The source strongly recommends documenting the hydrated page as the blessed feed pattern.

**Repro.** Not recorded.

**Where in the skills.** Not recorded; `react-generated-client.md` is the natural home.

**Checked at 1.6.0.** python/references/react-generated-client.md:112-116 presents per-hook subscriptions as free with no burst-cost or hydrated-page pattern.
