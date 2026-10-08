---
id: new-theater-02
project: new-theater
source: "new-theater/FINDINGS.md § Framework, item 2"
reboot_version: 1.6.0
severity: yellow
target: framework
names:
  - python/references/rpc-refs.md
tags: [error-text]
cluster: ""
duplicate_of: reboot-air-141-13
still_applies: yes
status: Open
resolved_by: ""
---
# A Reader named schedule fails rbt generate with only "protoc failed"

**What happened.** A Reader named `schedule` (reserved: it collides with `ref().schedule()`) makes `rbt generate` print only "`protoc` failed with exit status 1" with no hint of the cause; mypy then reports `Too many positional arguments for "schedule" of "WeakReference"`. `rpc-refs.md` lists the reserved names.

**Expected.** The generator names the method and says the name is reserved.

**Repro.** Declare a Reader named `schedule` and run `rbt generate`.

**Where in the skills.** `python/references/rpc-refs.md` (reserved names are listed there).
