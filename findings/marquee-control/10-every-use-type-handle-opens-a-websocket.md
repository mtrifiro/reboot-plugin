---
id: marquee-control-10
project: marquee-control
source: "v 1.4.1 Reboot/Archive/marquee-control/docs/reboot-learnings.md §2026-08-17 build session, bullet 10"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - python/references/react-generated-client.md
tags: [frontend, cost, negative-space]
cluster: ""
still_applies: unknown
status: Resolved
resolved_by: "python/references/react-generated-client.md § Limits"
---

# Every use<Type>({id}) handle opens its own reactive WebSocket, even with no reader hook

**What happened.** Even if you never call a `use<Reader>()` hook on it, each `use<Type>({id})` handle opens a reactive WebSocket: the lab's fixed pool of 24 `useCart` handles showed up as 24 `/__/reboot/rpc/marquee.v1.Cart:lab-cart-NN` sockets (visible as 502 handshakes during a backend hot-restart; they reconnect). Budget handle pools accordingly.

**Expected.** Not recorded.

**Repro.** Mount 24 `useCart({id})` handles without calling any reader hook; watch the network panel.

**Where in the skills.** `python/references/react-generated-client.md` (Limits / Scales as).

**Checked at 1.6.0.** `react-generated-client.md` § Limits describes the local transport as 'a WebSocket multiplex' and budgets per subscription, not per handle; nothing says a bare handle opens a socket. Not re-tested against the 1.6.0 client, so whether it still applies is unknown.

**Resolution (2026-10-10).** `react-generated-client.md` § Limits: every `useFoo({ id })` handle opens its own reactive WebSocket; a pool of handles costs one socket each.
