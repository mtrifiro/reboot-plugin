---
id: reboot-air-141-01
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §1"
reboot_version: 1.4.1
severity: yellow
target: plugin
names:
  - python/references/api-pydantic.md
tags: [negative-space]
cluster: "4.1"
still_applies: yes
status: Resolved
resolved_by: "python/references/api-pydantic.md § Do this"
---

# response=X reuse versus clone is never stated

**What happened.** `api-pydantic.md` (section "Generated Request/Response Names Come From the Method Name") says the generated name is method-derived (`Airport.DetailsResponse`) but never says whether that is the same class as the model passed to `response=` or a distinct generated message with copied fields. This matters when one model is both a method's `response=` and the element type of a `list[...]` on another method's response (`Airport.details` returns one airport; `Airline.network` returns 24). Unable to tell, the author wrapped every shared model in a one-field envelope (`AirportDetailsResponse { airport: Optional[AirportDetails] }`), costing an extra model, an extra `Optional` unwrap at each call site, and an extra layer in the generated TypeScript. The alternative was reading generated `*_rbt.py`, which the web-app skill forbids.

**Expected.** A subsection "Reusing a model across methods" stating the rule and showing the canonical shape for a model that is both a single response and a list element. If the envelope pattern is the recommendation, say so.

**Repro.** Not recorded.

**Where in the skills.** `python/references/api-pydantic.md`, section "Generated Request/Response Names Come From the Method Name".

**Checked at 1.6.0.** No statement on reuse versus clone found in `python/references/api-pydantic.md` or `python/references/react-generated-client.md` (grep for same class / clone / reuse / envelope / shared model / list element returned nothing).
