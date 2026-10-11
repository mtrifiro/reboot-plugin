#!/usr/bin/env sh
# PreToolUse, for Claude Code and Codex: while this project's test suite
# runs, refuses the tool calls that make scenarios fail for reasons that
# look like the framework's (the findings A.14 and P3.169): regenerating
# code, starting the dev loop or a dev server, expunging, and edits under
# api/, backend/, web/ and frontend/. `tests/last_run.py` keeps
# `tests/.suite-running` (the pytest process's pid) while a run is on;
# a run killed outright leaves the file behind, so a dead pid lifts the
# guard. `hooks.json` registers this beside the schema guard.
#
# Fails open: no python3, unreadable input, or no project lets the call
# through.

set -eu

input=$(cat)
command -v python3 >/dev/null 2>&1 || exit 0

printf '%s' "$input" | python3 -c '
import json
import os
import re
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
if data.get("hook_event_name", "PreToolUse") != "PreToolUse":
    sys.exit(0)
tool = data.get("tool_name", "")
inp = data.get("tool_input") or {}
cwd = data.get("cwd") or os.getcwd()

RUNS = re.compile(r"\brbt\s+(?:dev\s+run|generate|dev\s+expunge)\b|\bnpm\s+run\s+dev\b|(?:^|[\s;&|])vite\b")
CODE = ("api", "backend", "web", "frontend")


def root_of(path):
    d = os.path.abspath(path)
    while True:
        if os.path.isfile(os.path.join(d, ".rbtrc")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def running(root):
    """The pid of a live suite in `root`, or None."""
    try:
        with open(os.path.join(root, "tests", ".suite-running")) as f:
            pid = int(json.load(f).get("pid", 0))
        os.kill(pid, 0)
        return pid
    except Exception:
        return None


def deny(pid, what):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            f"The test suite is running (pid {pid}; tests/.suite-running). {what} during a run "
            "fails scenarios with `Method not found!` on unrelated methods (AGENTS.md, rule 4). "
            f"Wait for the run to finish, or stop it (kill {pid}) and run it again afterwards."),
    }}))
    sys.exit(0)


paths = []
if tool in ("Edit", "MultiEdit", "Write") and isinstance(inp.get("file_path"), str):
    paths = [inp["file_path"]]
elif tool == "apply_patch":
    text = inp.get("input") if isinstance(inp, dict) else ""
    if not isinstance(text, str):
        text = ""
    paths = re.findall(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", text, re.M)
elif tool == "Bash" and isinstance(inp.get("command"), str):
    command = inp["command"]
    root = root_of(cwd)
    pid = running(root) if root else None
    if pid and RUNS.search(command):
        deny(pid, "Regenerating, restarting the backend or a dev server, or expunging")
    sys.exit(0)
else:
    sys.exit(0)

for path in paths:
    full = os.path.abspath(os.path.join(cwd, path))
    root = root_of(os.path.dirname(full))
    if not root:
        continue
    rel = os.path.relpath(full, root)
    if rel.split(os.sep)[0] not in CODE:
        continue
    pid = running(root)
    if pid:
        deny(pid, f"Editing {rel}")
' 2>/dev/null || true
exit 0
