"""Tests for `hooks/schema-guard.sh`, the schema guard for Claude Code
and Codex.

The comparison rules are `hooks/schema-guard/schema.test.ts`, which the
first test runs on Node's test runner. The rest feed the hook the JSON
each agent sends and check whether it denies: Claude Code's Edit,
MultiEdit, Write and Read; Codex's `apply_patch` and its events (with
a `turn_id`, which Claude Code never sends for these); shell rewrites;
the rules counted as read line by line; and compaction.

The hook runs on the plugin's own Node (`bin/node`). The fast checks
have no network, so without a cached Node this skips itself;
`REBOOT_FETCH_NODE=1` (set by `tools/check-all.sh --full`) lets the
shim download it. Run from the repository root:
`python3 tests/hooks/schema_guard_test.py`.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOOK = os.path.join(ROOT, "hooks/schema-guard.sh")
RULES = os.path.join(ROOT, "skills/python/references/api-schema-evolution.md")


def node_available() -> bool:
    if os.environ.get("REBOOT_FETCH_NODE") == "1":
        return True
    with open(os.path.join(ROOT, "lib/install_node.sh")) as f:
        version = re.search(r'^NODE_VERSION="([^"]+)"', f.read(), re.M).group(1)
    cache = os.path.expanduser(f"~/.claude/plugins/data/reboot/bin/node-v{version}-*/bin/node")
    return bool(glob.glob(cache))


API = '''from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


class UserState(Model):
    count: int = Field(tag=1, default=0)
    label: str = Field(tag=2, default="")


api = API(
    User=Type(
        state=UserState,
        description="The signed-in user.",
        methods=Methods(
            get=Reader(
                request=None,
                response=None,
                description="Get the user's count.",
                mcp=None,
            ),
            increment=Writer(
                request=None,
                response=None,
                description="Add one.",
                mcp=None,
            ),
        ),
    ),
)
'''

ADD_FIELD = """*** Begin Patch
*** Update File: api/hello/v1/hello.py
@@ class UserState(Model):
     count: int = Field(tag=1, default=0)
     label: str = Field(tag=2, default="")
+    note: str = Field(tag=3, default="")
*** End Patch
"""

CHANGE_TYPE = """*** Begin Patch
*** Update File: api/hello/v1/hello.py
@@
-    count: int = Field(tag=1, default=0)
+    count: str = Field(tag=1, default="")
*** End Patch
"""

DELETE_METHOD = """*** Begin Patch
*** Update File: api/hello/v1/hello.py
@@ methods=Methods(
-            get=Reader(
-                request=None,
-                response=None,
-                description="Get the user's count.",
-                mcp=None,
-            ),
             increment=Writer(
*** End Patch
"""


@unittest.skipUnless(node_available(), "the plugin's Node isn't cached (REBOOT_FETCH_NODE=1 fetches it)")
class SchemaGuardTest(unittest.TestCase):

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        self.data = os.path.join(self.tmp, "data")
        self.project = os.path.join(self.tmp, "app")
        os.makedirs(os.path.join(self.project, "api/hello/v1"))
        os.makedirs(os.path.join(self.project, "backend/api/hello/v1"))
        with open(os.path.join(self.project, ".rbtrc"), "w") as f:
            f.write("dev run --application-name=hello\n")
        self.write("api/hello/v1/hello.py", API)
        self.write("backend/api/hello/v1/hello.py", API)
        self.session = "s1"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, text: str) -> None:
        with open(os.path.join(self.project, rel), "w") as f:
            f.write(text)

    def with_dev_state(self) -> None:
        os.makedirs(os.path.join(self.project, ".rbt/dev/hello"))

    def run_hook(self, payload: dict) -> str:
        payload = {
            "session_id": self.session,
            "turn_id": "t1",
            "cwd": self.project,
            **payload,
        }
        result = subprocess.run(
            ["sh", HOOK],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": ROOT, "PLUGIN_DATA": self.data},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def patch(self, patch: str) -> str:
        """The deny reason for an apply_patch call, or "" when it may run."""
        out = self.run_hook({
            "hook_event_name": "PreToolUse",
            "tool_name": "apply_patch",
            "tool_input": {"command": patch},
        })
        if not out.strip():
            return ""
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        return decision["permissionDecisionReason"]

    def bash(self, command: str) -> str:
        out = self.run_hook({
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })
        return json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"] if out.strip() else ""

    def ran(self, command: str, exit_code: int = 0) -> None:
        """A Bash call that has finished (PostToolUse)."""
        self.assertEqual(self.run_hook({
            "hook_event_name": "PostToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "tool_response": {"exit_code": exit_code},
        }), "")

    def test_the_comparison_rules(self) -> None:
        result = subprocess.run(
            [os.path.join(ROOT, "bin/node"), "--experimental-strip-types", "--no-warnings", "--test",
             os.path.join(ROOT, "hooks/schema-guard/schema.test.ts")],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_without_state_nothing_is_guarded(self) -> None:
        self.assertEqual(self.patch(CHANGE_TYPE), "")
        self.assertEqual(self.bash("sed -i 's/int/str/' api/hello/v1/hello.py"), "")

    def claude(self, tool: str, tool_input: dict, event: str = "PreToolUse") -> str:
        """The deny reason for a Claude Code call (no turn_id), or ""."""
        payload = {
            "session_id": self.session,
            "cwd": self.project,
            "hook_event_name": event,
            "tool_name": tool,
            "tool_input": tool_input,
        }
        result = subprocess.run(
            ["sh", HOOK], input=json.dumps(payload), capture_output=True, text=True, timeout=120,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": ROOT, "CLAUDE_PLUGIN_DATA": self.data},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return ""
        return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]

    def test_claude_code_edits_are_guarded(self) -> None:
        self.with_dev_state()
        api = os.path.join(self.project, "api/hello/v1/hello.py")
        change_type = {"file_path": api, "old_string": "count: int = Field(tag=1, default=0)",
                       "new_string": 'count: str = Field(tag=1, default="")'}
        add_field = {"file_path": api, "old_string": '    label: str = Field(tag=2, default="")\n',
                     "new_string": '    label: str = Field(tag=2, default="")\n    note: str = Field(tag=3, default="")\n'}
        self.assertIn("changes type, int → str", self.claude("Edit", change_type))
        self.assertIn("Read all of", self.claude("Edit", add_field))
        self.assertIn("is deleted or renamed", self.claude("Write", {"file_path": api, "content": "x = 1\n"}))
        self.assertIn("changes type", self.claude("MultiEdit", {"file_path": api, "edits": [add_field, change_type]}))
        self.assertIn("with the Edit or Write tool", self.claude("Bash", {"command": "sed -i '' s/int/str/ api/hello/v1/hello.py"}))
        # A partial Read doesn't count; the rest of the file does.
        self.claude("Read", {"file_path": RULES, "offset": 1, "limit": 20}, event="PostToolUse")
        self.assertIn("Read all of", self.claude("Edit", add_field))
        self.claude("Read", {"file_path": RULES, "offset": 21}, event="PostToolUse")
        self.assertEqual(self.claude("Edit", add_field), "")
        self.assertEqual(self.claude("MultiEdit", {"file_path": api, "edits": [add_field]}), "")
        self.assertIn("changes type", self.claude("Edit", change_type))
        # A new API file and the generated copy are not guarded.
        self.assertEqual(self.claude("Write", {"file_path": os.path.join(self.project, "api/hello/v1/new.py"), "content": "x = 1\n"}), "")
        generated = os.path.join(self.project, "backend/api/hello/v1/hello.py")
        self.assertEqual(self.claude("Edit", {**change_type, "file_path": generated}), "")
        # Compaction forgets the rules here too.
        self.claude("PostCompact", {}, event="PostCompact")
        self.assertIn("Read all of", self.claude("Edit", add_field))

    def test_a_whole_read_in_claude_code(self) -> None:
        self.with_dev_state()
        api = os.path.join(self.project, "api/hello/v1/hello.py")
        self.claude("Read", {"file_path": RULES}, event="PostToolUse")
        self.assertEqual(self.claude("Write", {"file_path": api, "content": API + "\n# note\n"}), "")

    def test_an_incompatible_patch_is_refused_with_the_reason(self) -> None:
        self.with_dev_state()
        reason = self.patch(CHANGE_TYPE)
        self.assertIn("changes type, int → str", reason)
        self.assertIn("api/hello/v1/hello.py", reason)
        reason = self.patch(DELETE_METHOD)
        self.assertIn("method `User.get` is deleted or renamed", reason)

    def test_a_compatible_patch_waits_for_the_rules(self) -> None:
        self.with_dev_state()
        self.assertIn("Read all of", self.patch(ADD_FIELD))
        self.ran(f"cat {RULES}")
        self.assertEqual(self.patch(ADD_FIELD), "")
        # Incompatible stays refused after reading.
        self.assertIn("changes type", self.patch(CHANGE_TYPE))

    def test_a_production_deploy_counts_as_state(self) -> None:
        os.makedirs(os.path.join(self.project, "deploy"))
        self.write("deploy/ledger.jsonl", "{}\n")
        self.assertIn("a production deploy", self.patch(CHANGE_TYPE))

    def test_the_rules_count_as_read_once_every_line_is_shown(self) -> None:
        self.with_dev_state()
        with open(RULES) as f:
            total = len(f.read().splitlines())
        half = total // 2
        self.ran(f"sed -n '1,{half}p' {RULES}")
        self.assertIn("Read all of", self.patch(ADD_FIELD))
        self.ran(f"grep -n Field {RULES}")  # shows matches, not the file
        self.ran(f"sed -n '{half + 2},$p' {RULES}")  # one line still missing
        self.assertIn("Read all of", self.patch(ADD_FIELD))
        self.ran(f"cat {RULES} | head -n {half + 1}", exit_code=1)  # failed: doesn't count
        self.assertIn("Read all of", self.patch(ADD_FIELD))
        self.ran(f"nl -ba {RULES} | sed -n '{half},{half + 1}p'")
        self.assertEqual(self.patch(ADD_FIELD), "")

    def test_compaction_forgets_the_rules(self) -> None:
        self.with_dev_state()
        self.ran(f"cat {RULES}")
        self.assertEqual(self.patch(ADD_FIELD), "")
        self.run_hook({"hook_event_name": "PostCompact", "trigger": "auto"})
        self.assertIn("Read all of", self.patch(ADD_FIELD))

    def test_another_session_has_not_read_them(self) -> None:
        self.with_dev_state()
        self.ran(f"cat {RULES}")
        self.session = "s2"
        self.assertIn("Read all of", self.patch(ADD_FIELD))

    def test_paths_heredocs_new_files_and_generated_code(self) -> None:
        self.with_dev_state()
        absolute = ADD_FIELD.replace("api/hello/v1/hello.py", f"{self.project}/api/hello/v1/hello.py")
        self.assertIn("Read all of", self.patch(absolute))
        heredoc = f"apply_patch <<'EOF'\n{CHANGE_TYPE}EOF\n"
        self.assertIn("changes type", self.patch(heredoc))
        new_file = "*** Begin Patch\n*** Add File: api/hello/v1/other.py\n+x = 1\n*** End Patch\n"
        self.assertEqual(self.patch(new_file), "")
        generated = CHANGE_TYPE.replace("api/hello/v1/hello.py", "backend/api/hello/v1/hello.py")
        self.assertEqual(self.patch(generated), "")
        elsewhere = "*** Begin Patch\n*** Update File: README.md\n+x\n*** End Patch\n"
        self.assertEqual(self.patch(elsewhere), "")

    def test_deleting_or_moving_an_api_file_is_refused(self) -> None:
        self.with_dev_state()
        self.ran(f"cat {RULES}")
        reason = self.patch("*** Begin Patch\n*** Delete File: api/hello/v1/hello.py\n*** End Patch\n")
        self.assertIn("state type `User` is deleted or renamed", reason)
        moved = ADD_FIELD.replace(
            "*** Update File: api/hello/v1/hello.py\n",
            "*** Update File: api/hello/v1/hello.py\n*** Move to: api/hello/v1/greeting.py\n",
        )
        self.assertIn("is moved to `api/hello/v1/greeting.py`", self.patch(moved))

    def test_a_patch_that_does_not_apply_is_left_to_apply_patch(self) -> None:
        self.with_dev_state()
        stale = CHANGE_TYPE.replace("-    count: int", "-    total: int")
        self.assertEqual(self.patch(stale), "")

    def test_shell_rewrites_of_an_api_file_are_refused(self) -> None:
        self.with_dev_state()
        for command in [
            "sed -i '' 's/int/str/' api/hello/v1/hello.py",
            "cat new.py > api/hello/v1/hello.py",
            "mv api/hello/v1/hello.py /tmp/",
            "git checkout HEAD~1 -- api/hello/v1/hello.py",
        ]:
            with self.subTest(command=command):
                self.assertIn("with apply_patch", self.bash(command))
        for command in ["cat api/hello/v1/hello.py", "sed -n '1,20p' api/hello/v1/hello.py", "ls"]:
            with self.subTest(command=command):
                self.assertEqual(self.bash(command), "")


if __name__ == "__main__":
    unittest.main()
