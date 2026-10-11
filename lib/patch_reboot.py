#!/usr/bin/env python3
"""Patch known defects of the installed reboot wheel in a project's .venv.

    python3 lib/patch_reboot.py [--check] [--quiet] <project dir>

bin/uv runs it after `uv sync`, `add`, `remove`, `lock` and `uv pip
install|sync|uninstall`, and quietly before `uv run`; bin/rbt runs it
quietly before the project's own rbt. REBOOT_SKIP_PATCHES=1 turns both
off.

The defects live in lib/known-defects.json (findings P1.2 and P1.1).
Each patch applies only to the reboot versions and platforms its entry
names, finds its text exactly once, and is idempotent: a file that
already carries the entry's marker is left alone. Files are replaced
through a temporary file (a fresh inode, so uv's cache, which a venv
may hard-link, is never written through). The outcome goes to
.venv/.reboot-patches.json.

It also checks finding P1.22: an app whose backend/src uses
`reboot.std.oauth` or `store_tokens=True` needs the plugin's vendored
reboot-std-oauth package when the installed wheel lacks the module.

Output and exit status:
  - Without --check, lines go to stderr (the patcher runs beside
    another command whose stdout may be parsed) and the exit status
    is 1 when a patch cannot apply or the P1.22 check fails, else 0.
  - --check writes nothing, prints the same lines to stdout and always
    exits 0: it is a report, never a gate.
  - --quiet prints only patches it applied and failures.

Runs on the system python3 (3.9): no 3.10-only syntax, standard
library only, and it never imports reboot (a namespace package), it
finds site-packages/reboot by path.
"""

import datetime
import glob
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
DEFECTS = os.path.join(HERE, "known-defects.json")
RECORD = ".reboot-patches.json"
OAUTH_USE = re.compile(r"reboot\.std\.oauth|store_tokens\s*=\s*True")


def find_project(start):
    """The project directory and its venv, or (start, None)."""
    start = os.path.abspath(start)
    directory = start
    while True:
        if os.path.isfile(os.path.join(directory, "pyproject.toml")) or \
                os.path.isdir(os.path.join(directory, ".venv")):
            break
        parent = os.path.dirname(directory)
        if parent == directory:
            directory = start
            break
        directory = parent
    environment = os.environ.get("UV_PROJECT_ENVIRONMENT")
    if environment:
        venv = environment if os.path.isabs(environment) else os.path.join(directory, environment)
    else:
        venv = os.path.join(directory, ".venv")
    return directory, (venv if os.path.isdir(venv) else None)


def site_packages(venv):
    for path in sorted(glob.glob(os.path.join(venv, "lib", "python*", "site-packages"))):
        return path
    path = os.path.join(venv, "Lib", "site-packages")
    return path if os.path.isdir(path) else None


def installed_version(site):
    for info in glob.glob(os.path.join(site, "reboot-*.dist-info")):
        return os.path.basename(info)[len("reboot-"):-len(".dist-info")]
    return None


def version_tuple(text):
    parts = []
    for part in text.strip().split("."):
        digits = re.match(r"\d+", part)
        parts.append(int(digits.group(0)) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def version_matches(version, spec):
    have = version_tuple(version)
    for clause in spec.split(","):
        clause = clause.strip()
        if not clause:
            continue
        match = re.match(r"(==|!=|<=|>=|<|>)\s*(.+)", clause)
        if not match:
            raise ValueError("bad version clause %r" % clause)
        operator, want = match.group(1), version_tuple(match.group(2))
        ok = {
            "==": have == want, "!=": have != want, "<": have < want,
            "<=": have <= want, ">": have > want, ">=": have >= want,
        }[operator]
        if not ok:
            return False
    return True


def current_platform():
    override = os.environ.get("REBOOT_PATCH_PLATFORM")
    if override:
        return override
    system = platform.system().lower()
    machine = platform.machine().lower()
    machine = {"aarch64": "arm64", "amd64": "x86_64"}.get(machine, machine)
    if system == "darwin" and machine == "x86_64":
        # Rosetta: the hardware is arm64 and so is the Envoy that runs.
        try:
            out = subprocess.run(["sysctl", "-n", "hw.optional.arm64"],
                                 capture_output=True, text=True, timeout=5).stdout
            if out.strip() == "1":
                machine = "arm64"
        except (OSError, subprocess.SubprocessError):
            pass
    return "%s-%s" % (system, machine)


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def replace_file(path, data):
    directory = os.path.dirname(path)
    fd, temporary = tempfile.mkstemp(dir=directory, prefix=".reboot-patch-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(temporary, os.stat(path).st_mode & 0o7777)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def apply_defect(defect, site, version, where, check):
    """One defect's outcome: (status, line, sha256 or None)."""
    ident = defect["id"]
    prefix = "reboot %s: %s" % (version, ident)
    if not version_matches(version, defect["versions"]):
        return "not-needed", "%s not needed (affects %s)." % (prefix, defect["versions"]), None
    platforms = defect.get("platforms")
    if platforms and where not in platforms:
        return "not-needed", "%s not needed on %s (affects %s)." % (
            prefix, where, ", ".join(platforms)), None
    path = os.path.join(site, defect["file"])
    if not os.path.isfile(path):
        return "skipped", "%s skipped: %s is not installed." % (prefix, defect["file"]), None
    with open(path, "rb") as handle:
        data = handle.read()
    if defect["marker"].encode() in data:
        return "present", "%s already present (%s)." % (prefix, defect["file"]), sha256(path)
    find = defect["find"].encode()
    count = data.count(find)
    if count != 1:
        return "error", (
            "%s cannot apply: the text it replaces occurs %d times in %s, not once. "
            "The file differs from the release the patch was written for; see reboot-findings %s "
            "and apply its workaround by hand." % (prefix, count, defect["file"], ident)), None
    if check:
        return "needed", "%s needed (%s); a run without --check applies it." % (
            prefix, defect["file"]), None
    replace_file(path, data.replace(find, defect["replace"].encode()))
    return "applied", "%s applied (%s): %s Then %s." % (
        prefix, defect["file"], defect["description"], defect["after"]), sha256(path)


def uses_oauth_tokens(project):
    source = os.path.join(project, "backend", "src")
    for directory, subdirectories, files in os.walk(source):
        subdirectories[:] = [d for d in subdirectories
                             if d not in ("__pycache__", "node_modules", ".venv")]
        for name in files:
            if not name.endswith(".py"):
                continue
            try:
                with open(os.path.join(directory, name), encoding="utf-8", errors="replace") as handle:
                    if OAUTH_USE.search(handle.read()):
                        return True
            except OSError:
                continue
    return False


def oauth_problem(project, site, version):
    """The P1.22 message when the app needs reboot.std.oauth and lacks it."""
    if not uses_oauth_tokens(project):
        return None
    if glob.glob(os.path.join(site, "reboot_std_oauth-*.dist-info")):
        return None
    if os.path.isfile(os.path.join(site, "reboot", "std", "oauth", "v1", "oauth.py")):
        return None
    vendor = shlex.quote(os.path.join(PLUGIN_ROOT, "skills", "python", "vendor", "reboot-std-oauth"))
    return (
        "reboot %s: this app stores OAuth tokens, and the %s wheel lacks reboot.std.oauth "
        "(reboot-findings P1.22). Add the plugin's vendored package:\n"
        "  mkdir -p vendor && cp -R %s vendor/\n"
        "  uv add --no-workspace ./vendor/reboot-std-oauth" % (version, version, vendor))


def write_record(venv, version, where, outcomes):
    path = os.path.join(venv, RECORD)
    try:
        with open(path) as handle:
            previous = json.load(handle).get("defects", {})
    except (OSError, ValueError, AttributeError):
        previous = {}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    defects = {}
    for ident, (status, digest, file) in outcomes.items():
        entry = {"status": status, "file": file, "sha256": digest}
        earlier = previous.get(ident) if isinstance(previous, dict) else None
        if status == "applied":
            entry["applied_at"] = now
        elif status == "present" and isinstance(earlier, dict) and earlier.get("sha256") == digest:
            entry["applied_at"] = earlier.get("applied_at")
        else:
            entry["applied_at"] = None
        defects[ident] = entry
    record = {"reboot": version, "platform": where, "defects": defects}
    text = json.dumps(record, indent=2, sort_keys=True) + "\n"
    try:
        with open(path) as handle:
            if handle.read() == text:
                return
    except OSError:
        pass
    with open(path, "w") as handle:
        handle.write(text)


def main(argv):
    check = quiet = False
    paths = []
    for arg in argv:
        if arg == "--check":
            check = True
        elif arg == "--quiet":
            quiet = True
        elif arg in ("-h", "--help"):
            print(__doc__.strip())
            return 0
        elif arg.startswith("-"):
            print("patch_reboot.py: unknown option %s" % arg, file=sys.stderr)
            return 2
        else:
            paths.append(arg)
    if len(paths) > 1:
        print("patch_reboot.py: one project directory, at most", file=sys.stderr)
        return 2
    out = sys.stdout if check else sys.stderr

    project, venv = find_project(paths[0] if paths else os.getcwd())
    if venv is None:
        return 0
    site = site_packages(venv)
    version = installed_version(site) if site else None
    if version is None:
        return 0

    with open(DEFECTS) as handle:
        defects = json.load(handle)["defects"]
    where = current_platform()
    failed = False
    outcomes = {}
    for defect in defects:
        status, line, digest = apply_defect(defect, site, version, where, check)
        outcomes[defect["id"]] = (status, digest, defect["file"])
        if status == "error":
            failed = True
            print(line, file=sys.stdout if check else sys.stderr)
        elif not quiet or status == "applied":
            print(line, file=out)

    problem = oauth_problem(project, site, version)
    if problem:
        failed = True
        print(problem, file=sys.stdout if check else sys.stderr)

    if check:
        return 0
    write_record(venv, version, where, outcomes)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
