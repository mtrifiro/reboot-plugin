#!/usr/bin/env sh
# PreToolUse, for Claude Code and Codex: while this project's test suite
# runs, refuses the tool calls that make scenarios fail for reasons that
# look like the framework's (the findings A.14 and P3.169): regenerating
# code, starting the dev loop or a dev server, expunging, and edits under
# api/, backend/, web/ and frontend/, whether by an edit tool or by a
# shell command (`sed -i`, a redirect, `cp`, `mv`, `rm`, `tee`, also
# after a `cd`; a `git checkout`, `restore`, `stash` or `reset --hard`
# that rewrites them). `tests/last_run.py` keeps
# `tests/.suite-running` (the pytest process's pid) while a run is on;
# a run killed outright leaves the file behind, so a dead pid lifts the
# guard. `hooks.json` registers this beside the schema guard.
#
# Fails open: no python3, unreadable input, or no project lets the call
# through.

set -eu

input=$(cat)
command -v python3 >/dev/null 2>&1 || exit 0

# shellcheck disable=SC2016  # the python program is the single-quoted string
printf '%s' "$input" | python3 -c '
import json
import os
import re
import shlex
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


def heredoc_free(command):
    """The command without line continuations and heredoc bodies (data)."""
    command = command.replace("\\\n", " ")
    out, pending = [], []
    for line in command.split("\n"):
        if pending:
            end, strip = pending[0]
            if (line.lstrip("\t") if strip else line) == end:
                pending.pop(0)
            continue
        out.append(line)
        for m in re.finditer(r"(?<!<)<<(-?)\s*([\x27\x22]?)([\w.-]+)\2", line):
            pending.append((m.group(3), m.group(1) == "-"))
    return "\n".join(out)


OPS = ("&>>", "<<<", "<<-", "&&", "||", ";;", ">>", ">|", ">&", "&>", "<<", "<>",
       "(", ")", ";", "|", "&", ">", "<", "\n")
WRITE_OPS = {">", ">>", ">|", "&>", "&>>", "<>", ">&"}
PREFIXES = {"sudo", "command", "builtin", "exec", "nohup", "time", "nice", "env", "xargs"}


def pieces(command):
    """Simple commands as (words, written files), and "(" / ")" for a subshell."""
    lex = shlex.shlex(heredoc_free(command), posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    try:
        tokens = list(lex)
    except ValueError:
        tokens = command.split()
    words, writes, redirect = [], [], None
    for token in tokens:
        if token and all(c in "();<>|&\n" for c in token):
            ops, i = [], 0
            while i < len(token):
                op = next(o for o in OPS if token.startswith(o, i))
                ops.append(op)
                i += len(op)
            for op in ops:
                if op in WRITE_OPS or op in ("<", "<<<", "<<", "<<-"):
                    if words and words[-1].isdigit():
                        words.pop()
                    redirect = op
                    continue
                if words or writes:
                    yield words, writes
                words, writes, redirect = [], [], None
                if op in ("(", ")"):
                    yield op
            continue
        if redirect is not None:
            if redirect in WRITE_OPS and not (redirect == ">&" and re.fullmatch(r"\d+|-", token)):
                writes.append(token)
            redirect = None
            continue
        if token == "$":
            continue
        words.append(token)
    if words or writes:
        yield words, writes


def positionals(args, takes=()):
    out, options, i = [], True, 0
    while i < len(args):
        a = args[i]
        if options and a == "--":
            options = False
        elif options and a.startswith("-") and len(a) > 1:
            if a in takes:
                i += 1
        elif a:
            out.append(a)
        i += 1
    return out


def option_value(args, option):
    i = args.index(option) if option in args else -1
    return [args[i + 1]] if 0 <= i < len(args) - 1 else []


def write_targets(name, args):
    if name == "sed":
        if not any(re.match(r"-[a-zA-Z]*i", a) or a.startswith("--in-place") for a in args):
            return []
        scripted = any(a in ("-e", "-f") or a.startswith(("--expression", "--file")) for a in args)
        rest = positionals(args, ("-e", "-f", "--expression", "--file"))
        return rest if scripted else rest[1:]
    if name == "perl":
        if not any(re.match(r"-[a-zA-Z]*i", a) for a in args):
            return []
        scripted = any(re.fullmatch(r"-[a-zA-Z]*[eE]", a) for a in args)
        rest = positionals(args, ("-e", "-E", "-pe", "-ne", "-pie", "-nie", "-lpe", "-lne"))
        return rest if scripted else rest[1:]
    if name in ("mv", "rm", "rmdir", "unlink", "shred", "tee"):
        return positionals(args, ("-t", "-S")) + option_value(args, "-t")
    if name == "truncate":
        return positionals(args, ("-s", "-r"))
    if name in ("cp", "ln", "rsync", "install"):
        return option_value(args, "-t") or positionals(args, ("-t", "-S", "-m", "-o", "-g", "-e"))[-1:]
    if name == "dd":
        return [a[3:] for a in args if a.startswith("of=")]
    return []


def git_targets(args, cwd, at):
    """"all" when the git command replaces the working tree, else the paths it rewrites."""
    i = 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            cwd = at(cwd, args[i + 1])
            i += 2
        elif args[i] == "-c":
            i += 2
        else:
            i += 1
    sub = args[i] if i < len(args) else ""
    rest = args[i + 1:]
    dash = rest.index("--") if "--" in rest else -1
    before = rest if dash < 0 else rest[:dash]
    after = [] if dash < 0 else [a for a in rest[dash + 1:] if a]
    paths = lambda names: [at(cwd, n) for n in names]
    if sub in ("checkout", "switch"):
        takes = ("-b", "-B", "--orphan", "-c", "-C", "--conflict")
        named = positionals(before, takes)
        if sub == "switch":
            return "all" if named or "--orphan" in before else []
        if dash >= 0:
            return paths(after)
        if not named:
            return "all" if "--orphan" in before else []
        out = []
        for k, name in enumerate(named):
            path = at(cwd, name)
            if re.search(r"[*?[{]", name) or os.path.exists(path):
                out.append(path)
            elif k == 0:
                return "all"
        return out
    if sub == "restore":
        staged = any(a == "--staged" or re.match(r"-[a-zA-Z]*S", a) for a in rest)
        worktree = any(a == "--worktree" or re.match(r"-[a-zA-Z]*W", a) for a in rest)
        if staged and not worktree:
            return []
        return paths(positionals(before, ("-s", "--source")) + after)
    if sub == "stash":
        action = next((a for a in before if not a.startswith("-")), None)
        if action in ("list", "show", "drop", "clear", "create", "store"):
            return []
        if action in (None, "push") and after:
            return paths(after)
        return "all"
    if sub == "reset":
        return "all" if any(a in ("--hard", "--merge", "--keep") for a in rest) else []
    if sub == "clean":
        force = any(a == "--force" or re.match(r"-[a-zA-Z]*f", a) for a in rest)
        dry = any(a == "--dry-run" or re.match(r"-[a-zA-Z]*n", a) for a in rest)
        if not force or dry:
            return []
        named = positionals(before, ("-e", "--exclude")) + after
        return paths(named) if named else "all"
    if sub in ("rm", "mv"):
        return paths(positionals(before) + after)
    return []


def glob_part(part):
    out, braces, i = "", 0, 0
    while i < len(part):
        c = part[i]
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[" and "]" in part[i + 1:]:
            end = part.index("]", i + 1)
            out += "[" + part[i + 1:end].replace("!", "^", 1) + "]"
            i = end
        elif c == "{":
            braces += 1
            out += "(?:"
        elif c == "}" and braces:
            braces -= 1
            out += ")"
        elif c == "," and braces:
            out += "|"
        else:
            out += re.escape(c)
        i += 1
    return re.compile(out + r"\Z")


def same_line(path, target):
    """Whether `path` (maybe a glob) is `target`, holds it, or lies under it."""
    a = [p for p in path.split("/") if p]
    b = [p for p in target.split("/") if p]
    for x, y in zip(a, b):
        if re.search(r"[*?[{]", x):
            if not glob_part(x).match(y):
                return False
        elif x != y:
            return False
    return True


def shell_writes_code(command, cwd, root):
    """The code directory a shell command rewrites, or None."""
    home = os.path.expanduser("~")
    targets = [os.path.join(root, d) for d in CODE]

    def at(d, word):
        word = home + word[1:] if word.startswith("~") else word
        return os.path.normpath(os.path.join(d, word))

    def hit(path):
        return next((t for t in targets if same_line(path, t)), None)

    d, subshells, pushed = os.path.normpath(cwd), [], []
    for piece in pieces(command):
        if piece == "(":
            subshells.append(d)
            continue
        if piece == ")":
            d = subshells.pop() if subshells else d
            continue
        words, writes = piece
        for w in writes:
            if hit(at(d, w)):
                return hit(at(d, w))
        i = 0
        while i < len(words) and (re.match(r"[A-Za-z_][A-Za-z0-9_]*=", words[i])
                                  or os.path.basename(words[i]) in PREFIXES):
            i += 1
            if os.path.basename(words[i - 1]) in PREFIXES:
                while i < len(words) and words[i].startswith("-"):
                    i += 1
        args = words[i:]
        if not args:
            continue
        name, rest = os.path.basename(args[0]), args[1:]
        if name in ("cd", "pushd"):
            to = next((a for a in rest if not a.startswith("-") or a == "-"), None)
            if name == "pushd":
                pushed.append(d)
            if to is None:
                d = home
            elif to != "-":
                d = at(d, to)
            continue
        if name == "popd":
            d = pushed.pop() if pushed else d
            continue
        found = git_targets(rest, d, at) if name == "git" else [at(d, w) for w in write_targets(name, rest)]
        if found == "all":
            return root
        for path in found:
            if hit(path):
                return hit(path)
    return None


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
    if pid:
        target = shell_writes_code(command, cwd, root)
        if target:
            rel = os.path.relpath(target, root)
            deny(pid, "Rewriting the code" if rel == "." else f"Rewriting {rel}/")
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
