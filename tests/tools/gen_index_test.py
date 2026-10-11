#!/usr/bin/env python3
"""Tests for `tools/gen-index.py`'s reading-list invariant: a reference
with a build step (api to tests) on no reading list or always list is
an error; one reached through a router (via:) is not; step any, run or
deploy on no list is one warning, not an error and not two warnings;
and the real tree has no such error.

    python3 tests/tools/gen_index_test.py
"""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location("gen_index", TOOLS / "gen-index.py")
gen_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_index)
from reflib import SKILLS, Ref  # noqa: E402


def ref(name: str, **fm) -> Ref:
    return Ref(SKILLS / "python" / "references" / name, fm)


class OffListTest(unittest.TestCase):
    def test_build_step_off_every_list_is_an_error(self) -> None:
        errors, warnings = gen_index.off_list_problems([ref("rpc-x.md", step="servicer")], set())
        self.assertEqual(len(errors), 1)
        self.assertIn("python/references/rpc-x.md: step servicer", errors[0])
        self.assertEqual(warnings, [])

    def test_build_step_on_a_list_passes(self) -> None:
        r = ref("rpc-x.md", step="api")
        self.assertEqual(gen_index.off_list_problems([r], {r.rel}), ([], []))

    def test_routed_reference_passes(self) -> None:
        r = ref("rpc-x.md", step="frontend", via="rpc-router.md")
        self.assertEqual(gen_index.off_list_problems([r], set()), ([], []))

    def test_any_run_deploy_warn_once(self) -> None:
        refs = [ref(f"lifecycle-{s}.md", step=s) for s in ("any", "run", "deploy")]
        errors, warnings = gen_index.off_list_problems(refs, set())
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 3)

    def test_no_double_warning(self) -> None:
        # A file off every index that the reading-list check already
        # reported gets no second "not listed" warning.
        class TmpRef(Ref):
            rel = "python/references/lifecycle-y.md"

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lifecycle-y.md"
            path.write_text("---\nstep: deploy\n---\n")
            _, warnings = gen_index.check_invariants([TmpRef(path, {"step": "deploy"})], set(), set())
        mine = [w for w in warnings if w.startswith(TmpRef.rel) and "docs:" not in w]
        self.assertEqual(mine, [f"{TmpRef.rel}: step deploy, on no reading list"])

    def test_tree_has_no_off_list_error(self) -> None:
        out = subprocess.run([sys.executable, str(TOOLS / "gen-index.py"), "--check", "--quiet"],
                             capture_output=True, text=True).stdout
        self.assertNotIn("on no reading list (check", out)


if __name__ == "__main__":
    unittest.main()
