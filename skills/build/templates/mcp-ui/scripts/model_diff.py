#!/usr/bin/env python3
"""What a change did to the domain model and the feature files.

    scripts/model_diff.py                    # the accepted design..working tree
    scripts/model_diff.py <base>             # base..working tree
    scripts/model_diff.py --head             # ..HEAD, committed, instead of the working tree
    scripts/model_diff.py --json             # for the release record
    scripts/model_diff.py --accept           # record the working tree's design as accepted

The domain model is the API under `api/`: its state types, their
methods and method kinds, and the fields of every model, with their
tags. Who may call each method is the `authorizer()` of each servicer
under `backend/`, with the module-level rules it names. The feature
files are `tests/*.feature`: their features, rules and scenarios. All
three are read at the two revisions and compared, so the list is short
and exact where `git diff` is long and noisy.

Each change is sorted by the Reboot Flywheel's routing rule
(`build/references/flywheel.md`):

- **Design**: any change to the domain model or to who may call a
  method; a feature, rule or
  feature description added, removed or reworded; a scenario removed,
  or its steps changed. These go back to Design for acceptance.
- **Prove**: a new scenario under a rule that already existed, and
  `@wip` coming off a scenario. These stay in Prove.

It also names every servicer with no `authorizer()`, which `rbt dev`
allows with a warning and Reboot Cloud denies.

The accepted design is recorded in `design/accepted.json` (`--accept`
writes it: the date and a fingerprint of `api/` and the feature files;
commit it with them). With no `<base>`, the diff measures from the
commit that last changed that file, the acceptance, and says whether
the design is still the accepted one. Without a record the base is
required.

It is evidence, not a gate: it always exits 0. `scripts/api_removals.py`
is what stops a deploy that would break stored state.
"""

from __future__ import annotations

import ast
import copy
import datetime
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACCEPTED = "design/accepted.json"

# Method factories, as the API declares them (`reboot.api`).
KINDS = ("Reader", "Writer", "Transaction", "Workflow", "UI")


@dataclass
class Change:
    area: str  # "model", "auth" or "features"
    stage: str  # "design" or "prove"
    what: str


# -- reading a revision ------------------------------------------------------


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def files_at(rev: str | None, folder: str, suffix: str) -> dict[str, str]:
    """`{path: text}` under `folder` at `rev`, or in the working tree."""
    if rev is None:
        base = ROOT / folder
        return {
            str(p.relative_to(ROOT)): p.read_text()
            for p in sorted(base.rglob(f"*{suffix}"))
            if "__pycache__" not in p.parts
        } if base.is_dir() else {}
    names = git("ls-tree", "-r", "--name-only", rev, "--", folder).split()
    return {n: git("show", f"{rev}:{n}") for n in names if n.endswith(suffix)}


# -- the accepted design ---------------------------------------------------


def fingerprint_of(api: dict[str, str], features: dict[str, str]) -> str:
    """One hash over the API definition files and the feature files."""
    digest = hashlib.sha256()
    for path, text in sorted(api.items()) + sorted(features.items()):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update(text.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def accept() -> dict:
    """Write `design/accepted.json` for the working tree's design."""
    api = files_at(None, "api", ".py")
    features = files_at(None, "tests", ".feature")
    record = {
        "at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "fingerprint": fingerprint_of(api, features),
        "api": sorted(api),
        "features": sorted(features),
    }
    (ROOT / "design").mkdir(exist_ok=True)
    (ROOT / ACCEPTED).write_text(json.dumps(record, indent=2) + "\n")
    return record


def read_accepted() -> dict | None:
    """The committed acceptance: its commit, date, and whether the
    record's fingerprint matches what that commit holds. None when
    there is no record, or it is not committed yet."""
    path = ROOT / ACCEPTED
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text())
    except ValueError:
        return None
    commit = git("log", "-1", "--format=%H", "--", ACCEPTED).strip()
    if not commit:
        return None
    at_commit = fingerprint_of(
        files_at(commit, "api", ".py"), files_at(commit, "tests", ".feature")
    )
    return {
        "commit": commit,
        "at": record.get("at", ""),
        "fingerprint_ok": record.get("fingerprint") == at_commit,
    }


# -- the domain model ------------------------------------------------------


def literal(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Constant):
        return repr(node.value) if not isinstance(node.value, str) else node.value
    return ast.unparse(node)


def keywords(call: ast.Call) -> dict[str, ast.AST]:
    return {k.arg: k.value for k in call.keywords if k.arg}


def name_of(call: ast.Call) -> str:
    f = call.func
    return f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else ""


def model_of(sources: dict[str, str]) -> tuple[dict, dict]:
    """(types, models) declared across the API files.

    types:  {Type: {"state", "description", "methods": {m: {"kind", ...}}}}
    models: {Class: {field: {"type", "tag", "description"}}}
    """
    types: dict = {}
    models: dict = {}
    for source in sources.values():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        # Module-level names, so `methods=UserMethods` (a `Methods(...)`
        # assigned above the API) and `User=UserType` both resolve.
        named = {
            t.id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            for t in node.targets
            if isinstance(t, ast.Name)
        }

        def resolve(value: ast.AST | None) -> ast.AST | None:
            return named.get(value.id, value) if isinstance(value, ast.Name) else value

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                literal(b).split(".")[-1] == "Model" for b in node.bases
            ):
                fields = {}
                for item in node.body:
                    if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                        kw = keywords(item.value) if isinstance(item.value, ast.Call) else {}
                        fields[item.target.id] = {
                            "type": literal(item.annotation),
                            "tag": literal(kw.get("tag")),
                            "description": literal(kw.get("description")),
                        }
                models[node.name] = fields
            if isinstance(node, ast.Call) and name_of(node) == "API":
                for type_name, declared in keywords(node).items():
                    value = resolve(declared)
                    if not (isinstance(value, ast.Call) and name_of(value) == "Type"):
                        continue
                    kw = keywords(value)
                    methods = {}
                    holder = resolve(kw.get("methods"))
                    if isinstance(holder, ast.Call):
                        for method, factory in keywords(holder).items():
                            if not isinstance(factory, ast.Call):
                                continue
                            mkw = keywords(factory)
                            methods[method] = {
                                "kind": name_of(factory),
                                "request": literal(mkw.get("request")),
                                "response": literal(mkw.get("response")),
                                "description": literal(mkw.get("description")),
                                "mcp": literal(mkw.get("mcp")),
                            }
                    types[type_name] = {
                        "state": literal(kw.get("state")),
                        "description": literal(kw.get("description")),
                        "methods": methods,
                    }
    return types, models


def model_changes(before: dict[str, str], after: dict[str, str]) -> list[Change]:
    old_types, old_models = model_of(before)
    new_types, new_models = model_of(after)
    out: list[Change] = []

    def add(what: str) -> None:
        out.append(Change("model", "design", what))

    for t in sorted(old_types.keys() | new_types.keys()):
        old, new = old_types.get(t), new_types.get(t)
        if old is None:
            assert new is not None
            add(f"state type `{t}` added (state `{new['state']}`)")
        elif new is None:
            add(f"state type `{t}` removed")
        else:
            if old["state"] != new["state"]:
                add(f"`{t}` state: `{old['state']}` → `{new['state']}`")
            if old["description"] != new["description"]:
                add(f"`{t}` description reworded")
        if new is None:
            continue
        old_methods = old["methods"] if old else {}
        for m in sorted(old_methods.keys() | new["methods"].keys()):
            om, nm = old_methods.get(m), new["methods"].get(m)
            if om is None:
                add(f"`{t}.{m}` added, {nm['kind']}")
            elif nm is None:
                add(f"`{t}.{m}` removed (was {om['kind']})")
            else:
                if om["kind"] != nm["kind"]:
                    add(f"`{t}.{m}` method kind: {om['kind']} → {nm['kind']}")
                for key in ("request", "response", "mcp"):
                    if om[key] != nm[key]:
                        add(f"`{t}.{m}` {key}: `{om[key] or 'None'}` → `{nm[key] or 'None'}`")
                if om["description"] != nm["description"]:
                    add(f"`{t}.{m}` description reworded")
    for c in sorted(old_models.keys() | new_models.keys()):
        old, new = old_models.get(c), new_models.get(c)
        if old is None:
            assert new is not None
            add(f"model `{c}` added ({len(new)} field{'s' if len(new) != 1 else ''})")
            continue
        if new is None:
            add(f"model `{c}` removed")
            continue
        for f in sorted(old.keys() | new.keys()):
            of, nf = old.get(f), new.get(f)
            if of is None:
                add(f"`{c}.{f}` added: `{nf['type']}`, tag {nf['tag'] or '?'}")
            elif nf is None:
                add(f"`{c}.{f}` removed (tag {of['tag'] or '?'})")
            else:
                if of["type"] != nf["type"]:
                    add(f"`{c}.{f}` type: `{of['type']}` → `{nf['type']}`")
                if of["tag"] != nf["tag"]:
                    add(f"`{c}.{f}` tag: {of['tag']} → {nf['tag']}")
                if of["description"] != nf["description"]:
                    add(f"`{c}.{f}` description reworded")
    return out


# -- who may call ----------------------------------------------------------


def backend_files_at(rev: str | None) -> dict[str, str]:
    """The servicer sources: `backend/`, less its generated `backend/api/`."""
    return {
        path: text
        for path, text in files_at(rev, "backend", ".py").items()
        if not path.startswith("backend/api/")
    }


def authorizers_of(sources: dict[str, str]) -> dict[str, dict[str, str]]:
    """`{Servicer: {"": rule, method: rule}}` for every `authorizer()`.

    A rule is a fingerprint of its code (comments and docstrings drop
    out) and of every module-level function or name it uses, followed
    across the backend, so a change to a shared check such as
    `is_manager` counts against each authorizer that calls it. When the
    authorizer returns `<Type>.Authorizer(method=..., ...)`, each method
    gets its own entry, so the report says which method changed.
    """
    trees = []
    for source in sources.values():
        try:
            trees.append(ast.parse(source))
        except SyntaxError:
            continue
    helpers: dict[str, ast.AST] = {}
    for tree in trees:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                helpers[node.name] = node
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        helpers[t.id] = node.value

    def strip_docstring(node: ast.AST) -> ast.AST:
        body = getattr(node, "body", None)
        if (
            isinstance(body, list) and body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            node = copy.copy(node)
            setattr(node, "body", body[1:])
        return node

    def fingerprint(node: ast.AST) -> str:
        parts, seen, todo = [], set(), [node]
        while todo:
            current = strip_docstring(todo.pop())
            parts.append(ast.dump(current))
            for n in ast.walk(current):
                if isinstance(n, ast.Name) and n.id in helpers and n.id not in seen:
                    seen.add(n.id)
                    todo.append(helpers[n.id])
        return "\n".join(parts)

    found: dict[str, dict[str, str]] = {}
    for tree in trees:
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            for item in cls.body:
                if not (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == "authorizer"
                ):
                    continue
                rules = {"": fingerprint(item)}
                returned = [
                    n.value for n in ast.walk(item)
                    if isinstance(n, ast.Return) and isinstance(n.value, ast.Call)
                ]
                if len(returned) == 1 and name_of(returned[0]) == "Authorizer":
                    for method, rule in keywords(returned[0]).items():
                        rules[method] = fingerprint(rule)
                found[cls.name] = rules
    return found


def servicers_without_authorizer(sources: dict[str, str]) -> list[str]:
    """Servicer classes (a base named `<Type>.Servicer`) with no
    `authorizer()`. `rbt dev` runs them with a warning in its log;
    `rbt serve` and Reboot Cloud deny every call to them, so a missing
    one passes every local scenario and fails in production. The `User`
    type is the exception: its generated default admits each signed-in
    user to their own state (`state_id_is_user_id` or `is_app_internal`),
    so a `User.Servicer` without one is by design."""
    out = []
    for source in sources.values():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            bases = [
                b.attr if isinstance(b, ast.Attribute) else getattr(b, "id", "")
                for b in cls.bases
            ]
            if not any(b.endswith("Servicer") for b in bases):
                continue
            if any(
                isinstance(b, ast.Attribute) and isinstance(b.value, ast.Name)
                and b.value.id == "User" and b.attr == "Servicer"
                for b in cls.bases
            ):
                continue
            if not any(
                isinstance(i, (ast.FunctionDef, ast.AsyncFunctionDef)) and i.name == "authorizer"
                for i in cls.body
            ):
                out.append(cls.name.removesuffix("Servicer") or cls.name)
    return sorted(out)


def auth_changes(before: dict[str, str], after: dict[str, str]) -> list[Change]:
    old_all, new_all = authorizers_of(before), authorizers_of(after)
    out: list[Change] = []

    def add(what: str) -> None:
        out.append(Change("auth", "design", what))

    for servicer in sorted(old_all.keys() | new_all.keys()):
        name = servicer.removesuffix("Servicer") or servicer
        old, new = old_all.get(servicer), new_all.get(servicer)
        if old is None:
            add(f"`{name}` gains an `authorizer()`")
            continue
        if new is None:
            add(f"`{name}` `authorizer()` removed: the generated default applies")
            continue
        if old[""] == new[""]:
            continue
        old_methods = {m: r for m, r in old.items() if m}
        new_methods = {m: r for m, r in new.items() if m}
        if not (old_methods and new_methods):
            add(f"who may call `{name}` changed (`authorizer()`)")
            continue
        changed = [
            m for m in sorted(old_methods.keys() | new_methods.keys())
            if old_methods.get(m) != new_methods.get(m)
        ]
        for m in changed:
            if m not in old_methods:
                add(f"who may call `{name}.{m}`: rule added")
            elif m not in new_methods:
                add(f"who may call `{name}.{m}`: rule removed")
            else:
                add(f"who may call `{name}.{m}` changed")
        if not changed:
            # Something the methods share changed (a helper, the
            # default): name the servicer.
            add(f"who may call `{name}` changed (`authorizer()`)")
    return out


# -- the feature files ------------------------------------------------------


@dataclass
class Scenario:
    steps: tuple[str, ...]
    tags: frozenset[str]


@dataclass
class Feature:
    title: str
    description: str
    rules: dict[str, dict[str, Scenario]]  # rule ("" = none) -> scenarios


def parse_feature(text: str) -> Feature:
    title, description = "", []
    rules: dict[str, dict[str, Scenario]] = {"": {}}
    rule, tags = "", set()
    scenario: str | None = None
    in_description = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            tags.update(re.findall(r"@[\w-]+", line))
            continue
        keyword, _, rest = line.partition(":")
        if keyword == "Feature":
            title, in_description, tags = rest.strip(), True, set()
        elif keyword == "Rule":
            rule, scenario, in_description = rest.strip(), None, False
            rules.setdefault(rule, {})
            tags = set()
        elif keyword in ("Scenario", "Scenario Outline", "Example"):
            scenario, in_description = rest.strip(), False
            rules[rule][scenario] = Scenario((), frozenset(tags))
            tags = set()
        elif keyword == "Background":
            scenario, in_description = None, False
        elif keyword == "Examples":
            # Its table rows belong to the outline above.
            in_description = False
        elif in_description:
            description.append(line)
        elif scenario is not None:
            s = rules[rule][scenario]
            rules[rule][scenario] = Scenario(s.steps + (line,), s.tags)
    if not rules[""]:
        del rules[""]
    return Feature(title, " ".join(description), rules)


def feature_changes(before: dict[str, str], after: dict[str, str]) -> list[Change]:
    out: list[Change] = []

    def add(stage: str, what: str) -> None:
        out.append(Change("features", stage, what))

    for path in sorted(before.keys() | after.keys()):
        if path not in before:
            add("design", f"`{path}` added: \"{parse_feature(after[path]).title}\"")
            continue
        if path not in after:
            add("design", f"`{path}` removed: \"{parse_feature(before[path]).title}\"")
            continue
        old, new = parse_feature(before[path]), parse_feature(after[path])
        if old.title != new.title:
            add("design", f"`{path}`: feature \"{old.title}\" → \"{new.title}\"")
        if old.description != new.description:
            add("design", f"`{path}`: feature description reworded")
        for rule in sorted(old.rules.keys() | new.rules.keys()):
            label = f'rule "{rule}"' if rule else "no rule"
            if rule not in old.rules:
                count = len(new.rules[rule])
                scenarios = f"{count} scenario{'s' if count != 1 else ''}"
                if rule:
                    add("design", f"`{path}`: rule \"{rule}\" added, {scenarios}")
                else:
                    add("design", f"`{path}`: {scenarios} added outside any rule")
                continue
            if rule not in new.rules:
                add("design", f"`{path}`: rule \"{rule}\" removed")
                continue
            os_, ns = old.rules[rule], new.rules[rule]
            for s in sorted(os_.keys() | ns.keys()):
                if s not in os_:
                    under = f"under existing {label}" if rule else "to the feature (no rule)"
                    add("prove", f"`{path}`: scenario \"{s}\" added {under}")
                elif s not in ns:
                    add("design", f"`{path}`: scenario \"{s}\" removed ({label})")
                else:
                    if os_[s].steps != ns[s].steps:
                        add("design", f"`{path}`: scenario \"{s}\" steps changed ({label})")
                    if "@wip" in os_[s].tags and "@wip" not in ns[s].tags:
                        add("prove", f"`{path}`: scenario \"{s}\" no longer `@wip`")
    return out


def tickets_of(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """`Ticket: ABC-123` ids named in feature files that changed."""
    found = set()
    for path in before.keys() | after.keys():
        if before.get(path) != after.get(path):
            found.update(re.findall(r"\bTicket:\s*([A-Za-z0-9_#-]+)", after.get(path, "")))
    return sorted(found)


# -- output ----------------------------------------------------------------


def accepted_line(accepted: dict | None, design_changes: int) -> str:
    """One line on whether the design is still the accepted one.
    `accepted` carries `is_base` when the diff measures from the
    acceptance commit."""
    if accepted is None:
        return (
            "**Design accepted**: no record (`design/accepted.json`): built without "
            "stopping, or a project older than the record."
        )
    sha, at = accepted["commit"][:7], accepted.get("at", "")[:10]
    note = (
        ""
        if accepted.get("fingerprint_ok", True)
        else " (the record's fingerprint does not match that commit's `api/` and feature files)"
    )
    if not accepted.get("is_base", True):
        return f"**Design accepted** at {sha} on {at}{note}; this diff does not measure from it."
    if design_changes == 0:
        return f"**Design accepted**: yes, at {sha} on {at}{note}."
    plural = "s" if design_changes != 1 else ""
    return (
        f"**Design accepted**: no, {design_changes} design change{plural} since the "
        f"acceptance at {sha} on {at}{note}."
    )


def markdown(
    base: str,
    head: str,
    changes: list[Change],
    unauthorized: list[str] | None = None,
    accepted: dict | None = None,
    tickets: list[str] | None = None,
) -> str:
    if not changes:
        lines = [
            f"**Model diff** `{base}..{head}`: no change to the domain model, "
            "who may call, or the feature files."
        ]
    else:
        design = [c for c in changes if c.stage == "design"]
        lines = [f"**Model diff** `{base}..{head}`", ""]
        if design:
            lines.append(
                f"**{len(design)} design change{'s' if len(design) != 1 else ''}**: "
                "these go back to Design for acceptance."
            )
        else:
            lines.append("**No design change**: this stays in Prove.")
        for area, heading in (
            ("model", "Domain model"),
            ("auth", "Who may call"),
            ("features", "Feature files"),
        ):
            group = [c for c in changes if c.area == area]
            if group:
                lines += ["", f"_{heading}_", ""]
                lines += [f"- [{c.stage}] {c.what}" for c in group]
    if unauthorized:
        lines += [
            "",
            "_Servicers without an authorizer_ (`rbt dev` allows every call with a "
            "warning; Reboot Cloud denies every call):",
            "",
        ]
        lines += [f"- `{name}`" for name in unauthorized]
    if tickets:
        lines += ["", "_Tickets_: " + ", ".join(tickets)]
    design_count = sum(1 for c in changes if c.stage == "design")
    lines += ["", accepted_line(accepted, design_count)]
    return "\n".join(lines) + "\n"


def main() -> int:
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) > 1 or not flags <= {"--head", "--json", "--accept"}:
        print(__doc__, file=sys.stderr)
        return 2
    if "--accept" in flags:
        record = accept()
        print(
            f"wrote {ACCEPTED}: {len(record['api'])} API file(s), "
            f"{len(record['features'])} feature file(s). Commit api/, tests/*.feature "
            "and design/ together (\"Design accepted: <title>\"): that commit is the "
            "base every later model diff measures from."
        )
        return 0
    accepted = read_accepted()
    if args:
        base = args[0]
    elif accepted:
        base = accepted["commit"]
    else:
        print(f"no {ACCEPTED} in this project: give the base revision to diff from.",
              file=sys.stderr)
        return 2
    if accepted:
        try:
            accepted["is_base"] = git("rev-parse", base).strip() == accepted["commit"]
        except subprocess.CalledProcessError:
            accepted["is_base"] = False
    head = "HEAD" if "--head" in flags else None
    features_before = files_at(base, "tests", ".feature")
    features_after = files_at(head, "tests", ".feature")
    changes = model_changes(
        files_at(base, "api", ".py"), files_at(head, "api", ".py")
    ) + auth_changes(
        backend_files_at(base), backend_files_at(head)
    ) + feature_changes(features_before, features_after)
    tickets = tickets_of(features_before, features_after)
    unauthorized = servicers_without_authorizer(backend_files_at(head))
    head_label = head or "working tree"
    if accepted and accepted.get("is_base"):
        base = base[:7]
    if accepted:
        accepted["design_changes"] = sum(1 for c in changes if c.stage == "design")
    if "--json" in flags:
        print(json.dumps({
            "base": base,
            "head": head_label,
            "design": [c.what for c in changes if c.stage == "design"],
            "prove": [c.what for c in changes if c.stage == "prove"],
            "unauthorized_servicers": unauthorized,
            "accepted": accepted,
            "tickets": tickets,
        }, indent=2))
    else:
        print(markdown(base, head_label, changes, unauthorized, accepted, tickets), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
