#!/usr/bin/env python3
"""Refuses an API definition `rbt generate` or a deploy would refuse
later, with a worse message, before either runs:

    python3 scripts/api_lint.py            # every file under api/
    python3 scripts/api_lint.py <dir>      # another API directory

Each check is one thing a build lost time to (the Reboot plugin's
findings, by number):

- a reserved method name: `read`, `write`, `delete`, `state`, `schedule`
  and `spawn` on any type, `create` and `set_claims` on `User`
  (`rbt generate` says only "protoc failed" or "<Name> is reserved";
  P4.24, P3.95);
- syntax the Cloud image's Python 3.10 cannot read, or a quoted forward
  reference in a field's type, which 3.10 cannot resolve (the deploy
  fails in `rbt generate` with `issubclass() arg 1 must be a class`;
  P3.165);
- a `Model` imported from another API package (the generated code
  references it without importing it and fails at import with
  `NameError`, after a clean generate; P1.16, P3.180);
- a `bytes` field (not supported; store base64 in a `str`; P3.28);
- an error `Model` with no fields (the generated React client throws
  at import, and the page is blank; P3.125);
- a `Writer(factory=True)`, as a note that does not fail: a
  constructor's kind can never change, so one that may one day
  construct another actor has to be a `Transaction(mode=Exclusive(),
  factory=True)` from the start (P1.6).

Prints `<file>:<line>: <what> (<reference>)` per problem and exits 1
when there is one; `rbt generate` is the next step otherwise.
`prove.yml` and the build skill's Step 1 run it; keep it in step with
the plugin's `python/references/api-*.md`."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

RESERVED = {"read", "write", "delete", "state", "schedule", "spawn"}
RESERVED_ON_USER = {"create", "set_claims"}
METHOD_FACTORIES = {"Reader", "Writer", "Transaction", "Workflow"}


class Problem:
    def __init__(self, path: Path, line: int, what: str, reference: str,
                 note: bool = False) -> None:
        self.path, self.line, self.what, self.reference = path, line, what, reference
        self.note = note  # printed, but does not fail the lint

    def __str__(self) -> str:
        kind = "note: " if self.note else ""
        return f"{self.path}:{self.line}: {kind}{self.what} ({self.reference})"


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
    return ""


def keyword(call: ast.Call, name: str) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def annotation_names(node: ast.AST | None) -> set[str]:
    """Every name an annotation mentions (`Optional[list[bytes]]` -> all three)."""
    names: set[str] = set()
    if node is None:
        return names
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return names


def quoted_in(node: ast.AST | None) -> ast.Constant | None:
    """A string constant inside an annotation: a quoted forward reference."""
    if node is None:
        return None
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            return sub
    return None


def lint_file(path: Path, api_dir: Path, packages: set[str]) -> list[Problem]:
    problems: list[Problem] = []
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path), feature_version=(3, 10))
    except SyntaxError as error:
        problems.append(Problem(
            path, error.lineno or 1,
            f"not Python 3.10, which the Reboot Cloud image runs: {error.msg}",
            "python/references/lifecycle-dockerfile.md"))
        return problems

    try:
        own_package = path.relative_to(api_dir).parts[0]
    except (ValueError, IndexError):
        own_package = ""

    # Models: fields, and which models the file declares as errors.
    models: dict[str, ast.ClassDef] = {}
    error_models: dict[str, int] = {}
    methods_by_name: dict[str, ast.Call] = {}  # `UserMethods = Methods(...)`
    type_methods: dict[str, ast.AST] = {}      # `API(User=Type(methods=...))`

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = {base.id for base in node.bases if isinstance(base, ast.Name)}
            bases |= {base.attr for base in node.bases if isinstance(base, ast.Attribute)}
            if "Model" in bases:
                models[node.name] = node
        elif isinstance(node, ast.Assign) and call_name(node.value) == "Methods":
            for target in node.targets:
                if isinstance(target, ast.Name):
                    methods_by_name[target.id] = node.value  # type: ignore[assignment]
        elif isinstance(node, ast.Call):
            name = call_name(node)
            if name in METHOD_FACTORIES:
                errors = keyword(node, "errors")
                if isinstance(errors, (ast.List, ast.Tuple)):
                    for element in errors.elts:
                        if isinstance(element, ast.Name):
                            error_models.setdefault(element.id, element.lineno)
                if name == "Writer":
                    factory = keyword(node, "factory")
                    if isinstance(factory, ast.Constant) and factory.value is True:
                        problems.append(Problem(
                            path, node.lineno,
                            "a Writer(factory=True): a constructor's kind can never change, "
                            "so if this one may ever construct another actor, declare it "
                            "Transaction(mode=Exclusive(), factory=True) now",
                            "python/references/servicer-constructor.md", note=True))
            elif name == "API":
                for kw in node.keywords:
                    if kw.arg and call_name(kw.value) == "Type":
                        methods = keyword(kw.value, "methods")  # type: ignore[arg-type]
                        if methods is not None:
                            type_methods[kw.arg] = methods

    # Imports from another API package.
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            top = node.module.split(".")[0]
            if top in packages and top != own_package:
                problems.append(Problem(
                    path, node.lineno,
                    f"imports from the API package `{top}`: generated code references a "
                    "Model from another package without importing it and fails at import "
                    "(NameError) after a clean rbt generate; define shared fields in a plain "
                    "module under api/ with no API(...) and subclass it in each package",
                    "python/references/api-pydantic.md"))

    # Fields.
    for model in models.values():
        fields = [s for s in model.body if isinstance(s, ast.AnnAssign)]
        if model.name in error_models and not fields:
            problems.append(Problem(
                path, model.lineno,
                f"the error Model `{model.name}` has no fields: the generated React client "
                "throws at import and the page is blank; give it one, e.g. "
                'reason: str = Field(tag=1, default="")',
                "python/references/api-errors.md"))
        for field in fields:
            if "bytes" in annotation_names(field.annotation):
                problems.append(Problem(
                    path, field.lineno,
                    "a bytes field: not a supported field type (the refusal is an empty "
                    "`Failed to import schema file:`); store base64 text in a str",
                    "python/references/state-scalar-fields.md"))
            quoted = quoted_in(field.annotation)
            if quoted is not None:
                problems.append(Problem(
                    path, field.lineno,
                    f"a quoted forward reference `{quoted.value!r}` in a field's type: the Cloud "
                    "image's Python 3.10 cannot resolve it and the deploy fails in rbt generate "
                    "(`issubclass() arg 1 must be a class`); define the Model above, unquoted",
                    "python/references/lifecycle-dockerfile.md"))

    # Method names.
    def methods_of(value: ast.AST) -> ast.Call | None:
        if isinstance(value, ast.Name):
            return methods_by_name.get(value.id)
        if isinstance(value, ast.Call) and call_name(value) == "Methods":
            return value
        return None

    seen: set[int] = set()
    for type_name, value in type_methods.items():
        call = methods_of(value)
        if call is None:
            continue
        seen.add(id(call))
        for kw in call.keywords:
            check_method(kw, type_name, path, problems)
    for call in methods_by_name.values():
        if id(call) in seen:
            continue
        for kw in call.keywords:
            check_method(kw, "", path, problems)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and call_name(node) == "Methods" and id(node) not in seen \
                and node not in methods_by_name.values():
            for kw in node.keywords:
                check_method(kw, "", path, problems)
            seen.add(id(node))
    return problems


def check_method(kw: ast.keyword, type_name: str, path: Path, problems: list[Problem]) -> None:
    name = kw.arg or ""
    line = kw.value.lineno if hasattr(kw.value, "lineno") else 1
    if name in RESERVED:
        problems.append(Problem(
            path, line,
            f"the method name `{name}` is reserved by Reboot (rbt generate fails with "
            f"`{name.capitalize()} is reserved`, or only `protoc failed`); rename it, "
            f"e.g. `{name}_{'sent' if name == 'read' else 'item'}`",
            "python/references/api-methods.md"))
    elif type_name == "User" and name in RESERVED_ON_USER:
        problems.append(Problem(
            path, line,
            f"`{name}` is a reserved method name on User types; override it in the "
            "servicer instead of declaring it in the API",
            "python/references/auth-claims.md"))


def main(argv: list[str]) -> int:
    api_dir = Path(argv[1] if len(argv) > 1 else "api").resolve()
    if not api_dir.is_dir():
        print(f"api_lint: {api_dir} is not a directory", file=sys.stderr)
        return 2
    files = sorted(p for p in api_dir.rglob("*.py") if "__pycache__" not in p.parts)
    packages = {p.name for p in api_dir.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))}
    problems: list[Problem] = []
    for path in files:
        problems += lint_file(path, api_dir, packages)
    cwd = Path.cwd()
    for problem in problems:
        try:
            problem.path = problem.path.relative_to(cwd)
        except ValueError:
            pass
        print(problem)
    failing = [p for p in problems if not p.note]
    if failing:
        print(f"api_lint: {len(failing)} problem(s) rbt generate or a deploy would refuse "
              "later; fix them first", file=sys.stderr)
        return 1
    print(f"api_lint: {len(files)} file(s) under {api_dir.name}/ pass")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
