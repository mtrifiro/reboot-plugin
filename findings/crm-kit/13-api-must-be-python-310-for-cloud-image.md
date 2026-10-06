---
id: crm-kit-13
project: crm-kit
source: "crm-maker/crm-kit/references/lessons.md §2"
reboot_version: 1.6.0
severity: unrated
target: plugin
names:
  - python/references/lifecycle-dockerfile.md
  - python/references/api-pydantic.md
tags: [negative-space, error-text]
cluster: ""
still_applies: yes
status: Open
resolved_by: ""
---

# api/ must be valid Python 3.10: the Cloud base image runs 3.10.12 and the deploy fails in rbt generate

**What happened.** The Cloud image `ghcr.io/reboot-dev/reboot-base:1.6.0` runs Python 3.10.12. Quoted forward references (`list["AccountCard"]`) or 3.11+ syntax in `api/` make the deploy fail in `RUN rbt generate` with `Failed to import schema file: issubclass() arg 1 must be a class`, though local Python 3.12 accepts them. Check: `docker run --rm -v "$PWD/api:/app/api:ro" -w /app ghcr.io/reboot-dev/reboot-base:1.6.0 python -c "import sys; sys.path.insert(0,'api'); import <pkg>.v1.<pkg>"`.

**Expected.** Keep `api/` valid Python 3.10: no quoted forward references, no 3.11+ syntax.

**Repro.** Not recorded.

**Where in the skills.** Not named by the source.

**Checked at 1.6.0.** `lifecycle-dockerfile.md` names the `reboot-base:1.6.0` image and `lifecycle-project-setup.md` says "Python 3.10+", but nothing says the image's interpreter is 3.10 or that quoted forward references fail there; `issubclass() arg 1` is not in `errors.md` (grep).
