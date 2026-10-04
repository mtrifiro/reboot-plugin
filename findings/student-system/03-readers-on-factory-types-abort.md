---
id: student-system-03
project: student-system
source: "student-system/reboot-findings.md §3"
reboot_version: 1.5.0
severity: unrated
target: plugin
names:
  - python/references/rpc-refs.md
tags: [contradiction, error-text, negative-space]
cluster: "4.1"
still_applies: yes
status: Open
resolved_by: ""
---

# Readers on factory-constructed types abort instead of returning zero state

**What happened.** `rpc-refs.md` says a reader on a non-existent actor "returns the zero-valued state". For every type with `factory=True` (Term, Course, Program, Student, CourseAttempt, Petition, GraduationApplication) it raises `<Type>.GetAborted: aborted with 'StateNotConstructed'`. The app probes for existence constantly. Workaround: four helpers in `backend/src/servicers/common.py` (`get_course`, `get_term`, `get_program`, `get_application`) catch `<Type>.GetAborted` and return `None`. Side effect: every probe of a missing actor logs `WARNING State '<id>' for state type '<type>' not constructed (call any writer to construct). Will silence this message for the next 5 minutes.`, which drowns test output. Repeat of Reboot Air 2 and 14 (reboot-air-02, reboot-air-14).

**Expected.** Either the documented behaviour should hold, or a failed probe should not warn.

**Repro.** Not recorded.

**Where in the skills.** `python/references/rpc-refs.md`, "Refs Don't Materialize Actors" (contradicts `python/references/stdlib-ordered-map.md` on unconstructed reads).

**Checked at 1.6.0.** `python/references/rpc-refs.md` line ~105 still reads "A reader call on a non-existent actor returns the zero-valued state".
