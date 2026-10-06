---
id: reboot-crm-08
project: reboot-crm
source: "reboot-crm/docs/REBOOT_FINDINGS.md P1.2"
reboot_version: 1.6.0
severity: red
target: plugin
names:
  - python/references/patterns-common-gotchas.md
tags: [negative-space, error-text, operations]
cluster: "4.4"
still_applies: yes
status: Open
resolved_by: ""
---

# rbt generate dies with ENOBUFS once the generated TypeScript passes 1 MiB

**What happened.** On 2026-09-20, adding two `Optional[Research]` fields to request models made every `rbt generate` fail, and with it `rbt dev run` ("Protoc compilation failed ... waiting for modification"): `protoc-gen-es-with-deps: spawnSync /bin/sh ENOBUFS`, `--es_out: protoc-gen-es: Plugin failed with status code 1`, `protoc failed with exit status 1`. The Python side generated and `mypy` passed; only the TypeScript plugin died. Cause: `reboot/protoc_gen_es_with_deps.cjs` runs the real plugin with `execSync("protoc-gen-es", { encoding: "buffer", input })` and no `maxBuffer`; Node's default is 1 MiB and covers the whole `CodeGeneratorResponse`. The app's `crm_pb.ts` alone was 1.03 MB. Workaround: patch the wrapper in the venv with `maxBuffer: 256 * 1024 * 1024`; `uv sync` or any reinstall of `reboot==1.6.0` undoes it (it did, see reboot-crm-07). Seen again 2026-10-05 in a much smaller app: Testboard (later Ultraboard, `alt-dashboard`), a separate Reboot 1.6.0 web app with **5 state types** across three API files (`testboard.py`, `domain.py`, `history.py`), hit the same wall. The cap is on the whole response, not one file: no generated file was over 1 MiB (`testboard_pb.ts` 728 KB, `history_pb.ts` 167 KB, `domain_pb.ts` 106 KB, together 1.00 MB), and adding one `list[str]` field to one model tipped it, so splitting an API across files does not help. And a running `rbt dev run` keeps failing after the patch: a standalone `rbt generate` succeeded, but the `rbt dev run` already up kept printing `spawnSync /bin/sh ENOBUFS` on every change until it was stopped and started again. Same workaround there (`maxBuffer: 64 * 1024 * 1024`), plus the restart.

**Expected.** No cap, or one large enough that an ordinary first project cannot hit it (a five-type app did), and an error that names the limit rather than `ENOBUFS`. Source fix list: (1) pass `maxBuffer` (256 MB or `Infinity`), recommended immediately; (2) stream the response; (3) catch `ENOBUFS` and name the 1 MiB default; (4) `python/references/patterns-common-gotchas.md` records the symptom and the venv patch, noting that `uv sync` undoes it and that a running `rbt dev run` must be restarted after the patch. The five-type case makes (1) more urgent.

**Repro.** Any API whose generated `*_pb.ts` approaches 1 MB; here `api/crm/v1/crm.py` at ~154 KB of pydantic models; or a 5-type app whose generated `*_pb.ts` files together reach 1 MiB (alt-dashboard).

**Where in the skills.** `python/references/patterns-common-gotchas.md`.

**Checked at 1.6.0.** No `ENOBUFS` or `maxBuffer` anywhere under `skills/` (grep).
