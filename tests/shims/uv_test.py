#!/usr/bin/env python3
"""Tests for the reboot venv patches: `lib/patch_reboot.py` against a
fake venv holding the reboot 1.6.0 texts it patches (P1.2, P1.1), its
P1.22 check for an app that stores OAuth tokens, and the `bin/uv` shim
that runs it (after sync and the other installing commands, quietly
before `uv run`) and hands `uv run rbt` to the rbt shim.

    python3 tests/shims/uv_test.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent.parent
UV = ROOT / "bin" / "uv"
PATCHER = ROOT / "lib" / "patch_reboot.py"
DEFECTS = ROOT / "lib" / "known-defects.json"

CJS = """#!/usr/bin/env node
const { execSync } = require("child_process");
const reqBytes = require("fs").readFileSync(0);
    const resBytes = execSync("protoc-gen-es", {
      input: reqBytes,
    });
process.stdout.write(resBytes);
"""
ENVOY = """from google.protobuf import any_pb2


def _lua_any(source_code: str) -> any_pb2.Any:
    return any_pack(source_code)
"""
FAKE_UV = "#!/bin/sh\necho \"uv $*\"\nexit ${FAKE_UV_EXIT:-0}\n"
FAKE_RBT = "#!/bin/sh\necho \"rbt-shim $*\"\necho \"REBOOT_UV_RUN=${REBOOT_UV_RUN:-}\"\n"
FAKE_OWN = "#!/bin/sh\nexit 0\n"


class PatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.plugin = Path(self.tmp) / "plugin"
        (self.plugin / "bin").mkdir(parents=True)
        (self.plugin / "lib").mkdir()
        shutil.copy(UV, self.plugin / "bin" / "uv")
        shutil.copy(PATCHER, self.plugin / "lib" / "patch_reboot.py")
        shutil.copy(DEFECTS, self.plugin / "lib" / "known-defects.json")
        uv_dir = Path(self.tmp) / "uvdir"
        uv_dir.mkdir()
        self.write(uv_dir / "uv", FAKE_UV)
        self.write(self.plugin / "lib" / "install_uv.sh", "#!/bin/sh\necho %s\n" % uv_dir)
        self.write(self.plugin / "lib" / "own.sh", FAKE_OWN)
        self.write(self.plugin / "bin" / "rbt", FAKE_RBT)
        self.project = Path(self.tmp) / "app"
        (self.project / "backend" / "src").mkdir(parents=True)
        (self.project / "pyproject.toml").write_text("[project]\nname = \"app\"\n")
        self.site = self.make_venv(self.project, "1.6.0")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def write(path: Path, text: str) -> None:
        path.write_text(text)
        path.chmod(0o755)

    def make_venv(self, project: Path, version: str) -> Path:
        site = project / ".venv" / "lib" / "python3.12" / "site-packages"
        (site / ("reboot-%s.dist-info" % version)).mkdir(parents=True)
        (site / "reboot" / "routing").mkdir(parents=True)
        self.write(site / "reboot" / "protoc_gen_es_with_deps.cjs", CJS)
        (site / "reboot" / "routing" / "envoy_config.py").write_text(ENVOY)
        return site

    def patch(self, *args: str, patcher: Optional[Path] = None,
              **env: str) -> subprocess.CompletedProcess:
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("UV_PROJECT_ENVIRONMENT", "REBOOT_SKIP_PATCHES")}
        environment["REBOOT_PATCH_PLATFORM"] = "darwin-arm64"
        environment.update(env)
        return subprocess.run(
            [sys.executable, str(patcher or self.plugin / "lib" / "patch_reboot.py"), *args],
            env=environment, capture_output=True, text=True)

    def uv(self, *args: str, cwd: Optional[Path] = None, **env: str) -> subprocess.CompletedProcess:
        environment = {k: v for k, v in os.environ.items()
                       if k not in ("CLAUDE_PLUGIN_ROOT", "REBOOT_SKIP_PATCHES", "REBOOT_UV_RUN",
                                    "UV_PROJECT_ENVIRONMENT")}
        environment["CLAUDE_PLUGIN_ROOT"] = str(self.plugin)
        environment["REBOOT_PATCH_PLATFORM"] = "darwin-arm64"
        environment.update(env)
        return subprocess.run(["sh", str(self.plugin / "bin" / "uv"), *args],
                              cwd=str(cwd or self.project), env=environment,
                              stdin=subprocess.DEVNULL, capture_output=True, text=True)

    @property
    def cjs(self) -> Path:
        return self.site / "reboot" / "protoc_gen_es_with_deps.cjs"

    @property
    def envoy(self) -> Path:
        return self.site / "reboot" / "routing" / "envoy_config.py"

    @property
    def record(self) -> Path:
        return self.project / ".venv" / ".reboot-patches.json"

    def use_oauth(self) -> None:
        (self.project / "backend" / "src" / "main.py").write_text(
            "from reboot.aio.auth.oauth_providers import Google\n"
            "oauth = Google(store_tokens=True)\n")

    # patch_reboot.py

    def test_applies_once_then_reports_present(self) -> None:
        r = self.patch(str(self.project))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("reboot 1.6.0: P1.2 applied", r.stderr)
        self.assertIn("reboot 1.6.0: P1.1 applied", r.stderr)
        self.assertIn('execSync("protoc-gen-es", { maxBuffer: 256 * 1024 * 1024,',
                      self.cjs.read_text())
        self.assertIn('    source_code = "if jit then jit.off() end\\n" + source_code\n',
                      self.envoy.read_text())
        self.assertTrue(os.access(self.cjs, os.X_OK), "the .cjs keeps its mode")
        compile(self.envoy.read_text(), "envoy_config.py", "exec")
        record = json.loads(self.record.read_text())
        self.assertEqual(record["reboot"], "1.6.0")
        self.assertEqual(record["defects"]["P1.2"]["status"], "applied")
        self.assertTrue(record["defects"]["P1.1"]["applied_at"])
        before = (self.cjs.read_bytes(), self.envoy.read_bytes())
        again = self.patch(str(self.project))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("P1.2 already present", again.stderr)
        self.assertIn("P1.1 already present", again.stderr)
        self.assertNotIn("applied", again.stderr)
        self.assertEqual(before, (self.cjs.read_bytes(), self.envoy.read_bytes()))
        record2 = json.loads(self.record.read_text())
        self.assertEqual(record2["defects"]["P1.2"]["status"], "present")
        self.assertEqual(record2["defects"]["P1.2"]["applied_at"],
                         record["defects"]["P1.2"]["applied_at"])

    def test_fresh_inode_leaves_a_hard_linked_cache_alone(self) -> None:
        cache = Path(self.tmp) / "cache.cjs"
        os.link(self.cjs, cache)
        self.assertEqual(self.patch(str(self.project)).returncode, 0)
        self.assertEqual(cache.read_text(), CJS)

    def test_check_writes_nothing(self) -> None:
        r = self.patch("--check", str(self.project))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("P1.2 needed", r.stdout)
        self.assertEqual(self.cjs.read_text(), CJS)
        self.assertEqual(self.envoy.read_text(), ENVOY)
        self.assertFalse(self.record.exists())

    def test_finds_the_venv_from_a_subdirectory(self) -> None:
        r = self.patch(str(self.project / "backend" / "src"))
        self.assertIn("P1.2 applied", r.stderr)

    def test_other_version_applies_nothing(self) -> None:
        shutil.rmtree(self.project / ".venv")
        self.site = self.make_venv(self.project, "1.5.0")
        r = self.patch(str(self.project))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("reboot 1.5.0: P1.2 not needed (affects ==1.6.0)", r.stderr)
        self.assertEqual(self.cjs.read_text(), CJS)
        self.assertEqual(self.envoy.read_text(), ENVOY)

    def test_changed_file_fails_naming_the_finding(self) -> None:
        self.cjs.write_text(CJS.replace('execSync("protoc-gen-es", {', 'execSync("protoc-gen-es",{'))
        r = self.patch(str(self.project))
        self.assertEqual(r.returncode, 1)
        self.assertIn("P1.2 cannot apply", r.stderr)
        self.assertIn("reboot-findings P1.2", r.stderr)
        self.assertIn("P1.1 applied", r.stderr, "the other entries still run")
        self.assertEqual(json.loads(self.record.read_text())["defects"]["P1.2"]["status"], "error")

    def test_other_platform_skips_the_envoy_patch(self) -> None:
        r = self.patch(str(self.project), REBOOT_PATCH_PLATFORM="linux-x86_64")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("P1.2 applied", r.stderr)
        self.assertIn("P1.1 not needed on linux-x86_64", r.stderr)
        self.assertEqual(self.envoy.read_text(), ENVOY)

    def test_quiet_prints_only_applied(self) -> None:
        r = self.patch("--quiet", str(self.project))
        self.assertIn("P1.2 applied", r.stderr)
        again = self.patch("--quiet", str(self.project))
        self.assertEqual((again.returncode, again.stdout, again.stderr), (0, "", ""))

    def test_no_venv_or_no_reboot_is_silent(self) -> None:
        bare = Path(self.tmp) / "bare"
        bare.mkdir()
        r = self.patch(str(bare))
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        shutil.rmtree(self.site / "reboot-1.6.0.dist-info")
        r = self.patch(str(self.project))
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_uv_project_environment(self) -> None:
        (self.project / ".venv").rename(self.project / "env")
        self.site = self.project / "env" / "lib" / "python3.12" / "site-packages"
        r = self.patch(str(self.project), UV_PROJECT_ENVIRONMENT="env")
        self.assertIn("P1.2 applied", r.stderr)
        self.assertTrue((self.project / "env" / ".reboot-patches.json").exists())

    def test_oauth_tokens_without_the_package_fail_with_the_commands(self) -> None:
        self.use_oauth()
        r = self.patch(str(self.project), patcher=PATCHER)
        self.assertEqual(r.returncode, 1, r.stderr)
        vendor = ROOT.resolve() / "skills" / "python" / "vendor" / "reboot-std-oauth"
        self.assertTrue(vendor.is_dir())
        self.assertIn(
            "reboot 1.6.0: this app stores OAuth tokens, and the 1.6.0 wheel lacks "
            "reboot.std.oauth (reboot-findings P1.22). Add the plugin's vendored package:\n"
            "  mkdir -p vendor && cp -R %s vendor/\n"
            "  uv add --no-workspace ./vendor/reboot-std-oauth" % vendor, r.stderr)
        self.assertIn("P1.2 applied", r.stderr, "the patches still apply")
        check = self.patch("--check", str(self.project), patcher=PATCHER)
        self.assertEqual(check.returncode, 0, "--check stays a report")
        self.assertIn("lacks reboot.std.oauth", check.stdout)

    def test_oauth_tokens_with_the_package_pass(self) -> None:
        self.use_oauth()
        (self.site / "reboot_std_oauth-1.6.0.dist-info").mkdir()
        r = self.patch(str(self.project))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("OAuth", r.stderr)

    def test_oauth_import_counts_too(self) -> None:
        (self.project / "backend" / "src" / "tokens.py").write_text(
            "from reboot.std.oauth.v1.oauth import oauth_library\n")
        r = self.patch(str(self.project))
        self.assertEqual(r.returncode, 1)
        self.assertIn("lacks reboot.std.oauth", r.stderr)

    # bin/uv

    def test_sync_patches_after_uv(self) -> None:
        r = self.uv("sync")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "uv sync\n")
        self.assertIn("P1.2 applied", r.stderr)
        self.assertIn("maxBuffer", self.cjs.read_text())

    def test_pip_install_patches(self) -> None:
        r = self.uv("pip", "install", "reboot==1.6.0")
        self.assertIn("P1.2 applied", r.stderr)

    def test_skip_patches(self) -> None:
        r = self.uv("sync", REBOOT_SKIP_PATCHES="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.cjs.read_text(), CJS)
        self.assertNotIn("P1.2", r.stderr)

    def test_uv_failure_propagates_and_skips_patches(self) -> None:
        r = self.uv("sync", FAKE_UV_EXIT="3")
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.cjs.read_text(), CJS)

    def test_oauth_failure_fails_the_sync(self) -> None:
        self.use_oauth()
        r = self.uv("sync")
        self.assertEqual(r.returncode, 1)
        self.assertIn("lacks reboot.std.oauth", r.stderr)

    def test_other_commands_do_not_patch(self) -> None:
        r = self.uv("--version")
        self.assertEqual(r.stdout, "uv --version\n")
        self.assertEqual(r.stderr, "")
        self.assertEqual(self.cjs.read_text(), CJS)
        self.uv("tree")
        self.assertEqual(self.cjs.read_text(), CJS)

    def test_run_patches_quietly(self) -> None:
        r = self.uv("run", "pytest", "--project", "elsewhere")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "uv run pytest --project elsewhere\n")
        self.assertIn("P1.2 applied", r.stderr)
        again = self.uv("run", "pytest")
        self.assertEqual(again.stderr, "")

    def test_project_option_from_elsewhere(self) -> None:
        r = self.uv("--project", str(self.project), "sync", cwd=Path(self.tmp))
        self.assertIn("P1.2 applied", r.stderr)
        self.cjs.write_text(CJS)
        r = self.uv("sync", "--directory=%s" % self.project, cwd=Path(self.tmp))
        self.assertIn("P1.2 applied", r.stderr)

    def test_run_rbt_goes_to_the_rbt_shim(self) -> None:
        r = self.uv("run", "rbt", "dev", "run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("rbt-shim dev run\n", r.stdout)
        self.assertIn("REBOOT_UV_RUN=%s" % (Path(self.tmp) / "uvdir" / "uv"), r.stdout)
        self.assertEqual(r.stderr, "", "the rbt shim patches, not this one")
        self.assertEqual(self.cjs.read_text(), CJS)

    def test_run_rbt_from_the_rbt_shim_runs_uv(self) -> None:
        r = self.uv("run", "rbt", "dev", "run", REBOOT_UV_RUN="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout, "uv run rbt dev run\n")
        self.assertEqual(r.stderr, "", "the rbt shim already patched")


if __name__ == "__main__":
    unittest.main()
