---
id: restaurant-app-2-02
project: restaurant-app-2
source: "restaurant-app-2/FINDINGS.md § Plugin skills, item 1"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - web-app/references/ui-design.md
  - mcp-ui/references/ui-design.md
tags: [negative-space, frontend]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# ui-design.md is silent on restyling an existing app

**What happened.** Restyling the app to a new brand, editing the `:root` tokens wasn't enough: three earlier looks had been appended as override layers at the end of `styles.css`, and the last ones re-pinned `--bg` and `--nav` to raw hex, so they beat the token edit. The logo (`fill="#fff"`) and the favicon in `index.html` were hard-coded too. A brand with a page color, ink and highlight (not one accent) also doesn't fit "brand from one color". The dark-scheme accent was then made the brand's sage green, which the reference's own rule forbids next to a green `--good`.

**Expected.** `web-app/references/ui-design.md` to say: restyle by changing token values in place, never by appending a layer; fold or delete existing layers; update the logo, favicon and font link; how to read a brand from its site; multi-color brands set `--bg`/`--ink` directly; the accent may change per scheme but stays off green.

**Repro.** Ask for "a Linear look", then "friendlier", then "restyle in brand X" on a scaffolded web app; then grep `styles.css` for `:root` below the token blocks.

**Where in the skills.** `web-app/references/ui-design.md` (05, 12, Never); `mcp-ui/references/ui-design.md` (shared stylesheet).
