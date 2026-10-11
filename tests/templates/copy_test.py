#!/usr/bin/env python3
"""Tests for skills/build/templates/copy.sh: a plain copy, the refusal,
and `--merge` (the build flow's Step 2: keep the project's files,
replace the dashboard's stubs); a plain copy keeps the destination's
own .venv and node_modules; a project in no repository gets one, with
the hooks path set; each project gets an accent from the house palette
by its name, or REBOOT_ACCENT's, in every scheme block and the favicon.

    python3 tests/templates/copy_test.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
COPY = ROOT / "skills" / "build" / "templates" / "copy.sh"
PALETTES = {p["name"]: p for p in json.loads(
    (COPY.parent / "palettes.json").read_text())["palettes"]}
# The violet values no other palette shares (white and the neutrals aside).
VIOLET = {v for scheme in ("light", "dark") for k, v in PALETTES["violet"][scheme].items()
          if k not in ("on-accent", "on-deep", "bg-glow")}
STYLESHEETS = {"web-app": ["web/src/styles.css"], "both": ["frontend/styles.css"],
               "mcp-ui": ["frontend/mcp/styles.css"]}


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    clean = {k: v for k, v in os.environ.items() if k != "REBOOT_ACCENT"}
    return subprocess.run(["sh", str(COPY), *args], capture_output=True, text=True,
                          env={**clean, **(env or {})})


def accent_of(output: str) -> str:
    return next(line for line in output.splitlines() if line.startswith("Accent: "))[8:]


class CopyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dest = Path(self.tmp.name) / "proj"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_plain_copy_fills_placeholders_and_renames(self) -> None:
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        api = self.dest / "api" / "todo_list" / "v1" / "todo_list.py"
        self.assertTrue(api.is_file(), "the API file is renamed")
        self.assertIn('name = "todo-list"', (self.dest / "pyproject.toml").read_text())
        self.assertIn("--application-name=todo-list", (self.dest / ".rbtrc").read_text())
        leftovers = subprocess.run(
            ["grep", "-rl", r"__project__\|__app__\|__Title__\|__Initial__", str(self.dest)],
            capture_output=True, text=True).stdout
        self.assertEqual(leftovers, "", "no placeholder survives")
        junk = [p for p in self.dest.rglob("*") if p.name in (
            "__pycache__", ".mypy_cache", ".pytest_cache", ".reboot", ".last-run.json")]
        self.assertEqual(junk, [], "build and test leftovers in the template are not copied")

    def test_refuses_a_project_without_merge(self) -> None:
        self.dest.mkdir()
        (self.dest / ".rbtrc").write_text("generate api/\n")
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 1)
        self.assertIn("already has an .rbtrc", r.stderr)
        self.assertEqual(os.listdir(self.dest), [".rbtrc"], "nothing was written")

    def test_merge_keeps_the_project_and_replaces_the_stubs(self) -> None:
        # Step 1 and the dashboard skill have been here.
        api_dir = self.dest / "api" / "todo_list" / "v1"
        api_dir.mkdir(parents=True)
        (api_dir / "todo_list.py").write_text("# the real API\n")
        (self.dest / ".rbtrc").write_text("generate api/\n")
        (self.dest / "pyproject.toml").write_text('[project]\nname = "stub"\n')
        (self.dest / ".python-version").write_text("3.12\n")
        (self.dest / "CLAUDE.md").write_text("# my notes\n")

        r = run("--merge", "web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((api_dir / "todo_list.py").read_text(), "# the real API\n",
                         "Step 1's API file is kept, not the sample")
        self.assertEqual((self.dest / "CLAUDE.md").read_text(), "# my notes\n")
        self.assertIn("--application-name=todo-list", (self.dest / ".rbtrc").read_text(),
                      "the stub .rbtrc is replaced by the template's")
        self.assertIn('name = "todo-list"', (self.dest / "pyproject.toml").read_text())
        self.assertIn("kept api/todo_list/v1/todo_list.py", r.stdout)
        self.assertIn("kept CLAUDE.md", r.stdout)
        self.assertIn("replaced .rbtrc", r.stdout)
        self.assertTrue((self.dest / "backend" / "src" / "main.py").is_file(),
                        "the rest of the template arrives")
        self.assertFalse(list(self.dest.rglob("*__app__*")), "no placeholder path survives")
        leftovers = subprocess.run(
            ["grep", "-rl", r"__project__\|__app__\|__Title__\|__Initial__", str(self.dest)],
            capture_output=True, text=True).stdout
        self.assertEqual(leftovers, "", "no placeholder survives")

    def test_plain_copy_keeps_the_destinations_own_environment(self) -> None:
        for name in (".venv", "node_modules", "dist", ".reboot"):
            (self.dest / name).mkdir(parents=True)
            (self.dest / name / "x").write_text("mine\n")
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in (".venv", "node_modules", "dist", ".reboot"):
            self.assertEqual((self.dest / name / "x").read_text(), "mine\n", name)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.dest), *args],
                              capture_output=True, text=True).stdout.strip()

    def test_a_project_in_no_repository_gets_one_with_the_hooks(self) -> None:
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.dest / ".git").is_dir())
        self.assertEqual(self.git("symbolic-ref", "HEAD"), "refs/heads/main")
        self.assertEqual(self.git("config", "core.hooksPath"), ".githooks")

    def test_a_project_inside_another_repository_is_left_alone(self) -> None:
        outer = Path(self.tmp.name)
        subprocess.run(["git", "-C", str(outer), "init", "-q"], check=True)
        r = run("web-app", str(self.dest), "todo-list", "todo_list", "Todo List")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.dest / ".git").exists())
        self.assertEqual(self.git("config", "--local", "core.hooksPath"), "")

    # The accent.

    def copy(self, front_door: str, project: str, **env: str) -> str:
        dest = Path(self.tmp.name) / str(len(list(Path(self.tmp.name).iterdir())))
        r = run(front_door, str(dest), project, "todo_list", "Todo List", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.dest = dest
        return accent_of(r.stdout)

    def test_the_project_name_picks_the_accent(self) -> None:
        first = self.copy("web-app", "shop-1")
        self.assertIn(first, PALETTES)
        self.assertEqual(self.copy("web-app", "shop-1"), first, "the same name, the same accent")
        self.assertNotEqual(self.copy("web-app", "shop-2"), first, "numbered siblings differ")
        self.assertNotEqual(self.copy("web-app", "todo-list"), self.copy("web-app", "inventory"))

    def test_reboot_accent_wins(self) -> None:
        name = next(n for n in ("teal", "rose") if n != self.copy("web-app", "shop-1"))
        self.assertEqual(self.copy("web-app", "shop-1", REBOOT_ACCENT=name), name)
        css = (self.dest / "web/src/styles.css").read_text()
        self.assertIn(f"--accent: {PALETTES[name]['light']['accent']};", css)
        r = run("web-app", str(Path(self.tmp.name) / "x"), "shop-1", "todo_list", "Todo List",
                env={"REBOOT_ACCENT": "green"})
        self.assertEqual(r.returncode, 2)
        self.assertIn("names no palette", r.stderr)
        self.assertFalse((Path(self.tmp.name) / "x").exists(), "nothing was written")

    def test_every_accent_token_in_every_scheme_block_is_replaced(self) -> None:
        for front_door, sheets in STYLESHEETS.items():
            with self.subTest(front_door):
                self.assertEqual(self.copy(front_door, "shop-1", REBOOT_ACCENT="cyan"), "cyan")
                cyan = PALETTES["cyan"]
                for rel in sheets:
                    css = (self.dest / rel).read_text()
                    for name, value in cyan["light"].items():
                        self.assertEqual(css.count(f"--{name}: {value}"), 1, f"{rel} light --{name}")
                    for name, value in cyan["dark"].items():
                        self.assertEqual(css.count(f"--{name}: {value}"), 2, f"{rel} dark --{name}")
                leftovers = subprocess.run(
                    ["grep", "-rlE", "--exclude=accent.py", "|".join(v[1:] for v in VIOLET),
                     str(self.dest)], capture_output=True, text=True).stdout
                self.assertEqual(leftovers, "", "no violet left (but in the palette script)")
                for index in ("web/index.html", "frontend/web/index.html"):
                    if (self.dest / index).is_file():
                        self.assertIn(f"fill='%23{cyan['light']['accent'][1:]}'",
                                      (self.dest / index).read_text())

    def test_violet_leaves_the_template_as_it_is(self) -> None:
        self.copy("web-app", "shop-1", REBOOT_ACCENT="violet")
        template = COPY.parent / "web-app" / "web" / "src" / "styles.css"
        self.assertEqual((self.dest / "web/src/styles.css").read_text(), template.read_text())

    def test_a_merge_keeps_the_projects_stylesheet(self) -> None:
        sheet = self.dest / "web" / "src" / "styles.css"
        sheet.parent.mkdir(parents=True)
        sheet.write_text(":root { --accent: #123456; color-scheme: light; }\n")
        (self.dest / ".rbtrc").write_text("generate api/\n")
        r = run("--merge", "web-app", str(self.dest), "todo-list", "todo_list", "Todo List",
                env={"REBOOT_ACCENT": "teal"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("#123456", sheet.read_text())
        self.assertIn("Accent: unchanged", r.stdout)


if __name__ == "__main__":
    unittest.main()
