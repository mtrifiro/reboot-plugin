#!/usr/bin/env python3
"""Tests for the `bin/rbt` shim's guards and routing, against a fake
plugin root whose `uvx` only prints what it was asked to run: `dev
expunge` with no `--yes` and no terminal is refused with the fix; a
held state lock refuses `dev expunge` and `dev run`, naming the holder;
`dashboard` gets the Node heap; a project with its own `.venv` runs
that `rbt`, with a notice when its Reboot differs from the pin; the
shim finds its root through a symlink and names `lib/` when it is
missing; `uv run rbt` (REBOOT_UV_RUN, set by the uv shim) passes the
guards before it reaches `uv run`; the venv route applies the
known-defect patches unless REBOOT_SKIP_PATCHES is set; the project's
API lint runs before `generate` and a failure refuses it.

    python3 tests/shims/rbt_test.py
"""

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RBT = ROOT / "bin" / "rbt"

FAKE_UVX = "#!/bin/sh\necho \"uvx $*\"\necho \"NODE_OPTIONS=${NODE_OPTIONS:-}\"\n"
FAKE_OWN = "#!/bin/sh\nexit 0\n"
FAKE_VENV_RBT = "#!/bin/sh\necho \"venv-rbt $*\"\necho \"PATH=$PATH\"\n"
FAKE_UV = "#!/bin/sh\necho \"uv $*\"\necho \"REBOOT_UV_RUN=${REBOOT_UV_RUN:-}\"\n"
FAKE_PATCH = "import sys\nprint('patched', *sys.argv[1:])\n"
FAILING_LINT = "import sys\nprint('api/x.py:1: bad')\nsys.exit(1)\n"
PASSING_LINT = "print('api_lint: pass')\n"


class RbtShimTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.plugin = Path(self.tmp) / "plugin"
        (self.plugin / "bin").mkdir(parents=True)
        (self.plugin / "lib").mkdir()
        shutil.copy(RBT, self.plugin / "bin" / "rbt")
        self.write(self.plugin / "bin" / "uvx", FAKE_UVX)
        self.write(self.plugin / "lib" / "own.sh", FAKE_OWN)
        self.project = Path(self.tmp) / "app"
        self.project.mkdir()
        (self.project / ".rbtrc").write_text("generate api/\ndev run --application-name=app\n")
        self.holders: list[subprocess.Popen] = []

    def tearDown(self) -> None:
        for p in self.holders:
            p.kill()
            p.wait()
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def write(path: Path, text: str) -> None:
        path.write_text(text)
        path.chmod(0o755)

    def rbt(self, *args: str, cwd: Path | None = None, root: bool = True,
            shim: Path | None = None, **env: str) -> subprocess.CompletedProcess:
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("CLAUDE_PLUGIN_ROOT", "NODE_OPTIONS")}
        if root:
            environment["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        environment.update(env)
        return subprocess.run(["sh", str(shim or self.plugin / "bin" / "rbt"), *args],
                              cwd=cwd or self.tmp, env=environment, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True)

    def hold_lock(self) -> int:
        lock = self.project / ".rbt" / "dev" / "app" / "p000000" / "LOCK"
        lock.parent.mkdir(parents=True)
        lock.write_text("")
        holder = subprocess.Popen(
            ["python3", "-c", f"import time; f = open({str(lock)!r}); time.sleep(60)"])
        self.holders.append(holder)
        time.sleep(0.5)
        return holder.pid

    def test_passes_through_to_the_pinned_cli(self) -> None:
        r = self.rbt("generate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("uvx --from=reboot==", r.stdout)
        self.assertIn(" rbt generate", r.stdout)

    def test_expunge_without_yes_and_without_a_terminal_is_refused(self) -> None:
        r = self.rbt("dev", "expunge", cwd=self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("would wait forever", r.stderr)
        self.assertIn("--yes", r.stderr)
        self.assertEqual(r.stdout, "", "nothing ran")

    def test_expunge_with_yes_runs(self) -> None:
        r = self.rbt("dev", "expunge", "--yes", cwd=self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("rbt dev expunge --yes", r.stdout)

    @unittest.skipUnless(shutil.which("lsof"), "lsof is not installed")
    def test_a_held_lock_refuses_expunge_and_dev_run(self) -> None:
        pid = self.hold_lock()
        r = self.rbt("dev", "expunge", "--yes", cwd=self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"held by pid {pid}", r.stderr)
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"still held by pid {pid}", r.stderr)
        self.assertIn("Stop it completely first", r.stderr)

    def test_dev_run_with_no_lock_runs(self) -> None:
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("rbt dev run", r.stdout)

    def test_dashboard_gets_the_node_heap_unless_chosen(self) -> None:
        r = self.rbt("dashboard", "--port=9872")
        self.assertIn("NODE_OPTIONS=--max-old-space-size=12288", r.stdout)
        r = self.rbt("dashboard", NODE_OPTIONS="--max-old-space-size=4096")
        self.assertIn("NODE_OPTIONS=--max-old-space-size=4096", r.stdout)
        r = self.rbt("generate")
        self.assertIn("NODE_OPTIONS=\n", r.stdout)

    def test_a_project_venv_runs_its_own_rbt(self) -> None:
        venv = self.project / ".venv"
        (venv / "bin").mkdir(parents=True)
        self.write(venv / "bin" / "rbt", FAKE_VENV_RBT)
        (venv / "lib" / "python3.12" / "site-packages" / "reboot-1.6.0.dist-info").mkdir(parents=True)
        (self.project / "api").mkdir()
        r = self.rbt("generate", cwd=self.project / "api")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("venv-rbt generate", r.stdout, "found from a subdirectory too")
        self.assertIn(f"PATH={os.path.realpath(venv)}/bin:", r.stdout,
                      "the venv's bin/ leads PATH, as uv run arranges")
        self.assertEqual(r.stderr, "", "no notice when the versions agree")

    def test_a_project_venv_on_another_reboot_says_so(self) -> None:
        venv = self.project / ".venv"
        (venv / "bin").mkdir(parents=True)
        self.write(venv / "bin" / "rbt", FAKE_VENV_RBT)
        (venv / "lib" / "python3.12" / "site-packages" / "reboot-1.5.0.dist-info").mkdir(parents=True)
        r = self.rbt("generate", cwd=self.project)
        self.assertIn("venv-rbt generate", r.stdout)
        self.assertIn("reboot 1.5.0", r.stderr)
        self.assertIn("upgrade skill", r.stderr)

    def test_finds_its_root_through_a_symlink(self) -> None:
        linked = Path(self.tmp) / "linked-bin"
        linked.mkdir()
        os.symlink(self.plugin / "bin" / "rbt", linked / "rbt")
        r = self.rbt("generate", root=False, shim=linked / "rbt")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("uvx --from=reboot==", r.stdout)

    def test_names_the_missing_lib(self) -> None:
        bare = Path(self.tmp) / "bare"
        (bare / "bin").mkdir(parents=True)
        shutil.copy(RBT, bare / "bin" / "rbt")
        r = self.rbt("generate", root=False, shim=bare / "bin" / "rbt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("lib/ is missing", r.stderr)
        self.assertIn("CLAUDE_PLUGIN_ROOT", r.stderr)

    # `uv run rbt`, routed here by the uv shim.

    def uv_run(self, *args: str, cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess:
        uv = Path(self.tmp) / "real-uv"
        if not uv.exists():
            self.write(uv, FAKE_UV)
        return self.rbt(*args, cwd=cwd, REBOOT_UV_RUN=str(uv), **env)

    def test_uv_run_passes_through_to_uv(self) -> None:
        r = self.uv_run("generate", "--help", cwd=self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("uv run rbt generate --help", r.stdout)
        self.assertIn("REBOOT_UV_RUN=\n", r.stdout, "unset, so a nested rbt does not loop")

    def test_uv_run_expunge_without_a_terminal_is_refused(self) -> None:
        r = self.uv_run("dev", "expunge", cwd=self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("would wait forever", r.stderr)
        self.assertEqual(r.stdout, "", "uv never ran")

    @unittest.skipUnless(shutil.which("lsof"), "lsof is not installed")
    def test_uv_run_under_a_held_lock_is_refused(self) -> None:
        pid = self.hold_lock()
        r = self.uv_run("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 1)
        self.assertIn(f"still held by pid {pid}", r.stderr)
        self.assertEqual(r.stdout, "", "uv never ran")

    # Known-defect patches on the venv route.

    def make_venv(self) -> None:
        venv = self.project / ".venv"
        (venv / "bin").mkdir(parents=True)
        self.write(venv / "bin" / "rbt", FAKE_VENV_RBT)

    def test_the_venv_route_applies_the_patches(self) -> None:
        self.make_venv()
        (self.plugin / "lib" / "patch_reboot.py").write_text(FAKE_PATCH)
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"patched --quiet {os.path.realpath(self.project)}\n", r.stdout)
        self.assertIn("venv-rbt dev run", r.stdout)
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1", REBOOT_SKIP_PATCHES="1")
        self.assertNotIn("patched", r.stdout)
        self.assertIn("venv-rbt dev run", r.stdout)

    def test_uv_run_applies_the_patches_first(self) -> None:
        (self.plugin / "lib" / "patch_reboot.py").write_text(FAKE_PATCH)
        r = self.uv_run("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"patched --quiet {os.path.realpath(self.project)}\nuv run rbt dev run", r.stdout)
        r = self.uv_run("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1", REBOOT_SKIP_PATCHES="1")
        self.assertNotIn("patched", r.stdout)

    def test_the_venv_route_runs_without_the_patcher(self) -> None:
        self.make_venv()
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("venv-rbt dev run", r.stdout)

    def test_a_failing_patcher_does_not_stop_rbt(self) -> None:
        self.make_venv()
        (self.plugin / "lib" / "patch_reboot.py").write_text("import sys\nsys.exit(3)\n")
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("venv-rbt dev run", r.stdout)

    # The API lint before generate (decision 3).

    def lint(self, text: str) -> None:
        (self.project / "scripts").mkdir(exist_ok=True)
        (self.project / "scripts" / "api_lint.py").write_text(text)

    def test_a_failing_api_lint_refuses_generate(self) -> None:
        self.lint(FAILING_LINT)
        r = self.rbt("generate", cwd=self.project)
        self.assertEqual(r.returncode, 1)
        self.assertIn("api/x.py:1: bad", r.stderr)
        self.assertIn("REBOOT_SKIP_API_LINT=1", r.stderr)
        self.assertEqual(r.stdout, "", "generate never ran")
        r = self.uv_run("generate", cwd=self.project)
        self.assertEqual(r.returncode, 1, "uv run rbt generate is refused too")

    def test_a_passing_api_lint_lets_generate_run(self) -> None:
        self.lint(PASSING_LINT)
        r = self.rbt("generate", cwd=self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(" rbt generate", r.stdout)
        self.assertNotIn("api_lint", r.stdout + r.stderr, "quiet when it passes")

    def test_the_api_lint_is_skipped_on_request_and_for_help(self) -> None:
        self.lint(FAILING_LINT)
        r = self.rbt("generate", cwd=self.project, REBOOT_SKIP_API_LINT="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(" rbt generate", r.stdout)
        r = self.rbt("generate", "--help", cwd=self.project)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = self.rbt("dev", "run", cwd=self.project, REBOOT_LOCK_WAIT="1")
        self.assertEqual(r.returncode, 0, "only generate runs the lint")


if __name__ == "__main__":
    unittest.main()
