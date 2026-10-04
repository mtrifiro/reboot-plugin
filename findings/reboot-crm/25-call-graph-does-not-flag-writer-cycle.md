---
id: reboot-crm-25
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.15"
reboot_version: 1.6.0
severity: yellow
target: plugin
names:
  - python/references/rpc-calls.md
  - python/references/api-methods.md
tags: [negative-space, pattern, cost]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# The call graph does not flag the cross-actor writer cycle that deadlocks two ordinary requests

**What happened.** Twice in one afternoon (the first had been in the app for months). `Contact.update` wrote the account's copy of a seat holder's name inline while `Account.set_contact_role` holds the account and writes the contact: a writer cycle, so two people working normally deadlock each other, but it takes two concurrent requests on two specific paths and no test run produces that. The second: `Account.accept_domain` calling `Pipeline.note_domain` inside its transaction, when `Pipeline` already writes into `Account` in five places. `rbt generate`, `mypy` and the dashboard's call graph (which draws the cycle) all stayed silent. The hazard appears once in the references, in `api-methods.md`, as a symptom of picking the wrong factory ("deadlocks when a `Writer` tries to call into another actor"), filed under the wrong heading. Reboot's author, shown this, said a cycle "usually means that there is a bad data abstraction"; the first fix (inverting the call) worked and was wrong: the cycle was a symptom of `Pipeline.domains` being a second, half-maintained copy of `Account.domain`, with no reader in the application. Deleting it removed the cycle by removing the duplicated fact. `Account -> Intelligence -> Account` also exists and is fine because Intelligence reaches back through `per_workflow`, its own transaction later; it greps identically to the bug.

**Expected.** The graph already computed should flag writer cycles, phrased as a question about shared state and ownership ("`Pipeline` and `Account` both write the account's domain... decide which one owns it") rather than an instruction to move a method. Source fix list: (1) flag cycles in the call graph; (2) better, fail `rbt generate` naming the two methods; (3) give the hazard its own heading in `rpc-calls.md`, including the `per_workflow` distinction.

**Repro.** Give type A a transaction that calls a writer on type B, when some transaction on B already calls a writer on A; generate; nothing is reported.

**Where in the skills.** `python/references/rpc-calls.md` (heading missing), `python/references/api-methods.md` line ~186.

**Checked at 1.6.0.** `api-methods.md` line 186 still has only the one-clause "deadlocks when a `Writer` tries to call into another actor"; `rpc-calls.md` has no writer-cycle heading (grep for `deadlock` in references finds only that line).
